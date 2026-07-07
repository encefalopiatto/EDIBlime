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

try:
    # Normal case: imported as part of the Sublime Text package.
    from . import edi_data
except (ImportError, ValueError):
    # Standalone case: imported directly (e.g. the unit tests).
    import edi_data


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
            base.update({k: v for k, v in overrides.items() if v})
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
        """
        s, e = start, end
        while s < e and text[s] in "\r\n\t ":
            s += 1
        while e > s and text[e - 1] in "\r\n\t":
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


# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------

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

    # Heuristic fallback based on which terminator dominates.
    term = _dominant(stripped, ["'", "~", "\r"])
    if term == "~":
        return Dialect.from_family("x12")
    if term == "'":
        return Dialect.from_family("edifact")
    if term == "\r" and "|" in stripped:
        return _detect_hl7(stripped)
    return None


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
    # ISA is a fixed-width 106-character segment. The element separator is the
    # 4th character; the component separator and segment terminator are the
    # final two characters of the ISA segment.
    elem = text[3] if len(text) > 3 else "*"
    comp = ":"
    term = "~"
    rep = None
    if len(text) >= 106 and text[105] not in ("", "\n"):
        comp = text[104]
        term = text[105]
        rep = text[82] if text[82] not in (" ", elem) else None
    else:
        # Fall back: element separator known, find terminator after ~16 fields.
        term = _dominant(text, ["~", "'", "\n"]) or "~"
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
    lines = []
    for seg in segments:
        if dialect.family == "hl7":
            # HL7 terminator is CR; the newline *is* the terminator.
            lines.append(seg.content)
        elif keep_terminator:
            lines.append(seg.content + term)
        else:
            lines.append(seg.content)
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
