"""Champion Drakath -- quest in ``champevod``/``ultradrakath``.

One boss, one class.  What each of the four launcher slots wears lives in
``bot.ultra.config.LOADOUTS["drakath"]``; this file only says when and how
to fight.

.. warning::
   **There is still no fight loop here.**  ``CoreUltra.ChampionDrakath``
   only ever called ``apply_loadout`` -- it equipped the four slots and
   stopped -- and that is what this class does too.  Nothing accepts the
   quest, nothing attacks, nothing turns in.  Fill in the rotation before
   pointing a launcher at this module.
"""

from __future__ import annotations

from core.command import Command
from bot.ultra.core_ultra import CoreUltra


class UltraDrakath(CoreUltra):
    """Champion Drakath -- equips only; there is no fight loop yet.

    Kept as its own module for the day the rotation exists, so the gap is
    obvious (see the module docstring) rather than hidden inside
    ``core_ultra``.

    ========  ==========================================================
    quest     -- none accepted
    map       -- never joined
    target    -- none
    skills    -- none run
    equip     yes: ``apply_loadout("drakath")`` only, then ``stop_bot``
    ========  ==========================================================
    """

    BOSS = "drakath"

    async def run(self) -> None:
        """Equip the Drakath loadout and stop there."""
        loadout = await self.apply_loadout(self.BOSS)
        if loadout is None:
            return
        self.cmd.stop_bot(
            "equipped the drakath loadout, but this boss has no fight loop yet"
        )


async def main(cmd: Command) -> None:
    """Standalone entry for ``start.py`` / ``gui.py`` (``bot.ultra.ultra_drakath``).

    Uses launcher slot 1.  For the four-pane layout use ``bot.ultra.daily``,
    which picks the slot from stdin the way the ``.bat`` launchers feed it.
    """
    await UltraDrakath(cmd, 1).run()
