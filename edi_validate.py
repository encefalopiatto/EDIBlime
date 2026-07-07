# -*- coding: utf-8 -*-
"""
Structural validation of EDI envelopes.

Checks the control structures that every EDI dialect builds in for integrity
verification -- segment counts, message counts and control-reference echoes:

* EDIFACT:   UNH/UNT segment count + reference, UNB/UNZ count + reference,
             UNG/UNE when functional groups are used.
* X12:       ST/SE segment count + control number, GS/GE transaction count +
             control number, ISA/IEA group count + control number.
* TRADACOMS: MHD/MTR segment count, MHD sequence numbering, END message count.
* HL7:       MSH placement and encoding declaration sanity.

Like :mod:`edi_core`, this module has no Sublime Text dependency.
Issues are returned as dicts: ``{"offset", "severity", "message"}`` where
``severity`` is ``"error"``, ``"warning"`` or ``"info"`` and ``offset`` is a
character offset into the original text (for editor navigation).
"""

try:
    from . import edi_core
    from . import edi_data
except (ImportError, ValueError):
    import edi_core
    import edi_data


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
    unh = None           # (offset, ref, segment_count_so_far)
    saw_unz = False

    for start, _end, seg in spans:
        tag = seg.tag
        if unh is not None:
            unh[2] += 1

        if tag == "UNB":
            unb = (start, _first(seg, 4))
        elif tag == "UNG":
            group_count += 1
        elif tag == "UNH":
            if unh is not None:
                issues.append(_issue(
                    start, "error",
                    "UNH found before the previous message was closed by UNT"))
            message_count += 1
            unh = [start, _first(seg, 0), 1]  # counts UNH itself
        elif tag == "UNT":
            if unh is None:
                issues.append(_issue(start, "error", "UNT without a matching UNH"))
                continue
            declared = _first(seg, 0)
            actual = unh[2]
            if declared.isdigit() and int(declared) != actual:
                issues.append(_issue(
                    start, "error",
                    "UNT declares %s segments but the message contains %d"
                    % (declared, actual)))
            ref = _first(seg, 1)
            if ref != unh[1]:
                issues.append(_issue(
                    start, "error",
                    "UNT reference '%s' does not match UNH reference '%s'"
                    % (ref, unh[1])))
            unh = None
        elif tag == "UNZ":
            saw_unz = True
            declared = _first(seg, 0)
            expected = group_count if group_count else message_count
            if declared.isdigit() and int(declared) != expected:
                issues.append(_issue(
                    start, "error",
                    "UNZ declares %s %s but the interchange contains %d"
                    % (declared,
                       "groups" if group_count else "messages", expected)))
            ref = _first(seg, 1)
            if unb is not None and ref != unb[1]:
                issues.append(_issue(
                    start, "error",
                    "UNZ control reference '%s' does not match UNB reference '%s'"
                    % (ref, unb[1])))

    if unh is not None:
        issues.append(_issue(unh[0], "error", "UNH message is never closed by UNT"))
    if unb is not None and not saw_unz:
        issues.append(_issue(unb[0], "error", "UNB interchange is never closed by UNZ"))


# ---------------------------------------------------------------------------
# X12
# ---------------------------------------------------------------------------

def _validate_x12(spans, issues):
    isa = None          # (offset, control_number)
    gs = None           # (offset, control_number, txn_count)
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
            group_count += 1
            gs = [start, _first(seg, 5), 0]
        elif tag == "ST":
            if gs is not None:
                gs[2] += 1
            st = [start, _first(seg, 1), 1]  # counts ST itself
        elif tag == "SE":
            if st is None:
                issues.append(_issue(start, "error", "SE without a matching ST"))
                continue
            declared = _first(seg, 0)
            if declared.isdigit() and int(declared) != st[2]:
                issues.append(_issue(
                    start, "error",
                    "SE declares %s segments but the transaction set contains %d"
                    % (declared, st[2])))
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
            declared = _first(seg, 0)
            if declared.isdigit() and int(declared) != gs[2]:
                issues.append(_issue(
                    start, "error",
                    "GE declares %s transaction sets but the group contains %d"
                    % (declared, gs[2])))
            ctrl = _first(seg, 1)
            if ctrl != gs[1]:
                issues.append(_issue(
                    start, "error",
                    "GE control number '%s' does not match GS control number '%s'"
                    % (ctrl, gs[1])))
            gs = None
        elif tag == "IEA":
            saw_iea = True
            declared = _first(seg, 0)
            if declared.isdigit() and int(declared) != group_count:
                issues.append(_issue(
                    start, "error",
                    "IEA declares %s functional groups but the interchange contains %d"
                    % (declared, group_count)))
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
            if seq.isdigit() and int(seq) != expected_seq:
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
            declared = _first(seg, 0)
            if declared.isdigit() and int(declared) != mhd[2]:
                issues.append(_issue(
                    start, "error",
                    "MTR declares %s segments but the message contains %d"
                    % (declared, mhd[2])))
            mhd = None
        elif tag == "END":
            saw_end = True
            declared = _first(seg, 0)
            if declared.isdigit() and int(declared) != message_count:
                issues.append(_issue(
                    start, "error",
                    "END declares %s messages but the transmission contains %d"
                    % (declared, message_count)))

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
