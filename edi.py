# -*- coding: utf-8 -*-
"""
EDIBlime -- beautify, minify, annotate, explain, validate and convert EDI
files inside Sublime Text.

This module is the (thin) Sublime Text integration layer. All parsing,
formatting, conversion and validation logic lives in :mod:`edi_core`,
:mod:`edi_convert` and :mod:`edi_validate`, which have no Sublime dependency
and are unit tested separately.

Commands provided (command palette / menus / key bindings):

* ``edi_beautify``        -- one segment per line (valid, human readable EDI)
* ``edi_minify``          -- collapse back to a single compliant line
* ``edi_toggle_hints``    -- non-destructive inline segment descriptions
* ``edi_explain_segment`` -- popup explaining the segment under the caret,
                             element by element
* ``edi_validate``        -- check envelope integrity (counts / references)
* ``edi_convert``         -- convert the buffer to JSON, JSONC or XML
* ``edi_set_dialect``     -- override the auto-detected dialect for a view
* ``edi_detect_syntax``   -- (re)apply the matching syntax to the view

An :class:`EdiListener` auto-detects the dialect on load, applies the matching
syntax, keeps hint annotations in sync while editing, shows segment help on
hover, and reports the segment under the caret in the status bar.
"""

import sublime
import sublime_plugin

from . import edi_convert
from . import edi_core
from . import edi_data
from . import edi_validate

# Resolve the installed package name dynamically so bundled resource paths
# (syntaxes) keep working if the package folder is renamed.
_PACKAGE = (__package__ or "EDIBlime").split(".")[0]

SETTINGS_FILE = "EDIBlime.sublime-settings"
HINT_REGION_KEY = "edi_hints"
STATUS_KEY = "edi_status"
# Per-view flag (stored in view settings) tracking whether hints are shown.
HINTS_ENABLED_SETTING = "edi_hints_enabled"
# Per-view dialect override chosen via ``edi_set_dialect``.
DIALECT_OVERRIDE_SETTING = "edi_dialect_override"
# Views larger than this are left alone (annotations would be too slow).
MAX_AUTO_SIZE = 5 * 1024 * 1024

# Maps a resolved dialect family to the bundled ``.sublime-syntax`` file.
SYNTAX_FOR_DIALECT = {
    family: "Packages/%s/%s.sublime-syntax" % (_PACKAGE, name)
    for family, name in (
        ("edifact", "EDIFACT"),
        ("x12", "X12"),
        ("tradacoms", "TRADACOMS"),
        ("hl7", "HL7"),
    )
}


def _settings():
    return sublime.load_settings(SETTINGS_FILE)


def _view_text(view):
    return view.substr(sublime.Region(0, view.size()))


def _resolve_dialect(view, text=None):
    """Return the :class:`edi_core.Dialect` for ``view``.

    Honours a per-view override set via ``edi_set_dialect``; otherwise detects
    from the buffer contents.
    """
    text = _view_text(view) if text is None else text
    override = view.settings().get(DIALECT_OVERRIDE_SETTING)
    if override and override in edi_data.SEGMENTS:
        # Re-detect so message-specific delimiters (UNA/ISA/MSH) are honoured,
        # then re-key it to the requested dialect for name lookups.
        detected = edi_core.detect(text)
        if detected is not None and detected.family == edi_data.dialect_family(override):
            detected.key = override
            detected.label = edi_data.EDIFACT_SUBSETS.get(
                override, edi_data.DIALECTS[detected.family]["label"])
            return detected
        return edi_core.Dialect.from_family(override)
    return edi_core.detect(text)


def _looks_like_edi(view):
    return _resolve_dialect(view) is not None


# ---------------------------------------------------------------------------
# Formatting commands
# ---------------------------------------------------------------------------

class EdiBeautifyCommand(sublime_plugin.TextCommand):
    """Reformat the buffer with one segment per line."""

    def run(self, edit):
        text = _view_text(self.view)
        dialect = _resolve_dialect(self.view, text)
        if dialect is None:
            sublime.status_message("EDI: could not detect an EDI dialect")
            return
        newline = "\n" if self.view.line_endings() != "Windows" else "\r\n"
        result = edi_core.beautify(text, dialect=dialect, newline=newline)
        if result == text:
            sublime.status_message("EDI: already beautified")
            return
        self.view.replace(edit, sublime.Region(0, self.view.size()), result)
        sublime.status_message("EDI: beautified %s" % dialect.label)
        _apply_syntax(self.view, dialect)
        if self.view.settings().get(HINTS_ENABLED_SETTING):
            _refresh_hints(self.view)

    def is_enabled(self):
        return _looks_like_edi(self.view)


class EdiMinifyCommand(sublime_plugin.TextCommand):
    """Collapse the buffer back to a single compliant EDI line."""

    def run(self, edit):
        text = _view_text(self.view)
        dialect = _resolve_dialect(self.view, text)
        if dialect is None:
            sublime.status_message("EDI: could not detect an EDI dialect")
            return
        result = edi_core.minify(text, dialect=dialect)
        self.view.replace(edit, sublime.Region(0, self.view.size()), result)
        sublime.status_message("EDI: minified %s" % dialect.label)
        # Inline hints make no sense on a single line; clear them.
        self.view.erase_regions(HINT_REGION_KEY)

    def is_enabled(self):
        return _looks_like_edi(self.view)


class EdiToggleHintsCommand(sublime_plugin.TextCommand):
    """Toggle non-destructive inline segment descriptions."""

    def run(self, edit):
        settings = self.view.settings()
        enabled = not settings.get(HINTS_ENABLED_SETTING, False)
        settings.set(HINTS_ENABLED_SETTING, enabled)
        if enabled:
            count = _refresh_hints(self.view)
            sublime.status_message("EDI: hints on (%d segments)" % count)
        else:
            self.view.erase_regions(HINT_REGION_KEY)
            sublime.status_message("EDI: hints off")

    def is_enabled(self):
        return _looks_like_edi(self.view)


# ---------------------------------------------------------------------------
# Explain / validate commands
# ---------------------------------------------------------------------------

class EdiExplainSegmentCommand(sublime_plugin.TextCommand):
    """Show a popup explaining the segment under the caret."""

    def run(self, edit):
        sel = self.view.sel()
        if not sel:
            return
        point = sel[0].begin()
        html = _segment_popup_html(self.view, point)
        if html is None:
            sublime.status_message("EDI: no segment under the caret")
            return
        self.view.show_popup(
            html,
            flags=sublime.HIDE_ON_MOUSE_MOVE_AWAY,
            location=point,
            max_width=760,
            max_height=560,
        )

    def is_enabled(self):
        return _looks_like_edi(self.view)


class EdiValidateCommand(sublime_plugin.TextCommand):
    """Validate envelope integrity and browse issues in a quick panel."""

    def run(self, edit):
        text = _view_text(self.view)
        dialect = _resolve_dialect(self.view, text)
        if dialect is None:
            sublime.status_message("EDI: could not detect an EDI dialect")
            return
        issues = edi_validate.validate(text, dialect)
        if not issues:
            sublime.message_dialog(
                "EDI: %s structure is valid.\n\n"
                "All segment counts, message counts and control references check out."
                % dialect.label)
            return

        self._issues = issues
        items = []
        for issue in issues:
            row, col = self.view.rowcol(issue["offset"])
            items.append(sublime.QuickPanelItem(
                trigger=issue["message"],
                details="",
                annotation="line %d" % (row + 1),
                kind=_KIND_FOR_SEVERITY.get(issue["severity"], sublime.KIND_AMBIGUOUS),
            ))
        window = self.view.window()
        if window:
            window.show_quick_panel(
                items, self._on_done, on_highlight=self._jump_to)
        error_count = sum(1 for i in issues if i["severity"] == "error")
        sublime.status_message(
            "EDI: %d issue(s), %d error(s)" % (len(issues), error_count))

    def _jump_to(self, index):
        if index < 0:
            return
        offset = self._issues[index]["offset"]
        self.view.show_at_center(offset)
        self.view.sel().clear()
        self.view.sel().add(sublime.Region(offset))

    def _on_done(self, index):
        if index >= 0:
            self._jump_to(index)

    def is_enabled(self):
        return _looks_like_edi(self.view)


_KIND_FOR_SEVERITY = {
    "error": (sublime.KIND_ID_COLOR_REDISH, "E", "Error"),
    "warning": (sublime.KIND_ID_COLOR_YELLOWISH, "W", "Warning"),
    "info": (sublime.KIND_ID_COLOR_BLUISH, "I", "Info"),
}


# ---------------------------------------------------------------------------
# Conversion command
# ---------------------------------------------------------------------------

class EdiConvertCommand(sublime_plugin.TextCommand):
    """Convert the buffer to JSON, JSONC or XML into a new tab."""

    CONVERTERS = {
        "json": (edi_convert.to_json, "JSON.sublime-syntax", ".json"),
        "jsonc": (edi_convert.to_jsonc, "JSON.sublime-syntax", ".jsonc"),
        "xml": (edi_convert.to_xml, "XML.sublime-syntax", ".xml"),
    }

    def run(self, edit, format="json"):
        converter = self.CONVERTERS.get(format)
        if converter is None:
            sublime.status_message("EDI: unknown conversion format %r" % format)
            return
        text = _view_text(self.view)
        dialect = _resolve_dialect(self.view, text)
        if dialect is None:
            sublime.status_message("EDI: could not detect an EDI dialect")
            return
        func, syntax, extension = converter
        try:
            result = func(text, dialect)
        except ValueError as exc:
            sublime.status_message("EDI: %s" % exc)
            return

        window = self.view.window()
        if window is None:
            return
        out = window.new_file()
        out.set_scratch(True)
        out.set_name(self._output_name(extension))
        out.assign_syntax(_find_syntax(syntax))
        out.run_command("append", {"characters": result})
        sublime.status_message(
            "EDI: converted %s to %s" % (dialect.label, format.upper()))

    def _output_name(self, extension):
        name = self.view.name() or self.view.file_name() or "message"
        import os
        base = os.path.splitext(os.path.basename(name))[0]
        return base + extension

    def is_enabled(self):
        return _looks_like_edi(self.view)


def _find_syntax(basename):
    """Locate a syntax bundled with Sublime by file basename."""
    matches = sublime.find_resources(basename)
    return matches[-1] if matches else "Packages/Text/Plain text.tmLanguage"


# ---------------------------------------------------------------------------
# Dialect / syntax commands
# ---------------------------------------------------------------------------

class EdiSetDialectCommand(sublime_plugin.TextCommand):
    """Override the auto-detected dialect for this view via a quick panel."""

    def run(self, edit, dialect=None):
        if dialect is not None:
            self._apply(dialect)
            return
        self._keys = sorted(edi_data.SEGMENTS.keys())
        items = [self._label_for(k) for k in self._keys]
        window = self.view.window()
        if window:
            window.show_quick_panel(items, self._on_choose)

    def _label_for(self, key):
        if key in edi_data.EDIFACT_SUBSETS:
            return "%s (EDIFACT subset)" % edi_data.EDIFACT_SUBSETS[key]
        return edi_data.DIALECTS[edi_data.dialect_family(key)]["label"]

    def _on_choose(self, index):
        if index >= 0:
            self._apply(self._keys[index])

    def _apply(self, dialect):
        self.view.settings().set(DIALECT_OVERRIDE_SETTING, dialect)
        resolved = edi_core.Dialect.from_family(dialect)
        _apply_syntax(self.view, resolved)
        if self.view.settings().get(HINTS_ENABLED_SETTING):
            _refresh_hints(self.view)
        sublime.status_message("EDI: dialect set to %s" % resolved.label)


class EdiDetectSyntaxCommand(sublime_plugin.TextCommand):
    """(Re)detect the dialect and apply the matching syntax."""

    def run(self, edit):
        self.view.settings().erase(DIALECT_OVERRIDE_SETTING)
        dialect = _resolve_dialect(self.view)
        if dialect is None:
            sublime.status_message("EDI: could not detect an EDI dialect")
            return
        _apply_syntax(self.view, dialect)
        sublime.status_message("EDI: detected %s" % dialect.label)


# ---------------------------------------------------------------------------
# Annotations / popup / syntax helpers
# ---------------------------------------------------------------------------

def _apply_syntax(view, dialect):
    syntax = SYNTAX_FOR_DIALECT.get(dialect.family)
    if syntax:
        # Avoid needless syntax reloads (which reset folds/selection state).
        current = view.settings().get("syntax")
        if current != syntax:
            view.assign_syntax(syntax)


def _hint_color(view):
    color = _settings().get("hint_color")
    if color:
        return color
    # Derive a subdued colour from the active colour scheme.
    try:
        style = view.style_for_scope("comment")
        return style.get("foreground", "#808080")
    except Exception:
        return "#808080"


def _refresh_hints(view):
    """Recompute and render inline hint annotations. Returns the segment count."""
    view.erase_regions(HINT_REGION_KEY)
    text = _view_text(view)
    dialect = _resolve_dialect(view, text)
    if dialect is None:
        return 0
    spans = edi_core.describe_spans(text, dialect=dialect)
    if not spans:
        return 0

    verbose = _settings().get("hints_show_descriptions", False)
    color = _hint_color(view)
    regions = []
    annotations = []
    for start, end, seg, name in spans:
        if not name:
            continue
        label = "%s &mdash; %s" % (_escape(seg.tag), _escape(name))
        if verbose:
            detail = edi_data.segment_detail(dialect.key, seg.tag)
            if detail:
                label += ": %s" % _escape(_truncate(detail, 120))
        # Anchor the annotation to the end of the segment's line so it renders
        # to the right of the data without disturbing it.
        regions.append(sublime.Region(end, end))
        annotations.append('<body style="color:%s">%s</body>' % (color, label))

    if not regions:
        return 0
    view.add_regions(
        HINT_REGION_KEY,
        regions,
        "",              # no scope highlight
        "",              # no gutter icon
        sublime.HIDDEN,  # do not underline / box the anchor region
        annotations,
        color,
    )
    return len(regions)


def _truncate(text, limit):
    if len(text) <= limit:
        return text
    return text[:limit].rsplit(" ", 1)[0] + "…"


def _escape(s):
    return (s.replace("&", "&amp;")
             .replace("<", "&lt;")
             .replace(">", "&gt;"))


POPUP_CSS = """
body { margin: 0.4rem 0.6rem; font-size: 0.92rem; }
h1 { font-size: 1.05rem; margin: 0 0 0.2rem 0; }
h1 code { color: var(--orangish); }
.dialect { color: color(var(--foreground) alpha(0.55)); font-size: 0.85rem; }
p.detail { margin: 0.4rem 0; }
.el { margin: 0.12rem 0; }
.idx { color: color(var(--foreground) alpha(0.5)); }
.val { color: var(--greenish); }
.name { color: color(var(--foreground) alpha(0.75)); }
"""


def _segment_popup_html(view, point):
    """Build the explain-segment popup for the segment containing ``point``."""
    text = _view_text(view)
    dialect = _resolve_dialect(view, text)
    if dialect is None:
        return None
    target = None
    for start, end, seg in dialect.segment_spans(text):
        if start <= point <= end:
            target = seg
            break
    if target is None:
        return None

    tag = target.tag
    name = edi_data.segment_name(dialect.key, tag)
    detail = edi_data.segment_detail(dialect.key, tag)
    names = edi_data.element_names(dialect.key, tag)

    parts = ["<style>%s</style>" % POPUP_CSS]
    title = "<code>%s</code>" % _escape(tag)
    if name:
        title += " &mdash; %s" % _escape(name)
    parts.append("<h1>%s</h1>" % title)
    parts.append('<div class="dialect">%s segment</div>' % _escape(dialect.label))
    if detail:
        parts.append('<p class="detail">%s</p>' % _escape(detail))

    elements = target.elements()
    if elements:
        rows = []
        for i, components in enumerate(elements):
            value = dialect.component_separator.join(components)
            if not value:
                continue
            label = names[i] if i < len(names) else ""
            row = ('<div class="el"><span class="idx">%d.</span> '
                   '<span class="val">%s</span>' % (i + 1, _escape(value)))
            if label:
                row += ' <span class="name">&mdash; %s</span>' % _escape(label)
            row += "</div>"
            rows.append(row)
        if rows:
            parts.append("".join(rows))
    return "".join(parts)


# ---------------------------------------------------------------------------
# Event listener
# ---------------------------------------------------------------------------

class EdiListener(sublime_plugin.EventListener):
    """Auto-detect dialect on load, keep hints fresh, hover help, status bar."""

    def on_load_async(self, view):
        self._auto(view)

    def on_activated_async(self, view):
        # Handle buffers that were already open when the plugin loaded.
        if view.settings().get("edi_seen"):
            return
        self._auto(view)

    def on_modified_async(self, view):
        if view.settings().get(HINTS_ENABLED_SETTING):
            _debounce(view)

    def on_selection_modified_async(self, view):
        if not view.settings().get("edi_seen"):
            return
        if view.size() > MAX_AUTO_SIZE:
            return
        dialect = _resolve_dialect(view)
        if dialect is None:
            view.erase_status(STATUS_KEY)
            return
        sel = view.sel()
        if not sel:
            return
        point = sel[0].begin()
        text = _view_text(view)
        for start, end, seg in dialect.segment_spans(text):
            if start <= point <= end:
                name = edi_data.segment_name(dialect.key, seg.tag)
                status = "%s · %s" % (dialect.label, seg.tag)
                if name:
                    status += " — %s" % name
                view.set_status(STATUS_KEY, status)
                return
        view.set_status(STATUS_KEY, dialect.label)

    def on_hover(self, view, point, hover_zone):
        if hover_zone != sublime.HOVER_TEXT:
            return
        if not _settings().get("hover_help", True):
            return
        if view.size() > MAX_AUTO_SIZE or not view.settings().get("edi_seen"):
            return
        if not _looks_like_edi(view):
            return
        html = _segment_popup_html(view, point)
        if html is None:
            return
        view.show_popup(
            html,
            flags=sublime.HIDE_ON_MOUSE_MOVE_AWAY,
            location=point,
            max_width=760,
            max_height=560,
        )

    def _auto(self, view):
        view.settings().set("edi_seen", True)
        if view.size() == 0 or view.size() > MAX_AUTO_SIZE:
            return
        dialect = _resolve_dialect(view)
        if dialect is None:
            return
        _apply_syntax(view, dialect)
        if _settings().get("auto_hints", False):
            view.settings().set(HINTS_ENABLED_SETTING, True)
            _refresh_hints(view)


# Simple debounce so hints only recompute after typing settles.
_pending = {}


def _debounce(view, delay=350):
    vid = view.id()
    token = _pending.get(vid, 0) + 1
    _pending[vid] = token

    def go():
        if _pending.get(vid) == token and view.is_valid():
            _refresh_hints(view)

    sublime.set_timeout_async(go, delay)
