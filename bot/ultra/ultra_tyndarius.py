"""Ultra Tyndarius -- quest 8245 in ``ultratyndarius``.

One boss, one class.  What each of the four launcher slots wears lives in
``bot.ultra.config.LOADOUTS["tyndarius"]``; this file only says when and how
to fight.
"""

from __future__ import annotations

from core.command import Command
from bot.ultra.core_ultra import CoreUltra


class UltraTyndarius(CoreUltra):
    """Tyndarius -- the first of the four daily bosses.

    Slot 1/2 DPS and support rotate a six-step list against ``id.2``;
    slots 3/4 stand by and top up whoever drops below 60%.  Slot 1 opens on
    ``id.1`` and slot 2 on ``id.3`` so each crystal dies before the boss,
    swapping over when its own is already down -- that ordering is the
    loadout's ``monster_prio``, not code.

    ========  ==========================================================
    quest     8245
    map       ``ultratyndarius``, cell ``Boss`` / ``Left``
    target    ``id.2`` (``monster=``) + ``monster_prio`` from the loadout
    skills    ``0 1 2 0 3 4 5``
    heal      below 60% with skill 2
    finishes  ``finish(8245)`` -- turn in, Yulgar, rest
    ========  ==========================================================
    """

    BOSS = "tyndarius"
    QUEST = 8245
    MAP = "ultratyndarius"

    async def run(self) -> None:
        """Equip, accept the quest, fight, turn in, go rest."""
        loadout = await self.apply_loadout(self.BOSS)
        if loadout is None:
            return
        monster_prio = loadout.monster_prio

        await self.cmd.accept_quest(self.QUEST)
        await self.join_and_wait(self.MAP)
        await self.precast_buffs()
        await self.cmd.jump_cell("Boss", "Left")

        skill_list = [0, 1, 2, 0, 3, 4, 5]

        async def fight() -> None:
            await self.attack_loop(
                skill_list,
                monster="id.2",
                monster_prio=monster_prio,
                heal_below=60,
                heal_skill=2,
            )

        print("attacking")
        await self.fight_until_party_ready(self.QUEST, fight)

        print("finished ultra tyndarius")
        await self.finish(self.QUEST)


async def main(cmd: Command) -> None:
    """Standalone entry for ``start.py`` / ``gui.py`` (``bot.ultra.ultra_tyndarius``).

    Uses launcher slot 1.  For the four-pane layout use ``bot.ultra.daily``,
    which picks the slot from stdin the way ``ultra_daily_pane.bat`` feeds it.
    """
    await UltraTyndarius(cmd, 1).run()
