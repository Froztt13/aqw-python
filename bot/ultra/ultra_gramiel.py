"""Ultra Gramiel -- quest 10301 in ``ultragramiel``.

One boss, one class.  What each of the four launcher slots wears lives in
``bot.ultra.config.LOADOUTS["grammiel"]``; this file only says when and how
to fight.

This is the boss with a real state machine: two side crystals are cleared in
the order the loadout names them (``kill_order``), and ``message_handler``
reads the telegraphs to decide *which* class taunts and when.
"""

from __future__ import annotations

import time
from datetime import datetime, timedelta
from typing import Optional

from core.command import Command
from bot.ultra.core_ultra import CoreUltra


class UltraGrammiel(CoreUltra):
    """Gramiel the Graceful at quest 10301.

    Everything that was a module global in the old shared handler --
    ``LTaunt``, ``RTaunt``, ``force_taunt``, ``taunter_list``,
    ``taunter_index``, ``taunt_date``, ``wait_taunt`` -- is instance state
    here, reset by :meth:`initUltraGrammiel` at the top of every run.

    Order of the fight: crystals first in ``loadout.kill_order``, then the
    boss, with a taunt armed whenever a crystal telegraph says the *next*
    taunter in :attr:`taunter_list` is the class we happen to be wearing.

    ========  ==========================================================
    quest     10301
    map       ``ultragramiel``, cells ``Enter``/``Spawn`` then ``r2``/``Bottom``
    party     blocks until 4 players are present (``wait_count_player``)
    target    phase 1: ``loadout.kill_order`` -- ``("id.3","id.2")`` or
              ``("id.2","id.3")`` depending on slot; phase 2:
              ``Gramiel The Graceful``
    skills    ``0 1 2 0 3 4`` on a rotating index
    taunt     skill 5, armed by ``_on_gramiel_taunt``; 1000 ms wind-up on a
              crystal, 1200 ms on the boss
    heal      party heal below 50% -- skill 3 for LightCaster and Obsidian
              Paladin Chronomancer, skill 2 for Lord Of Order, none for
              StoneCrusher
    telegraph subscribes ``message_handler``: base counter-attack handling
              **plus** the Grace Crystal / ``Point`` taunt telegraphs
    drop      ``Gramiel the Graceful's Insignia``
    finishes  turn in 10301 -> ``yulgar`` -> rest (not ``finish()``)
    ========  ==========================================================
    """

    BOSS = "grammiel"
    QUEST = 10301
    MAP = "ultragramiel"
    BOSS_NAME = "Gramiel The Graceful"
    DROP = "Gramiel the Graceful's Insignia"

    def __init__(self, cmd: Command, index_class: int) -> None:
        super().__init__(cmd, index_class)
        self.initUltraGrammiel()

    def initUltraGrammiel(self) -> None:
        """Reset the taunt counters for a fresh attempt."""
        self.LTaunt = 0
        self.RTaunt = 0
        self.LTauntClass = ""
        self.RTauntClass = ""
        self.force_taunt = False
        self.taunter_list: list[str] = [
            "obsidian paladin chronomancer", "stonecrusher",
            "lightcaster", "lord of order",
        ]
        self.taunter_index: int = 0
        self.taunt_date: datetime = datetime.now()
        self.wait_taunt: bool = False

    async def run(self) -> None:
        """Equip, accept the quest, clear the crystals, kill Gramiel, turn in."""
        self.initUltraGrammiel()
        self.cmd.add_drop(self.DROP)

        loadout = await self.apply_loadout(self.BOSS)
        if loadout is None:
            return
        kill_order = loadout.kill_order

        await self.cmd.accept_quest(self.QUEST)
        while self.cmd.is_not_in_map(self.MAP):
            await self.cmd.join_map(self.MAP, self.private_room)
            await self.cmd.sleep(100)
        await self.cmd.jump_cell("Enter", "Spawn")

        self.cmd.bot.subscribe(self.message_handler)

        while not self.cmd.wait_count_player(4):
            await self.cmd.sleep(100)

        await self.precast_buffs()

        equipped_class = self.equipped_class_name()
        await self.cmd.jump_cell("r2", "Bottom")

        skill_index = 0
        skill_list = [0, 1, 2, 0, 3, 4]
        start_time = time.time()
        print("attacking...")

        # --- phase 1: the two side crystals, in the loadout's order -----
        for prio in kill_order:
            while self.cmd.is_monster_alive(prio) and self.cmd.is_still_connected():
                mons_hp = self.cmd.get_monster_hp(prio)
                if mons_hp and mons_hp > -1:
                    print(f"{prio}: {mons_hp} : "
                          f"{self.cmd.get_monster_hp_percentage(prio)}%")
                await self.party_heal(equipped_class)
                if self.force_taunt:
                    await self.cmd.sleep(1000)
                    await self.cmd.use_skill(5, prio)
                    print(f"{equipped_class} taunt")
                    self.force_taunt = False
                    continue
                await self.cmd.use_skill(skill_list[skill_index], prio)
                skill_index += 1
                if skill_index >= len(skill_list):
                    skill_index = 0
                await self.cmd.sleep(100)

        self.force_taunt = False
        if equipped_class == self.taunter_list[self.taunter_index]:
            self.wait_taunt = True
            self.taunt_date = datetime.now()

        # --- phase 2: Gramiel himself -----------------------------------
        while (self.cmd.is_monster_alive(self.BOSS_NAME)
               and self.cmd.is_still_connected()):
            mons_hp = self.cmd.get_monster_hp(self.BOSS_NAME)
            if mons_hp and mons_hp > -1:
                print(f"{self.BOSS_NAME}: {mons_hp} : "
                      f"{self.cmd.get_monster_hp_percentage(self.BOSS_NAME)}%")
            await self.party_heal(equipped_class)
            if self.wait_taunt:
                if datetime.now() >= self.taunt_date:
                    self.force_taunt = True
                    self.wait_taunt = False
            if self.force_taunt:
                await self.cmd.sleep(1200)
                await self.cmd.use_skill(5, self.BOSS_NAME)
                print(f"{equipped_class} taunt {self.BOSS_NAME}")
                self.force_taunt = False
                continue
            await self.cmd.use_skill(skill_list[skill_index], self.BOSS_NAME)
            skill_index += 1
            if skill_index >= len(skill_list):
                skill_index = 0
            await self.cmd.sleep(100)

        elapsed_time = time.time() - start_time
        minutes = int(elapsed_time // 60)
        seconds = int(elapsed_time % 60)
        print(f"Elapsed time: {minutes} minutes, {seconds} seconds")

        await self.cmd.turn_in_quest(self.QUEST)
        await self.cmd.join_map("yulgar")
        await self.cmd.rest()
        await self.cmd.sleep(4000)

    async def party_heal(self, equipped_class: str) -> None:
        """Cast the party heal this slot is responsible for, if anyone is low.

        The skill differs by class rather than by slot: LightCaster and
        Obsidian Paladin Chronomancer heal with 3, Lord Of Order with 2.
        StoneCrusher deliberately has none, matching the original.
        """
        for player in self.cmd.bot.player_in_area:
            if player.is_hp_below(50):
                if equipped_class in ("lightcaster", "obsidian paladin chronomancer"):
                    await self.cmd.use_skill(3)
                elif equipped_class == "lord of order":
                    await self.cmd.use_skill(2)

    # ------------------------------------------------------------------
    # telegraph handling
    # ------------------------------------------------------------------

    def message_handler(self, message) -> None:
        """Counter-attack handling plus Gramiel's own taunt telegraphs.

        ``super()`` runs first because the handler this replaced was one
        shared function covering both bosses, so Gramiel's fight always saw
        the counter-attack flags too -- even though neither loop reads them.
        """
        data = self._parse_message(message)
        if not data or data.get("cmd") != "ct":
            return
        self._on_counter_attack(data)
        self._on_gramiel_taunt(data)

    def _on_gramiel_taunt(self, data: dict) -> None:
        """Arm ``force_taunt`` from a crystal telegraph, or rotate the taunter."""
        anims = data.get("anims")
        if not anims:
            return
        equipped_class = self.equipped_class_name()

        for anim in anims:
            target = anim.get("tInf")
            msg = anim.get("msg")
            animStr: Optional[str] = anim.get("animStr")

            if msg and isinstance(msg, str):
                if (msg.lower()
                        == "The Grace Crystal prepares a defense shattering attack!".lower()):
                    if target == "m:3":
                        self.RTaunt += 1
                        if self.RTaunt % 2 == 0 and equipped_class == "lord of order":
                            self.force_taunt = True
                        elif self.RTaunt % 2 == 1 and equipped_class == "lightcaster":
                            self.force_taunt = True
                    if target == "m:2":
                        self.LTaunt += 1
                        if self.LTaunt % 2 == 0 and equipped_class == "obsidian paladin chronomancer":
                            self.force_taunt = True
                        elif self.LTaunt % 2 == 1 and equipped_class == "stonecrusher":
                            self.force_taunt = True

            if animStr:
                if (self.cmd.bot.strMapName.lower() == "ultragramiel"
                        and animStr == "Point" and target == "m:1"):
                    self.taunter_index += 1
                    if self.taunter_index >= len(self.taunter_list):
                        self.taunter_index = 0
                    if equipped_class == self.taunter_list[self.taunter_index]:
                        self.wait_taunt = True
                        self.taunt_date = datetime.now() + timedelta(seconds=4)


async def main(cmd: Command) -> None:
    """Standalone entry for ``start.py`` / ``gui.py`` (``bot.ultra.ultra_gramiel``).

    Uses launcher slot 1.  For the four-pane layout use ``bot.ultra.grammiel``,
    which picks the slot from stdin the way ``ultra_grammiel.bat`` feeds it.
    """
    await UltraGrammiel(cmd, 1).run()
