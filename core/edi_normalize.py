# -*- coding: utf-8 -*-
"""
Normalize EDI messages into structured, named JSON.

Where :mod:`edi_convert` is *structural* (a flat list of segments with
positional elements), this module is *semantic*: it produces the kind of JSON
an integration platform works with -- every segment, composite and element
keyed by its official name from the standard, and the envelope hierarchy
(interchange -> functional group -> message) turned into real nesting.

For the EDIFACT family the keys come from the UN/EDIFACT directories
(UNTDID): a key is the snake_cased official name followed by the code that
names it in the standard -- segment tags (``beginning_of_message_BGM``),
composite data elements (``document_message_name_C002``) and simple data
elements (``document_message_number_1004``). Service segments/elements (UNB,
UNH, S001, 0020, ...) follow ISO 9735. For X12, TRADACOMS and HL7 the same
convention is applied with positional suffixes (``purchase_order_number_03``)
because those standards name elements by segment position.

Output shape (mirrors one payload per interchange)::

    {
      "payloads": [
        {
          "interchange_header_UNB": {...},
          "messages": [
            {
              "MESSAGE_TYPE": "SLSRPT",
              "message_header_UNH": {...},
              "beginning_of_message_BGM": {...},
              "date_time_period_DTM_list": [...],
              "name_and_address_NAD_groups": [{...}],
              "message_trailer_UNT": {...}
            }
          ],
          "interchange_trailer_UNZ": {...}
        }
      ],
      "context": {}
    }

Structure rules:

* A segment the message definition allows only once is a plain object; a
  repeatable segment becomes a ``..._list`` array (always an array, even when
  only one occurrence is present, so downstream consumers see a stable shape).
* An EDIFACT segment group becomes a ``..._groups`` array named after its
  trigger segment; each instance nests its own segments and sub-groups. Group
  nesting follows the official message definitions vendored in
  :mod:`edi_norm_data` (D.96A segment tables). Messages without a vendored
  definition degrade gracefully: every segment becomes a ``..._list`` entry at
  message level, in document order.
* Empty elements/components are omitted. All values stay strings (leading
  zeros and implied decimals survive). Release characters are resolved, HL7
  escapes decoded; repetition separators are not expanded (a repeated field
  arrives verbatim), matching :mod:`edi_convert`.
* Unknown segments/elements never fail: they fall back to ``tag``-derived
  keys (``xyz_XYZ``, ``element_3``), and segments found where the envelope
  does not allow them are collected under ``unparsed_segments`` as raw text
  so no data is silently dropped.
"""

import json

from . import edi_core
from . import edi_norm_data


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def normalize(text, dialect=None):
    """Parse ``text`` and return the normalized tree (dicts/lists/strings).

    Raises ``ValueError`` when the text is not recognisable EDI.
    """
    dialect = dialect or edi_core.detect(text)
    if dialect is None:
        raise ValueError("could not detect an EDI dialect")
    segments = dialect.split_segments(text)
    family = dialect.family

    if family == "edifact":
        payloads = _edifact_payloads(segments)
    elif family == "x12":
        payloads = _x12_payloads(segments)
    elif family == "tradacoms":
        payloads = _tradacoms_payloads(segments)
    elif family == "hl7":
        payloads = _hl7_payloads(segments)
    else:  # pragma: no cover -- every dialect maps to a family above
        raise ValueError("no normalizer for dialect %r" % dialect.label)

    return {"payloads": payloads, "context": {}}


def to_json(text, dialect=None, indent=2):
    """Normalize ``text`` and render it as a pretty-printed JSON document."""
    tree = normalize(text, dialect)
    return json.dumps(tree, indent=indent, ensure_ascii=False) + "\n"


# ---------------------------------------------------------------------------
# Shared helpers
# ---------------------------------------------------------------------------

def _append(container, key, value):
    """Append ``value`` to the list at ``container[key]``, creating it."""
    existing = container.get(key)
    if existing is None:
        container[key] = [value]
    else:
        existing.append(value)


def _dedup_keys(bases):
    """Make a list of key names unique, position-stable.

    A repeated name -- e.g. the two C504 currency composites of CUX or the
    five 3124 address lines of C058 -- gets an occurrence suffix
    (``currency_details_C504``, ``currency_details_C504_2``) determined by
    its *position in the definition*, so a key never changes meaning based on
    which occurrences happen to be present in the data.
    """
    seen = {}
    keys = []
    for base in bases:
        seen[base] = seen.get(base, 0) + 1
        keys.append(base if seen[base] == 1 else "%s_%d" % (base, seen[base]))
    return keys


def _position_keys(pairs):
    """``[(code, name), ...]`` -> unique ``name_code`` JSON keys."""
    return _dedup_keys(["%s_%s" % (name, code) for code, name in pairs])


def _value_or_list(components):
    """Collapse a component list: one component -> string, several -> list.

    Multi-component values are kept verbatim (including inner empties) so
    positional meaning survives even without a definition to name them.
    """
    if len(components) == 1:
        return components[0]
    return list(components)


def _is_empty(components):
    return all(c == "" for c in components)


def _seg_key(tag, defs):
    entry = defs.get(tag)
    name = entry[0] if entry else tag.lower()
    return "%s_%s" % (name, tag)


def _flat_append(message, seg, seg_object, defs):
    _append(message, _seg_key(seg.tag, defs) + "_list", seg_object)


def _unparsed(container, seg):
    """Record a segment the envelope grammar has no place for."""
    _append(container, "unparsed_segments", seg.content)


# ---------------------------------------------------------------------------
# EDIFACT (and its subsets: EANCOM, ODETTE, EDIG@S, IATA/PADIS)
# ---------------------------------------------------------------------------

_EDIFACT_DEFS = edi_norm_data.EDIFACT_ALL_SEGMENT_DEFS
_EDIFACT_STRUCTURES = edi_norm_data.EDIFACT_MESSAGE_STRUCTURES


# Key lists per segment tag are static; cache them so large documents
# (a sales report can carry thousands of LIN groups) compute them once.
_EDIFACT_KEY_CACHE = {}


def _edifact_keys(tag, positions):
    cached = _EDIFACT_KEY_CACHE.get(tag)
    if cached is None:
        pos_keys = _position_keys([(p[0], p[1]) for p in positions])
        comp_keys = [
            _position_keys([(c[0], c[1]) for c in p[2]]) if len(p) == 3 else None
            for p in positions
        ]
        cached = (pos_keys, comp_keys)
        _EDIFACT_KEY_CACHE[tag] = cached
    return cached


def _edifact_segment_object(seg):
    """Build the named object for one EDIFACT segment.

    Composites always nest (the definition decides, not the data), simple
    elements map to plain string values, and anything beyond the definition
    falls back to positional ``element_N`` keys.
    """
    entry = _EDIFACT_DEFS.get(seg.tag)
    positions = entry[1] if entry else ()
    pos_keys, all_comp_keys = _edifact_keys(seg.tag, positions)
    obj = {}
    for idx, components in enumerate(seg.elements()):
        if _is_empty(components):
            continue
        pos = positions[idx] if idx < len(positions) else None
        if pos is None:
            obj["element_%d" % (idx + 1)] = _value_or_list(components)
        elif len(pos) == 3:  # composite: (code, name, ((code, name), ...))
            comp_keys = all_comp_keys[idx]
            sub = {}
            for ci, component in enumerate(components):
                if component == "":
                    continue
                if ci < len(comp_keys):
                    sub[comp_keys[ci]] = component
                else:
                    sub["component_%d" % (ci + 1)] = component
            if sub:
                obj[pos_keys[idx]] = sub
        else:  # simple element: (code, name)
            obj[pos_keys[idx]] = _value_or_list(components)
    return obj


def _edifact_parse_level(entries, segs, i, out):
    """Recursive-descent match of ``segs[i:]`` against a message definition.

    ``entries`` come from ``EDIFACT_MESSAGE_STRUCTURES``: ``(tag, max)`` for
    a segment position, ``("SG", max, (children...))`` for a segment group
    whose first child is the trigger. Returns the index of the first segment
    that did not fit this level.
    """
    n = len(segs)
    for entry in entries:
        if entry[0] == "SG":
            children = entry[2]
            trigger = children[0][0]
            key = _seg_key(trigger, _EDIFACT_DEFS) + "_groups"
            while i < n and segs[i].tag == trigger:
                group = {}
                j = _edifact_parse_level(children, segs, i, group)
                if j == i:  # no progress: malformed definition, bail out
                    return i
                i = j
                _append(out, key, group)
        else:
            tag, max_repeat = entry
            key = _seg_key(tag, _EDIFACT_DEFS)
            if max_repeat > 1:
                while i < n and segs[i].tag == tag:
                    _append(out, key + "_list", _edifact_segment_object(segs[i]))
                    i += 1
            elif i < n and segs[i].tag == tag:
                out[key] = _edifact_segment_object(segs[i])
                i += 1
    return i


def _edifact_message(segs):
    """Build one message object from the ``UNH .. UNT`` segment run."""
    unh = segs[0]
    elements = unh.elements()
    msg_type = ""
    if len(elements) > 1 and elements[1]:
        msg_type = elements[1][0]

    message = {}
    if msg_type:
        message["MESSAGE_TYPE"] = msg_type
    message["message_header_UNH"] = _edifact_segment_object(unh)

    body = list(segs[1:])
    trailer = None
    if body and body[-1].tag == "UNT":
        trailer = body.pop()

    structure = _EDIFACT_STRUCTURES.get(msg_type)
    if structure:
        consumed = _edifact_parse_level(structure, body, 0, message)
        leftover = body[consumed:]
    else:
        leftover = body
    # Segments the message definition could not place (or the whole body when
    # the message type has no vendored definition) keep document order as
    # deterministic ``_list`` entries -- nothing is dropped.
    for seg in leftover:
        _flat_append(message, seg, _edifact_segment_object(seg), _EDIFACT_DEFS)

    if trailer is not None:
        message["message_trailer_UNT"] = _edifact_segment_object(trailer)
    return message


def _edifact_payloads(segments):
    payloads = []
    payload = None
    group = None      # open UNG..UNE functional group
    msg_buf = None    # segments of the currently open UNH..UNT message

    def ensure_payload():
        return payload if payload is not None else {}

    def attach_message(buf):
        message = _edifact_message(buf)
        target = group if group is not None else payload
        _append(target, "messages", message)

    for seg in segments:
        tag = seg.tag
        if tag == "UNA":
            continue
        if msg_buf is not None:
            msg_buf.append(seg)
            if tag == "UNT":
                attach_message(msg_buf)
                msg_buf = None
            continue
        if tag == "UNB":
            if payload is not None:  # unterminated previous interchange
                payloads.append(payload)
            payload = {"interchange_header_UNB": _edifact_segment_object(seg)}
            group = None
        elif tag == "UNH":
            payload = ensure_payload()
            msg_buf = [seg]
        elif tag == "UNG":
            payload = ensure_payload()
            group = {"functional_group_header_UNG": _edifact_segment_object(seg)}
            _append(payload, "functional_groups", group)
        elif tag == "UNE":
            if group is not None:
                group["functional_group_trailer_UNE"] = _edifact_segment_object(seg)
                group = None
            else:
                payload = ensure_payload()
                _unparsed(payload, seg)
        elif tag == "UNZ":
            payload = ensure_payload()
            payload["interchange_trailer_UNZ"] = _edifact_segment_object(seg)
            payloads.append(payload)
            payload = None
            group = None
        else:
            payload = ensure_payload()
            _unparsed(payload, seg)

    if msg_buf:  # message never closed by UNT
        attach_message(msg_buf)
    if payload is not None:
        payloads.append(payload)
    return payloads


# ---------------------------------------------------------------------------
# X12
# ---------------------------------------------------------------------------

_X12_DEFS = edi_norm_data.X12_SEGMENT_DEFS


def _positional_segment_object(seg, defs, pad):
    """Named object for dialects that name elements by position.

    ``defs`` values are ``(segment_name, (position, ...))`` where a position
    is either ``"name"`` (simple) or ``("name", ("component", ...))``
    (composite). Keys carry the 1-based position, zero-padded to ``pad``
    digits (X12 convention ``BEG01`` -> ``..._01``; HL7 ``PID-3`` -> ``_3``).
    """
    entry = defs.get(seg.tag)
    positions = entry[1] if entry else ()
    obj = {}
    for idx, components in enumerate(seg.elements()):
        if _is_empty(components):
            continue
        pos = positions[idx] if idx < len(positions) else None
        suffix = str(idx + 1).zfill(pad)
        if pos is None:
            obj["element_%s" % suffix] = _value_or_list(components)
        elif isinstance(pos, tuple):  # composite: (name, (component, ...))
            comp_keys = _dedup_keys(list(pos[1]))
            sub = {}
            for ci, component in enumerate(components):
                if component == "":
                    continue
                if ci < len(comp_keys):
                    sub[comp_keys[ci]] = component
                else:
                    sub["component_%d" % (ci + 1)] = component
            if sub:
                obj["%s_%s" % (pos[0], suffix)] = sub
        else:
            obj["%s_%s" % (pos, suffix)] = _value_or_list(components)
    return obj


def _x12_segment_object(seg):
    return _positional_segment_object(seg, _X12_DEFS, 2)


def _x12_payloads(segments):
    payloads = []
    payload = None
    group = None
    message = None

    def ensure_payload():
        return payload if payload is not None else {}

    for seg in segments:
        tag = seg.tag
        obj = _x12_segment_object(seg)
        if tag == "ISA":
            if payload is not None:
                payloads.append(payload)
            payload = {"interchange_control_header_ISA": obj}
            group = None
            message = None
        elif tag == "GS":
            payload = ensure_payload()
            group = {"functional_group_header_GS": obj}
            _append(payload, "functional_groups", group)
            message = None
        elif tag == "ST":
            payload = ensure_payload()
            elements = seg.elements()
            message = {}
            if elements and elements[0][0]:
                message["MESSAGE_TYPE"] = elements[0][0]
            message["transaction_set_header_ST"] = obj
            _append(group if group is not None else payload, "messages", message)
        elif tag == "SE":
            if message is not None:
                message["transaction_set_trailer_SE"] = obj
                message = None
            else:
                payload = ensure_payload()
                _unparsed(payload, seg)
        elif tag == "GE":
            if group is not None:
                group["functional_group_trailer_GE"] = obj
                group = None
            else:
                payload = ensure_payload()
                _unparsed(payload, seg)
        elif tag == "IEA":
            payload = ensure_payload()
            payload["interchange_control_trailer_IEA"] = obj
            payloads.append(payload)
            payload = None
            group = None
            message = None
        elif message is not None:
            _flat_append(message, seg, obj, _X12_DEFS)
        elif tag == "TA1":  # interchange-level acknowledgment
            payload = ensure_payload()
            _flat_append(payload, seg, obj, _X12_DEFS)
        else:
            payload = ensure_payload()
            _unparsed(payload, seg)

    if payload is not None:
        payloads.append(payload)
    return payloads


# ---------------------------------------------------------------------------
# TRADACOMS
# ---------------------------------------------------------------------------

_TRADACOMS_DEFS = edi_norm_data.TRADACOMS_SEGMENT_DEFS


def _tradacoms_segment_object(seg):
    return _positional_segment_object(seg, _TRADACOMS_DEFS, 2)


def _tradacoms_payloads(segments):
    payloads = []
    payload = None
    message = None

    def ensure_payload():
        return payload if payload is not None else {}

    for seg in segments:
        tag = seg.tag
        obj = _tradacoms_segment_object(seg)
        if tag == "STX":
            if payload is not None:
                payloads.append(payload)
            payload = {"start_of_transmission_STX": obj}
            message = None
        elif tag == "MHD":
            payload = ensure_payload()
            elements = seg.elements()
            message = {}
            if len(elements) > 1 and elements[1][0]:
                message["MESSAGE_TYPE"] = elements[1][0]
            message["message_header_MHD"] = obj
            _append(payload, "messages", message)
        elif tag == "MTR":
            if message is not None:
                message["message_trailer_MTR"] = obj
                message = None
            else:
                payload = ensure_payload()
                _unparsed(payload, seg)
        elif tag == "END":
            payload = ensure_payload()
            payload["end_of_transmission_END"] = obj
            payloads.append(payload)
            payload = None
            message = None
        elif message is not None:
            _flat_append(message, seg, obj, _TRADACOMS_DEFS)
        else:
            payload = ensure_payload()
            _unparsed(payload, seg)

    if payload is not None:
        payloads.append(payload)
    return payloads


# ---------------------------------------------------------------------------
# HL7 v2.x
# ---------------------------------------------------------------------------

_HL7_DEFS = edi_norm_data.HL7_SEGMENT_DEFS


def _hl7_segment_object(seg):
    return _positional_segment_object(seg, _HL7_DEFS, 1)


def _hl7_payloads(segments):
    """HL7 has no interchange envelope: one payload holding the messages."""
    payload = {}
    message = None
    for seg in segments:
        obj = _hl7_segment_object(seg)
        if seg.tag == "MSH":
            elements = seg.elements()
            message = {}
            if len(elements) > 8 and not _is_empty(elements[8]):
                message["MESSAGE_TYPE"] = "_".join(
                    c for c in elements[8] if c != "")
            message["message_header_MSH"] = obj
            _append(payload, "messages", message)
        elif message is not None:
            _flat_append(message, seg, obj, _HL7_DEFS)
        else:
            _unparsed(payload, seg)
    return [payload] if payload else []
