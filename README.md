# SublimeEDI

A [Sublime Text](https://www.sublimetext.com/) package to **beautify, clean,
minify and annotate EDI documents** — with first-class support for **UN/EDIFACT**
and the other major delimiter-based EDI standards.

Raw EDI arrives as one long, unreadable line. SublimeEDI turns it into something
a human can actually work with: one segment per line, syntax highlighting, and
optional inline hints that name every segment — without ever changing the data.

```
UNB+UNOC:3+SENDER:14+RECEIVER:14+200101:1200+1'UNH+1+ORDERS:D:96A:UN'BGM+220+PO12345+9'...
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
- **Automatic dialect detection** — the delimiters are read from the message
  itself (EDIFACT `UNA`, X12 `ISA`, HL7 `MSH`) with sensible fallbacks, so
  non-standard delimiter sets are handled correctly.
- **Syntax highlighting** — dedicated syntax definitions highlight segment tags,
  service/envelope segments, element/component separators, release characters
  and terminators.
- **Release/escape aware** — an escaped terminator (EDIFACT `?'`, HL7 `\`)
  never falsely ends a segment.

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
type "EDI"), the **Tools → EDI** menu, and the editor context menu.

| Command | Palette entry | Default key binding |
|---------|---------------|---------------------|
| `edi_beautify` | EDI: Beautify (one segment per line) | `Ctrl+Alt+B` / `Cmd+Alt+B` |
| `edi_minify` | EDI: Minify (collapse to single line) | `Ctrl+Alt+M` / `Cmd+Alt+M` |
| `edi_toggle_hints` | EDI: Toggle Inline Hints | `Ctrl+Alt+H` / `Cmd+Alt+H` |
| `edi_set_dialect` | EDI: Set Dialect… | — |
| `edi_detect_syntax` | EDI: Detect Syntax | — |

## Settings

`Preferences → Package Settings → EDI → Settings`:

```jsonc
{
    // Turn on inline hints automatically when an EDI file is opened.
    "auto_hints": false,

    // Colour for the inline hint annotations. Empty = inherit the colour
    // scheme's "comment" colour. Accepts any CSS colour.
    "hint_color": ""
}
```

## Installation

### Package Control (recommended once published)

1. Open the Command Palette and run **Package Control: Install Package**.
2. Search for **EDI** and install.

### Manual

Clone into your Sublime Text `Packages` directory (the folder revealed by
**Preferences → Browse Packages…**):

```sh
git clone https://github.com/encefalopiatto/SublimeEDI.git "SublimeEDI"
```

> The package folder **must** be named `SublimeEDI` so the bundled syntax
> references (`Packages/SublimeEDI/…`) resolve.

Requires **Sublime Text 4** (build 4050+) for the inline annotation API.

## How it works

The package is split into a Sublime-independent engine and a thin editor layer:

- **`edi_data.py`** — delimiter dialects and segment-name reference tables.
- **`edi_core.py`** — detection, release-aware segment splitting, beautify,
  minify and describe. No Sublime dependency, so it is unit tested directly.
- **`edi.py`** — Sublime commands, menus, annotations and auto-detection.

## Try it

Sample messages live in [`samples/`](samples). Open one and run
**EDI: Beautify**, then **EDI: Toggle Inline Hints**.

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
