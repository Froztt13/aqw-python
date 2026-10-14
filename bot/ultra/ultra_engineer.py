"""Ultra Engineer -- quest 8154 in ``ultraengineer``.

One boss, one class.  What each of the four launcher slots wears lives in
``bot.ultra.config.LOADOUTS["engineer"]``; this file only says when and how
to fight.
"""

from __future__ import annotations

from core.command import Command
from bot.ultra.core_ultra import CoreUltra


class UltraEngineer(CoreUltra):
    """Ultra Engineer -- the only boss whose targets are the adds.

    Every rotation is aimed at ``Attack Drone,Defense Drone`` (that string
    comes from the loadout's ``monster_prio``, set on all four slots),
    because the drones are what make the fight drag.  ``monster=`` below is
    only the fallback for a slot with an empty ``monster_prio``.

    ========  ==========================================================
    quest     8154
    map       ``ultraengineer``, cell ``r2`` / ``Left``
    target    ``monster_prio`` = ``Attack Drone,Defense Drone``;
              fallback ``monster="Ultra Engineer"``
    skills    ``0 1 2 0 3 4``
    heal      below 60% with skill 2
    scroll    never -- the loadout leaves it ``None`` on purpose
    finishes  ``finish(8154)``
    ========  ==========================================================
    """

    BOSS = "engineer"
    QUEST = 8154
    MAP = "ultraengineer"
    BOSS_CELL = "r2"

    async def run(self) -> None:
        """Equip, accept the quest, fight, turn in, go rest."""
        loadout = await self.apply_loadout(self.BOSS)
        if loadout is None:
            return
        monster_prio = loadout.monster_prio

        await self.cmd.accept_quest(self.QUEST)
        await self.join_and_wait(self.MAP)
        await self.precast_buffs()
        await self.cmd.jump_cell("r2", "Left")

        async def fight() -> None:
            await self.attack_loop(
                [0, 1, 2, 0, 3, 4],
                monster="Ultra Engineer",
                monster_prio=monster_prio,
                heal_below=60,
                heal_skill=2,
            )

        print("attacking")
        await self.fight_until_party_ready(self.QUEST, fight)

        print("finished ultra engineer")
        await self.finish(self.QUEST)


async def main(cmd: Command) -> None:
    """Standalone entry for ``start.py`` / ``gui.py`` (``bot.ultra.ultra_engineer``).

    Uses launcher slot 1.  For the four-pane layout use ``bot.ultra.daily``,
    which picks the slot from stdin the way ``ultra_daily_pane.bat`` feeds it.
    """
    await UltraEngineer(cmd, 1).run()
