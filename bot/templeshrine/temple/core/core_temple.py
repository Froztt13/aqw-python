import asyncio
import time
import json
from datetime import datetime
from colorama import Fore
from core.command import Command, SkillMode
from core.utils import is_valid_json


class CoreTempleBot:
    def __init__(self, cmd: Command, role: str, temple: str, target_monsters: str,
                 is_taunter: bool = False):
        self.cmd = cmd
        self.pid = None
        self.do_taunt = False
        self.role = role
        self.is_taunter = is_taunter
        self.temple = temple              # "midnightsun" atau "solsticemoon"
        self.target_monsters = target_monsters
        self._target_monsters = target_monsters
        self.timeleapse = 0
        self.cleared_count = 0

        # skill setup
        self.skill_list = [0, 1, 2, 0, 3, 4]
        self.skill_index = 0
        self.is_attacking = False

        # subscribe ke event
        self.cmd.bot.subscribe(self.msg_handler)

    def print_debug(self, message):
        print(f"[{datetime.now().strftime('%H:%M:%S')}] "
              f"[{self.cmd.get_player.CELL}] {Fore.YELLOW}{message}{Fore.RESET}")

    def msg_handler(self, message):
        if not message or not is_valid_json(message):
            return
        try:
            data = json.loads(message)["b"]["o"]
            cmd = data["cmd"]

            if cmd == "pi":
                self.pid = data.get("pid")

            if cmd == "ct":
                anims = data.get("anims")
                monsters = data.get("m")
                actions = data.get("a")

                if actions:
                        for action in actions:
                            for aura in action.get("auras", []):
                                if self.cmd.bot.user_id in action.get("tInf", ""):
                                    if aura.get("nam") == "Sun's Warmth":
                                        # Create 5 seconds delayed taunt
                                        async def delayed_taunt():
                                            await asyncio.sleep(5)
                                            self.target_monsters = "Dawn Knight"
                                            self.do_taunt = True
                                        asyncio.create_task(delayed_taunt())
                if anims:
                    for anim in anims:
                        msg = anim.get("msg")
                        if msg:
                            if self.is_taunter:
                                self.print_debug(f"Received message: {msg}")
                            if "gather" in msg.lower():
                                self.target_monsters = "Dying Light"
                                self.do_taunt = True
                            elif "converges" in msg.lower():
                                self.do_taunt = True

                if monsters:
                    for mon_map_id, mon_condition in monsters.items():
                        is_alive = int(mon_condition.get("intHP")) > 0
                        if not is_alive:
                            print(f"Monster id:{mon_map_id} is dead.")
        except:
            return

    async def enter_dungeon(self):
        self.timeleapse = time.monotonic()
        await self.cmd.sleep(1000)
        await self.cmd.send_packet(f"%xt%zm%dungeonQueue%25127%{self.temple}%")
        while self.cmd.is_not_in_map(self.temple):
            self.print_debug("Waiting for dungeon queue...")
            await self.cmd.sleep(200)

    async def to_next_cell(self):
        self.print_debug("Moving to next cell...")
        await self.cmd.sleep(2000)

        if self.cmd.get_player.CELL == "Enter" and not self.cmd.is_monster_alive():
            await self.cmd.jump_cell("r1", "Left")
        elif self.cmd.get_player.CELL == "r1" and not self.cmd.is_monster_alive():
            await self.cmd.jump_cell("r2", "Left")
        elif self.cmd.get_player.CELL == "r2" and not self.cmd.is_monster_alive():
            await self.cmd.jump_cell("r3", "Left")
        elif self.cmd.get_player.CELL == "r3" and not self.cmd.is_monster_alive():
            elapsed_seconds = time.monotonic() - self.timeleapse
            minutes = int(elapsed_seconds // 60)
            seconds = int(elapsed_seconds % 60)
            self.cleared_count += 1
            await self.cmd.send_chat(f"Dungeon cleared {self.cleared_count} times.")
            await self.cmd.sleep(1000)
            await self.cmd.send_chat(f"Total time taken: {minutes} minutes and {seconds} seconds.")
            await self.cmd.sleep(1000)
            await self.cmd.join_map("templeshrine", roomNumber=999999)
            while self.cmd.is_not_in_map("templeshrine"):
                await self.cmd.sleep(200)
            self.print_debug("Entering new queue...")
            await self.enter_dungeon()

    async def setup_party(self):
        # hanya untuk master
        await self.cmd.join_map("yulgar", roomNumber=999999)
        await self.cmd.sleep(4000)

        self.print_debug("Waiting for all slaves to be online...")
        while not self.cmd.wait_count_player(4):
            await self.cmd.sleep(100)

        for slave in self.cmd.bot.slaves_player:
            await self.cmd.send_packet(f"%xt%zm%gp%1%pi%{slave}%")
            await self.cmd.sleep(500)

        await self.enter_dungeon()

    async def go_to_master(self):
        self.print_debug(f"Going to master's place...")
        await self.cmd.goto_player(self.cmd.bot.follow_player)
        await self.cmd.sleep(1000)

    async def wait_party_invite(self):
        self.print_debug("Waiting for party invitation...")
        while self.pid is None:
            await self.go_to_master()
            await self.cmd.sleep(1000)
        self.print_debug(f"Accepting party invitation from PID: {self.pid}")
        await self.cmd.send_packet(f"%xt%zm%gp%1%pa%{self.pid}%")
        await self.cmd.sleep(1000)

    async def attack_loop(self):
        skill_mode = SkillMode.ALL
        while self.cmd.is_still_connected():
            if self.role == "master":
                await self.to_next_cell()
            if self.role == "slave":
                await self.go_to_master()

            master = self.cmd.get_player_in_map(self.cmd.bot.follow_player)
            check_master_in_cell = self.role == "master" or (
                master and master.str_frame == self.cmd.get_player.CELL
            )
            while self.cmd.is_monster_alive() and check_master_in_cell and self.cmd.is_still_connected():
                if not self.is_attacking:
                    self.print_debug("Attacking monsters...")
                    self.is_attacking = True

                if self.do_taunt and self.is_taunter:
                    self.print_debug("Doing taunt...")
                    await self.cmd.sleep(500)
                    await self.cmd.wait_use_skill(5, target_monsters=self.target_monsters)
                    self.do_taunt = False
                    self.target_monsters = self._target_monsters
                    await self.cmd.sleep(200)
                    continue

                if self.cmd.get_player().hasAura("Sun's Heat"):
                    skill_mode = SkillMode.ATTACK_ONLY # dont use heal when having inverted dmg debuff
                else:
                    skill_mode = SkillMode.ALL
                    
                await self.cmd.use_skill(
                    self.skill_list[self.skill_index],
                    target_monsters=self.target_monsters,
                    skill_mode=skill_mode
                )
                self.skill_index = (self.skill_index + 1) % len(self.skill_list)

                await self.cmd.sleep(200)
            self.is_attacking = False

    async def start(self):
        await self.cmd.equip_item(self.cmd.get_farm_class())
        if self.is_taunter:
            await self.cmd.equip_scroll("Scroll of Enrage")

        if self.role == "master":
            await self.setup_party()
        if self.role == "slave":
            await self.wait_party_invite()

        await self.attack_loop()


# ---------- Subclass ----------
class MidnightSunBot(CoreTempleBot):
    def __init__(self, cmd: Command, role: str, is_taunter: bool = False):
        super().__init__(cmd, role,
                         temple="midnightsun",
                         target_monsters="Dying Light,Dawn Knight",
                         is_taunter=is_taunter)


class SolsticeMoonBot(CoreTempleBot):
    def __init__(self, cmd: Command, role: str, is_taunter: bool = False):
        super().__init__(cmd, role,
                         temple="solsticemoon",
                         target_monsters="Lunar Haze",
                         is_taunter=is_taunter)
