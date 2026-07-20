# -*- coding: utf-8 -*-
"""EDIBlime's Sublime-independent engine.

Sublime Text loads every root-level ``.py`` file of a package as a separate
plugin, and plugins must not import each other (reloads are not atomic). So
``edi.py`` is the only plugin at the package root, and everything it imports
lives in this subpackage.
"""
