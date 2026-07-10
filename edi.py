# -*- coding: utf-8 -*-
"""
EDIBlime -- beautify, minify, annotate, explain, validate, repair and convert
EDI files inside Sublime Text.

This module is the (thin) Sublime Text integration layer. All parsing,
formatting, conversion, normalization and validation logic lives in
:mod:`edi_core`, :mod:`edi_convert`, :mod:`edi_normalize` and
:mod:`edi_validate`, which have no Sublime dependency and are unit tested
separately.

Commands provided (command palette / menus / key bindings):

* ``edi_beautify``        -- one segment per line (valid, human readable EDI)
* ``edi_minify``          -- collapse back to a single compliant line
* ``edi_toggle_hints``    -- non-destructive inline segment descriptions
* ``edi_explain_segment`` -- popup explaining the segment under the caret,
                             element by element (with qualifier decoding)
* ``edi_validate``        -- check envelope integrity (counts / references)
* ``edi_repair``          -- recompute counts and re-sync control references
* ``edi_outline``         -- browse the message structure in a quick panel
* ``edi_convert``         -- convert the buffer to JSON, JSONC or XML, or
                             normalize it to JSON with named elements
* ``edi_set_dialect``     -- override the auto-detected dialect for a view
* ``edi_detect_syntax``   -- (re)apply the matching syntax to the view

An :class:`EdiListener` auto-detects the dialect on load, applies the matching
syntax, keeps hint annotations in sync while editing, shows segment help on
hover, and reports the segment/element under the caret in the status bar.

Performance notes: detection results and parsed segment spans are cached per
view and keyed to ``view.change_count()``, so caret movement and hovering
never re-parse an unchanged buffer, and none of the listeners do any work in
views that were not positively identified as EDI.
"""

import bisect
import os

import sublime
import sublime_plugin

from . import edi_convert
from . import edi_core
from . import edi_data
from . import edi_normalize
from . import edi_validate

# Resolve the installed package name dynamically so bundled resource paths
# (syntaxes) keep working if the package folder is renamed.
_PACKAGE = (__package__ or "EDIBlime").split(".")[0]

SETTINGS_FILE = "EDIBlime.sublime-settings"
HINT_REGION_KEY = "edi_hints"
ISSUE_REGION_KEY = "edi_issues"
STATUS_KEY = "edi_status"
# Per-view flag (stored in view settings) tracking whether hints are shown.
HINTS_ENABLED_SETTING = "edi_hints_enabled"
# Per-view detection verdict: set to True/False once _auto has looked at real
# content. All listeners gate on this so non-EDI views cost nothing.
IS_EDI_SETTING = "edi_is_edi"
# Per-view dialect override chosen via ``edi_set_dialect``.
DIALECT_OVERRIDE_SETTING = "edi_dialect_override"
# Views larger than this are left alone (parsing/annotating would be too slow).
MAX_AUTO_SIZE = 5 * 1024 * 1024
# is_enabled() may run a live detection on buffers up to this size when the
# view has not been classified yet (fresh paste, palette opened immediately).
MAX_ENABLED_PROBE_SIZE = 256 * 1024

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
    """Cheap enablement check for commands.

    Uses the cached per-view verdict when available; falls back to a live
    detection only for buffers small enough that it cannot hurt (so commands
    still work on a fresh paste before the listener has classified the view).
    """
    verdict = view.settings().get(IS_EDI_SETTING)
    if verdict is not None:
        return bool(verdict)
    if view.size() == 0 or view.size() > MAX_ENABLED_PROBE_SIZE:
        return False
    return _resolve_dialect(view) is not None


# ---------------------------------------------------------------------------
# Per-view analysis cache (dialect + parsed spans, keyed by change_count)
# ---------------------------------------------------------------------------

_analysis_cache = {}  # view_id -> (change_count, dialect, spans)


def _cached_analysis(view):
    """Return ``(dialect, spans)`` for the view, parsing at most once per edit.

    ``spans`` is ``[(start, end, Segment), ...]``. Returns ``(None, None)``
    when the buffer is too large or is not EDI.
    """
    if view.size() > MAX_AUTO_SIZE:
        return None, None
    vid = view.id()
    change_count = view.change_count()
    hit = _analysis_cache.get(vid)
    if hit is not None and hit[0] == change_count:
        return hit[1], hit[2]
    text = _view_text(view)
    dialect = _resolve_dialect(view, text)
    spans = dialect.segment_spans(text) if dialect is not None else None
    _analysis_cache[vid] = (change_count, dialect, spans)
    return dialect, spans


def _drop_view_state(view):
    _analysis_cache.pop(view.id(), None)
    _pending.pop(view.id(), None)


def _span_at(spans, point):
    """Binary-search the span containing ``point``; None when between spans."""
    if not spans:
        return None
    idx = bisect.bisect_right([s[0] for s in spans], point) - 1
    if idx < 0:
        return None
    start, end, seg = spans[idx]
    if start <= point <= end:
        return spans[idx]
    return None


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
        # Always insert "\n": Sublime buffers store line breaks as "\n"
        # internally and convert to the view's line_endings only on save;
        # inserting "\r\n" would leave literal CR characters in the buffer.
        result = edi_core.beautify(text, dialect=dialect, newline="\n")
        if result == text:
            sublime.status_message("EDI: already beautified")
            return
        self.view.replace(edit, sublime.Region(0, self.view.size()), result)
        sublime.status_message("EDI: beautified %s" % dialect.label)
        self.view.settings().set(IS_EDI_SETTING, True)
        _apply_syntax(self.view, dialect)
        if self.view.settings().get(HINTS_ENABLED_SETTING):
            _refresh_hints(self.view)

    def is_enabled(self):
        return _looks_like_edi(self.view)

    # Hide (not just grey out) the menu entries in non-EDI files.
    is_visible = is_enabled


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
        # Inline hints make no sense on a single line; turn them off properly
        # so the toggle state stays in sync.
        self.view.erase_regions(HINT_REGION_KEY)
        self.view.settings().set(HINTS_ENABLED_SETTING, False)

    def is_enabled(self):
        return _looks_like_edi(self.view)

    # Hide (not just grey out) the menu entries in non-EDI files.
    is_visible = is_enabled


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

    # Hide (not just grey out) the menu entries in non-EDI files.
    is_visible = is_enabled


# ---------------------------------------------------------------------------
# Explain / validate / repair / outline commands
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

    # Hide (not just grey out) the menu entries in non-EDI files.
    is_visible = is_enabled


class EdiValidateCommand(sublime_plugin.TextCommand):
    """Validate envelope integrity and browse issues in a quick panel."""

    def run(self, edit):
        dialect, _spans = _cached_analysis(self.view)
        if dialect is None:
            sublime.status_message("EDI: could not detect an EDI dialect")
            return
        issues = edi_validate.validate(_view_text(self.view), dialect)
        _render_issue_regions(self.view, issues)
        if not issues:
            sublime.message_dialog(
                "EDI: %s structure is valid.\n\n"
                "All segment counts, message counts and control references check out."
                % dialect.label)
            return

        view = self.view
        # Keep everything local (no state on the command instance) and restore
        # the original position when the panel is cancelled.
        original_sel = [(r.a, r.b) for r in view.sel()]
        original_viewport = view.viewport_position()

        items = []
        for issue in issues:
            row, _col = view.rowcol(issue["offset"])
            items.append(sublime.QuickPanelItem(
                trigger=issue["message"],
                details="",
                annotation="line %d" % (row + 1),
                kind=_KIND_FOR_SEVERITY.get(issue["severity"], sublime.KIND_AMBIGUOUS),
            ))

        def jump_to(index):
            if index < 0:
                return
            offset = issues[index]["offset"]
            view.show_at_center(offset)
            view.sel().clear()
            view.sel().add(sublime.Region(offset))

        def on_done(index):
            if index >= 0:
                jump_to(index)
                return
            view.sel().clear()
            for a, b in original_sel:
                view.sel().add(sublime.Region(a, b))
            view.set_viewport_position(original_viewport)

        window = view.window()
        if window:
            window.show_quick_panel(items, on_done, on_highlight=jump_to)
        error_count = sum(1 for i in issues if i["severity"] == "error")
        sublime.status_message(
            "EDI: %d issue(s), %d error(s)" % (len(issues), error_count))

    def is_enabled(self):
        return _looks_like_edi(self.view)

    # Hide (not just grey out) the menu entries in non-EDI files.
    is_visible = is_enabled


class EdiRepairCommand(sublime_plugin.TextCommand):
    """Recompute envelope counts and re-sync control references."""

    def run(self, edit):
        text = _view_text(self.view)
        dialect = _resolve_dialect(self.view, text)
        if dialect is None:
            sublime.status_message("EDI: could not detect an EDI dialect")
            return
        fixed, changed = edi_validate.repair(text, dialect)
        if not changed or fixed == text:
            sublime.status_message("EDI: envelope already consistent")
            return
        self.view.replace(edit, sublime.Region(0, self.view.size()), fixed)
        # The old issue squiggles refer to pre-repair offsets.
        self.view.erase_regions(ISSUE_REGION_KEY)
        sublime.status_message(
            "EDI: repaired %d envelope segment(s)" % changed)

    def is_enabled(self):
        return _looks_like_edi(self.view)

    # Hide (not just grey out) the menu entries in non-EDI files.
    is_visible = is_enabled


class EdiOutlineCommand(sublime_plugin.TextCommand):
    """Browse the message structure (all segments) in a quick panel."""

    def run(self, edit):
        dialect, spans = _cached_analysis(self.view)
        if dialect is None or not spans:
            sublime.status_message("EDI: could not detect an EDI dialect")
            return

        view = self.view
        original_sel = [(r.a, r.b) for r in view.sel()]
        original_viewport = view.viewport_position()

        items = []
        offsets = []
        for start, _end, seg in spans:
            name = edi_data.segment_name(dialect.key, seg.tag)
            preview = seg.content[:80].replace("\n", " ")
            items.append(sublime.QuickPanelItem(
                trigger="%s — %s" % (seg.tag, name) if name else seg.tag,
                details="",
                annotation=preview,
                kind=(sublime.KIND_ID_NAVIGATION, seg.tag[0], "Segment"),
            ))
            offsets.append(start)

        def jump_to(index):
            if index < 0:
                return
            view.show_at_center(offsets[index])
            view.sel().clear()
            view.sel().add(sublime.Region(offsets[index]))

        def on_done(index):
            if index >= 0:
                jump_to(index)
                return
            view.sel().clear()
            for a, b in original_sel:
                view.sel().add(sublime.Region(a, b))
            view.set_viewport_position(original_viewport)

        window = view.window()
        if window:
            window.show_quick_panel(items, on_done, on_highlight=jump_to)

    def is_enabled(self):
        return _looks_like_edi(self.view)

    # Hide (not just grey out) the menu entries in non-EDI files.
    is_visible = is_enabled


_KIND_FOR_SEVERITY = {
    "error": (sublime.KIND_ID_COLOR_REDISH, "E", "Error"),
    "warning": (sublime.KIND_ID_COLOR_YELLOWISH, "W", "Warning"),
    "info": (sublime.KIND_ID_COLOR_BLUISH, "I", "Info"),
}


def _render_issue_regions(view, issues):
    """Squiggle the segments that have errors/warnings (info is panel-only)."""
    view.erase_regions(ISSUE_REGION_KEY)
    regions = [sublime.Region(i["offset"], i["offset"] + 3)
               for i in issues if i["severity"] in ("error", "warning")]
    if regions:
        view.add_regions(
            ISSUE_REGION_KEY,
            regions,
            "region.redish",
            "dot",
            sublime.DRAW_SQUIGGLY_UNDERLINE | sublime.DRAW_NO_FILL |
            sublime.DRAW_NO_OUTLINE,
        )


# ---------------------------------------------------------------------------
# Conversion command
# ---------------------------------------------------------------------------

class EdiConvertCommand(sublime_plugin.TextCommand):
    """Convert the buffer to JSON, JSONC, XML or normalized JSON in a new tab."""

    CONVERTERS = {
        "json": (edi_convert.to_json, "JSON.sublime-syntax", ".json"),
        "jsonc": (edi_convert.to_jsonc, "JSON.sublime-syntax", ".jsonc"),
        "xml": (edi_convert.to_xml, "XML.sublime-syntax", ".xml"),
        "normalized": (edi_normalize.to_json, "JSON.sublime-syntax",
                       ".normalized.json"),
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
        # Mark the converted document as classified so the EDI listeners
        # never try to analyse it.
        out.settings().set(IS_EDI_SETTING, False)
        out.run_command("append", {"characters": result})
        sublime.status_message(
            "EDI: converted %s to %s" % (dialect.label, format.upper()))

    def _output_name(self, extension):
        name = self.view.name() or self.view.file_name() or "message"
        base = os.path.splitext(os.path.basename(name))[0]
        return base + extension

    def is_enabled(self):
        return _looks_like_edi(self.view)

    # Hide (not just grey out) the menu entries in non-EDI files.
    is_visible = is_enabled


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
        keys = sorted(edi_data.SEGMENTS.keys())
        items = [self._label_for(k) for k in keys]
        window = self.view.window()
        if window:
            window.show_quick_panel(
                items,
                lambda index: self._apply(keys[index]) if index >= 0 else None)

    def _label_for(self, key):
        if key in edi_data.EDIFACT_SUBSETS:
            return "%s (EDIFACT subset)" % edi_data.EDIFACT_SUBSETS[key]
        return edi_data.DIALECTS[edi_data.dialect_family(key)]["label"]

    def _apply(self, dialect):
        self.view.settings().set(DIALECT_OVERRIDE_SETTING, dialect)
        self.view.settings().set(IS_EDI_SETTING, True)
        _drop_view_state(self.view)
        resolved = edi_core.Dialect.from_family(dialect)
        _apply_syntax(self.view, resolved)
        if self.view.settings().get(HINTS_ENABLED_SETTING):
            _refresh_hints(self.view)
        sublime.status_message("EDI: dialect set to %s" % resolved.label)


class EdiDetectSyntaxCommand(sublime_plugin.TextCommand):
    """(Re)detect the dialect and apply the matching syntax."""

    def run(self, edit):
        self.view.settings().erase(DIALECT_OVERRIDE_SETTING)
        _drop_view_state(self.view)
        dialect = _resolve_dialect(self.view)
        self.view.settings().set(IS_EDI_SETTING, dialect is not None)
        if dialect is None:
            sublime.status_message("EDI: could not detect an EDI dialect")
            return
        _apply_syntax(self.view, dialect)
        sublime.status_message("EDI: detected %s" % dialect.label)

    def is_enabled(self):
        return self.view.size() <= MAX_AUTO_SIZE


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
    dialect, spans = _cached_analysis(view)
    if dialect is None or not spans:
        return 0

    verbose = _settings().get("hints_show_descriptions", False)
    color = _hint_color(view)
    regions = []
    annotations = []
    for start, end, seg in spans:
        name = edi_data.segment_name(dialect.key, seg.tag)
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
.decoded { color: var(--bluish); }
"""


def _segment_popup_html(view, point):
    """Build the explain-segment popup for the segment containing ``point``."""
    dialect, spans = _cached_analysis(view)
    if dialect is None:
        return None
    hit = _span_at(spans, point)
    if hit is None:
        return None
    _start, _end, target = hit

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
            decoded = edi_data.qualifier_label(
                dialect.key, tag, i + 1, components[0])
            row = ('<div class="el"><span class="idx">%d.</span> '
                   '<span class="val">%s</span>' % (i + 1, _escape(value)))
            if decoded:
                row += ' <span class="decoded">= %s</span>' % _escape(decoded)
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
        if view.settings().get(IS_EDI_SETTING) is None:
            self._auto(view)

    def on_modified_async(self, view):
        settings = view.settings()
        if settings.get(IS_EDI_SETTING) is None:
            # A fresh (e.g. new/pasted) buffer that was empty when activated:
            # classify it once it has content, debounced while typing settles.
            if view.size() > 0:
                _debounce(view, lambda: self._auto(view))
            return
        if settings.get(HINTS_ENABLED_SETTING):
            _debounce(view, lambda: _refresh_hints(view))

    def on_selection_modified_async(self, view):
        if not view.settings().get(IS_EDI_SETTING):
            return
        dialect, spans = _cached_analysis(view)
        if dialect is None:
            view.erase_status(STATUS_KEY)
            return
        sel = view.sel()
        if not sel:
            return
        point = sel[0].begin()
        hit = _span_at(spans, point)
        if hit is None:
            view.set_status(STATUS_KEY, dialect.label)
            return
        start, _end, seg = hit
        status = "%s · %s" % (dialect.label, seg.tag)
        elem_no, comp_no = edi_core.element_at(seg, point - start)
        if elem_no > 0:
            status += "-%d" % elem_no
            if comp_no > 1 or dialect.component_separator in seg.content:
                status += ".%d" % comp_no
            names = edi_data.element_names(dialect.key, seg.tag)
            if elem_no <= len(names) and names[elem_no - 1]:
                status += " — %s" % names[elem_no - 1]
        else:
            name = edi_data.segment_name(dialect.key, seg.tag)
            if name:
                status += " — %s" % name
        view.set_status(STATUS_KEY, status)

    def on_hover(self, view, point, hover_zone):
        if hover_zone != sublime.HOVER_TEXT:
            return
        if not view.settings().get(IS_EDI_SETTING):
            return
        if not _settings().get("hover_help", True):
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

    def on_post_save_async(self, view):
        if not view.settings().get(IS_EDI_SETTING):
            return
        if not _settings().get("validate_on_save", False):
            return
        dialect, _spans = _cached_analysis(view)
        if dialect is None:
            return
        issues = edi_validate.validate(_view_text(view), dialect)
        _render_issue_regions(view, issues)
        problems = [i for i in issues if i["severity"] in ("error", "warning")]
        if problems:
            sublime.status_message(
                "EDI: %d validation issue(s) — run \"EDI: Validate Structure\""
                % len(problems))

    def on_close(self, view):
        _drop_view_state(view)

    def _auto(self, view):
        if view.size() == 0 or view.size() > MAX_AUTO_SIZE:
            # Not classified yet: leave IS_EDI_SETTING unset so a later
            # modification (paste into a new buffer) triggers classification.
            return
        dialect = _resolve_dialect(view)
        view.settings().set(IS_EDI_SETTING, dialect is not None)
        if dialect is None:
            return
        _apply_syntax(view, dialect)
        if _settings().get("auto_hints", False):
            view.settings().set(HINTS_ENABLED_SETTING, True)
            _refresh_hints(view)


# Debounce helper so expensive work only runs after typing settles.
_pending = {}


def _debounce(view, callback, delay=350):
    vid = view.id()
    token = _pending.get(vid, 0) + 1
    _pending[vid] = token

    def go():
        if _pending.get(vid) == token and view.is_valid():
            callback()

    sublime.set_timeout_async(go, delay)
