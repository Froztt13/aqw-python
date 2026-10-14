"""Ultra Ezrajal -- quest 8152 in ``ultraezrajal``.

One boss, one class.  What each of the four launcher slots wears lives in
``bot.ultra.config.LOADOUTS["ezrajal"]``; this file only says when and how
to fight.

Ezrajal is the boss that telegraphs a counter attack, so this fight
subscribes ``CoreUltra.message_handler`` for the duration (``finish`` removes
it again) and passes ``respect_counter_attack=True`` to the rotation.
"""

from __future__ import annotations

from core.command import Command
from bot.ultra.core_ultra import CoreUltra


class UltraEzrajal(CoreUltra):
    """Ultra Ezrajal -- the boss that telegraphs a counter attack.

    The loop is identical to Engineer's apart from the target, which is
    left open (no ``monster=`` and an empty ``monster_prio``) because
    Ezrajal has no adds worth naming.  What makes it different is the
    subscribe: this is the one daily fight that reads server telegraphs.

    ========  ==========================================================
    quest     8152
    map       ``ultraezrajal``, cell ``r2`` / ``Left``
    target    whatever is alive (no ``monster=``, no ``monster_prio``)
    skills    ``0 1 2 0 3 4``
    heal      below 50% with skill 2
    telegraph subscribes ``message_handler`` for the run and passes
              ``respect_counter_attack=True``, so the rotation skips while
              the counter-attack aura is up; ``finish(..., unsubscribe=True)``
              removes it again
    finishes  ``finish(8152, unsubscribe=True)``
    ========  ==========================================================
    """

    BOSS = "ezrajal"
    QUEST = 8152
    MAP = "ultraezrajal"
    BOSS_CELL = "r2"

    async def run(self) -> None:
        """Equip, accept the quest, fight, turn in, go rest."""
        loadout = await self.apply_loadout(self.BOSS)
        if loadout is None:
            return
        monster_prio = loadout.monster_prio

        self.cmd.bot.subscribe(self.message_handler)
        await self.cmd.accept_quest(self.QUEST)
        await self.join_and_wait(self.MAP)
        await self.precast_buffs()
        await self.cmd.jump_cell("r2", "Left")

        print("attacking")
        async def fight() -> None:
            await self.attack_loop(
                [0, 1, 2, 0, 3, 4],
                monster="Ultra Ezrajal",
                monster_prio=monster_prio,
                heal_below=50,
                heal_skill=2,
                respect_counter_attack=True,
            )

        await self.fight_until_party_ready(self.QUEST, fight)

        print("finished ultra ezrajal")
        await self.finish(self.QUEST, unsubscribe=True)


async def main(cmd: Command) -> None:
    """Standalone entry for ``start.py`` / ``gui.py`` (``bot.ultra.ultra_ezrajal``).

    Uses launcher slot 1.  For the four-pane layout use ``bot.ultra.daily``,
    which picks the slot from stdin the way ``ultra_daily_pane.bat`` feeds it.
    """
    await UltraEzrajal(cmd, 1).run()
