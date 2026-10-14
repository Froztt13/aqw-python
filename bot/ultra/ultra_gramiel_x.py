"""Compatibility shim for ``bot.ultra.ultra_gramiel_x``.

This file used to be a byte-identical copy of ``ultra_gramiel.py``
(sha ``373027f1...``) -- same fight, same module-level taunt globals, same
``# SETUP MANUALLY`` header -- so the two copies could only ever drift apart.
``plan.md`` Phase 4 collapsed it into this re-export: the fight now exists
once, in :mod:`bot.ultra.ultra_gramiel`.

Two per-file tweaks that only the copy had were dropped with it, since they
were differences between duplicates rather than anything this entry point
was for::

    cmd.bot.showDebug = True
    cmd.bot.auto_relogin = False

Nothing imports this module (verified across all files, not just ``.py``), so
it is kept only in case something still *names* it -- ``bot.ultra.ultra_gramiel_x``
is a valid ``BOT_PATH`` for ``start.py`` / ``gui.py``.  Delete it once that is
ruled out.
"""

from bot.ultra.ultra_gramiel import UltraGrammiel, main

__all__ = ["UltraGrammiel", "main"]
