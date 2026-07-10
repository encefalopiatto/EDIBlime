# EDIBlime

A [Sublime Text](https://www.sublimetext.com/) package to **beautify, clean,
minify and annotate EDI documents** — with first-class support for **UN/EDIFACT**
and the other major delimiter-based EDI standards.

Raw EDI arrives as one long, unreadable line. EDIBlime turns it into something
a human can actually work with: one segment per line, syntax highlighting, and
optional inline hints that name every segment — without ever changing the data.

```
UNA:+.? 'UNB+UNOC:3+SENDER:14+RECEIVER:14+200101:1200+1'UNH+1+ORDERS:D:96A:UN'BGM+220+PO12345+9'...
```

becomes

```
UNA:+.? '
UNB+UNOC:3+SENDER:14+RECEIVER:14+200101:1200+1'   UNB — Interchange Header
UNH+1+ORDERS:D:96A:UN'                            UNH — Message Header
BGM+220+PO12345+9'                                BGM — Beginning of Message
DTM+137:20200101:102'                             DTM — Date/Time/Period
NAD+BY+5412345000013::9'                          NAD — Name and Address
UNT+6+1'                                          UNT — Message Trailer
UNZ+1+1'                                          UNZ — Interchange Trailer
```

The segment descriptions on the right are **non-destructive annotations** — they
are rendered by the editor, not written into your file, so the buffer stays a
valid, byte-for-byte EDI document.

## Features

- **Beautify** — split a message so each segment sits on its own line. The
  original segment terminators are kept, so the result is still valid EDI.
- **Minify / Clean** — collapse a beautified message back to the canonical
  single-line wire format, stripping the whitespace editors and humans add.
- **Inline hints** — toggle human-readable segment descriptions shown as
  end-of-line annotations. Completely non-destructive.
- **Segment explanations** — hover any segment (or press `Ctrl+Alt+E`) for a
  popup that explains what the segment means and does, plus an
  **element-by-element breakdown** with the value and the element's name
  (e.g. `1. "UNOC:3" — Syntax identifier : version`). Works for EDIFACT, X12,
  TRADACOMS and HL7. The status bar names the segment *and element* under the
  caret (e.g. `EDIFACT · NAD-3.1 — City`) as you move around.
- **Validation** — check the envelope integrity every dialect builds in:
  segment counts (`UNT`, `SE`, `MTR`), message/transaction counts (`UNZ`,
  `GE`, `IEA`, `END`, `UNE`), unclosed messages/groups/transaction sets, and
  control-reference echoes (`UNB`↔`UNZ`, `ISA`↔`IEA`, `UNH`↔`UNT`, `ST`↔`SE`,
  `UNG`↔`UNE`). Issues open in a quick panel that jumps to the offending
  segment, problem segments get a squiggly underline, and the optional
  `validate_on_save` setting re-checks on every save.
- **Envelope repair** — after hand-editing a message, `EDI: Repair Envelope`
  recomputes every count and re-syncs the control references in one step.
- **Qualifier decoding** — common code values are translated inline: hover
  `DTM+137:...` and the popup reads `137 = Document/message date`; `NAD+BY`,
  `QTY+21`, X12 `ST*850`, HL7 `PV1` patient classes and many more.
- **Outline & completions** — `EDI: Outline` browses the segment structure in
  a quick panel, Goto Symbol (`Ctrl+R`) navigates by segment, and typing a
  segment tag offers completions with the segment's name.
- **Convert to JSON / JSONC / XML** — turn a message into a structured
  document in a new tab. The JSONC output is self-documenting: every segment
  is preceded by a comment explaining what it does, and every element carries
  its positional name. Release characters and HL7 escapes are decoded; values
  stay strings so leading zeros and implied decimals survive.
- **Normalize to JSON** — the integration-platform view of a message: every
  segment, composite and element keyed by its *official name* from the
  standard (`beginning_of_message_BGM`, `document_message_number_1004`), the
  envelope turned into real nesting (interchange → functional group →
  message) and EDIFACT segment groups nested per the official message
  definitions (the D.96A directory is bundled). See
  [Normalized output](#normalized-output).
- **Automatic dialect detection** — the delimiters are read from the message
  itself (EDIFACT `UNA`, X12 `ISA`, HL7 `MSH`) with sensible fallbacks, so
  non-standard delimiter sets are handled correctly.
- **Syntax highlighting** — dedicated syntax definitions highlight segment tags
  (also mid-line in minified messages), service/envelope segments, separators,
  release characters, terminators and numeric values; `first_line_match` lets
  Sublime pick the right syntax on its own. Goto Symbol (`Ctrl+R`) navigates
  by segment.
- **Release/escape aware** — an escaped terminator (EDIFACT `?'`, HL7 `\`)
  never falsely ends a segment, and escaped values are decoded on conversion.

## Supported formats

| # | Format | Family | Notes |
|---|--------|--------|-------|
| 1 | **UN/EDIFACT** | EDIFACT | Full delimiter + `UNA` service-string detection |
| 2 | **ANSI ASC X12** | X12 | Delimiters read from the fixed-width `ISA` header |
| 3 | **TRADACOMS** | TRADACOMS | UK retail; `=` tag separator |
| 4 | **HL7 v2.x** | HL7 | `MSH` encoding characters; CR-delimited segments |
| 5 | **EANCOM** | EDIFACT subset | Shares EDIFACT delimiters |
| 6 | **ODETTE** | EDIFACT subset | Automotive; shares EDIFACT delimiters |
| 7 | **EDIG@S** | EDIFACT subset | Gas industry; shares EDIFACT delimiters |
| 8 | **IATA / PADIS** | EDIFACT subset | Air transport; shares EDIFACT delimiters |
| 9 | **VDA** | *(planned)* | German automotive, fixed-length records |
| 10 | **VICS / EDIFICE / GS1** | X12 / EDIFACT subsets | Industry profiles of X12 / EDIFACT |

EDIFACT and its subsets (EANCOM, ODETTE, EDIG@S, IATA/PADIS) share one parsing
engine because they use identical delimiters and service strings; the dialect is
still reported individually so segment tables can diverge over time.

## Commands

All commands are available from the **Command Palette** (`Ctrl/Cmd+Shift+P`,
type "EDI") and the **Tools → EDIBlime** menu; the editor context menu carries
the common actions (beautify, minify, hints, explain, validate, repair,
outline, convert).

| Command | Palette entry | Default key binding |
|---------|---------------|---------------------|
| `edi_beautify` | EDI: Beautify (one segment per line) | `Ctrl+Alt+B` / `Cmd+Alt+B` |
| `edi_minify` | EDI: Minify (collapse to single line) | `Ctrl+Alt+M` / `Cmd+Alt+M` |
| `edi_toggle_hints` | EDI: Toggle Inline Hints | `Ctrl+Alt+H` / `Cmd+Alt+H` |
| `edi_explain_segment` | EDI: Explain Segment Under Caret | `Ctrl+Alt+E` / `Cmd+Alt+E` |
| `edi_validate` | EDI: Validate Structure | `Ctrl+Alt+V` / `Ctrl+Cmd+V` |
| `edi_repair` | EDI: Repair Envelope (fix counts and references) | `Ctrl+Alt+R` / `Ctrl+Cmd+R` |
| `edi_outline` | EDI: Outline (browse segments) | `Ctrl+Alt+O` / `Ctrl+Cmd+O` |
| `edi_convert` (json) | EDI: Convert to JSON | — |
| `edi_convert` (jsonc) | EDI: Convert to JSONC (with descriptions) | — |
| `edi_convert` (xml) | EDI: Convert to XML | — |
| `edi_convert` (normalized) | EDI: Normalize to JSON (named elements) | — |
| `edi_set_dialect` | EDI: Set Dialect… | — |
| `edi_detect_syntax` | EDI: Detect Syntax | — |

Key bindings are scoped to the package's own syntaxes, so they never fire
(or shadow other packages) in ordinary files.

### Conversion output

`EDI: Convert to JSONC` produces a self-documenting document:

```jsonc
{
  // EDIFACT message converted by EDIBlime
  "dialect": "EDIFACT",
  "delimiters": { "segment": "'", "element": "+", "component": ":" },
  "segments": [

    // UNB — Interchange Header
    // Opens the interchange. Carries the syntax identifier and version (e.g. UNOC:3), ...
    {
      "tag": "UNB",
      "name": "Interchange Header",
      "elements": [
        ["UNOC", "3"],  // 1. Syntax identifier : version (e.g. UNOC:3)
        ["SENDER", "14"],  // 2. Interchange sender (id : qualifier)
        "1"  // 5. Interchange control reference (repeated in UNZ)
      ]
    }
  ]
}
```

Qualifier codes are decoded inline where known — a `DTM+137:...` element's
comment reads `[137 = Document/message date]`.

JSON is the same structure without comments; XML nests
`<segment>` → `<element>` → `<component>` with `name` attributes.

### Normalized output

`EDI: Normalize to JSON` produces the semantic view instead of the
structural one — the shape EDI integration platforms work with. Keys are the
snake_cased **official names** followed by the code that names the item in
the standard:

- the segment tag (`beginning_of_message_BGM`),
- the composite data element code (`document_message_name_C002`,
  `syntax_identifier_S001` for ISO 9735 service composites),
- the simple data element code (`document_message_number_1004`,
  `interchange_control_reference_0020`).

```json
{
  "payloads": [
    {
      "interchange_header_UNB": { "...": "..." },
      "messages": [
        {
          "MESSAGE_TYPE": "ORDERS",
          "message_header_UNH": { "...": "..." },
          "beginning_of_message_BGM": {
            "document_message_name_C002": { "document_message_name_coded_1001": "220" },
            "document_message_number_1004": "PO12345"
          },
          "date_time_period_DTM_list": [ { "...": "..." } ],
          "line_item_LIN_groups": [ { "...": "..." } ],
          "message_trailer_UNT": { "...": "..." }
        }
      ],
      "interchange_trailer_UNZ": { "...": "..." }
    }
  ],
  "context": {}
}
```

The envelope becomes real nesting (one payload per interchange, functional
groups when `UNG`/`GS` are present), repeatable segments become stable
`..._list` arrays, and EDIFACT segment groups become `..._groups` arrays
named after their trigger segment, nested per the official message
definitions. The EDIFACT names come from the bundled UNTDID **D.96A**
directory (the basis of EANCOM 1997) plus ISO 9735 for service segments;
message structures are bundled for ORDERS, ORDRSP, ORDCHG, DESADV, RECADV,
INVOIC, REMADV, PRICAT, SLSRPT, INVRPT, DELFOR, DELJIT, PARTIN, QUOTES and
REQOTE. X12, TRADACOMS and HL7 use the same convention with positional
suffixes (`purchase_order_number_03`, `patient_name_5`) and their own
envelopes (ISA/GS/ST, STX/MHD, MSH). Anything unknown degrades gracefully to
tag/position keys, and stray segments are collected under
`unparsed_segments` — nothing is dropped.

## Settings

`Preferences → Package Settings → EDIBlime → Settings`:

```jsonc
{
    // Turn on inline hints automatically when an EDI file is opened.
    "auto_hints": false,

    // Add a short description to each inline hint (hover for the full one).
    "hints_show_descriptions": false,

    // Explain segments in a popup on mouse hover.
    "hover_help": true,

    // Re-run envelope validation on every save and mark problem segments
    // with a squiggly underline.
    "validate_on_save": false,

    // Colour for the inline hint annotations. Empty = inherit the colour
    // scheme's "comment" colour. Accepts any CSS colour.
    "hint_color": ""
}
```

## Installation

### Package Control (recommended once published)

1. Open the Command Palette and run **Package Control: Install Package**.
2. Search for **EDIBlime** and install.

### Manual

Clone into your Sublime Text `Packages` directory (the folder revealed by
**Preferences → Browse Packages…**):

```sh
git clone https://github.com/encefalopiatto/EDIBlime.git
```

> Name the folder `EDIBlime`. (Resource paths are resolved from the installed
> folder name, so another name still works — but menus and docs assume `EDIBlime`.)

Requires **Sublime Text 4**, build 4095 or later — any stable ST4 release
(4107+) qualifies. The floor is set by the coloured quick-panel kinds (4095);
`QuickPanelItem` (4083) and the inline annotation API (4050) are older.

## How it works

The package is split into a Sublime-independent engine and a thin editor layer:

- **`edi_data.py`** — delimiter dialects, segment names, detailed segment
  descriptions and positional element names.
- **`edi_core.py`** — detection, release-aware segment splitting, element
  parsing, beautify, minify and describe. No Sublime dependency, so it is
  unit tested directly.
- **`edi_convert.py`** — JSON / JSONC / XML conversion.
- **`edi_normalize.py`** — normalization to named JSON (envelope nesting,
  segment groups, official element names).
- **`edi_norm_data.py`** — the normalization reference data: the UNTDID
  D.96A segment directory and message structures, ISO 9735 service segments,
  and the X12 / TRADACOMS / HL7 name tables.
- **`edi_validate.py`** — envelope integrity validation.
- **`edi.py`** — Sublime commands, menus, annotations, hover popups, status
  bar and auto-detection.

## Try it

Sample messages live in [`samples/`](samples). With a git clone, just open
one; with a Package Control install the package is zipped, so run
**View Package File** from the Command Palette, type `EDIBlime/samples` and
pick one, then copy its contents into a new tab (package files open
read-only). Run **EDI: Beautify**, then **EDI: Toggle Inline Hints**.

## Development

Run the test suite from the package root:

```sh
python -m unittest discover -s tests -v
```

The tests cover dialect detection, delimiter extraction, release-character
handling, beautify ↔ minify round-tripping, and segment description lookups
for every supported family.

Segment reference tables are plain dictionaries in `edi_data.py` — adding names
or a new dialect subset needs no code changes to the engine.

## License

[MIT](LICENSE)
