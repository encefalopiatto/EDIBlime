# -*- coding: utf-8 -*-
"""
Structural validation and repair of EDI envelopes.

Checks the control structures that every EDI dialect builds in for integrity
verification -- segment counts, message counts and control-reference echoes:

* EDIFACT:   UNH/UNT segment count + reference, UNB/UNZ count + reference,
             UNG/UNE group count + reference, unclosed messages/groups.
* X12:       ST/SE segment count + control number, GS/GE transaction count +
             control number, ISA/IEA group count + control number, unclosed
             transaction sets/groups, ST outside a functional group.
* TRADACOMS: MHD/MTR segment count, MHD sequence numbering, END message count.
* HL7:       MSH placement and encoding declaration sanity.

:func:`repair` recomputes the counts and re-syncs the control references, so a
hand-edited message can be made consistent again in one step.

Like :mod:`edi_core`, this module has no Sublime Text dependency.
Issues are returned as dicts: ``{"offset", "severity", "message"}`` where
``severity`` is ``"error"``, ``"warning"`` or ``"info"`` and ``offset`` is a
character offset into the original text (for editor navigation).
"""

from . import edi_core
from . import edi_data


def validate(text, dialect=None):
    """Validate ``text`` and return a list of issue dicts (empty = clean)."""
    dialect = dialect or edi_core.detect(text)
    if dialect is None:
        return [_issue(0, "error", "Could not detect an EDI dialect")]

    spans = dialect.segment_spans(text)
    if not spans:
        return [_issue(0, "error", "No segments found")]

    issues = []
    if dialect.family == "edifact":
        _validate_edifact(spans, issues)
    elif dialect.family == "x12":
        _validate_x12(spans, issues)
    elif dialect.family == "tradacoms":
        _validate_tradacoms(spans, issues)
    elif dialect.family == "hl7":
        _validate_hl7(spans, issues)

    _flag_unknown_tags(dialect, spans, issues)
    return issues


def _issue(offset, severity, message):
    return {"offset": offset, "severity": severity, "message": message}


def _first(seg, index):
    """First component of element ``index`` (0-based), or '' when absent."""
    elements = seg.elements()
    if index < len(elements) and elements[index]:
        return elements[index][0]
    return ""


def _to_int(value):
    """Parse an ASCII decimal count. Returns ``None`` for anything else.

    ``str.isdigit()`` alone is unsafe: it accepts Unicode digits (e.g. ``²``)
    that ``int()`` rejects, which would crash the validator on odd input.
    """
    value = value.strip()
    if value and all("0" <= c <= "9" for c in value):
        return int(value)
    return None


def _check_count(issues, offset, declared, actual, what_declares, what_contains):
    """Compare a declared count against reality, flagging non-numeric values."""
    n = _to_int(declared)
    if n is None:
        issues.append(_issue(
            offset, "warning",
            "%s declares a non-numeric count '%s'" % (what_declares, declared)))
    elif n != actual:
        issues.append(_issue(
            offset, "error",
            "%s declares %s %s but it contains %d"
            % (what_declares, declared, what_contains, actual)))


def _flag_unknown_tags(dialect, spans, issues):
    for start, _end, seg in spans:
        if not edi_data.segment_name(dialect.key, seg.tag):
            issues.append(_issue(
                start, "info",
                "Unknown segment tag '%s' (no reference data; may still be valid)"
                % seg.tag))


# ---------------------------------------------------------------------------
# EDIFACT
# ---------------------------------------------------------------------------

def _validate_edifact(spans, issues):
    unb = None
    message_count = 0
    group_count = 0
    unh = None           # [offset, ref, segment_count_so_far]
    ung = None           # [offset, ref, messages_in_group]
    saw_unz = False

    for start, _end, seg in spans:
        tag = seg.tag
        if unh is not None:
            unh[2] += 1

        if tag == "UNB":
            unb = (start, _first(seg, 4))
        elif tag == "UNG":
            if ung is not None:
                issues.append(_issue(
                    start, "error",
                    "UNG found before the previous group was closed by UNE"))
            group_count += 1
            ung = [start, _first(seg, 4), 0]
        elif tag == "UNE":
            if ung is None:
                issues.append(_issue(start, "error", "UNE without a matching UNG"))
                continue
            _check_count(issues, start, _first(seg, 0), ung[2],
                         "UNE", "messages in the group")
            ref = _first(seg, 1)
            if ref != ung[1]:
                issues.append(_issue(
                    start, "error",
                    "UNE reference '%s' does not match UNG reference '%s'"
                    % (ref, ung[1])))
            ung = None
        elif tag == "UNH":
            if unh is not None:
                issues.append(_issue(
                    start, "error",
                    "UNH found before the previous message was closed by UNT"))
            message_count += 1
            if ung is not None:
                ung[2] += 1
            unh = [start, _first(seg, 0), 1]  # counts UNH itself
        elif tag == "UNT":
            if unh is None:
                issues.append(_issue(start, "error", "UNT without a matching UNH"))
                continue
            _check_count(issues, start, _first(seg, 0), unh[2],
                         "UNT", "segments")
            ref = _first(seg, 1)
            if ref != unh[1]:
                issues.append(_issue(
                    start, "error",
                    "UNT reference '%s' does not match UNH reference '%s'"
                    % (ref, unh[1])))
            unh = None
        elif tag == "UNZ":
            saw_unz = True
            expected = group_count if group_count else message_count
            _check_count(issues, start, _first(seg, 0), expected,
                         "UNZ", "groups" if group_count else "messages")
            ref = _first(seg, 1)
            if unb is not None and ref != unb[1]:
                issues.append(_issue(
                    start, "error",
                    "UNZ control reference '%s' does not match UNB reference '%s'"
                    % (ref, unb[1])))

    if unh is not None:
        issues.append(_issue(unh[0], "error", "UNH message is never closed by UNT"))
    if ung is not None:
        issues.append(_issue(ung[0], "error", "UNG group is never closed by UNE"))
    if unb is not None and not saw_unz:
        issues.append(_issue(unb[0], "error", "UNB interchange is never closed by UNZ"))


# ---------------------------------------------------------------------------
# X12
# ---------------------------------------------------------------------------

def _validate_x12(spans, issues):
    isa = None          # (offset, control_number)
    gs = None           # [offset, control_number, txn_count]
    st = None           # [offset, control_number, segment_count]
    group_count = 0
    saw_iea = False

    for start, _end, seg in spans:
        tag = seg.tag
        if st is not None:
            st[2] += 1

        if tag == "ISA":
            isa = (start, _first(seg, 12).strip())
        elif tag == "GS":
            if gs is not None:
                issues.append(_issue(
                    start, "error",
                    "GS found before the previous group was closed by GE"))
            group_count += 1
            gs = [start, _first(seg, 5), 0]
        elif tag == "ST":
            if st is not None:
                issues.append(_issue(
                    start, "error",
                    "ST found before the previous transaction set was closed by SE"))
            if gs is None:
                issues.append(_issue(
                    start, "warning",
                    "ST outside any functional group (no open GS)"))
            else:
                gs[2] += 1
            st = [start, _first(seg, 1), 1]  # counts ST itself
        elif tag == "SE":
            if st is None:
                issues.append(_issue(start, "error", "SE without a matching ST"))
                continue
            _check_count(issues, start, _first(seg, 0), st[2],
                         "SE", "segments in the transaction set")
            ctrl = _first(seg, 1)
            if ctrl != st[1]:
                issues.append(_issue(
                    start, "error",
                    "SE control number '%s' does not match ST control number '%s'"
                    % (ctrl, st[1])))
            st = None
        elif tag == "GE":
            if gs is None:
                issues.append(_issue(start, "error", "GE without a matching GS"))
                continue
            _check_count(issues, start, _first(seg, 0), gs[2],
                         "GE", "transaction sets in the group")
            ctrl = _first(seg, 1)
            if ctrl != gs[1]:
                issues.append(_issue(
                    start, "error",
                    "GE control number '%s' does not match GS control number '%s'"
                    % (ctrl, gs[1])))
            gs = None
        elif tag == "IEA":
            saw_iea = True
            _check_count(issues, start, _first(seg, 0), group_count,
                         "IEA", "functional groups in the interchange")
            ctrl = _first(seg, 1).strip()
            if isa is not None and ctrl != isa[1]:
                issues.append(_issue(
                    start, "error",
                    "IEA control number '%s' does not match ISA control number '%s'"
                    % (ctrl, isa[1])))

    if st is not None:
        issues.append(_issue(st[0], "error", "ST transaction set is never closed by SE"))
    if gs is not None:
        issues.append(_issue(gs[0], "error", "GS functional group is never closed by GE"))
    if isa is not None and not saw_iea:
        issues.append(_issue(isa[0], "error", "ISA interchange is never closed by IEA"))


# ---------------------------------------------------------------------------
# TRADACOMS
# ---------------------------------------------------------------------------

def _validate_tradacoms(spans, issues):
    mhd = None          # [offset, sequence, segment_count]
    message_count = 0
    expected_seq = 1
    saw_end = False
    saw_stx = False

    for start, _end, seg in spans:
        tag = seg.tag
        if mhd is not None:
            mhd[2] += 1

        if tag == "STX":
            saw_stx = True
        elif tag == "MHD":
            if mhd is not None:
                issues.append(_issue(
                    start, "error",
                    "MHD found before the previous message was closed by MTR"))
            message_count += 1
            seq = _first(seg, 0)
            seq_n = _to_int(seq)
            if seq_n is not None and seq_n != expected_seq:
                issues.append(_issue(
                    start, "warning",
                    "MHD sequence number %s out of order (expected %d)"
                    % (seq, expected_seq)))
            expected_seq += 1
            mhd = [start, seq, 1]  # counts MHD itself
        elif tag == "MTR":
            if mhd is None:
                issues.append(_issue(start, "error", "MTR without a matching MHD"))
                continue
            _check_count(issues, start, _first(seg, 0), mhd[2],
                         "MTR", "segments in the message")
            mhd = None
        elif tag == "END":
            saw_end = True
            _check_count(issues, start, _first(seg, 0), message_count,
                         "END", "messages in the transmission")

    if mhd is not None:
        issues.append(_issue(mhd[0], "error", "MHD message is never closed by MTR"))
    if saw_stx and not saw_end:
        issues.append(_issue(0, "error", "STX transmission is never closed by END"))


# ---------------------------------------------------------------------------
# HL7
# ---------------------------------------------------------------------------

def _validate_hl7(spans, issues):
    for i, (start, _end, seg) in enumerate(spans):
        if i == 0:
            if seg.tag != "MSH":
                issues.append(_issue(
                    start, "error", "First segment must be MSH, found '%s'" % seg.tag))
            elif len(seg.content) < 8:
                issues.append(_issue(
                    start, "error",
                    "MSH is too short to declare the encoding characters"))
        elif seg.tag == "MSH":
            # A second MSH means a new message batched in the same buffer;
            # legal, just point it out.
            issues.append(_issue(start, "info", "Additional message starts here (MSH)"))
        if len(seg.content) < 3 or not seg.tag.isalnum():
            issues.append(_issue(
                start, "warning", "Segment name '%s' is malformed" % seg.content[:3]))


# ---------------------------------------------------------------------------
# Repair: recompute counts and re-sync control references
# ---------------------------------------------------------------------------

def repair(text, dialect=None):
    """Recompute envelope counts and control references in ``text``.

    Fixes UNT/UNZ/UNE (EDIFACT), SE/GE/IEA (X12) and MTR/END (TRADACOMS)
    counts, and re-syncs the trailer references to their matching headers
    (UNT<-UNH, UNZ<-UNB, UNE<-UNG, SE<-ST, GE<-GS, IEA<-ISA). HL7 has no
    counted envelope, so it is returned unchanged.

    Returns ``(fixed_text, changed_segment_count)``. Only the affected
    trailer segments are rewritten; formatting elsewhere is untouched.
    """
    dialect = dialect or edi_core.detect(text)
    if dialect is None:
        return text, 0
    spans = dialect.segment_spans(text)
    fixes = {}  # span index -> [(element_index, new_raw_value), ...]

    family = dialect.family
    if family == "edifact":
        _repair_edifact(spans, fixes)
    elif family == "x12":
        _repair_x12(spans, fixes)
    elif family == "tradacoms":
        _repair_tradacoms(spans, fixes)
    if not fixes:
        return text, 0

    out = []
    last = 0
    changed = 0
    for idx, (start, end, seg) in enumerate(spans):
        if idx not in fixes:
            continue
        raw = seg.raw_elements()
        for element_index, value in fixes[idx]:
            while len(raw) <= element_index:
                raw.append("")
            raw[element_index] = value
        rebuilt = seg.with_raw_elements(raw)
        if rebuilt != seg.content:
            out.append(text[last:start])
            out.append(rebuilt)
            last = end
            changed += 1
    out.append(text[last:])
    return "".join(out), changed


def _repair_edifact(spans, fixes):
    unb_ref = None
    unh = None           # [ref, count]
    ung_ref = None
    ung_messages = 0
    message_count = 0
    group_count = 0

    for idx, (_s, _e, seg) in enumerate(spans):
        tag = seg.tag
        if unh is not None:
            unh[1] += 1
        if tag == "UNB":
            unb_ref = _first(seg, 4)
        elif tag == "UNG":
            group_count += 1
            ung_ref = _first(seg, 4)
            ung_messages = 0
        elif tag == "UNE":
            fix = [(0, str(ung_messages))]
            if ung_ref:
                fix.append((1, ung_ref))
            fixes[idx] = fix
        elif tag == "UNH":
            message_count += 1
            ung_messages += 1
            unh = [_first(seg, 0), 1]
        elif tag == "UNT":
            if unh is not None:
                fixes[idx] = [(0, str(unh[1])), (1, unh[0])]
                unh = None
        elif tag == "UNZ":
            fix = [(0, str(group_count if group_count else message_count))]
            if unb_ref:
                fix.append((1, unb_ref))
            fixes[idx] = fix


def _repair_x12(spans, fixes):
    isa_ctrl = None
    st = None            # [ctrl, count]
    gs_ctrl = None
    gs_txns = 0
    group_count = 0

    for idx, (_s, _e, seg) in enumerate(spans):
        tag = seg.tag
        if st is not None:
            st[1] += 1
        if tag == "ISA":
            # Keep the raw (padded) value so IEA02 matches byte for byte.
            raw = seg.raw_elements()
            isa_ctrl = raw[12] if len(raw) > 12 else None
        elif tag == "GS":
            group_count += 1
            gs_ctrl = _first(seg, 5)
            gs_txns = 0
        elif tag == "ST":
            gs_txns += 1
            st = [_first(seg, 1), 1]
        elif tag == "SE":
            if st is not None:
                fixes[idx] = [(0, str(st[1])), (1, st[0])]
                st = None
        elif tag == "GE":
            fix = [(0, str(gs_txns))]
            if gs_ctrl:
                fix.append((1, gs_ctrl))
            fixes[idx] = fix
        elif tag == "IEA":
            fix = [(0, str(group_count))]
            if isa_ctrl is not None:
                fix.append((1, isa_ctrl))
            fixes[idx] = fix


def _repair_tradacoms(spans, fixes):
    mhd_count = None
    message_count = 0

    for idx, (_s, _e, seg) in enumerate(spans):
        tag = seg.tag
        if mhd_count is not None:
            mhd_count += 1
        if tag == "MHD":
            message_count += 1
            mhd_count = 1
        elif tag == "MTR":
            if mhd_count is not None:
                fixes[idx] = [(0, str(mhd_count))]
                mhd_count = None
        elif tag == "END":
            fixes[idx] = [(0, str(message_count))]
