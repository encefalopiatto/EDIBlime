# -*- coding: utf-8 -*-
"""
Dialect-agnostic EDI parsing and formatting engine.

This module has **no dependency on the Sublime Text API** so that it can be
unit tested in isolation (see ``tests/``). ``edi.py`` is the thin Sublime layer
that wires these functions to commands, menus and annotations.

The engine understands delimiter-separated EDI: the EDIFACT family (including
its subsets EANCOM / ODETTE / EDIG@S / IATA-PADIS), ANSI ASC X12, TRADACOMS and
HL7 v2.x. All of these encode a message as a stream of *segments* terminated by
a segment terminator, with data *elements* inside a segment separated by an
element separator, and *components* inside an element separated by a component
separator.

The public surface is small and stable:

    detect(text)                 -> Dialect
    Dialect.split_segments(text) -> [Segment, ...]
    beautify(text, ...)          -> str
    minify(text, ...)            -> str
    describe_segments(text, ...) -> [(Segment, name), ...]
"""

import re

from . import edi_data


class Dialect(object):
    """Resolved delimiter set for a single message.

    ``key`` is the fine-grained dialect (e.g. ``eancom``) used for segment name
    lookups, while ``family`` is the delimiter family (e.g. ``edifact``) that
    determines parsing behaviour.
    """

    __slots__ = (
        "key", "family", "label",
        "segment_terminator", "element_separator", "component_separator",
        "repetition_separator", "release_character", "decimal_mark",
        "tag_separator",
    )

    def __init__(self, key, family, label, **delims):
        self.key = key
        self.family = family
        self.label = label
        self.segment_terminator = delims["segment_terminator"]
        self.element_separator = delims["element_separator"]
        self.component_separator = delims["component_separator"]
        self.repetition_separator = delims.get("repetition_separator")
        self.release_character = delims.get("release_character")
        self.decimal_mark = delims.get("decimal_mark", ".")
        self.tag_separator = delims.get("tag_separator")

    # -- construction ----------------------------------------------------
    @classmethod
    def from_family(cls, key, family=None, overrides=None):
        family = family or edi_data.dialect_family(key)
        base = dict(edi_data.DIALECTS[family])
        if overrides:
            # Overrides are applied verbatim: callers only include keys they
            # actually resolved, and an explicit None is meaningful (e.g. a
            # UNA declaring "no release character" via a space).
            base.update(overrides)
        label = base.pop("label", family.upper())
        # EDIFACT subsets carry their own display label.
        if key in edi_data.EDIFACT_SUBSETS:
            label = edi_data.EDIFACT_SUBSETS[key]
        return cls(key, family, label, **base)

    # -- segment splitting ----------------------------------------------
    def segment_spans(self, text):
        """Split ``text`` into ``[(start, end, Segment), ...]`` with offsets.

        ``start``/``end`` are character offsets into ``text`` that bound the
        segment's data (leading/trailing inter-segment whitespace excluded and
        the terminator excluded), which lets callers map segments back to
        buffer regions.

        Honours the dialect release/escape character so that an escaped
        segment terminator (e.g. ``?'`` in EDIFACT) does not end a segment.
        """
        spans = []
        # HL7 segments are carriage-return delimited; once beautified they are
        # line-feed delimited. Neither ever appears inside HL7 data (embedded
        # breaks are escape-encoded), so accept both as terminators. Other
        # dialects use their single declared terminator.
        if self.family == "hl7":
            terminators = ("\r", "\n")
            # HL7's "\\" escape works as *delimited pairs* (\F\, \.br\, ...),
            # not as a release character prefixing the next byte, and a CR can
            # never be escaped -- skipping here would let a field that ends in
            # an escape sequence swallow the segment terminator.
            release = None
        else:
            terminators = (self.segment_terminator,)
            release = self.release_character
        n = len(text)
        i = 0
        seg_start = 0          # offset where the current raw segment begins
        has_content = False    # any non-whitespace seen in the current segment
        while i < n:
            ch = text[i]
            if release and ch == release and i + 1 < n:
                has_content = True
                i += 2
                continue
            if ch in terminators:
                self._emit_span(text, seg_start, i, spans)
                i += 1
                seg_start = i
                has_content = False
                continue
            if not ch.isspace():
                has_content = True
            i += 1
        # Trailing content with no terminator (tolerated, e.g. truncated data).
        if has_content or seg_start < n:
            self._emit_span(text, seg_start, n, spans)
        return spans

    def _emit_span(self, text, start, end, spans):
        """Trim inter-segment formatting from ``text[start:end]`` and record it.

        Beautify only ever *inserts* line breaks between segments, so leading
        whitespace (including any indentation a user added) is dropped, while
        the trailing edge only sheds line breaks/tabs -- a trailing data space
        such as the EDIFACT UNA reserved character must survive the round trip.
        A UTF-8 BOM (U+FEFF) is likewise trimmed so it cannot leak into the
        first segment's tag.
        """
        s, e = start, end
        while s < e and text[s] in "\r\n\t ﻿":
            s += 1
        while e > s and text[e - 1] in "\r\n\t﻿":
            e -= 1
        if e > s:
            spans.append((s, e, Segment(text[s:e], self)))

    def split_segments(self, text):
        """Split ``text`` into :class:`Segment` objects (offsets discarded)."""
        return [seg for _s, _e, seg in self.segment_spans(text)]


class Segment(object):
    """A single EDI segment (its raw text, minus the terminator)."""

    __slots__ = ("content", "dialect")

    def __init__(self, content, dialect):
        self.content = content
        self.dialect = dialect

    @property
    def tag(self):
        """The segment tag / code (e.g. ``UNH``, ``ISA``, ``MSH``, ``MHD``)."""
        content = self.content
        d = self.dialect
        if d.family == "hl7":
            return content[:3]
        # The EDIFACT UNA service string advice is fixed-format: the tag is
        # always ``UNA`` and the following six characters are literal delimiter
        # definitions, not separators.
        if d.family == "edifact" and content[:3] == "UNA":
            return "UNA"
        stops = [d.element_separator]
        if d.tag_separator:
            stops.append(d.tag_separator)
        cut = len(content)
        for sep in stops:
            idx = content.find(sep)
            if idx != -1 and idx < cut:
                cut = idx
        return content[:cut]

    def __repr__(self):
        return "Segment(%r)" % (self.content,)

    def elements(self):
        """Parse this segment's data elements.

        Returns a list of elements, where each element is a list of component
        strings (a simple element yields a one-component list). The segment
        tag itself is not included. Release characters are resolved, i.e. the
        returned values are the *decoded* data.

        Dialect specifics handled here:

        * EDIFACT ``UNA`` is fixed-format -- the six service characters are
          returned as a single element and never split.
        * TRADACOMS tags are separated from the data by ``=``.
        * HL7 ``MSH`` follows the standard's numbering: MSH-1 is the field
          separator itself and MSH-2 the four encoding characters (returned
          verbatim, never component-split or unescaped).
        """
        d = self.dialect
        content = self.content

        if d.family == "edifact" and self.tag == "UNA":
            return [[content[3:]]]

        if d.family == "hl7":
            if len(content) <= 4:
                return []
            body = content[4:]
            fields = body.split(d.element_separator)
            if self.tag == "MSH":
                # MSH-1 = field separator, MSH-2 = encoding characters (raw).
                encoding = fields[0] if fields else ""
                rest = fields[1:]
                elements = [[d.element_separator], [encoding]]
                elements.extend(
                    [_hl7_unescape(c, d) for c in f.split(d.component_separator)]
                    for f in rest)
                return elements
            return [
                [_hl7_unescape(c, d) for c in f.split(d.component_separator)]
                for f in fields
            ]

        # Delimiter-based dialects with an optional release character.
        return [
            [_unescape(c, d.release_character)
             for c in _split_released(e, d.component_separator, d.release_character)]
            for e in self.raw_elements()
        ]

    def raw_elements(self):
        """This segment's element strings exactly as written.

        Unlike :meth:`elements`, components are not split and release
        characters stay in place, so ``rebuild_segment(tag, raw_elements)``
        reproduces the original content byte for byte.
        """
        d = self.dialect
        content = self.content
        if d.family == "hl7":
            if len(content) <= 4:
                return []
            return content[4:].split(d.element_separator)
        if d.family == "edifact" and self.tag == "UNA":
            return [content[3:]]
        body = content[len(self.tag):]
        # The tag may be followed by the dialect's tag separator (TRADACOMS
        # ``=``) or directly by the element separator; strip whichever is
        # actually there so indices stay aligned either way.
        if body and (body[0] == d.element_separator
                     or (d.tag_separator and body[0] == d.tag_separator)):
            body = body[1:]
        if not body:
            return []
        return _split_released(body, d.element_separator, d.release_character)

    def with_raw_elements(self, raw):
        """Rebuild this segment's content from raw element strings."""
        d = self.dialect
        if d.family == "edifact" and self.tag == "UNA":
            return self.tag + "".join(raw)
        first = d.element_separator if d.family == "hl7" else (d.tag_separator or d.element_separator)
        return self.tag + first + d.element_separator.join(raw)


# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------

def _split_released(text, separator, release):
    """Split ``text`` on ``separator``, honouring the release character.

    A separator preceded by the release character is data, not structure. The
    release characters are kept in the returned parts (``_unescape`` removes
    them afterwards).
    """
    if not release or release not in text:
        return text.split(separator)
    parts = []
    buf = []
    i = 0
    n = len(text)
    while i < n:
        ch = text[i]
        if ch == release and i + 1 < n:
            buf.append(ch)
            buf.append(text[i + 1])
            i += 2
            continue
        if ch == separator:
            parts.append("".join(buf))
            buf = []
            i += 1
            continue
        buf.append(ch)
        i += 1
    parts.append("".join(buf))
    return parts


def _unescape(value, release):
    """Resolve release characters: ``?+`` becomes ``+``, ``??`` becomes ``?``."""
    if not release or release not in value:
        return value
    out = []
    i = 0
    n = len(value)
    while i < n:
        ch = value[i]
        if ch == release and i + 1 < n:
            out.append(value[i + 1])
            i += 2
            continue
        out.append(ch)
        i += 1
    return "".join(out)


# The five standard HL7 escape sequences (\F\ etc.) map to the *default*
# delimiter roles; the actual characters come from the message's MSH segment.
def _hl7_unescape(value, dialect):
    """Decode the standard HL7 escape sequences into their literal characters.

    ``\\F\\`` = field separator, ``\\S\\`` = component, ``\\R\\`` = repetition,
    ``\\T\\`` = subcomponent, ``\\E\\`` = escape character itself. Unknown
    sequences (``\\X..\\``, ``\\.br\\``, ...) are preserved verbatim.
    """
    esc = dialect.release_character or "\\"
    if esc not in value:
        return value
    mapping = {
        "F": dialect.element_separator,
        "S": dialect.component_separator,
        "R": dialect.repetition_separator or "~",
        "T": "&",
        "E": esc,
    }
    out = []
    i = 0
    n = len(value)
    while i < n:
        ch = value[i]
        if ch == esc:
            end = value.find(esc, i + 1)
            if end != -1:
                seq = value[i + 1:end]
                if seq in mapping:
                    out.append(mapping[seq])
                    i = end + 1
                    continue
            # Unknown / unterminated sequence: keep verbatim.
        out.append(ch)
        i += 1
    return "".join(out)


def _dominant(text, candidates):
    """Return the candidate character that occurs most often in ``text``."""
    best = None
    best_count = -1
    for ch in candidates:
        c = text.count(ch)
        if c > best_count:
            best_count = c
            best = ch
    return best if best_count > 0 else None


# ---------------------------------------------------------------------------
# Detection
# ---------------------------------------------------------------------------

def detect(text):
    """Detect the EDI dialect of ``text`` and resolve its delimiters.

    Detection prefers explicit service-string advertisements (``UNA``/``UNB``,
    ``ISA``, ``STX``, ``MSH``) and falls back to a delimiter heuristic. Returns
    a :class:`Dialect`, or ``None`` when the text does not look like EDI.
    """
    if not text:
        return None
    stripped = text.lstrip("\r\n\t ﻿")
    head = stripped[:4]

    if head.startswith("ISA"):
        return _detect_x12(stripped)
    if head.startswith("UNA") or head.startswith("UNB"):
        return _detect_edifact(stripped)
    if head.startswith("STX"):
        return Dialect.from_family("tradacoms")
    if head.startswith("MSH"):
        return _detect_hl7(stripped)

    # Heuristic fallback for messages without their envelope. Requires real
    # structural evidence -- segments shaped like ``TAG<element sep>...`` --
    # so that ordinary prose or code (which merely *contains* an apostrophe
    # or tilde) is never claimed as EDI.
    if _plausible_fallback(stripped, "'", "+"):
        return Dialect.from_family("edifact")
    if _plausible_fallback(stripped, "~", "*"):
        return Dialect.from_family("x12")
    if _HL7_HEAD.match(stripped) and stripped.count("|") >= 3:
        return _detect_hl7(stripped)
    return None


_TAG_SHAPE = re.compile(r"^[A-Z][A-Z0-9]{1,3}$")
_HL7_HEAD = re.compile(r"^[A-Z][A-Z0-9]{2}\|")


def _plausible_fallback(text, term, elem):
    """True when ``text`` plausibly consists of ``TAG<elem>...<term>`` segments.

    Demands at least two segment terminators and a leading segment whose tag
    (2-4 uppercase alphanumerics) is immediately followed by the element
    separator.
    """
    if text.count(term) < 2:
        return False
    first = text.split(term, 1)[0].strip()
    idx = first.find(elem)
    if idx < 2 or idx > 4:
        return False
    return bool(_TAG_SHAPE.match(first[:idx]))


def _detect_edifact(text):
    overrides = None
    if text.startswith("UNA") and len(text) >= 9:
        # UNA<comp><elem><decimal><release><reserved><segterm>
        overrides = {
            "component_separator": text[3],
            "element_separator": text[4],
            "decimal_mark": text[5],
            "release_character": text[6] if text[6] != " " else None,
            "segment_terminator": text[8],
        }
    return Dialect.from_family("edifact", overrides=overrides)


def _detect_x12(text):
    # ISA is a fixed-width 106-character segment: element separator at index
    # 3, repetition separator (version 00402+) at 82, component separator at
    # 104 and the segment terminator at 105. Verify the fixed-width shape
    # (element separators at their known positions) before trusting those
    # offsets -- some senders emit unpadded ISA segments, and blindly indexing
    # into one yields garbage delimiters.
    elem = text[3] if len(text) > 3 else "*"
    comp = ":"
    term = "~"
    rep = None
    fixed = (len(text) >= 106
             and text[99] == elem and text[101] == elem and text[103] == elem)
    if fixed:
        comp = text[104]
        # A line break is a perfectly valid terminator (one segment per line).
        term = text[105]
        # ISA11 is the repetition separator only from control version 00402;
        # before that it held the standards identifier (usually "U").
        version = text[84:89]
        if version >= "00402" and text[82] not in (" ", elem):
            rep = text[82]
    else:
        # Unpadded ISA: pick the dominating terminator, and read ISA16 (the
        # component separator) as the last element of the ISA segment.
        term = _dominant(text, ["~", "'", "\n"]) or "~"
        end = text.find(term)
        if end > 4 and text[end - 2] == elem:
            comp = text[end - 1]
    overrides = {
        "element_separator": elem,
        "component_separator": comp,
        "segment_terminator": term,
        "repetition_separator": rep,
    }
    return Dialect.from_family("x12", overrides=overrides)


def _detect_hl7(text):
    overrides = None
    if text.startswith("MSH") and len(text) >= 8:
        # MSH<field><comp><rep><escape><subcomp>|
        field = text[3]
        enc = text[4:8]  # component, repetition, escape, subcomponent
        overrides = {
            "element_separator": field,
            "component_separator": enc[0] if len(enc) > 0 else "^",
            "repetition_separator": enc[1] if len(enc) > 1 else "~",
            "release_character": enc[2] if len(enc) > 2 else "\\",
        }
    return Dialect.from_family("hl7", overrides=overrides)


# ---------------------------------------------------------------------------
# Formatting operations
# ---------------------------------------------------------------------------

def beautify(text, dialect=None, keep_terminator=True, newline="\n"):
    """Return ``text`` with each segment on its own line.

    ``keep_terminator`` keeps the original segment terminator at the end of
    each line so the output remains valid EDI (parsers treat the added
    newlines as ignorable inter-segment whitespace). For HL7 the ``\\r``
    terminator is replaced by the requested ``newline`` because a literal
    carriage return is what separates HL7 segments in the first place.
    """
    dialect = dialect or detect(text)
    if dialect is None:
        return text
    segments = dialect.split_segments(text)
    if not segments:
        return text

    term = dialect.segment_terminator
    # When the terminator is itself a line break (HL7's CR, or an interchange
    # that declared a newline terminator), the joining newline *is* the
    # terminator -- appending it again would emit blank lines.
    newline_is_term = dialect.family == "hl7" or term in ("\n", "\r", "\r\n")
    lines = []
    for seg in segments:
        if newline_is_term or not keep_terminator:
            lines.append(seg.content)
        else:
            lines.append(seg.content + term)
    return newline.join(lines) + newline


def minify(text, dialect=None):
    """Collapse ``text`` back into a single compliant EDI stream.

    Removes the inter-segment newlines/indentation that ``beautify`` adds,
    producing one continuous line (the canonical wire format).
    """
    dialect = dialect or detect(text)
    if dialect is None:
        return text
    segments = dialect.split_segments(text)
    if not segments:
        return text

    term = dialect.segment_terminator
    if dialect.family == "hl7":
        # Preserve HL7's carriage-return terminators without extra whitespace.
        return "\r".join(seg.content for seg in segments) + "\r"
    return "".join(seg.content + term for seg in segments)


def describe_segments(text, dialect=None):
    """Return ``[(Segment, name), ...]`` for every segment in ``text``.

    ``name`` is the human readable description of the segment tag, or an empty
    string when the tag is not in the reference tables.
    """
    return [(seg, name) for _s, _e, seg, name in describe_spans(text, dialect)]


def element_at(segment, offset):
    """Locate the element/component containing ``offset`` within a segment.

    ``offset`` is 0-based relative to ``segment.content``. Returns a
    ``(element_number, component_number)`` pair using the same 1-based
    numbering as :meth:`Segment.elements` (HL7's MSH counts the field
    separator itself as MSH-1, so its numbers shift by one). ``(0, 0)`` means
    the offset sits on the segment tag (or inside a fixed-format UNA).
    """
    d = segment.dialect
    content = segment.content
    offset = max(0, min(offset, len(content)))
    if d.family == "edifact" and segment.tag == "UNA":
        return (0, 0)
    if d.family == "hl7":
        elem_no = content.count(d.element_separator, 0, offset)
        if segment.tag == "MSH":
            elem_no += 1 if elem_no else 0
            if elem_no == 2:
                # MSH-2 is the encoding declaration: its ^ ~ \ & are literal.
                return (2, 1)
        start = content.rfind(d.element_separator, 0, offset) + 1
        comp_no = content.count(d.component_separator, start, offset) + 1
        return (elem_no, comp_no) if elem_no > 0 else (0, 0)
    release = d.release_character
    elem_no = 0
    comp_no = 1
    i = 0
    while i < offset:
        ch = content[i]
        if release and ch == release:
            i += 2
            continue
        if ch == d.element_separator or (d.tag_separator and ch == d.tag_separator):
            elem_no += 1
            comp_no = 1
        elif ch == d.component_separator:
            comp_no += 1
        i += 1
    return (elem_no, comp_no) if elem_no > 0 else (0, 0)


def describe_spans(text, dialect=None):
    """Return ``[(start, end, Segment, name), ...]`` for every segment.

    Like :func:`describe_segments` but keeps the character offsets so callers
    (e.g. the editor layer) can attach annotations to the right region.
    """
    dialect = dialect or detect(text)
    if dialect is None:
        return []
    out = []
    for start, end, seg in dialect.segment_spans(text):
        out.append((start, end, seg, edi_data.segment_name(dialect.key, seg.tag)))
    return out
