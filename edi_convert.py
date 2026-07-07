# -*- coding: utf-8 -*-
"""
Convert EDI messages to JSON, JSONC and XML.

Like :mod:`edi_core`, this module has no Sublime Text dependency and is unit
tested in isolation. The conversions are *structural*: they turn the segment /
element / component hierarchy into the target format, with the human readable
segment names (and, for JSONC, full descriptions and per-element names) mixed
in so the output is self-documenting.

Value handling:

* All values stay strings -- EDI values like ``0012`` carry meaning in their
  leading zeros, and X12 amounts often have implied decimals.
* Release characters are resolved (EDIFACT ``?+`` becomes ``+``); the five
  standard HL7 escape sequences are decoded.
* An element with a single component collapses to a plain string; an element
  with multiple components becomes a list of strings.
* Repetition separators are not expanded; a repeated field arrives verbatim.
"""

import json
import re

try:
    from . import edi_core
    from . import edi_data
except (ImportError, ValueError):
    import edi_core
    import edi_data

# Control characters sanitized out of ``//`` comments (a newline in raw data
# would otherwise break the "strip comments -> valid JSON" contract) and out
# of XML output (illegal in XML 1.0 even as character references).
_CONTROL_RE = re.compile("[\x00-\x08\x0b\x0c\x0e-\x1f]")
_COMMENT_UNSAFE_RE = re.compile(r"[\x00-\x1f\x7f]+")


def _comment_safe(value):
    """Collapse control characters so ``value`` stays on one comment line."""
    return _COMMENT_UNSAFE_RE.sub(" ", value)


# ---------------------------------------------------------------------------
# Structural tree
# ---------------------------------------------------------------------------

def to_tree(text, dialect=None):
    """Parse ``text`` into a plain-data tree (dicts/lists/strings).

    Shape::

        {
          "dialect": "EDIFACT",
          "delimiters": {"segment": "'", "element": "+", "component": ":"},
          "segments": [
            {"tag": "UNB", "name": "Interchange Header",
             "elements": [["UNOC", "3"], "SENDER", ...]},
            ...
          ]
        }

    Raises ``ValueError`` when the text is not recognisable EDI.
    """
    dialect = dialect or edi_core.detect(text)
    if dialect is None:
        raise ValueError("could not detect an EDI dialect")

    segments = []
    for seg in dialect.split_segments(text):
        elements = [_collapse(el) for el in seg.elements()]
        entry = {"tag": seg.tag, "elements": elements}
        name = edi_data.segment_name(dialect.key, seg.tag)
        if name:
            entry["name"] = name
        segments.append(entry)

    return {
        "dialect": dialect.label,
        "delimiters": {
            "segment": dialect.segment_terminator,
            "element": dialect.element_separator,
            "component": dialect.component_separator,
        },
        "segments": segments,
    }


def _collapse(components):
    """A single-component element becomes a plain string."""
    if len(components) == 1:
        return components[0]
    return components


# ---------------------------------------------------------------------------
# JSON
# ---------------------------------------------------------------------------

def to_json(text, dialect=None, indent=2):
    """Convert ``text`` to a pretty-printed JSON document."""
    tree = to_tree(text, dialect)
    return json.dumps(tree, indent=indent, ensure_ascii=False) + "\n"


# ---------------------------------------------------------------------------
# JSONC (JSON with comments describing every segment and element)
# ---------------------------------------------------------------------------

def to_jsonc(text, dialect=None):
    """Convert ``text`` to JSONC: JSON annotated with ``//`` comments.

    Every segment object is preceded by a comment stating its name and what it
    means/does, and every element carries a trailing comment with its position
    and -- for well-known segments -- its element name. Stripping the comments
    yields valid JSON identical in structure to :func:`to_json`.
    """
    dialect = dialect or edi_core.detect(text)
    if dialect is None:
        raise ValueError("could not detect an EDI dialect")

    dumps = lambda v: json.dumps(v, ensure_ascii=False)  # noqa: E731
    lines = []
    push = lines.append

    push("{")
    push('  // %s message converted by EDIBlime' % dialect.label)
    push('  "dialect": %s,' % dumps(dialect.label))
    push('  "delimiters": {')
    push('    "segment": %s,' % dumps(dialect.segment_terminator))
    push('    "element": %s,' % dumps(dialect.element_separator))
    push('    "component": %s' % dumps(dialect.component_separator))
    push("  },")
    push('  "segments": [')

    segments = dialect.split_segments(text)
    for si, seg in enumerate(segments):
        tag = _comment_safe(seg.tag)
        name = edi_data.segment_name(dialect.key, seg.tag)
        detail = edi_data.segment_detail(dialect.key, seg.tag)
        el_names = edi_data.element_names(dialect.key, seg.tag)

        push("")
        if name:
            push("    // %s — %s" % (tag, name))
        else:
            push("    // %s" % tag)
        for wrapped in _wrap(detail, 96):
            push("    // %s" % wrapped)

        push("    {")
        push('      "tag": %s,' % dumps(seg.tag))
        if name:
            push('      "name": %s,' % dumps(name))

        elements = [_collapse(el) for el in seg.elements()]
        if not elements:
            push('      "elements": []')
        else:
            push('      "elements": [')
            for ei, element in enumerate(elements):
                comma = "," if ei < len(elements) - 1 else ""
                label = el_names[ei] if ei < len(el_names) else ""
                code = element if isinstance(element, str) else element[0]
                decoded = edi_data.qualifier_label(dialect.key, seg.tag, ei + 1, code)
                comment = "  // %d" % (ei + 1)
                if label:
                    comment += ". %s" % label
                if decoded:
                    comment += " [%s = %s]" % (_comment_safe(code), decoded)
                push("        %s%s%s" % (dumps(element), comma, comment))
            push("      ]")
        push("    }%s" % ("," if si < len(segments) - 1 else ""))

    push("  ]")
    push("}")
    return "\n".join(lines) + "\n"


def _wrap(text, width):
    """Naive word-wrap for comment lines (no textwrap: keep deps minimal)."""
    if not text:
        return []
    words = text.split()
    out = []
    line = []
    length = 0
    for w in words:
        add = len(w) + (1 if line else 0)
        if length + add > width and line:
            out.append(" ".join(line))
            line = [w]
            length = len(w)
        else:
            line.append(w)
            length += add
    if line:
        out.append(" ".join(line))
    return out


# ---------------------------------------------------------------------------
# XML
# ---------------------------------------------------------------------------

def to_xml(text, dialect=None):
    """Convert ``text`` to an XML document.

    Shape::

        <?xml version="1.0" encoding="UTF-8"?>
        <edi dialect="EDIFACT">
          <segment tag="UNB" name="Interchange Header">
            <element index="1" name="Syntax identifier ...">
              <component>UNOC</component>
              <component>3</component>
            </element>
            <element index="2">SENDER</element>
          </segment>
        </edi>

    Single-component elements carry their value as text content; composite
    elements nest ``<component>`` children.
    """
    dialect = dialect or edi_core.detect(text)
    if dialect is None:
        raise ValueError("could not detect an EDI dialect")

    lines = ['<?xml version="1.0" encoding="UTF-8"?>',
             '<edi dialect="%s">' % _xml_attr(dialect.label)]
    for seg in dialect.split_segments(text):
        name = edi_data.segment_name(dialect.key, seg.tag)
        el_names = edi_data.element_names(dialect.key, seg.tag)
        attrs = ' tag="%s"' % _xml_attr(seg.tag)
        if name:
            attrs += ' name="%s"' % _xml_attr(name)
        elements = seg.elements()
        if not elements:
            lines.append("  <segment%s/>" % attrs)
            continue
        lines.append("  <segment%s>" % attrs)
        for ei, components in enumerate(elements):
            el_attrs = ' index="%d"' % (ei + 1)
            if ei < len(el_names) and el_names[ei]:
                el_attrs += ' name="%s"' % _xml_attr(el_names[ei])
            decoded = edi_data.qualifier_label(
                dialect.key, seg.tag, ei + 1, components[0] if components else "")
            if decoded:
                el_attrs += ' decoded="%s"' % _xml_attr(decoded)
            if len(components) == 1:
                lines.append("    <element%s>%s</element>"
                             % (el_attrs, _xml_text(components[0])))
            else:
                lines.append("    <element%s>" % el_attrs)
                for comp in components:
                    lines.append("      <component>%s</component>" % _xml_text(comp))
                lines.append("    </element>")
        lines.append("  </segment>")
    lines.append("</edi>")
    return "\n".join(lines) + "\n"


def _xml_text(value):
    # Characters outside the XML 1.0 Char production are illegal even as
    # character references (EDI payloads pick them up from MLLP framing,
    # stray separators, binary garbage); replace them visibly with U+FFFD.
    value = _CONTROL_RE.sub("�", value)
    return (value.replace("&", "&amp;")
                 .replace("<", "&lt;")
                 .replace(">", "&gt;"))


def _xml_attr(value):
    return (_xml_text(value)
            .replace('"', "&quot;")
            .replace("\n", "&#10;")
            .replace("\r", "&#13;")
            .replace("\t", "&#9;"))
