"""Ultra Warden -- quest 8153 in ``ultrawarden``.

One boss, one class.  What each of the four launcher slots wears lives in
``bot.ultra.config.LOADOUTS["warden"]``; this file only says when and how
to fight.
"""

from __future__ import annotations

from core.command import Command
from bot.ultra.core_ultra import CoreUltra


class UltraWarden(CoreUltra):
    """Warden at quest 8153.

    Two things set this fight apart from the other three:

    * **no explicit monster** -- the loadout leaves ``monster_prio`` empty, so
      the rotation hits whatever is alive, as the original did by calling
      ``is_monster_alive()`` and ``use_skill(...)`` with no target;
    * **a finisher** -- slot 1 (Legendary Hero) drops skill 4 and slot 2
      skill 5 once Warden is under 600k, checked every tick.  That is what
      ``on_tick`` is for; the healing threshold here is 5%, far lower than
      the 50-60% the other bosses use.

    ========  ==========================================================
    quest     8153
    map       ``ultrawarden``, cell ``r2`` / ``Left``
    target    whatever is alive (no ``monster=``, no ``monster_prio``)
    skills    ``0 1 2 0 3 4``
    heal      below **5%** with skill 2 -- the lowest of the four
    finisher  ``on_tick``: HP <= 600_000 -> slot 1 casts skill 4,
              slot 2 casts skill 5 (neither for slots 3/4)
    finishes  ``finish(8153)``
    ========  ==========================================================
    """

    BOSS = "warden"
    QUEST = 8153
    MAP = "ultrawarden"

    #: Warden's finisher HP gate.
    FINISHER_HP = 600_000

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

        async def warden_tick() -> None:
            mons_hp = self.cmd.get_monster_hp("Ultra Warden")
            if mons_hp and mons_hp <= self.FINISHER_HP:
                if self.index_class == 1:
                    await self.cmd.use_skill(4)
                elif self.index_class == 2:
                    await self.cmd.use_skill(5)

        async def fight() -> None:
            await self.attack_loop(
                [0, 1, 2, 0, 3, 4],
                monster="Ultra Warden",
                monster_prio=monster_prio,
                heal_below=5,
                heal_skill=2,
                on_tick=warden_tick,
            )

        print("attacking")
        await self.fight_until_party_ready(self.QUEST, fight)

        print("finished ultra warden")
        await self.finish(self.QUEST)


async def main(cmd: Command) -> None:
    """Standalone entry for ``start.py`` / ``gui.py`` (``bot.ultra.ultra_warden``).

    Uses launcher slot 1.  For the four-pane layout use ``bot.ultra.daily``,
    which picks the slot from stdin the way ``ultra_daily_pane.bat`` feeds it.
    """
    await UltraWarden(cmd, 1).run()
