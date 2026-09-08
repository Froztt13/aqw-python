import os
import sys
import time
import json
import asyncio
import threading
import re

# Add base directory to sys.path
base_dir = os.path.dirname(os.path.abspath(__file__))
if base_dir not in sys.path:
    sys.path.insert(0, base_dir)

from core.bot import Bot
from bot.templeshrine.temple.core.core_temple import MidnightSunBot, SolsticeMoonBot
from bot.templeshrine.eclipse.core.core_eclipse import EclipseMasterBot, EclipseSlaveBot
from bot.doom.weekly_doom import WeeklyDoomManager
from bot.slavery.bot_slave import main as slave_main

# Global log callback to Kotlin
kotlin_log_callback = None

ANSI_ESCAPE_PATTERN = re.compile(
    r'\x1B(?:[@-Z\\-_]|\[[0-?]*[ -/]*[@-~])|'  # Standard ANSI escapes
    r'\[\d{1,3}(?:;\d{1,3})*m|'                # Broken/stripped ANSI codes like [34m, [39m
    r'\x1b\[[0-9;]*[a-zA-Z]'                    # Explicit \x1b code
)

def strip_ansi_codes(text: str) -> str:
    if not text:
        return ""
    return ANSI_ESCAPE_PATTERN.sub("", text)

# --- Thread-Aware Log Redirector ---
class ThreadAwareLogRedirector:
    def __init__(self, original_stream):
        self.original_stream = original_stream
        self.thread_callbacks = {}

    def register_thread(self, thread_id, bot_type, username):
        self.thread_callbacks[thread_id] = (bot_type, username)

    def unregister_thread(self, thread_id):
        if thread_id in self.thread_callbacks:
            del self.thread_callbacks[thread_id]

    def write(self, message):
        self.original_stream.write(message)
        if not message:
            return
            
        clean_msg = strip_ansi_codes(message).strip()
        if not clean_msg:
            return
            
        current_thread_id = threading.get_ident()
        if current_thread_id in self.thread_callbacks:
            bot_type, username = self.thread_callbacks[current_thread_id]
            if kotlin_log_callback:
                try:
                    kotlin_log_callback(bot_type, username, clean_msg)
                except Exception:
                    pass
        else:
            if kotlin_log_callback:
                try:
                    kotlin_log_callback("System", "System", clean_msg)
                except Exception:
                    pass

    def flush(self):
        self.original_stream.flush()

global_redirector_out = ThreadAwareLogRedirector(sys.stdout)
global_redirector_err = ThreadAwareLogRedirector(sys.stderr)
sys.stdout = global_redirector_out
sys.stderr = global_redirector_err

# --- Taunt Coordinator ---
class TauntCoordinator:
    def __init__(self):
        self.taunters = []
        self.current_index = 0
        self.last_taunt_time = 0
        self.taunt_duration = 6.0
        self.active_taunter = None
        self.last_event_time = 0

    def register_taunter(self, username):
        if username not in self.taunters:
            self.taunters.append(username)
            self.taunters.sort()

    def unregister_taunter(self, username):
        if username in self.taunters:
            self.taunters.remove(username)
            if self.current_index >= len(self.taunters):
                self.current_index = 0

    def get_active_taunter(self):
        if not self.taunters:
            self.active_taunter = None
            return None
        now = time.time()
        if self.active_taunter is None or (now - self.last_taunt_time >= 15.0):
            if self.active_taunter is not None:
                self.current_index = (self.current_index + 1) % len(self.taunters)
            self.active_taunter = self.taunters[self.current_index]
            self.last_taunt_time = now
        return self.active_taunter

    def rotate_taunt(self):
        if self.taunters:
            self.current_index = (self.current_index + 1) % len(self.taunters)
            self.active_taunter = self.taunters[self.current_index]
            self.last_taunt_time = time.time()

    def skip_taunt(self, username):
        if self.active_taunter == username:
            self.rotate_taunt()

    def request_taunt(self, username):
        now = time.time()
        if now - self.last_event_time < 5.0:
            return False
            
        active = self.get_active_taunter()
        if active == username:
            self.last_event_time = now
            self.rotate_taunt()
            return True
        return False

# --- Config Directory Helper ---
def get_config_dir():
    app_data = os.environ.get("ANDROID_DATA_DIR")
    if app_data and os.path.exists(app_data):
        return app_data
    cfg_dir = os.path.expanduser("~/.aqw_bot")
    os.makedirs(cfg_dir, exist_ok=True)
    return cfg_dir

# --- Temple Bot Handler ---
class TempleManager:
    def __init__(self):
        self.config_path = os.path.join(get_config_dir(), "temple_config.json")
        self.active_threads = {}
        self.start_time = None
        self.taunt_coordinator = TauntCoordinator()
        self.last_error = None

    def load_config(self):
        default_config = {
            "server": "Alteon",
            "room_number": 9099,
            "temple_bot_type": "MidnightSunBot",
            "slots": {
                "slot1": {"username": "", "password": "", "char_class": "ArchPaladin", "role": "master", "is_taunter": True, "default_target": "Ascended Midnight,Blessless Deer"},
                "slot2": {"username": "", "password": "", "char_class": "StoneCrusher", "role": "slave", "is_taunter": False, "default_target": "Ascended Midnight,Blessless Deer"},
                "slot3": {"username": "", "password": "", "char_class": "Legion Revenant", "role": "slave", "is_taunter": False, "default_target": "Ascended Midnight,Blessless Deer"},
                "slot4": {"username": "", "password": "", "char_class": "Lord of Order", "role": "slave", "is_taunter": False, "default_target": "Ascended Midnight,Blessless Deer"}
            }
        }
        if os.path.exists(self.config_path):
            try:
                with open(self.config_path, "r") as f:
                    user_conf = json.load(f)
                    if "slots" in user_conf:
                        for sk, sv in user_conf["slots"].items():
                            if sk in default_config["slots"]:
                                default_config["slots"][sk].update(sv)
                        del user_conf["slots"]
                    default_config.update(user_conf)
            except Exception:
                pass
        return default_config

    def save_config(self, config):
        try:
            with open(self.config_path, "w") as f:
                json.dump(config, f, indent=4)
            return {"success": True}
        except Exception as e:
            return {"success": False, "error": str(e)}

    def reset_config(self):
        if os.path.exists(self.config_path):
            try:
                os.remove(self.config_path)
            except Exception:
                pass
        return self.load_config()

    def get_status(self):
        from datetime import datetime
        now = datetime.now()
        status_data = {}
        for s_id, t in list(self.active_threads.items()):
            if t and t.is_alive() and t.bot_instance:
                b = t.bot_instance
                p = b.player
                cooldowns = {0: 0.0, 1: 0.0, 2: 0.0, 3: 0.0, 4: 0.0, 5: 0.0}
                if p and hasattr(p, "SKILLS"):
                    for i in range(0, 6):
                        if i < len(p.SKILLS):
                            skill_data = p.SKILLS[i]
                            next_use = skill_data.get("nextUse")
                            if next_use and next_use > now:
                                cooldowns[i] = round((next_use - now).total_seconds(), 1)

                soe_qty = 0
                if p and hasattr(p, "get_item_inventory"):
                    item_soe = p.get_item_inventory("Scroll of Enrage")
                    if item_soe:
                        soe_qty = getattr(item_soe, "qty", 0)

                cell_monsters = []
                if hasattr(b, "monsters") and b.monsters and p and getattr(p, "CELL", None):
                    for mon in b.monsters:
                        if mon.frame and p.CELL and mon.frame.lower() == p.CELL.lower() and mon.max_hp > 0:
                            cell_monsters.append({
                                "id": mon.mon_map_id,
                                "name": mon.mon_name or f"Monster {mon.mon_map_id}",
                                "hp": mon.current_hp,
                                "max_hp": mon.max_hp,
                                "is_alive": mon.is_alive
                            })

                target_monsters = ""
                logic = getattr(b, "bot_logic_instance", None)
                if logic:
                    target_monsters = getattr(logic, "target_monsters", "") or getattr(logic, "default_target", "")

                status_data[s_id] = {
                    "running": True,
                    "is_connected": b.is_client_connected,
                    "map": getattr(b, "strMapName", "-"),
                    "cell": p.CELL if p else "-",
                    "pad": p.PAD if p else "-",
                    "hp": p.CURRENT_HP if p else 0,
                    "max_hp": p.MAX_HP if p else 0,
                    "mp": p.MANA if p else 0,
                    "max_mp": p.MAX_MP if p else 0,
                    "is_dead": p.ISDEAD if p else False,
                    "cooldowns": cooldowns,
                    "soe_qty": soe_qty,
                    "monsters": cell_monsters,
                    "target_monsters": target_monsters
                }
            else:
                status_data[s_id] = {"running": False}

        for s_id in ["slot1", "slot2", "slot3", "slot4"]:
            if s_id not in status_data:
                status_data[s_id] = {"running": False}

        # Check for thread-level or bot-level critical errors (e.g. missing SoE)
        for t in list(self.active_threads.values()):
            if t and t.bot_instance:
                err = getattr(t.bot_instance, "soe_error", None)
                if err:
                    self.last_error = err
                    self.stop_party()
                    break

        if self.last_error:
            status_data["_error"] = self.last_error
            self.last_error = None

        cleared_count = 0
        for t in self.active_threads.values():
            if t and t.is_alive() and t.bot_instance:
                b = t.bot_instance
                logic = getattr(b, "bot_logic_instance", None)
                if logic and hasattr(logic, "cleared_count"):
                    cleared_count = max(cleared_count, logic.cleared_count)

        time_running = int(time.time() - self.start_time) if self.start_time and any(t.is_alive() for t in self.active_threads.values()) else 0

        status_data["_active_taunter"] = self.taunt_coordinator.active_taunter
        status_data["_stats"] = {
            "time_running": time_running,
            "cleared_count": cleared_count
        }
        return status_data

    def start_party(self, config):
        if any(t.is_alive() for t in self.active_threads.values()):
            return {"success": False, "error": "Party is already running!"}

        self.last_error = None

        self.taunt_coordinator = TauntCoordinator()
        slots = config.get("slots", {})
        bot_type = config.get("temple_bot_type", "MidnightSunBot")
        bot_class = MidnightSunBot if bot_type == "MidnightSunBot" else SolsticeMoonBot
        
        for s_id in ["slot1", "slot2", "slot3", "slot4"]:
            s = slots.get(s_id, {})
            if not s.get("username") or not s.get("password") or not s.get("char_class"):
                return {"success": False, "error": f"Please fill credentials for all 4 slots ({s_id})."}

        master_user = slots["slot1"]["username"]
        slave_users = [slots[s]["username"] for s in ["slot2", "slot3", "slot4"]]

        self.start_time = time.time()
        for s_id in ["slot1", "slot2", "slot3", "slot4"]:
            s = slots[s_id]
            is_master = (s_id == "slot1")
            
            def make_runner(slot_id, slot_info, is_lead):
                def runner():
                    loop = asyncio.new_event_loop()
                    asyncio.set_event_loop(loop)
                    
                    t_id = threading.get_ident()
                    global_redirector_out.register_thread(t_id, "temple", slot_info["username"])
                    global_redirector_err.register_thread(t_id, "temple", slot_info["username"])

                    b = Bot(
                        roomNumber=int(config.get("room_number", 9099)),
                        itemsDropWhiteList=["Fragment of Midnight", "Fragment of Sunlight", "Ecliptic Offering"],
                        showLog=True,
                        showChat=True,
                        isScriptable=True,
                        followPlayer=master_user.lower(),
                        slavesPlayer=slave_users,
                        farmClass=slot_info.get("char_class", ""),
                        respawnCellPad=["Enter", "Spawn"],
                        muteSpamWarning=True
                    )
                    b.set_login_info(slot_info["username"], slot_info["password"], config.get("server", "Alteon"))
                    b.taunt_coordinator = self.taunt_coordinator
                    
                    t_inst = threading.current_thread()
                    t_inst.bot_instance = b

                    async def run_bot(cmd):
                        target_mon = slot_info.get("default_target")
                        inst = bot_class(
                            cmd,
                            role="master" if is_lead else "slave",
                            is_taunter=slot_info.get("is_taunter", False),
                            target_monsters=target_mon if target_mon else None
                        )
                        b.bot_logic_instance = inst
                        await inst.start()

                    try:
                        loop.run_until_complete(b.start_bot(run_bot))
                    except Exception as e:
                        print(f"[{slot_info['username']}] Temple Thread Error: {e}")
                    finally:
                        global_redirector_out.unregister_thread(t_id)
                        global_redirector_err.unregister_thread(t_id)
                        loop.close()

                return runner

            t = threading.Thread(target=make_runner(s_id, s, is_master), daemon=True)
            t.bot_instance = None
            t.username = s["username"]
            t.start()
            self.active_threads[s_id] = t

        return {"success": True}

    def stop_party(self):
        for s_id, t in list(self.active_threads.items()):
            if t and t.bot_instance:
                try:
                    t.bot_instance.stop_bot(user_triggered=True)
                except Exception:
                    pass
        self.active_threads.clear()
        self.start_time = None
        self.last_error = None
        return {"success": True}

# --- Eclipse Bot Handler ---
class EclipseManager:
    def __init__(self):
        self.config_path = os.path.join(get_config_dir(), "eclipse_config.json")
        self.active_threads = {}
        self.start_time = None
        self.taunt_coordinator = TauntCoordinator()
        self.last_error = None

    def load_config(self):
        default_config = {
            "server": "Alteon",
            "room_number": 9099,
            "slots": {
                "slot1": {"username": "", "password": "", "char_class": "Legion Revenant", "role": "master", "is_taunter": True, "moon_haze_taunter": False, "sunset_knight_taunter": False, "default_target": "Ascended Solstice,Blessless Deer"},
                "slot2": {"username": "", "password": "", "char_class": "StoneCrusher", "role": "slave", "is_taunter": False, "moon_haze_taunter": False, "sunset_knight_taunter": False, "default_target": "Ascended Solstice"},
                "slot3": {"username": "", "password": "", "char_class": "ArchPaladin", "role": "slave", "is_taunter": True, "moon_haze_taunter": True, "sunset_knight_taunter": False, "default_target": "Ascended Midnight"},
                "slot4": {"username": "", "password": "", "char_class": "Lord of Order", "role": "slave", "is_taunter": True, "moon_haze_taunter": False, "sunset_knight_taunter": True, "default_target": "Ascended Midnight"}
            }
        }
        if os.path.exists(self.config_path):
            try:
                with open(self.config_path, "r") as f:
                    user_conf = json.load(f)
                    if "slots" in user_conf:
                        for sk, sv in user_conf["slots"].items():
                            if sk in default_config["slots"]:
                                default_config["slots"][sk].update(sv)
                        del user_conf["slots"]
                    default_config.update(user_conf)
            except Exception:
                pass
        return default_config

    def save_config(self, config):
        try:
            with open(self.config_path, "w") as f:
                json.dump(config, f, indent=4)
            return {"success": True}
        except Exception as e:
            return {"success": False, "error": str(e)}

    def reset_config(self):
        if os.path.exists(self.config_path):
            try:
                os.remove(self.config_path)
            except Exception:
                pass
        return self.load_config()

    def get_status(self):
        from datetime import datetime
        now = datetime.now()
        status_data = {}
        for s_id, t in list(self.active_threads.items()):
            if t and t.is_alive() and t.bot_instance:
                b = t.bot_instance
                p = b.player
                cooldowns = {0: 0.0, 1: 0.0, 2: 0.0, 3: 0.0, 4: 0.0, 5: 0.0}
                if p and hasattr(p, "SKILLS"):
                    for i in range(0, 6):
                        if i < len(p.SKILLS):
                            skill_data = p.SKILLS[i]
                            next_use = skill_data.get("nextUse")
                            if next_use and next_use > now:
                                cooldowns[i] = round((next_use - now).total_seconds(), 1)

                soe_qty = 0
                if p and hasattr(p, "get_item_inventory"):
                    item_soe = p.get_item_inventory("Scroll of Enrage")
                    if item_soe:
                        soe_qty = getattr(item_soe, "qty", 0)

                cell_monsters = []
                if hasattr(b, "monsters") and b.monsters and p and getattr(p, "CELL", None):
                    for mon in b.monsters:
                        if mon.frame and p.CELL and mon.frame.lower() == p.CELL.lower() and mon.max_hp > 0:
                            cell_monsters.append({
                                "id": mon.mon_map_id,
                                "name": mon.mon_name or f"Monster {mon.mon_map_id}",
                                "hp": mon.current_hp,
                                "max_hp": mon.max_hp,
                                "is_alive": mon.is_alive
                            })

                target_monsters = ""
                logic = getattr(b, "bot_logic_instance", None)
                if logic:
                    target_monsters = getattr(logic, "target_monsters", "") or getattr(logic, "default_target", "")

                status_data[s_id] = {
                    "running": True,
                    "is_connected": b.is_client_connected,
                    "map": getattr(b, "strMapName", "-"),
                    "cell": p.CELL if p else "-",
                    "pad": p.PAD if p else "-",
                    "hp": p.CURRENT_HP if p else 0,
                    "max_hp": p.MAX_HP if p else 0,
                    "mp": p.MANA if p else 0,
                    "max_mp": p.MAX_MP if p else 0,
                    "is_dead": p.ISDEAD if p else False,
                    "cooldowns": cooldowns,
                    "taunt_error": getattr(b, "taunt_error", False),
                    "soe_qty": soe_qty,
                    "monsters": cell_monsters,
                    "target_monsters": target_monsters
                }
            else:
                status_data[s_id] = {"running": False}

        for s_id in ["slot1", "slot2", "slot3", "slot4"]:
            if s_id not in status_data:
                status_data[s_id] = {"running": False}

        # Check for thread-level or bot-level critical errors (e.g. missing SoE)
        for t in list(self.active_threads.values()):
            if t and t.bot_instance:
                err = getattr(t.bot_instance, "soe_error", None)
                if err:
                    self.last_error = err
                    self.stop_party()
                    break

        if self.last_error:
            status_data["_error"] = self.last_error
            self.last_error = None

        cleared_count = 0
        for t in self.active_threads.values():
            if t and t.is_alive() and t.bot_instance:
                b = t.bot_instance
                logic = getattr(b, "bot_logic_instance", None)
                if logic and hasattr(logic, "cleared_count"):
                    cleared_count = max(cleared_count, logic.cleared_count)

        time_running = int(time.time() - self.start_time) if self.start_time and any(t.is_alive() for t in self.active_threads.values()) else 0

        status_data["_active_taunter"] = self.taunt_coordinator.active_taunter
        status_data["_stats"] = {
            "time_running": time_running,
            "cleared_count": cleared_count
        }
        return status_data

    def start_party(self, config):
        if any(t.is_alive() for t in self.active_threads.values()):
            return {"success": False, "error": "Party is already running!"}

        self.last_error = None

        self.taunt_coordinator = TauntCoordinator()
        slots = config.get("slots", {})
        
        for s_id in ["slot1", "slot2", "slot3", "slot4"]:
            s = slots.get(s_id, {})
            if not s.get("username") or not s.get("password") or not s.get("char_class"):
                return {"success": False, "error": f"Please fill credentials for all 4 slots ({s_id})."}

        master_user = slots["slot1"]["username"]
        slave_users = [slots[s]["username"] for s in ["slot2", "slot3", "slot4"]]

        moon_haze_slots = [
            s_id for s_id in ["slot1", "slot2", "slot3", "slot4"]
            if slots[s_id].get("moon_haze_taunter", s_id == "slot3")
        ]
        sunset_knight_slots = [
            s_id for s_id in ["slot1", "slot2", "slot3", "slot4"]
            if slots[s_id].get("sunset_knight_taunter", s_id == "slot4")
        ]

        self.start_time = time.time()
        for s_id in ["slot1", "slot2", "slot3", "slot4"]:
            s = slots[s_id]
            is_master = (s_id == "slot1")

            def make_runner(slot_id, slot_info, is_lead):
                def runner():
                    loop = asyncio.new_event_loop()
                    asyncio.set_event_loop(loop)
                    
                    t_id = threading.get_ident()
                    global_redirector_out.register_thread(t_id, "eclipse", slot_info["username"])
                    global_redirector_err.register_thread(t_id, "eclipse", slot_info["username"])

                    b = Bot(
                        roomNumber=int(config.get("room_number", 9099)),
                        itemsDropWhiteList=["Eclipse General", "Fragment of the Sun", "Fragment of the Moon", "Soleil", "Lunette", "Midnight Sun", "Solstice Moon"],
                        showLog=True,
                        showChat=True,
                        isScriptable=True,
                        followPlayer=master_user.lower(),
                        slavesPlayer=slave_users,
                        farmClass=slot_info.get("char_class", ""),
                        respawnCellPad=["Enter", "Spawn"],
                        muteSpamWarning=True
                    )
                    b.set_login_info(slot_info["username"], slot_info["password"], config.get("server", "Alteon"))
                    b.taunt_coordinator = self.taunt_coordinator
                    
                    t_inst = threading.current_thread()
                    t_inst.bot_instance = b

                    async def run_bot(cmd):
                        moon_haze = slot_id in moon_haze_slots
                        moon_haze_idx = moon_haze_slots.index(slot_id) if moon_haze else 0
                        moon_haze_total = len(moon_haze_slots)

                        sunset_knight = slot_id in sunset_knight_slots
                        sunset_knight_idx = sunset_knight_slots.index(slot_id) if sunset_knight else 0
                        sunset_knight_total = len(sunset_knight_slots)

                        default_targets_preset = {
                            "slot1": "Ascended Solstice,Blessless Deer",
                            "slot2": "Ascended Solstice",
                            "slot3": "Ascended Midnight",
                            "slot4": "Ascended Midnight",
                        }
                        target_mon = slot_info.get("default_target") or default_targets_preset.get(slot_id, "")

                        if slot_id == "slot1":
                            inst = EclipseMasterBot(
                                cmd,
                                default_target=target_mon,
                                taunt_parity="odd",
                                converge_type="sun",
                                light_gather_taunter=True,
                                moon_haze_taunter=moon_haze,
                                moon_haze_index=moon_haze_idx,
                                moon_haze_total=moon_haze_total,
                                sunset_knight_taunter=sunset_knight,
                                sunset_knight_index=sunset_knight_idx,
                                sunset_knight_total=sunset_knight_total,
                            )
                        elif slot_id == "slot2":
                            inst = EclipseSlaveBot(
                                cmd,
                                default_target=target_mon,
                                taunt_parity="even",
                                converge_type="sun",
                                light_gather_taunter=True,
                                moon_haze_taunter=moon_haze,
                                moon_haze_index=moon_haze_idx,
                                moon_haze_total=moon_haze_total,
                                sunset_knight_taunter=sunset_knight,
                                sunset_knight_index=sunset_knight_idx,
                                sunset_knight_total=sunset_knight_total,
                            )
                        elif slot_id == "slot3":
                            inst = EclipseSlaveBot(
                                cmd,
                                default_target=target_mon,
                                taunt_parity="odd",
                                converge_type="moon",
                                light_gather_taunter=True,
                                moon_haze_taunter=moon_haze,
                                moon_haze_index=moon_haze_idx,
                                moon_haze_total=moon_haze_total,
                                sunset_knight_taunter=sunset_knight,
                                sunset_knight_index=sunset_knight_idx,
                                sunset_knight_total=sunset_knight_total,
                            )
                        else:  # slot4
                            inst = EclipseSlaveBot(
                                cmd,
                                default_target=target_mon,
                                taunt_parity="even",
                                converge_type="moon",
                                light_gather_taunter=True,
                                moon_haze_taunter=moon_haze,
                                moon_haze_index=moon_haze_idx,
                                moon_haze_total=moon_haze_total,
                                sunset_knight_taunter=sunset_knight,
                                sunset_knight_index=sunset_knight_idx,
                                sunset_knight_total=sunset_knight_total,
                            )
                        b.bot_logic_instance = inst
                        await inst.start()

                    try:
                        loop.run_until_complete(b.start_bot(run_bot))
                    except Exception as e:
                        print(f"[{slot_info['username']}] Eclipse Thread Error: {e}")
                    finally:
                        global_redirector_out.unregister_thread(t_id)
                        global_redirector_err.unregister_thread(t_id)
                        loop.close()

                return runner

            t = threading.Thread(target=make_runner(s_id, s, is_master), daemon=True)
            t.bot_instance = None
            t.username = s["username"]
            t.start()
            self.active_threads[s_id] = t

        return {"success": True}

    def stop_party(self):
        for s_id, t in list(self.active_threads.items()):
            if t and t.bot_instance:
                try:
                    t.bot_instance.stop_bot(user_triggered=True)
                except Exception:
                    pass
        self.active_threads.clear()
        self.start_time = None
        self.last_error = None
        return {"success": True}

# --- Slavery Bot Handler ---
class SlaveryManager:
    def __init__(self):
        self.config_path = os.path.join(get_config_dir(), "slavery_config.json")
        self.active_threads = {}
        self.start_time = None
        self.taunt_coordinator = TauntCoordinator()
        self.last_error = None

    def load_config(self):
        default_config = {
            "server": "Gravelyn",
            "follow_player": "",
            "default_room_number": 9099,
            "copy_walk": True,
            "auto_zone": "none",
            "targets_priority": "Defense Drone,Staff of Inversion",
            "whitelist": "Treasure Chest, Void Aura",
            "locked_zones": "ultraezrajal, ultrawarden, ultraengineer, doomvault, doomvaultb, championdrakath, tercessuinotlim, icestormunder",
            "slots": {
                "slot1": {
                    "enabled": True,
                    "username": "",
                    "password": "",
                    "char_class": "Lord of Order",
                    "skills": [
                        {"index": 1, "threshold_type": "NONE", "operator": "<", "threshold_value": 0},
                        {"index": 2, "threshold_type": "NONE", "operator": "<", "threshold_value": 0},
                        {"index": 3, "threshold_type": "NONE", "operator": "<", "threshold_value": 0},
                        {"index": 4, "threshold_type": "NONE", "operator": "<", "threshold_value": 0}
                    ],
                    "is_taunter": False
                },
                "slot2": {
                    "enabled": True,
                    "username": "",
                    "password": "",
                    "char_class": "Legion Revenant",
                    "skills": [
                        {"index": 1, "threshold_type": "NONE", "operator": "<", "threshold_value": 0},
                        {"index": 2, "threshold_type": "NONE", "operator": "<", "threshold_value": 0},
                        {"index": 3, "threshold_type": "NONE", "operator": "<", "threshold_value": 0},
                        {"index": 4, "threshold_type": "NONE", "operator": "<", "threshold_value": 0}
                    ],
                    "is_taunter": False
                },
                "slot3": {
                    "enabled": False,
                    "username": "",
                    "password": "",
                    "char_class": "ArchPaladin",
                    "skills": [
                        {"index": 1, "threshold_type": "NONE", "operator": "<", "threshold_value": 0},
                        {"index": 2, "threshold_type": "NONE", "operator": "<", "threshold_value": 0},
                        {"index": 3, "threshold_type": "NONE", "operator": "<", "threshold_value": 0},
                        {"index": 4, "threshold_type": "NONE", "operator": "<", "threshold_value": 0}
                    ],
                    "is_taunter": False
                },
                "slot4": {
                    "enabled": False,
                    "username": "",
                    "password": "",
                    "char_class": "StoneCrusher",
                    "skills": [
                        {"index": 1, "threshold_type": "NONE", "operator": "<", "threshold_value": 0},
                        {"index": 2, "threshold_type": "NONE", "operator": "<", "threshold_value": 0},
                        {"index": 3, "threshold_type": "NONE", "operator": "<", "threshold_value": 0},
                        {"index": 4, "threshold_type": "NONE", "operator": "<", "threshold_value": 0}
                    ],
                    "is_taunter": False
                }
            }
        }
        if os.path.exists(self.config_path):
            try:
                with open(self.config_path, "r") as f:
                    user_conf = json.load(f)
                    if "slots" in user_conf:
                        for sk, sv in user_conf["slots"].items():
                            if sk in default_config["slots"]:
                                default_config["slots"][sk].update(sv)
                        del user_conf["slots"]
                    default_config.update(user_conf)
            except Exception:
                pass
        return default_config

    def save_config(self, config):
        try:
            with open(self.config_path, "w") as f:
                json.dump(config, f, indent=4)
            return {"success": True}
        except Exception as e:
            return {"success": False, "error": str(e)}

    def reset_config(self):
        if os.path.exists(self.config_path):
            try:
                os.remove(self.config_path)
            except Exception:
                pass
        return self.load_config()

    def get_status(self):
        from datetime import datetime
        now = datetime.now()
        status_data = {}
        for s_id, t in list(self.active_threads.items()):
            if t and t.is_alive() and getattr(t, "bot_instance", None):
                b = t.bot_instance
                p = getattr(b, "player", None)
                cooldowns = {0: 0.0, 1: 0.0, 2: 0.0, 3: 0.0, 4: 0.0, 5: 0.0}
                if p and hasattr(p, "SKILLS"):
                    for i in range(0, 6):
                        if i < len(p.SKILLS):
                            skill_data = p.SKILLS[i]
                            next_use = skill_data.get("nextUse")
                            if next_use and next_use > now:
                                cooldowns[i] = round((next_use - now).total_seconds(), 1)

                soe_qty = 0
                if p and hasattr(p, "get_item_inventory"):
                    item_soe = p.get_item_inventory("Scroll of Enrage")
                    if item_soe:
                        soe_qty = getattr(item_soe, "qty", 0)

                cell_monsters = []
                if hasattr(b, "monsters") and b.monsters and p and getattr(p, "CELL", None):
                    for mon in b.monsters:
                        if mon.frame and p.CELL and mon.frame.lower() == p.CELL.lower() and mon.max_hp > 0:
                            cell_monsters.append({
                                "id": mon.mon_map_id,
                                "name": mon.mon_name or f"Monster {mon.mon_map_id}",
                                "hp": mon.current_hp,
                                "max_hp": mon.max_hp,
                                "is_alive": mon.is_alive
                            })

                target_monsters = getattr(b, "targets_priority", "")

                status_data[s_id] = {
                    "running": True,
                    "is_connected": getattr(b, "is_client_connected", False),
                    "map": getattr(b, "strMapName", "-"),
                    "cell": p.CELL if p else "-",
                    "pad": p.PAD if p else "-",
                    "hp": p.CURRENT_HP if p else 0,
                    "max_hp": p.MAX_HP if p else 0,
                    "mp": p.MANA if p else 0,
                    "max_mp": p.MAX_MP if p else 0,
                    "is_dead": p.ISDEAD if p else False,
                    "cooldowns": cooldowns,
                    "taunt_error": getattr(b, "taunt_error", False),
                    "soe_qty": soe_qty,
                    "monsters": cell_monsters,
                    "target_monsters": target_monsters
                }
            else:
                status_data[s_id] = {"running": False}

        for s_id in ["slot1", "slot2", "slot3", "slot4"]:
            if s_id not in status_data:
                status_data[s_id] = {"running": False}

        if self.last_error:
            status_data["_error"] = self.last_error
            self.last_error = None

        time_running = int(time.time() - self.start_time) if self.start_time and any(t.is_alive() for t in self.active_threads.values()) else 0

        status_data["_active_taunter"] = self.taunt_coordinator.active_taunter
        status_data["_stats"] = {
            "time_running": time_running,
            "cleared_count": 0
        }
        return status_data

    def start_party(self, config):
        if any(t.is_alive() for t in self.active_threads.values()):
            return {"success": False, "error": "Party is already running!"}

        self.last_error = None

        follow_player = config.get("follow_player", "").strip()
        if not follow_player:
            return {"success": False, "error": "Please specify the Master Account to follow."}

        slots = config.get("slots", {})
        active_slot_ids = []
        for s_id in ["slot1", "slot2", "slot3", "slot4"]:
            s = slots.get(s_id, {})
            if s.get("enabled", True):
                if not s.get("username") or not s.get("password") or not s.get("char_class"):
                    return {"success": False, "error": f"Please fill credentials for enabled {s_id}."}
                active_slot_ids.append(s_id)

        if not active_slot_ids:
            return {"success": False, "error": "No enabled account slots configured."}

        self.taunt_coordinator = TauntCoordinator()
        whitelist_val = config.get("whitelist", "Treasure Chest, Void Aura")
        if isinstance(whitelist_val, list):
            whitelist_items = whitelist_val
        else:
            whitelist_items = [x.strip() for x in whitelist_val.split(",") if x.strip()]

        locked_zones_val = config.get("locked_zones", "")
        if isinstance(locked_zones_val, list):
            locked_zones_list = locked_zones_val
        else:
            locked_zones_list = [x.strip() for x in locked_zones_val.split(",") if x.strip()]

        self.start_time = time.time()
        for s_id in active_slot_ids:
            s = slots[s_id]

            def make_runner(slot_id, slot_info):
                def runner():
                    loop = asyncio.new_event_loop()
                    asyncio.set_event_loop(loop)

                    t_id = threading.get_ident()
                    global_redirector_out.register_thread(t_id, "slavery", slot_info["username"])
                    global_redirector_err.register_thread(t_id, "slavery", slot_info["username"])

                    b = Bot(
                        itemsDropWhiteList=whitelist_items,
                        cmdDelay=500,
                        showDebug=True,
                        autoRelogin=True,
                        isScriptable=True,
                        followPlayer=follow_player.lower(),
                        farmClass=slot_info.get("char_class", ""),
                        roomNumber=int(config.get("default_room_number", 9099)),
                        respawnCellPad=["Enter", "Spawn"],
                        muteSpamWarning=True
                    )
                    b.set_login_info(slot_info["username"], slot_info["password"], config.get("server", "Gravelyn"))

                    # Set custom bot properties used by bot_slave.py
                    b.follow_player = follow_player
                    b.default_room_number = int(config.get("default_room_number", 9099))
                    b.targets_priority = config.get("targets_priority", "Defense Drone,Staff of Inversion")
                    b.copy_walk = config.get("copy_walk", True)
                    b.auto_zone = config.get("auto_zone", "none")
                    b.locked_zones = locked_zones_list
                    b.skills = slot_info.get("skills", [])
                    b.taunter = slot_info.get("is_taunter", False)
                    b.taunt_coordinator = self.taunt_coordinator
                    b.checking_locked_zone = False

                    t_inst = threading.current_thread()
                    t_inst.bot_instance = b

                    try:
                        loop.run_until_complete(b.start_bot(slave_main))
                    except Exception as e:
                        print(f"[{slot_info['username']}] Slavery Thread Error: {e}")
                    finally:
                        global_redirector_out.unregister_thread(t_id)
                        global_redirector_err.unregister_thread(t_id)

                return runner

            t = threading.Thread(target=make_runner(s_id, s), name=f"Slavery-{s_id}")
            t.daemon = True
            t.bot_instance = None
            t.username = s["username"]
            self.active_threads[s_id] = t
            t.start()

        return {"success": True}

    def stop_party(self):
        for s_id, t in list(self.active_threads.items()):
            if t and t.bot_instance:
                try:
                    t.bot_instance.stop_bot(user_triggered=True)
                except Exception:
                    pass
        self.active_threads.clear()
        self.start_time = None
        self.last_error = None
        return {"success": True}

# --- Singletons ---
temple_mgr = TempleManager()
eclipse_mgr = EclipseManager()
doom_mgr = WeeklyDoomManager(global_redirector_out, global_redirector_err, get_config_dir)
slavery_mgr = SlaveryManager()

# --- Public Kotlin-Chaquopy Bridge Interface ---
def init_bridge(callback=None):
    global kotlin_log_callback
    kotlin_log_callback = callback
    return True

# Temple Bridge Functions
def temple_load_config() -> str:
    return json.dumps(temple_mgr.load_config())

def temple_save_config(config_json: str) -> str:
    try:
        cfg = json.loads(config_json)
        return json.dumps(temple_mgr.save_config(cfg))
    except Exception as e:
        return json.dumps({"success": False, "error": str(e)})

def temple_reset_config() -> str:
    return json.dumps(temple_mgr.reset_config())

def temple_start_party(config_json: str) -> str:
    try:
        cfg = json.loads(config_json)
        return json.dumps(temple_mgr.start_party(cfg))
    except Exception as e:
        return json.dumps({"success": False, "error": str(e)})

def temple_stop_party() -> str:
    return json.dumps(temple_mgr.stop_party())

def temple_get_status() -> str:
    return json.dumps(temple_mgr.get_status())

# Eclipse Bridge Functions
def eclipse_load_config() -> str:
    return json.dumps(eclipse_mgr.load_config())

def eclipse_save_config(config_json: str) -> str:
    try:
        cfg = json.loads(config_json)
        return json.dumps(eclipse_mgr.save_config(cfg))
    except Exception as e:
        return json.dumps({"success": False, "error": str(e)})

def eclipse_reset_config() -> str:
    return json.dumps(eclipse_mgr.reset_config())

def eclipse_start_party(config_json: str) -> str:
    try:
        cfg = json.loads(config_json)
        return json.dumps(eclipse_mgr.start_party(cfg))
    except Exception as e:
        return json.dumps({"success": False, "error": str(e)})

def eclipse_stop_party() -> str:
    return json.dumps(eclipse_mgr.stop_party())

def eclipse_get_status() -> str:
    return json.dumps(eclipse_mgr.get_status())

# Weekly Doom Bridge Functions
def doom_load_config() -> str:
    return json.dumps(doom_mgr.load_config())

def doom_save_config(config_json: str) -> str:
    try:
        cfg = json.loads(config_json)
        return json.dumps(doom_mgr.save_config(cfg))
    except Exception as e:
        return json.dumps({"success": False, "error": str(e)})

def doom_reset_config() -> str:
    return json.dumps(doom_mgr.reset_config())

def doom_start(config_json: str) -> str:
    try:
        cfg = json.loads(config_json)
        return json.dumps(doom_mgr.start(cfg))
    except Exception as e:
        return json.dumps({"success": False, "error": str(e)})

def doom_stop() -> str:
    return json.dumps(doom_mgr.stop())

def doom_get_status() -> str:
    return json.dumps(doom_mgr.get_status())

# Slavery Bridge Functions
def slavery_load_config() -> str:
    return json.dumps(slavery_mgr.load_config())

def slavery_save_config(config_json: str) -> str:
    try:
        cfg = json.loads(config_json)
        return json.dumps(slavery_mgr.save_config(cfg))
    except Exception as e:
        return json.dumps({"success": False, "error": str(e)})

def slavery_reset_config() -> str:
    return json.dumps(slavery_mgr.reset_config())

def slavery_start_party(config_json: str) -> str:
    try:
        cfg = json.loads(config_json)
        return json.dumps(slavery_mgr.start_party(cfg))
    except Exception as e:
        return json.dumps({"success": False, "error": str(e)})

def slavery_stop_party() -> str:
    return json.dumps(slavery_mgr.stop_party())

def slavery_get_status() -> str:
    return json.dumps(slavery_mgr.get_status())

# Hub Overview Status
def get_hub_status() -> str:
    active_temple = [s for s, t in temple_mgr.active_threads.items() if t.is_alive()]
    temple_time = int(time.time() - temple_mgr.start_time) if temple_mgr.start_time and active_temple else 0
    
    active_eclipse = [s for s, t in eclipse_mgr.active_threads.items() if t.is_alive()]
    eclipse_time = int(time.time() - eclipse_mgr.start_time) if eclipse_mgr.start_time and active_eclipse else 0

    doom_time = int(time.time() - doom_mgr.start_time) if doom_mgr.start_time and doom_mgr.is_running else 0

    active_slavery = [s for s, t in slavery_mgr.active_threads.items() if t.is_alive()]
    slavery_time = int(time.time() - slavery_mgr.start_time) if slavery_mgr.start_time and active_slavery else 0

    status = {
        "temple": {
            "running": len(active_temple) > 0,
            "count": len(active_temple),
            "members": [t.username for t in temple_mgr.active_threads.values() if t.is_alive()],
            "time_running": temple_time
        },
        "eclipse": {
            "running": len(active_eclipse) > 0,
            "count": len(active_eclipse),
            "members": [t.username for t in eclipse_mgr.active_threads.values() if t.is_alive()],
            "time_running": eclipse_time
        },
        "doom": {
            "running": doom_mgr.is_running,
            "current_username": doom_mgr.current_username,
            "time_running": doom_time
        },
        "slavery": {
            "running": len(active_slavery) > 0,
            "count": len(active_slavery),
            "members": [t.username for t in slavery_mgr.active_threads.values() if t.is_alive()],
            "time_running": slavery_time
        }
    }
    return json.dumps(status)
