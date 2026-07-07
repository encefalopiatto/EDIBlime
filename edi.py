# -*- coding: utf-8 -*-
"""
SublimeEDI -- beautify, minify and annotate EDI files inside Sublime Text.

This module is the (thin) Sublime Text integration layer. All of the parsing
and formatting logic lives in :mod:`edi_core`, which has no Sublime dependency
and is unit tested separately.

Commands provided (command palette / menus / key bindings):

* ``edi_beautify``       -- one segment per line (valid, human readable EDI)
* ``edi_minify``         -- collapse back to a single compliant line
* ``edi_toggle_hints``   -- non-destructive inline segment descriptions
* ``edi_set_dialect``    -- override the auto-detected dialect for a view
* ``edi_detect_syntax``  -- (re)apply the matching syntax to the view

An :class:`EdiListener` auto-detects the dialect on load, applies the matching
syntax, and keeps hint annotations in sync while editing.
"""

import sublime
import sublime_plugin

from . import edi_core
from . import edi_data


SETTINGS_FILE = "EDI.sublime-settings"
HINT_REGION_KEY = "edi_hints"
# Per-view flag (stored in view settings) tracking whether hints are shown.
HINTS_ENABLED_SETTING = "edi_hints_enabled"
# Per-view dialect override chosen via ``edi_set_dialect``.
DIALECT_OVERRIDE_SETTING = "edi_dialect_override"

# Maps a resolved dialect family/key to the bundled ``.sublime-syntax`` file.
SYNTAX_FOR_DIALECT = {
    "edifact": "Packages/SublimeEDI/EDIFACT.sublime-syntax",
    "x12": "Packages/SublimeEDI/X12.sublime-syntax",
    "tradacoms": "Packages/SublimeEDI/TRADACOMS.sublime-syntax",
    "hl7": "Packages/SublimeEDI/HL7.sublime-syntax",
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
# Text commands
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


class EdiSetDialectCommand(sublime_plugin.TextCommand):
    """Override the auto-detected dialect for this view via a quick panel."""

    def run(self, edit, dialect=None):
        if dialect is not None:
            self._apply(dialect)
            return
        self._keys = sorted(edi_data.SEGMENTS.keys())
        items = [self._label_for(k) for k in self._keys]
        self.view.window().show_quick_panel(items, self._on_choose)

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
# Annotations / syntax helpers
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

    regions = []
    annotations = []
    for start, end, seg, name in spans:
        if not name:
            continue
        # Anchor the annotation to the end of the segment's line so it renders
        # to the right of the data without disturbing it.
        regions.append(sublime.Region(end, end))
        annotations.append(
            '<body style="color:%s">%s &mdash; %s</body>'
            % (_hint_color(view), _escape(seg.tag), _escape(name)))

    if not regions:
        return 0
    view.add_regions(
        HINT_REGION_KEY,
        regions,
        "",              # no scope highlight
        "",              # no gutter icon
        sublime.HIDDEN,  # do not underline / box the anchor region
        annotations,
        _hint_color(view),
    )
    return len(regions)


def _escape(s):
    return (s.replace("&", "&amp;")
             .replace("<", "&lt;")
             .replace(">", "&gt;"))


# ---------------------------------------------------------------------------
# Event listener
# ---------------------------------------------------------------------------

class EdiListener(sublime_plugin.EventListener):
    """Auto-detect dialect on load and keep hints fresh while editing."""

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

    def _auto(self, view):
        view.settings().set("edi_seen", True)
        if view.size() == 0 or view.size() > 5 * 1024 * 1024:
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
