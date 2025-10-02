from datetime import datetime
import time
import asyncio
import json
from collections import deque
from core.utils import is_valid_json
from core.command import Command, SkillMode
from colorama import Fore
import colorama

from handlers.death_handler import death_handler_task

class AscendEclipseBot:
    def __init__(self, cmd: Command, 
                 role: str, 
                 default_target: str,
                 taunt_parity: str = "odd", 
                 converge_type: str = "sun",
                 
                 light_gather_taunter: bool = False, # required 2 taunter
                 moon_haze_taunter: bool = False,
                 sunset_knight_taunter: bool = False,
                 
                 debug_mon: bool = False):
        """
        Base bot untuk dungeon Ascend Eclipse

        :param cmd: Command instance
        :param role: "master" atau "slave"
        :param default_target: target monster utama (ex: "Ascended Solstice")
        :param taunt_parity: "odd" (ganjil) atau "even" (genap) untuk trigger taunt
        :param converge_type: "sun" atau "moon" untuk pilih jenis converges
        :param light_gather_taunter: taunter for "light gather"
        :param moon_haze_taunter: taunter for "moon haze"
        :param sunset_knight_taunter: taunter for "sunset knight"
        :param debug_mon: showing monster HP
        """
        self.cmd = cmd
        self.role = role
        self.default_target = default_target
        self.taunt_parity = taunt_parity
        self.converge_type = converge_type
        self.light_gather_taunter = light_gather_taunter
        self.moon_haze_taunter = moon_haze_taunter
        self.sunset_knight_taunter = sunset_knight_taunter
        self.debug_mon = debug_mon

        # state variables
        self.pid = None
        self.target_monsters = default_target
        self.stop_attack = False
        self.do_taunt = False
        self.taunt_target = None
        self.log_taunt = True
        self.converges_count = 0
        self.light_gather_count = 0

        self.is_attacking = False
        self.skill_list = [0, 1, 2, 0, 3, 4]
        self.skill_index = 0
        
        self.bot_timeleapse = time.monotonic()

        # subscribe ke event
        self.cmd.subscribe(self.handle_message)

    def print_debug(self, message, color=Fore.YELLOW):
        print(color + f"[{datetime.now().strftime('%H:%M:%S')}] [{self.cmd.get_player().CELL}] {message}" + Fore.RESET)
        
    def print_aura(self, message):
        self.print_debug(f"{Fore.RED}You got \"{message}\"{Fore.RESET}")

    async def prepare_items(self):
        minimalScroll = 50
        if self.cmd.get_quant_item("Scroll of Enrage") < minimalScroll:
            self.cmd.stop_bot(f"Not enough Scroll of Enrage. Minimum {minimalScroll} scrolls is required.")
            return
        farm_class = self.cmd.get_farm_class()
        if farm_class:
            await self.cmd.equip_item(farm_class)
        await self.cmd.equip_scroll("Scroll of Enrage")
        await self.cmd.sleep(3000)

    async def go_to_master(self):
        if self.cmd.get_followed_player():
            if not self.cmd.is_player_in_cell(self.cmd.get_followed_player(), self.cmd.get_player().CELL):
                self.print_debug(f"Going to master's place...")
                while not self.cmd.is_player_in_cell(self.cmd.get_followed_player(), self.cmd.get_player().CELL):
                    await self.cmd.goto_player(self.cmd.get_followed_player())
                    if self.cmd.get_player_in_map(self.cmd.get_followed_player()):
                        await self.cmd.sleep(200)
                    else:
                        await self.cmd.sleep(1000)
            await self.cmd.sleep(100)
            if self.cmd.is_in_map("yulgar"):
                await self.cmd.rest()
        else:
            self.cmd.stop_bot("No master assigned to follow.")

    def reset_counters(self):
        self.do_taunt = False
        self.converges_count = 0
        self.light_gather_count = 0
        self.cmd.get_player().removeAllAuras()

    def _should_taunt(self, count: int) -> bool:
        if self.taunt_parity == "odd":
            return count % 2 != 0
        elif self.taunt_parity == "even":
            return count % 2 == 0
        return False

    def handle_message(self, message):
        if not message or not is_valid_json(message):
            return
        try:
            data = json.loads(message)["b"]["o"]
            cmdData = data["cmd"]

            if cmdData == "pi":
                self.pid = data.get("pid")

            if cmdData == "ct":
                self._parse_auras(data.get("a"))
                self._parse_anims(data.get("anims"))
                self._parse_monsters(data.get("m"))

        except Exception:
            return

    def _parse_auras(self, auras):
        if not auras:
            return
        for a_item in auras:
            for aura in a_item.get("auras", []):
                if self.cmd.get_user_id() in a_item.get("tInf", ""):
                    # Log specific auras for the player
                    if aura.get("nam") in ["Sun's Heat", "Moonlight Stun", "Noon of Radiance", "Midnight of Silence", "Hollowed Eclipse"]:
                        self.print_aura(aura.get("nam"))
                    # Create 5 seconds delayed taunt
                    if aura.get("nam") == "Sun's Warmth" and self.sunset_knight_taunter:
                        async def delayed_taunt():
                            await asyncio.sleep(5)
                            self.taunt_target = "Sunset Knight"
                            self.do_taunt = True
                        asyncio.create_task(delayed_taunt())
                    if aura.get("nam") == "Moonlight Gaze" and self.moon_haze_taunter:
                        async def delayed_taunt():
                            await asyncio.sleep(5)
                            self.taunt_target = "Moon Haze"
                            self.do_taunt = True
                        asyncio.create_task(delayed_taunt())

    def _parse_anims(self, anims):
        if not anims:
            return
        for anim in anims:
            msg = anim.get("msg", "").lower()

            # Gather event (opsional)
            if self.light_gather_taunter and "gather" in msg:
                self.light_gather_count += 1
                self.do_taunt = self._should_taunt(self.light_gather_count)
                if self.do_taunt:
                    self.taunt_target = "Suffocated Light"
                if self.log_taunt:
                    self.print_debug(f"Gather count: {self.light_gather_count}")

            # Converges event (sun / moon)
            if f"{self.converge_type} converges" in msg:
                self.converges_count += 1
                self.do_taunt = self._should_taunt(self.converges_count)
                if self.log_taunt:
                    self.print_debug(f"{self.converge_type.title()} Converges count: {self.converges_count}")

    def _parse_monsters(self, monsters):
        if not monsters:
            return
        for mon_map_id, mon_condition in monsters.items():
            monHp = int(mon_condition.get('intHP'))
            if monHp <= 0:
                self.print_debug(f"Monster id:{mon_map_id} is dead.")
            if monHp and self.debug_mon:
                mon = self.cmd.get_monster(f"id.{mon_map_id}")
                if mon:
                    monHpPercent = round(((mon.current_hp/mon.max_hp)*100), 2)
                    self.print_debug(f"id.{mon_map_id} - {mon.mon_name} HP: {monHpPercent}%")

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
            await self.cmd.sleep(200)
            self.reset_counters()
            
            if self.role == "master" and not self.cmd.is_monster_alive():
                await self.to_next_cell()
            if self.role == "slave":
                await self.go_to_master()
                
            while not self.cmd.wait_count_player(4):  # ganti 4 sesuai jumlah slave
                await self.cmd.sleep(100)

            while self.cmd.is_monster_alive():
                await self.cmd.sleep(200)
                
                master = self.cmd.get_player_in_map(self.cmd.get_followed_player())
                check_master_in_cell = self.role == "master" or (master and master.str_frame == self.cmd.get_player().CELL)
                if not check_master_in_cell:
                    break

                if self.cmd.get_player().hasAura("Solar Flare"):
                    self.target_monsters = "Blessless Deer"
                else:
                    self.target_monsters = self.default_target

                if not self.is_attacking:
                    self.print_debug(f"Attacking monsters...")
                    self.is_attacking = True

                if self.do_taunt:
                    target = self.taunt_target or self.target_monsters
                    self.print_debug(f"{Fore.BLUE}Taunting {target}...{Fore.RESET}")
                    await self.cmd.sleep(500)
                    await self.cmd.wait_use_skill(5, target_monsters=target)
                    self.taunt_target = None
                    self.do_taunt = False
                    continue

                if self.cmd.get_player().hasAura("Sun's Heat"):
                    skill_mode = SkillMode.ATTACK_ONLY # dont use heal when having inverted dmg debuff
                else:
                    skill_mode = SkillMode.ALL

                await self.cmd.use_skill(
                    index = self.skill_list[self.skill_index], 
                    target_monsters = self.target_monsters, 
                    skill_mode = skill_mode
                    )
                self.skill_index += 1
                if self.skill_index >= len(self.skill_list):
                    self.skill_index = 0
                
            self.is_attacking = False
        print("Disconnected.")

# -------- Subclass untuk tiap variasi --------

class EclipseSlaveBot(AscendEclipseBot):
    def __init__(self, cmd: Command, **kwargs):
        super().__init__(cmd, role="slave", **kwargs)

class EclipseMasterBot(AscendEclipseBot):
    def __init__(self, cmd: Command, **kwargs):
        super().__init__(cmd, role="master", **kwargs)
        self.dungeon_timeleapse = 0
        self.cleared_count = 0
        self.last_cell = "Enter"
        
    async def to_next_cell(self):
        self.do_taunt = False
        self.converges_count = 0
        self.light_gather_count = 0

        # reset to "Enter" if dead from "r3"
        if self.last_cell == "r3":
            await self.cmd.jump_cell("Enter", "Spawn")
            self.print_debug("Waiting all slaves to be ready...")
            for slave in self.cmd.get_slaves():
                player = self.cmd.get_player_in_map(slave)
                if player:
                    self.print_debug(f"Waiting for:{slave} Cell:{player.str_frame} State:{player.int_state} HP:{player.int_hp}")
                    while player.str_frame != self.cmd.get_player().CELL or player.int_state != 1:
                        await self.cmd.sleep(100)
                        player = self.cmd.get_player_in_map(slave)
                    await self.cmd.sleep(500)

        self.print_debug(f"Checking for monsters...")

        await self.cmd.jump_cell("Enter", "Spawn")
        self.last_cell = "Enter"
        if self.cmd.is_monster_alive("Blessless Deer") or self.cmd.is_monster_alive("Fallen Star"):
            return

        await self.cmd.jump_cell("r1", "Left")
        self.last_cell = "r1"
        if self.cmd.is_monster_alive("Suffocated Light") or self.cmd.is_monster_alive("Imprisoned Fairy"):
            return

        await self.cmd.jump_cell("r2", "Left")
        self.last_cell = "r2"
        if self.cmd.is_monster_alive("Sunset Knight") or self.cmd.is_monster_alive("Moon Haze"):
            return

        await self.cmd.jump_cell("r3", "Left")
        self.last_cell = "r3"
        if self.cmd.is_monster_alive("Ascended Midnight") or self.cmd.is_monster_alive("Ascended Solstice"):
            return

        await self.cmd.jump_cell("r3a", "Left")
        self.last_cell = "r3a"
        
        bot_elapsed_seconds = time.monotonic() - self.bot_timeleapse
        bot_minutes = int(bot_elapsed_seconds // 60)
        bot_seconds = int(bot_elapsed_seconds % 60)
        
        elapsed_seconds = time.monotonic() - self.dungeon_timeleapse
        minutes = int(elapsed_seconds // 60)
        seconds = int(elapsed_seconds % 60)
        
        self.cleared_count += 1
        
        self.print_debug(f"{Fore.CYAN}Finished in : {minutes} minutes and {seconds} seconds.{Fore.RESET}")
        self.print_debug(f"{Fore.CYAN}Dungeon cleared {self.cleared_count} times.{Fore.RESET}")
        self.print_debug(f"{Fore.CYAN}Total time running : {bot_minutes} minutes and {bot_seconds} seconds.{Fore.RESET} ")

        self.print_debug("Rest in yulgar...")
        await self.cmd.join_map("yulgar", roomNumber=999999)
        await self.cmd.rest()
        await self.cmd.sleep(10000)
        self.print_debug("Entering new queue...")
        await self.enter_dungeon()

    async def setup_party(self):
        """Invite slaves, tunggu sampai join party, lalu masuk dungeon"""
        await self.cmd.join_map("yulgar", roomNumber=999999)
        await self.cmd.sleep(4000)

        self.print_debug("Waiting for all slaves to be online...")
        while not self.cmd.wait_count_player(4):  # ganti 4 sesuai jumlah slave
            await self.cmd.sleep(100)

        for slave in self.cmd.get_slaves():
            await self.cmd.send_packet(f"%xt%zm%gp%1%pi%{slave}%")
            await self.cmd.sleep(500)

        await self.cmd.sleep(4000)
        await self.enter_dungeon()

    async def enter_dungeon(self):
        self.dungeon_timeleapse = time.monotonic()
        await self.cmd.send_packet("%xt%zm%dungeonQueue%25127%ascendeclipse%")
        while self.cmd.is_not_in_map("ascendeclipse"):
            self.print_debug("Waiting for dungeon queue...")
            await self.cmd.sleep(500)
