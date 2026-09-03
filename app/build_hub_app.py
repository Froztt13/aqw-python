import os
import sys
import time
import json
import asyncio
import threading
import socket
import html
import re
import importlib
import platform
import subprocess
import shutil
import hashlib
import webview
from bottle import Bottle, static_file, request

# Determine project root path
def get_project_root():
    if getattr(sys, 'frozen', False):
        contents_dir = os.path.dirname(os.path.dirname(sys.executable))
        app_dir = os.path.dirname(contents_dir)
        parent_dir = os.path.dirname(app_dir)
        grandparent_dir = os.path.dirname(parent_dir)
        for path in [grandparent_dir, parent_dir, os.getcwd()]:
            if os.path.exists(os.path.join(path, "bot")):
                return os.path.abspath(path)
        return os.path.abspath(grandparent_dir)
    else:
        return os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

project_root = get_project_root()
if project_root not in sys.path:
    sys.path.insert(0, project_root)

# Import Bot classes from core modules
from core.bot import Bot
from bot.templeshrine.temple.core.core_temple import MidnightSunBot, SolsticeMoonBot
from bot.templeshrine.eclipse.core.core_eclipse import EclipseMasterBot, EclipseSlaveBot

# --- TauntCoordinator Class ---
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
            print(f"[TauntCoordinator] Registered {username}. Current list: {self.taunters}")

    def unregister_taunter(self, username):
        if username in self.taunters:
            self.taunters.remove(username)
            if self.current_index >= len(self.taunters):
                self.current_index = 0
            print(f"[TauntCoordinator] Unregistered {username}. Current list: {self.taunters}")

    def get_active_taunter(self):
        if not self.taunters:
            self.active_taunter = None
            return None
        now = time.time()
        # Fallback rotation after 15 seconds if the active taunter failed to cast
        if self.active_taunter is None or (now - self.last_taunt_time >= 15.0):
            if self.active_taunter is not None:
                self.current_index = (self.current_index + 1) % len(self.taunters)
            self.active_taunter = self.taunters[self.current_index]
            self.last_taunt_time = now
            print(f"[TauntCoordinator] Fallback rotated to {self.active_taunter}")
        return self.active_taunter

    def rotate_taunt(self):
        if self.taunters:
            self.current_index = (self.current_index + 1) % len(self.taunters)
            self.active_taunter = self.taunters[self.current_index]
            self.last_taunt_time = time.time()
            print(f"[TauntCoordinator] Rotated to {self.active_taunter} after successful cast.")

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

# --- Helper to strip/convert ANSI codes from colorama to HTML classes ---
ansi_escape = re.compile(r'\x1B(?:[@-Z\\-_]|\[[0-?]*[ -/]*[@-~])')

def ansi_to_html(text):
    text = text.replace('\r', '')
    text = html.escape(text)
    replacements = {
        "\x1b[30m": '<span class="log-black">',
        "\x1b[31m": '<span class="log-red">',
        "\x1b[32m": '<span class="log-green">',
        "\x1b[33m": '<span class="log-yellow">',
        "\x1b[34m": '<span class="log-blue">',
        "\x1b[35m": '<span class="log-magenta">',
        "\x1b[36m": '<span class="log-cyan">',
        "\x1b[37m": '<span class="log-white">',
        "\x1b[39m": '</span>',
        "\x1b[1m": '<span class="log-bold">',
        "\x1b[22m": '</span>',
        "\x1b[0m": '</span>'
    }
    for code, tag in replacements.items():
        text = text.replace(code, tag)
    text = ansi_escape.sub('', text)
    return text

# --- Define Unified Log Redirector ---
class UnifiedThreadRedirector:
    def __init__(self, original_stream):
        self.original_stream = original_stream
        self.thread_callbacks = {}  # thread_id -> (username, callback)
        self.combined_api = None
        self.default_callback = lambda x: None

    def register_thread(self, thread_id, username, callback):
        self.thread_callbacks[thread_id] = (username, callback)

    def unregister_thread(self, thread_id):
        if thread_id in self.thread_callbacks:
            del self.thread_callbacks[thread_id]

    def write(self, message):
        self.original_stream.write(message)
        if not message:
            return
            
        current_thread_id = threading.get_ident()
        if current_thread_id in self.thread_callbacks:
            username, callback = self.thread_callbacks[current_thread_id]
            callback(username, message)
        else:
            # Fallback/default logging based on active page
            if self.combined_api and self.combined_api.window:
                try:
                    url = self.combined_api.window.get_current_url() or ""
                    if "/slavery" in url:
                        self.combined_api.slavery_api.handle_slave_log("System", message)
                    elif "/temple" in url:
                        self.combined_api.temple_api.handle_slave_log("System", message)
                    elif "/eclipse" in url:
                        self.combined_api.eclipse_api.handle_slave_log("System", message)
                    elif "/aqw" in url:
                        self.combined_api.aqw_api.handle_log(message)
                except Exception:
                    pass

    def flush(self):
        self.original_stream.flush()

# Setup unified global redirectors
unified_redirector_out = UnifiedThreadRedirector(sys.stdout)
unified_redirector_err = UnifiedThreadRedirector(sys.stderr)

# Assign global overrides
sys.stdout = unified_redirector_out
sys.stderr = unified_redirector_err

# --- Thread Classes for Sub-Bots ---
class BotThread(threading.Thread):
    def __init__(self, bot_instance, bot_path):
        super().__init__()
        self.bot_instance = bot_instance
        self.bot_path = bot_path
        self.loop = None
        self.daemon = True

    def run(self):
        self.loop = asyncio.new_event_loop()
        asyncio.set_event_loop(self.loop)
        try:
            bot_class = importlib.import_module(self.bot_path)
            print(f"Starting bot execution script: {self.bot_path}")
            self.loop.run_until_complete(self.bot_instance.start_bot(bot_class.main))
        except Exception as e:
            print(f"Bot execution stopped or error occurred: {e}")
        finally:
            self.loop.close()

class SlaveBotThread(threading.Thread):
    def __init__(self, username, password, char_class, config, callback, skills="1,2,3,4", hp_operator="<", hp_threshold=0, hp_skills="", mp_operator="<", mp_threshold=0, mp_skills="", taunter=False, taunt_coordinator=None):
        super().__init__()
        self.username = username
        self.password = password
        self.char_class = char_class
        self.config = config
        self.callback = callback
        self.skills = skills
        self.hp_operator = hp_operator
        self.hp_threshold = hp_threshold
        self.hp_skills = hp_skills
        self.mp_operator = mp_operator
        self.mp_threshold = mp_threshold
        self.mp_skills = mp_skills
        self.taunter = taunter
        self.taunt_coordinator = taunt_coordinator
        self.bot_instance = None
        self.loop = None
        self.daemon = True

    def run(self):
        thread_id = threading.get_ident()
        unified_redirector_out.register_thread(thread_id, self.username, self.callback)
        unified_redirector_err.register_thread(thread_id, self.username, self.callback)
        
        self.loop = asyncio.new_event_loop()
        asyncio.set_event_loop(self.loop)
        try:
            self.bot_instance = Bot(
                roomNumber=int(self.config.get("room_number", 1)),
                itemsDropWhiteList=self.config.get("whitelist", []),
                showLog=True,
                showDebug=False,
                showChat=True,
                isScriptable=True,
                followPlayer=self.config.get("follow_player", ""),
                farmClass=self.char_class,
                autoRelogin=True,
                muteSpamWarning=True,
                antiMod=True
            )
            self.bot_instance.set_login_info(self.username, self.password, self.config.get("server", "Artix"))
            
            # Inject properties into bot instance for thread safety
            self.bot_instance.default_room_number = int(self.config.get("room_number", 9099))
            self.bot_instance.targets_priority = self.config.get("targets_priority", "Defense Drone,Staff of Inversion")
            self.bot_instance.locked_zones = self.config.get("locked_zones", [])
            self.bot_instance.copy_walk = self.config.get("copy_walk", True)
            self.bot_instance.auto_zone = self.config.get("auto_zone", "none")
            self.bot_instance.skills = self.skills
            self.bot_instance.hp_operator = self.hp_operator
            self.bot_instance.hp_threshold = self.hp_threshold
            self.bot_instance.hp_skills = self.hp_skills
            self.bot_instance.mp_operator = self.mp_operator
            self.bot_instance.mp_threshold = self.mp_threshold
            self.bot_instance.mp_skills = self.mp_skills
            self.bot_instance.taunter = self.taunter
            self.bot_instance.taunt_coordinator = self.taunt_coordinator
            
            bot_module = importlib.import_module("bot.slavery.bot_slave")
            
            print(f"[{self.username}] Bot client launching...")
            self.loop.run_until_complete(self.bot_instance.start_bot(bot_module.main))
        except Exception as e:
            print(f"[{self.username}] Thread Exception: {e}")
        finally:
            print(f"[{self.username}] Thread terminated.")
            if self.taunt_coordinator:
                self.taunt_coordinator.unregister_taunter(self.username)
            unified_redirector_out.unregister_thread(thread_id)
            unified_redirector_err.unregister_thread(thread_id)
            self.loop.close()

class TempleBotThread(threading.Thread):
    def __init__(self, slot_id, username, password, char_class, bot_class, role, is_taunter, config, callback, taunt_coordinator=None):
        super().__init__()
        self.slot_id = slot_id
        self.username = username
        self.password = password
        self.char_class = char_class
        self.bot_class = bot_class
        self.role = role
        self.is_taunter = is_taunter
        self.config = config
        self.callback = callback
        self.taunt_coordinator = taunt_coordinator
        self.bot_instance = None
        self.daemon = True

    def run(self):
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        
        thread_id = threading.get_ident()
        unified_redirector_out.register_thread(thread_id, self.username, self.callback)
        unified_redirector_err.register_thread(thread_id, self.username, self.callback)

        b = Bot(
            roomNumber=int(self.config.get("room_number", 9099)),
            itemsDropWhiteList=[
                "Fragment of Midnight",
                "Fragment of Sunlight",
                "Ecliptic Offering",
            ],
            showLog=True,
            showDebug=False,
            showChat=True,
            isScriptable=True,
            followPlayer=self.config.get("master_username", "").lower(),
            slavesPlayer=self.config.get("slaves_usernames", []),
            farmClass=self.char_class,
            respawnCellPad=["Enter", "Spawn"],
            muteSpamWarning=True
        )
        b.set_login_info(self.username, self.password, self.config.get("server", "Alteon"))
        b.taunt_coordinator = self.taunt_coordinator
        self.bot_instance = b

        async def run_bot(cmd):
            bot_inst = self.bot_class(
                cmd,
                role=self.role,
                is_taunter=self.is_taunter
            )
            await bot_inst.start()
        
        try:
            loop.run_until_complete(b.start_bot(run_bot))
        except Exception as e:
            print(f"[{self.username}] Thread Exception: {e}")
        finally:
            unified_redirector_out.unregister_thread(thread_id)
            unified_redirector_err.unregister_thread(thread_id)

class EclipseBotThread(threading.Thread):
    def __init__(self, slot_id, username, password, char_class, bot_class, bot_kwargs, config, callback):
        super().__init__()
        self.slot_id = slot_id
        self.username = username
        self.password = password
        self.char_class = char_class
        self.bot_class = bot_class
        self.bot_kwargs = bot_kwargs
        self.config = config
        self.callback = callback
        self.bot_instance = None
        self.daemon = True

    def run(self):
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        
        thread_id = threading.get_ident()
        unified_redirector_out.register_thread(thread_id, self.username, self.callback)
        unified_redirector_err.register_thread(thread_id, self.username, self.callback)

        b = Bot(
            roomNumber=99999,
            itemsDropWhiteList=[
                "Sliver of Sunlight",
                "Sliver of Moonlight",
                "Ecliptic Offering",
            ],
            showLog=True,
            showDebug=False,
            showChat=True,
            isScriptable=True,
            followPlayer=self.config.get("master_username", "").lower(),
            slavesPlayer=self.config.get("slaves_usernames", []),
            farmClass=self.char_class,
            respawnCellPad=["Enter", "Spawn"],
            muteSpamWarning=True
        )
        b.set_login_info(self.username, self.password, self.config.get("server", "Alteon"))
        self.bot_instance = b

        async def run_bot(cmd):
            bot_inst = self.bot_class(cmd, **self.bot_kwargs)
            await bot_inst.prepare_items()    
            if isinstance(bot_inst, EclipseMasterBot):
                await bot_inst.setup_party()
            else:
                await bot_inst.wait_party_invite()
            await bot_inst.attack_loop()
        
        try:
            loop.run_until_complete(b.start_bot(run_bot))
        except Exception as e:
            print(f"[{self.username}] Thread Exception: {e}")
        finally:
            unified_redirector_out.unregister_thread(thread_id)
            unified_redirector_err.unregister_thread(thread_id)

# --- Sub-GUI API Implementations (Standalone-Compatible) ---
class AqwSoloApi:
    def __init__(self):
        self.bot_instance = None
        self.bot_thread = None
        self.window = None
        self.config_path = os.path.join(get_project_root(), "gui_config.json")

    def set_window(self, window):
        self.window = window

    def handle_log(self, message):
        html_msg = ansi_to_html(message)
        if self.window:
            self.window.evaluate_js(f"if(window.addLog) window.addLog({json.dumps(html_msg)});")

    def load_config(self):
        default_config = {
            "username": "",
            "password": "",
            "server": "Artix",
            "room_number": "1",
            "bot_path": "",
            "farm_class": "",
            "solo_class": "",
            "whitelist": [
                "Gem of Nulgath",
                "Diamond of Nulgath",
                "Voucher of Nulgath (non-mem)",
                "Tainted Gem",
                "Dark Crystal Shard"
            ],
            "auto_relogin": True,
            "show_chat": True,
            "mute_spam": True,
            "anti_mod": True
        }
        if os.path.exists(self.config_path):
            try:
                with open(self.config_path, "r") as f:
                    user_config = json.load(f)
                    default_config.update(user_config)
            except Exception as e:
                print(f"Failed to load config: {e}")
        return default_config

    def save_config(self, config):
        try:
            temp_path = self.config_path + ".tmp"
            with open(temp_path, "w") as f:
                json.dump(config, f, indent=4)
            os.replace(temp_path, self.config_path)
            return {"success": True}
        except Exception as e:
            print(f"Failed to save config: {e}")
            return {"success": False, "error": str(e)}

    def _resolve_module_path(self, file_path):
        root_dir = get_project_root()
        abs_file_path = os.path.abspath(file_path)
        abs_root_dir = os.path.abspath(root_dir)
        
        if abs_file_path.startswith(abs_root_dir):
            rel_path = os.path.relpath(abs_file_path, abs_root_dir)
            module_name = os.path.splitext(rel_path)[0]
            module_path = module_name.replace(os.path.sep, ".")
            return {
                "display_name": os.path.basename(abs_file_path),
                "path": module_path,
                "abs_path": abs_file_path,
                "external": False,
                "parent_dir": ""
            }
        else:
            parent_dir = os.path.dirname(abs_file_path)
            file_name = os.path.basename(abs_file_path)
            module_name = os.path.splitext(file_name)[0]
            return {
                "display_name": file_name,
                "path": module_name,
                "abs_path": abs_file_path,
                "external": True,
                "parent_dir": parent_dir
            }

    def select_script(self):
        if not self.window:
            return None
        file_types = ('Python files (*.py)', 'All files (*.*)')
        result = self.window.create_file_dialog(
            dialog_type=webview.OPEN_DIALOG,
            file_types=file_types
        )
        if result and len(result) > 0:
            return self._resolve_module_path(result[0])
        return None

    def start_bot(self, config):
        if self.bot_thread and self.bot_thread.is_alive():
            return {"success": False, "error": "Bot is already running."}

        self.save_config(config)

        whitelist = config.get("whitelist", [])
        if isinstance(whitelist, str):
            whitelist = [item.strip() for item in whitelist.split(",") if item.strip()]

        if config.get("bot_external") and config.get("bot_parent_dir"):
            ext_path = config.get("bot_parent_dir")
            if ext_path not in sys.path:
                sys.path.insert(0, ext_path)

        try:
            self.bot_instance = Bot(
                roomNumber=int(config.get("room_number", 1)),
                itemsDropWhiteList=whitelist,
                showLog=True,
                showDebug=False,
                showChat=config.get("show_chat", True),
                isScriptable=True,
                followPlayer="",
                slavesPlayer=[],
                farmClass=config.get("farm_class") or None,
                soloClass=config.get("solo_class") or None,
                autoRelogin=config.get("auto_relogin", True),
                muteSpamWarning=config.get("mute_spam", True),
                antiMod=config.get("anti_mod", True)
            )
            self.bot_instance.set_login_info(
                config.get("username"),
                config.get("password"),
                config.get("server", "Artix")
            )

            self.bot_thread = BotThread(self.bot_instance, config.get("bot_path"))
            self.bot_thread.start()
            return {"success": True}
        except Exception as e:
            return {"success": False, "error": str(e)}

    def stop_bot(self):
        if not self.bot_thread or not self.bot_thread.is_alive():
            return {"success": False, "error": "Bot is not running."}
        
        try:
            print("Stopping AQW Bot client...")
            if self.bot_instance:
                self.bot_instance.stop_bot(user_triggered=True)
            return {"success": True}
        except Exception as e:
            return {"success": False, "error": str(e)}

    def get_status(self):
        running = self.bot_thread is not None and self.bot_thread.is_alive()
        if running and self.bot_instance:
            b = self.bot_instance
            p = b.player
            
            # Form skill cooldowns
            cooldowns = {}
            from datetime import datetime
            now = datetime.now()
            if p and hasattr(p, "SKILLS"):
                for i in range(0, 6):
                    if i < len(p.SKILLS):
                        skill_data = p.SKILLS[i]
                        next_use = skill_data.get("nextUse")
                        if next_use and next_use > now:
                            cooldowns[i] = round((next_use - now).total_seconds(), 1)
                        else:
                            cooldowns[i] = 0.0
                    else:
                        cooldowns[i] = 0.0
            else:
                cooldowns = {0: 0.0, 1: 0.0, 2: 0.0, 3: 0.0, 4: 0.0, 5: 0.0}

            try:
                return {
                    "running": running,
                    "is_connected": b.is_client_connected,
                    "username": p.USERNAME if p else "-",
                    "hp": p.CURRENT_HP if p else 0,
                    "max_hp": p.MAX_HP if p else 0,
                    "mp": p.MANA if p else 0,
                    "max_mp": p.MAX_MP if p else 0,
                    "is_dead": p.ISDEAD if p else False,
                    "map": b.strMapName or "-",
                    "cell": p.CELL if p else "-",
                    "pad": p.PAD if p else "-",
                    "cooldowns": cooldowns
                }
            except Exception as e:
                return {
                    "running": running,
                    "is_connected": False,
                    "error": str(e)
                }
        else:
            return {
                "running": running,
                "is_connected": False
            }

class SlaveryApi:
    def __init__(self):
        self.window = None
        if getattr(sys, 'frozen', False):
            config_dir = os.path.expanduser("~/.aqw_bot")
            os.makedirs(config_dir, exist_ok=True)
            self.config_path = os.path.join(config_dir, "slavery_config.json")
        else:
            self.config_path = os.path.join(get_project_root(), "slavery_config.json")
        self.active_threads = {}
        self.taunt_coordinator = TauntCoordinator()

    def set_window(self, window):
        self.window = window

    def handle_slave_log(self, username, message):
        html_msg = ansi_to_html(message)
        if self.window:
            try:
                self.window.evaluate_js(
                    f"if(window.addSlaveLog) window.addSlaveLog({json.dumps(username)}, {json.dumps(html_msg)});"
                )
            except Exception:
                pass

    def load_config(self):
        default_config = {
            "server": "Artix",
            "room_number": 9099,
            "follow_player": "",
            "copy_walk": True,
            "auto_zone": "none",
            "targets_priority": "Defense Drone,Staff of Inversion",
            "whitelist": [
                "Treasure Chest",
                "Void Aura"
            ],
            "locked_zones": [
                "ultraezrajal",
                "ultrawarden",
                "ultraengineer",
                "doomvault",
                "doomvaultb",
                "championdrakath",
                "tercessuinotlim",
                "icestormunder"
            ],
            "slaves": [],
            "theme": "default",
            "settings_hidden": False
        }
        if os.path.exists(self.config_path):
            try:
                with open(self.config_path, "r") as f:
                    user_config = json.load(f)
                    default_config.update(user_config)
            except Exception as e:
                print(f"Failed to load slavery config: {e}")
        return default_config

    def save_config(self, config):
        try:
            temp_path = self.config_path + ".tmp"
            with open(temp_path, "w") as f:
                json.dump(config, f, indent=4)
            os.replace(temp_path, self.config_path)

            for username, thread in self.active_threads.items():
                if thread.bot_instance:
                    thread.bot_instance.default_room_number = int(config.get("room_number", 9099))
                    thread.bot_instance.follow_player = config.get("follow_player", "")
                    thread.bot_instance.targets_priority = config.get("targets_priority", "")
                    thread.bot_instance.copy_walk = config.get("copy_walk", True)
                    thread.bot_instance.auto_zone = config.get("auto_zone", "none")
                    thread.bot_instance.locked_zones = config.get("locked_zones", [])
                    thread.bot_instance.itemsDropWhiteList = config.get("whitelist", [])

                    slave_config = next((s for s in config.get("slaves", []) if s.get("username") == username), None)
                    if slave_config:
                        thread.bot_instance.taunter = slave_config.get("taunter", False)
            return {"success": True}
        except Exception as e:
            print(f"Failed to save config: {e}")
            return {"success": False, "error": str(e)}

    def start_slaves(self, config, usernames):
        self.stop_slaves()
        self.save_config(config)
        
        slaves_list = config.get("slaves", [])
        selected_slaves = [s for s in slaves_list if s.get("username") in usernames]
        
        if not selected_slaves:
            return {"success": False, "error": "No selected slaves found."}

        try:
            for slave in selected_slaves:
                username = slave.get("username")
                password = slave.get("password")
                char_class = slave.get("char_class")
                skills = slave.get("skills", "1,2,3,4")
                hp_operator = slave.get("hp_operator", "<")
                hp_threshold = slave.get("hp_threshold", 0)
                hp_skills = slave.get("hp_skills", "")
                mp_operator = slave.get("mp_operator", "<")
                mp_threshold = slave.get("mp_threshold", 0)
                mp_skills = slave.get("mp_skills", "")
                taunter = slave.get("taunter", False)
                
                thread = SlaveBotThread(
                    username=username,
                    password=password,
                    char_class=char_class,
                    config=config,
                    callback=self.handle_slave_log,
                    skills=skills,
                    hp_operator=hp_operator,
                    hp_threshold=hp_threshold,
                    hp_skills=hp_skills,
                    mp_operator=mp_operator,
                    mp_threshold=mp_threshold,
                    mp_skills=mp_skills,
                    taunter=taunter,
                    taunt_coordinator=self.taunt_coordinator
                )
                self.active_threads[username] = thread
                thread.start()
            return {"success": True}
        except Exception as e:
            return {"success": False, "error": str(e)}

    def stop_slaves(self):
        if not self.active_threads:
            return {"success": True}
        
        print("Stopping all slave bot instances...")
        for username, thread in self.active_threads.items():
            if thread.bot_instance:
                try:
                    thread.bot_instance.stop_bot(user_triggered=True)
                except Exception:
                    pass
        for username, thread in list(self.active_threads.items()):
            thread.join(timeout=1.0)
        self.active_threads.clear()
        return {"success": True}

    def toggle_pause_slaves(self, pause_state):
        for username, thread in self.active_threads.items():
            if thread.bot_instance:
                thread.bot_instance.is_script_paused = bool(pause_state)
        return {"success": True}

    def update_slave_taunter(self, username, taunter_state):
        thread = self.active_threads.get(username)
        if thread and thread.bot_instance:
            thread.bot_instance.taunter = bool(taunter_state)
            if bool(taunter_state):
                self.taunt_coordinator.register_taunter(username)
            else:
                self.taunt_coordinator.unregister_taunter(username)
            return {"success": True}
        return {"success": False, "error": "Slave not running."}

    def get_status(self):
        from datetime import datetime
        statuses = {}
        for username, thread in list(self.active_threads.items()):
            running = thread.is_alive()
            if running and thread.bot_instance:
                bot = thread.bot_instance
                player = bot.player
                
                cooldowns = {}
                now = datetime.now()
                if player and hasattr(player, "SKILLS"):
                    for i in range(0, 6):
                        if i < len(player.SKILLS):
                            skill_data = player.SKILLS[i]
                            next_use = skill_data.get("nextUse")
                            if next_use and next_use > now:
                                cooldowns[i] = round((next_use - now).total_seconds(), 1)
                            else:
                                cooldowns[i] = 0.0
                        else:
                            cooldowns[i] = 0.0
                else:
                    cooldowns = {0: 0.0, 1: 0.0, 2: 0.0, 3: 0.0, 4: 0.0, 5: 0.0}

                try:
                    statuses[username] = {
                        "running": running,
                        "is_connected": bot.is_client_connected,
                        "hp": player.CURRENT_HP if player else 0,
                        "max_hp": player.MAX_HP if player else 0,
                        "mp": player.MANA if player else 0,
                        "max_mp": player.MAX_MP if player else 0,
                        "is_dead": player.ISDEAD if player else False,
                        "map": bot.strMapName or "-",
                        "cell": player.CELL if player else "-",
                        "pad": player.PAD if player else "-",
                        "is_paused": bot.is_script_paused,
                        "cooldowns": cooldowns
                    }
                except Exception as e:
                    statuses[username] = {
                        "running": running,
                        "is_connected": False,
                        "error": str(e)
                    }
            else:
                statuses[username] = {
                    "running": running,
                    "is_connected": False
                }
        return statuses

    def get_version(self):
        return "v1.1.0"

class TempleApi:
    def __init__(self):
        self.window = None
        if getattr(sys, 'frozen', False):
            config_dir = os.path.expanduser("~/.aqw_bot")
            os.makedirs(config_dir, exist_ok=True)
            self.config_path = os.path.join(config_dir, "temple_config.json")
        else:
            self.config_path = os.path.join(get_project_root(), "temple_config.json")
        self.active_threads = {}
        self.start_time = None
        self.taunt_coordinator = TauntCoordinator()
        
        try:
            import psutil
            self.process = psutil.Process(os.getpid())
            self.process.cpu_percent(interval=None)
        except Exception:
            self.process = None

    def set_window(self, window):
        self.window = window

    def handle_slave_log(self, username, message):
        html_msg = ansi_to_html(message)
        if self.window:
            try:
                self.window.evaluate_js(
                    f"if(window.addSlaveLog) window.addSlaveLog({json.dumps(username)}, {json.dumps(html_msg)});"
                )
            except Exception:
                pass

    def load_config(self):
        default_config = {
            "server": "Alteon",
            "room_number": 9099,
            "temple_bot_type": "MidnightSunBot",
            "theme": "default",
            "slots": {
                "slot1": {
                    "username": "",
                    "password": "",
                    "char_class": "ArchPaladin",
                    "role": "master",
                    "is_taunter": True
                },
                "slot2": {
                    "username": "",
                    "password": "",
                    "char_class": "StoneCrusher",
                    "role": "slave",
                    "is_taunter": False
                },
                "slot3": {
                    "username": "",
                    "password": "",
                    "char_class": "Legion Revenant",
                    "role": "slave",
                    "is_taunter": False
                },
                "slot4": {
                    "username": "",
                    "password": "",
                    "char_class": "Lord of Order",
                    "role": "slave",
                    "is_taunter": False
                }
            },
            "auto_restart_enabled": True,
            "auto_restart_delay": 30,
            "auto_restart_max_attempts": 3
        }
        if os.path.exists(self.config_path):
            try:
                with open(self.config_path, "r") as f:
                    user_config = json.load(f)
                    if "slots" in user_config:
                        for s_k, s_v in user_config["slots"].items():
                            if s_k in default_config["slots"]:
                                default_config["slots"][s_k].update(s_v)
                        del user_config["slots"]
                    default_config.update(user_config)
            except Exception as e:
                print(f"Failed to load config: {e}")
        return default_config

    def save_config(self, config):
        try:
            temp_path = self.config_path + ".tmp"
            with open(temp_path, "w") as f:
                json.dump(config, f, indent=4)
            os.replace(temp_path, self.config_path)
            return {"success": True}
        except Exception as e:
            print(f"Failed to save config: {e}")
            return {"success": False, "error": str(e)}

    def reset_config(self):
        if os.path.exists(self.config_path):
            try:
                os.remove(self.config_path)
            except Exception:
                pass
        return self.load_config()

    def start_party(self, config):
        if self.active_threads:
            return {"success": False, "error": "Party is already running!"}
            
        self.taunt_coordinator = TauntCoordinator()
        self.start_time = time.time()
        server = config.get("server", "Alteon")
        room_number = int(config.get("room_number", 9099))
        temple_bot_type = config.get("temple_bot_type", "MidnightSunBot")
        slots = config.get("slots", {})
        
        for s_id in ["slot1", "slot2", "slot3", "slot4"]:
            slot = slots.get(s_id, {})
            if not slot.get("username") or not slot.get("password") or not slot.get("char_class"):
                return {"success": False, "error": f"Please fill credentials for all 4 slots."}

        master_username = slots["slot1"]["username"]
        slaves_usernames = [slots[s]["username"] for s in ["slot2", "slot3", "slot4"]]

        execution_config = {
            "server": server,
            "room_number": room_number,
            "master_username": master_username,
            "slaves_usernames": slaves_usernames
        }

        bot_class = MidnightSunBot if temple_bot_type == "MidnightSunBot" else SolsticeMoonBot

        for s_id in ["slot1", "slot2", "slot3", "slot4"]:
            s = slots[s_id]
            role = "master" if s_id == "slot1" else "slave"
            is_taunter = bool(s.get("is_taunter", False))
            
            t = TempleBotThread(
                s_id, 
                s["username"], 
                s["password"], 
                s["char_class"], 
                bot_class, 
                role, 
                is_taunter, 
                execution_config, 
                self.handle_slave_log,
                taunt_coordinator=self.taunt_coordinator
            )
            self.active_threads[s_id] = t
            t.start()
            
        return {"success": True}

    def stop_party(self):
        if not self.active_threads:
            return {"success": True}
            
        self.start_time = None
        for s_id, thread in self.active_threads.items():
            if thread.bot_instance:
                try:
                    thread.bot_instance.stop_bot()
                except Exception:
                    pass
        self.active_threads = {}
        return {"success": True}

    def get_status(self):
        from datetime import datetime
        status_data = {}
        for s_id, thread in self.active_threads.items():
            if thread.bot_instance:
                b = thread.bot_instance
                p = b.player
                
                cooldowns = {}
                now = datetime.now()
                if p and hasattr(p, "SKILLS"):
                    for i in range(0, 6):
                        if i < len(p.SKILLS):
                            skill_data = p.SKILLS[i]
                            next_use = skill_data.get("nextUse")
                            if next_use and next_use > now:
                                cooldowns[i] = round((next_use - now).total_seconds(), 1)
                            else:
                                cooldowns[i] = 0.0
                        else:
                            cooldowns[i] = 0.0
                else:
                    cooldowns = {0: 0.0, 1: 0.0, 2: 0.0, 3: 0.0, 4: 0.0, 5: 0.0}

                scroll_qty = 0
                if p:
                    item_enrage = p.get_item_inventory("Scroll of Enrage")
                    if item_enrage:
                        scroll_qty = item_enrage.qty

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
                    "scroll_enrage_qty": scroll_qty,
                    "taunt_error": getattr(b, "taunt_error", False)
                }
            else:
                status_data[s_id] = {"running": False}
                
        for s_id in ["slot1", "slot2", "slot3", "slot4"]:
            if s_id not in status_data:
                status_data[s_id] = {"running": False}
        
        mem_mb = 0.0
        cpu_pct = 0.0
        if hasattr(self, "process") and self.process:
            try:
                mem_mb = round(self.process.memory_info().rss / (1024 * 1024), 1)
                cpu_pct = round(self.process.cpu_percent(interval=None), 1)
            except Exception:
                pass

        status_data["_active_taunter"] = self.taunt_coordinator.active_taunter if hasattr(self, "taunt_coordinator") else None
        status_data["_time_running"] = int(time.time() - self.start_time) if getattr(self, "start_time", None) else 0
        status_data["system_stats"] = {
            "cpu": cpu_pct,
            "memory": mem_mb
        }
        return status_data

class EclipseApi:
    def __init__(self):
        self.window = None
        if getattr(sys, 'frozen', False):
            config_dir = os.path.expanduser("~/.aqw_bot")
            os.makedirs(config_dir, exist_ok=True)
            self.config_path = os.path.join(config_dir, "eclipse_config.json")
        else:
            self.config_path = os.path.join(get_project_root(), "eclipse_config.json")
            
        self.active_threads = {}
        self.start_time = None
        
        try:
            import psutil
            self.process = psutil.Process(os.getpid())
            self.process.cpu_percent(interval=None)
        except Exception:
            self.process = None

    def set_window(self, window):
        self.window = window

    def validate_password(self, password):
        target_hash = "080dcf0b2c402cb9ac5be3dc6907f79a3a2b113325755ecdd792bdc6b8c7399e"
        input_hash = hashlib.sha256(password.encode('utf-8')).hexdigest()
        return {"valid": input_hash == target_hash}

    def handle_slave_log(self, username, message):
        html_msg = ansi_to_html(message)
        if self.window:
            try:
                self.window.evaluate_js(
                    f"if(window.addSlaveLog) window.addSlaveLog({json.dumps(username)}, {json.dumps(html_msg)});"
                )
                if "Finished in" in message or "Dungeon cleared" in message or "Total time running" in message:
                    sys_msg = f"[{username}] {message}"
                    html_sys_msg = ansi_to_html(sys_msg)
                    self.window.evaluate_js(
                        f"if(window.addSlaveLog) window.addSlaveLog('System', {json.dumps(html_sys_msg)});"
                    )
            except Exception:
                pass

    def load_config(self):
        default_config = {
            "server": "Alteon",
            "room_number": 9099,
            "theme": "default",
            "slots": {
                "slot1": {
                    "username": "",
                    "password": "",
                    "char_class": "Legion Revenant",
                    "taunt_parity": "odd",
                    "converge_type": "sun",
                    "light_gather_taunter": False
                },
                "slot2": {
                    "username": "",
                    "password": "",
                    "char_class": "StoneCrusher",
                    "taunt_parity": "even",
                    "converge_type": "sun",
                    "light_gather_taunter": False
                },
                "slot3": {
                    "username": "",
                    "password": "",
                    "char_class": "ArchPaladin",
                    "taunt_parity": "odd",
                    "converge_type": "moon",
                    "light_gather_taunter": True,
                    "moon_haze_taunter": True
                },
                "slot4": {
                    "username": "",
                    "password": "",
                    "char_class": "Lord of Order",
                    "taunt_parity": "even",
                    "converge_type": "moon",
                    "light_gather_taunter": True,
                    "sunset_knight_taunter": True
                }
            },
            "auto_restart_enabled": True,
            "auto_restart_delay": 30,
            "auto_restart_max_attempts": 3
        }
        if os.path.exists(self.config_path):
            try:
                with open(self.config_path, "r") as f:
                    user_config = json.load(f)
                    if "slots" in user_config:
                        for s_k, s_v in user_config["slots"].items():
                            if s_k in default_config["slots"]:
                                default_config["slots"][s_k].update(s_v)
                        del user_config["slots"]
                    default_config.update(user_config)
            except Exception as e:
                print(f"Failed to load config: {e}")
        return default_config

    def save_config(self, config):
        try:
            temp_path = self.config_path + ".tmp"
            with open(temp_path, "w") as f:
                json.dump(config, f, indent=4)
            os.replace(temp_path, self.config_path)
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

    def start_party(self, config):
        if self.active_threads:
            return {"success": False, "error": "Party is already running!"}
            
        self.start_time = time.time()
        server = config.get("server", "Alteon")
        room_number = 99999
        slots = config.get("slots", {})
        
        for s_id in ["slot1", "slot2", "slot3", "slot4"]:
            slot = slots.get(s_id, {})
            if not slot.get("username") or not slot.get("password") or not slot.get("char_class"):
                return {"success": False, "error": f"Please fill credentials for all 4 slots."}

        master_username = slots["slot1"]["username"]
        slaves_usernames = [slots[s]["username"] for s in ["slot2", "slot3", "slot4"]]

        execution_config = {
            "server": server,
            "room_number": room_number,
            "master_username": master_username,
            "slaves_usernames": slaves_usernames
        }

        # Launch Slot 1 (Master / Sun / odd)
        s1 = slots["slot1"]
        s1_kwargs = {
            "default_target": "Ascended Solstice,Blessless Deer",
            "taunt_parity": "odd",
            "converge_type": "sun",
            "light_gather_taunter": bool(s1.get("light_gather_taunter", False))
        }
        t1 = EclipseBotThread("slot1", s1["username"], s1["password"], s1["char_class"], EclipseMasterBot, s1_kwargs, execution_config, self.handle_slave_log)
        self.active_threads["slot1"] = t1
        t1.start()

        # Launch Slot 2 (Slave 1 / Sun / even)
        s2 = slots["slot2"]
        s2_kwargs = {
            "default_target": "Ascended Solstice",
            "taunt_parity": "even",
            "converge_type": "sun",
            "light_gather_taunter": bool(s2.get("light_gather_taunter", False)),
            "debug_mon": True
        }
        t2 = EclipseBotThread("slot2", s2["username"], s2["password"], s2["char_class"], EclipseSlaveBot, s2_kwargs, execution_config, self.handle_slave_log)
        self.active_threads["slot2"] = t2
        t2.start()

        # Launch Slot 3 (Slave 2 / Moon / odd)
        s3 = slots["slot3"]
        s3_kwargs = {
            "default_target": "Ascended Midnight",
            "taunt_parity": "odd",
            "converge_type": "moon",
            "light_gather_taunter": bool(s3.get("light_gather_taunter", True)),
            "moon_haze_taunter": bool(s3.get("moon_haze_taunter", True))
        }
        t3 = EclipseBotThread("slot3", s3["username"], s3["password"], s3["char_class"], EclipseSlaveBot, s3_kwargs, execution_config, self.handle_slave_log)
        self.active_threads["slot3"] = t3
        t3.start()

        # Launch Slot 4 (Slave 3 / Moon / even)
        s4 = slots["slot4"]
        s4_kwargs = {
            "default_target": "Ascended Midnight",
            "taunt_parity": "even",
            "converge_type": "moon",
            "light_gather_taunter": bool(s4.get("light_gather_taunter", True)),
            "sunset_knight_taunter": bool(s4.get("sunset_knight_taunter", True))
        }
        t4 = EclipseBotThread("slot4", s4["username"], s4["password"], s4["char_class"], EclipseSlaveBot, s4_kwargs, execution_config, self.handle_slave_log)
        self.active_threads["slot4"] = t4
        t4.start()

        return {"success": True}

    def stop_party(self):
        if not self.active_threads:
            return {"success": True}
        
        self.start_time = None
        for slot_id, thread in self.active_threads.items():
            if thread.bot_instance:
                try:
                    thread.bot_instance.stop_bot()
                except Exception:
                    pass
                    
        for slot_id, thread in list(self.active_threads.items()):
            thread.join(timeout=1.0)
            
        self.active_threads.clear()
        return {"success": True}

    def get_status(self):
        from datetime import datetime
        statuses = {}
        for slot_id, thread in list(self.active_threads.items()):
            running = thread.is_alive()
            if running and thread.bot_instance:
                bot = thread.bot_instance
                player = bot.player
                
                cooldowns = {}
                now = datetime.now()
                if player and hasattr(player, "SKILLS"):
                    for i in range(0, 6):
                        if i < len(player.SKILLS):
                            skill_data = player.SKILLS[i]
                            next_use = skill_data.get("nextUse")
                            if next_use and next_use > now:
                                cooldowns[i] = round((next_use - now).total_seconds(), 1)
                            else:
                                cooldowns[i] = 0.0
                        else:
                            cooldowns[i] = 0.0
                else:
                    cooldowns = {0: 0.0, 1: 0.0, 2: 0.0, 3: 0.0, 4: 0.0, 5: 0.0}

                scroll_qty = 0
                if player:
                    item_enrage = player.get_item_inventory("Scroll of Enrage")
                    if item_enrage:
                        scroll_qty = item_enrage.qty

                try:
                    statuses[slot_id] = {
                        "running": running,
                        "hp": player.CURRENT_HP if player else 0,
                        "max_hp": player.MAX_HP if player else 0,
                        "mp": player.MANA if player else 0,
                        "max_mp": player.MAX_MP if player else 0,
                        "cell": player.CELL if player else "-",
                        "pad": player.PAD if player else "-",
                        "map": getattr(bot, "strMapName", "-"),
                        "is_connected": bot.is_client_connected,
                        "is_dead": player.ISDEAD if player else False,
                        "username": thread.username,
                        "cooldowns": cooldowns,
                        "scroll_enrage_qty": scroll_qty,
                        "taunt_error": getattr(bot, "taunt_error", False)
                    }
                except Exception as e:
                    statuses[slot_id] = {
                        "running": running,
                        "is_connected": False,
                        "error": str(e)
                    }
            else:
                statuses[slot_id] = {
                    "running": running,
                    "is_connected": False
                }
        
        for s_id in ["slot1", "slot2", "slot3", "slot4"]:
            if s_id not in statuses:
                statuses[s_id] = {"running": False}

        monsters_info = []
        for slot_id, thread in list(self.active_threads.items()):
            if thread.is_alive() and thread.bot_instance:
                bot = thread.bot_instance
                player = bot.player
                current_cell = player.CELL if player else None
                if current_cell and hasattr(bot, "monsters") and bot.monsters:
                    for mon in bot.monsters:
                        if mon.frame == current_cell and mon.current_hp > 0:
                            monsters_info.append({
                                "name": mon.mon_name,
                                "id": mon.mon_map_id,
                                "hp": mon.current_hp,
                                "max_hp": mon.max_hp
                            })
                    if monsters_info:
                        break

        mem_mb = 0.0
        cpu_pct = 0.0
        if hasattr(self, "process") and self.process:
            try:
                mem_mb = round(self.process.memory_info().rss / (1024 * 1024), 1)
                cpu_pct = round(self.process.cpu_percent(interval=None), 1)
            except Exception:
                pass

        time_running = int(time.time() - self.start_time) if getattr(self, "start_time", None) else 0

        return {
            "statuses": statuses,
            "monsters": monsters_info,
            "system_stats": {
                "cpu": cpu_pct,
                "memory": mem_mb
            },
            "_time_running": time_running
        }

# --- Combined API class ---
class CombinedApi:
    def __init__(self, aqw_api, slavery_api, temple_api, eclipse_api):
        self.aqw_api = aqw_api
        self.slavery_api = slavery_api
        self.temple_api = temple_api
        self.eclipse_api = eclipse_api
        self.window = None
        
        try:
            import psutil
            self.process = psutil.Process(os.getpid())
            self.process.cpu_percent(interval=None)
        except Exception:
            self.process = None

    def get_theme(self):
        config_path = os.path.expanduser("~/.aqw_bot/hub_config.json")
        if os.path.exists(config_path):
            try:
                with open(config_path, "r") as f:
                    cfg = json.load(f)
                    return cfg.get("theme", "default")
            except Exception:
                pass
        return "default"

    def save_theme(self, theme):
        config_dir = os.path.expanduser("~/.aqw_bot")
        os.makedirs(config_dir, exist_ok=True)
        config_path = os.path.join(config_dir, "hub_config.json")
        cfg = {}
        if os.path.exists(config_path):
            try:
                with open(config_path, "r") as f:
                    cfg = json.load(f)
            except Exception:
                pass
        cfg["theme"] = theme
        try:
            with open(config_path, "w") as f:
                json.dump(cfg, f, indent=4)
            return {"success": True}
        except Exception as e:
            return {"success": False, "error": str(e)}

    def set_window(self, window):
        self.window = window
        self.aqw_api.set_window(window)
        self.slavery_api.set_window(window)
        self.temple_api.set_window(window)
        self.eclipse_api.set_window(window)

    # --- NAMESPACED API FOR AQW BOT (IFRAME) ---
    def aqw_load_config(self):
        return self.aqw_api.load_config()

    def aqw_save_config(self, config):
        return self.aqw_api.save_config(config)

    def aqw_get_status(self):
        return self.aqw_api.get_status()

    def aqw_select_script(self):
        return self.aqw_api.select_script()

    def aqw_start_bot(self, config):
        res = self.aqw_api.start_bot(config)
        if res.get("success") and self.aqw_api.bot_thread:
            thread_id = self.aqw_api.bot_thread.ident
            if thread_id:
                unified_redirector_out.register_thread(thread_id, "AQW", lambda name, msg: self.aqw_api.handle_log(msg))
                unified_redirector_err.register_thread(thread_id, "AQW", lambda name, msg: self.aqw_api.handle_log(msg))
        return res

    def aqw_stop_bot(self):
        if self.aqw_api.bot_thread:
            thread_id = self.aqw_api.bot_thread.ident
            if thread_id:
                unified_redirector_out.unregister_thread(thread_id)
                unified_redirector_err.unregister_thread(thread_id)
        return self.aqw_api.stop_bot()

    # --- NAMESPACED API FOR SLAVERY BOT (IFRAME) ---
    def slavery_load_config(self):
        return self.slavery_api.load_config()

    def slavery_save_config(self, config):
        return self.slavery_api.save_config(config)

    def slavery_get_status(self):
        return self.slavery_api.get_status()

    def start_slaves(self, config, usernames):
        return self.slavery_api.start_slaves(config, usernames)

    def stop_slaves(self):
        return self.slavery_api.stop_slaves()

    def toggle_pause_slaves(self, pause_state):
        return self.slavery_api.toggle_pause_slaves(pause_state)

    def update_slave_taunter(self, username, taunter_state):
        return self.slavery_api.update_slave_taunter(username, taunter_state)

    def get_version(self):
        return self.slavery_api.get_version()

    # --- NAMESPACED API FOR TEMPLE BOT (IFRAME) ---
    def temple_load_config(self):
        return self.temple_api.load_config()

    def temple_save_config(self, config):
        return self.temple_api.save_config(config)

    def temple_get_status(self):
        return self.temple_api.get_status()

    def temple_reset_config(self):
        return self.temple_api.reset_config()

    def temple_start_party(self, config):
        return self.temple_api.start_party(config)

    def temple_stop_party(self):
        return self.temple_api.stop_party()

    # --- NAMESPACED API FOR ECLIPSE BOT (IFRAME) ---
    def eclipse_load_config(self):
        return self.eclipse_api.load_config()

    def eclipse_save_config(self, config):
        return self.eclipse_api.save_config(config)

    def eclipse_get_status(self):
        return self.eclipse_api.get_status()

    def eclipse_reset_config(self):
        return self.eclipse_api.reset_config()

    def eclipse_start_party(self, config):
        return self.eclipse_api.start_party(config)

    def eclipse_stop_party(self):
        return self.eclipse_api.stop_party()

    def validate_password(self, password):
        return self.eclipse_api.validate_password(password)

    def toggle_debug(self):
        if self.window:
            try:
                self.window.toggle_developer_tools()
                return {"success": True}
            except Exception as e:
                print(f"Error toggling developer tools: {e}")
                return {"success": False, "error": str(e)}

    # --- Dashboard Hub Status ---
    def get_hub_status(self):
        # 1. AQW Bot
        aqw_status = {"running": False}
        if self.aqw_api.bot_thread and self.aqw_api.bot_thread.is_alive():
            try:
                aqw_status = self.aqw_api.get_status()
            except Exception:
                aqw_status = {"running": True}
        
        # 2. Slavery Bot
        slavery_status = {"running": False}
        active_slaves = [username for username, thread in self.slavery_api.active_threads.items() if thread.is_alive()]
        if active_slaves:
            slavery_status = {
                "running": True,
                "count": len(active_slaves),
                "slaves": active_slaves
            }

        # 3. Temple Bot
        temple_status = {"running": False}
        active_temple = [s_id for s_id, thread in self.temple_api.active_threads.items() if thread.is_alive()]
        if active_temple:
            members = [thread.username for thread in self.temple_api.active_threads.values() if thread.is_alive()]
            elapsed = 0
            if getattr(self.temple_api, "start_time", None):
                elapsed = int(time.time() - self.temple_api.start_time)
            temple_status = {
                "running": True,
                "count": len(active_temple),
                "slots": active_temple,
                "members": members,
                "time_running": elapsed
            }
        else:
            self.temple_api.start_time = None

        # 4. Eclipse Bot
        eclipse_status = {"running": False}
        active_eclipse = [s_id for s_id, thread in self.eclipse_api.active_threads.items() if thread.is_alive()]
        if active_eclipse:
            members = [thread.username for thread in self.eclipse_api.active_threads.values() if thread.is_alive()]
            elapsed = 0
            if getattr(self.eclipse_api, "start_time", None):
                elapsed = int(time.time() - self.eclipse_api.start_time)
            eclipse_status = {
                "running": True,
                "count": len(active_eclipse),
                "slots": active_eclipse,
                "members": members,
                "time_running": elapsed
            }
        else:
            self.eclipse_api.start_time = None

        mem_mb = 0.0
        cpu_pct = 0.0
        if hasattr(self, "process") and self.process:
            try:
                mem_mb = round(self.process.memory_info().rss / (1024 * 1024), 1)
                cpu_pct = round(self.process.cpu_percent(interval=None), 1)
            except Exception:
                pass

        return {
            "aqw": aqw_status,
            "slavery": slavery_status,
            "temple": temple_status,
            "eclipse": eclipse_status,
            "system_stats": {
                "cpu": cpu_pct,
                "memory": mem_mb
            }
        }

# --- Bridge and Static Server Logic ---
def find_free_port():
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.bind(('127.0.0.1', 0))
    port = s.getsockname()[1]
    s.close()
    return port

def serve_injected_html(filepath, bot_type):
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            html_content = f.read()
            
        bridge_js = ""
        if bot_type == "aqw":
            bridge_js = """
            <script>
            (function() {
                if (window.parent && window.parent.pywebview) {
                    const topApi = window.parent.pywebview.api;
                    window.pywebview = {
                        api: {
                            load_config: () => topApi.aqw_load_config(),
                            save_config: (cfg) => topApi.aqw_save_config(cfg),
                            get_status: () => topApi.aqw_get_status(),
                            select_script: () => topApi.aqw_select_script(),
                            start_bot: (cfg) => topApi.aqw_start_bot(cfg),
                            stop_bot: () => topApi.aqw_stop_bot()
                        }
                    };
                }
            })();
            </script>
            """
        elif bot_type == "slavery":
            bridge_js = """
            <script>
            (function() {
                if (window.parent && window.parent.pywebview) {
                    const topApi = window.parent.pywebview.api;
                    window.pywebview = {
                        api: {
                            load_config: () => topApi.slavery_load_config(),
                            save_config: (cfg) => topApi.slavery_save_config(cfg),
                            get_status: () => topApi.slavery_get_status(),
                            start_slaves: (cfg, usernames) => topApi.start_slaves(cfg, usernames),
                            stop_slaves: () => topApi.stop_slaves(),
                            toggle_pause_slaves: (p) => topApi.toggle_pause_slaves(p),
                            update_slave_taunter: (u, t) => topApi.update_slave_taunter(u, t),
                            get_version: () => topApi.get_version()
                        }
                    };
                }
            })();
            </script>
            """
        elif bot_type == "temple":
            bridge_js = """
            <script>
            (function() {
                if (window.parent && window.parent.pywebview) {
                    const topApi = window.parent.pywebview.api;
                    window.pywebview = {
                        api: {
                            load_config: () => topApi.temple_load_config(),
                            save_config: (cfg) => topApi.temple_save_config(cfg),
                            get_status: () => topApi.temple_get_status(),
                            reset_config: () => topApi.temple_reset_config(),
                            start_party: (cfg) => topApi.temple_start_party(cfg),
                            stop_party: () => topApi.temple_stop_party()
                        }
                    };
                }
            })();
            </script>
            """
        elif bot_type == "eclipse":
            bridge_js = """
            <script>
            (function() {
                if (window.parent && window.parent.pywebview) {
                    const topApi = window.parent.pywebview.api;
                    window.pywebview = {
                        api: {
                            load_config: () => topApi.eclipse_load_config(),
                            save_config: (cfg) => topApi.eclipse_save_config(cfg),
                            get_status: () => topApi.eclipse_get_status(),
                            reset_config: () => topApi.eclipse_reset_config(),
                            start_party: (cfg) => topApi.eclipse_start_party(cfg),
                            stop_party: () => topApi.eclipse_stop_party(),
                            validate_password: (pwd) => topApi.validate_password(pwd)
                        }
                    };
                }
            })();
            </script>
            """
            
        if "<head>" in html_content:
            html_content = html_content.replace("<head>", f"<head>\n{bridge_js}")
        else:
            html_content = bridge_js + html_content
            
        return html_content
    except Exception as e:
        print(f"Failed to inject HTML for {filepath}: {e}")
        return static_file(os.path.basename(filepath), root=os.path.dirname(filepath))

def start_local_server(web_dashboard_dir, web_dir, web_slavery_dir, web_temple_dir, web_eclipse_dir):
    app = Bottle()

    # Dashboard routes
    @app.route('/')
    @app.route('/index.html')
    def serve_dashboard():
        return static_file('index.html', root=web_dashboard_dir)

    @app.route('/style.css')
    def serve_dashboard_css():
        return static_file('style.css', root=web_dashboard_dir)

    @app.route('/main.js')
    def serve_dashboard_js():
        return static_file('main.js', root=web_dashboard_dir)

    @app.route('/components.js')
    def serve_dashboard_components():
        return static_file('components.js', root=web_dashboard_dir)

    @app.route(r'/<filename:re:[^/]+\.(png|jpg|jpeg|gif|ico|svg)>')
    def serve_dashboard_images(filename):
        return static_file(filename, root=web_dashboard_dir)

    # AQW Bot routes
    @app.route('/aqw')
    @app.route('/aqw/')
    def serve_aqw_index():
        return serve_injected_html(os.path.join(web_dir, 'index.html'), 'aqw')

    @app.route('/aqw/<path:path>')
    def serve_aqw_files(path):
        return static_file(path, root=web_dir)

    # Slavery Bot routes
    @app.route('/slavery')
    @app.route('/slavery/')
    def serve_slavery_index():
        return serve_injected_html(os.path.join(web_slavery_dir, 'index.html'), 'slavery')

    @app.route('/slavery/<path:path>')
    def serve_slavery_files(path):
        return static_file(path, root=web_slavery_dir)

    # Temple Bot routes
    @app.route('/temple')
    @app.route('/temple/')
    def serve_temple_index():
        return serve_injected_html(os.path.join(web_temple_dir, 'index.html'), 'temple')

    @app.route('/temple/<path:path>')
    def serve_temple_files(path):
        return static_file(path, root=web_temple_dir)

    # Eclipse Bot routes
    @app.route('/eclipse')
    @app.route('/eclipse/')
    def serve_eclipse_index():
        return serve_injected_html(os.path.join(web_eclipse_dir, 'index.html'), 'eclipse')

    @app.route('/eclipse/<path:path>')
    def serve_eclipse_files(path):
        return static_file(path, root=web_eclipse_dir)

    port = find_free_port()
    t = threading.Thread(target=lambda: app.run(host='127.0.0.1', port=port, quiet=True))
    t.daemon = True
    t.start()
    return f"http://127.0.0.1:{port}"

# --- Launcher (Run) ---
def run_gui():
    aqw_api = AqwSoloApi()
    slavery_api = SlaveryApi()
    temple_api = TempleApi()
    eclipse_api = EclipseApi()

    combined_api = CombinedApi(aqw_api, slavery_api, temple_api, eclipse_api)
    
    unified_redirector_out.combined_api = combined_api
    unified_redirector_err.combined_api = combined_api

    if getattr(sys, 'frozen', False):
        base_path = getattr(sys, '_MEIPASS', '')
        web_dashboard_dir = os.path.join(base_path, 'web_dashboard')
    else:
        web_dashboard_dir = os.path.join(project_root, 'app', 'web_dashboard')

    web_dir = os.path.join(web_dashboard_dir, 'aqw')
    web_slavery_dir = os.path.join(web_dashboard_dir, 'slavery')
    web_temple_dir = os.path.join(web_dashboard_dir, 'temple')
    web_eclipse_dir = os.path.join(web_dashboard_dir, 'eclipse')

    print(f"Loading GUI assets from: {web_dashboard_dir}")
    url = start_local_server(web_dashboard_dir, web_dir, web_slavery_dir, web_temple_dir, web_eclipse_dir)
    print(f"Combined Bot Hub server running at: {url}")

    window = webview.create_window(
        title='AQW Multi-Bot Hub',
        url=url,
        js_api=combined_api,
        width=1280,
        height=880,
        min_size=(1020, 700),
        resizable=True
    )
    
    combined_api.set_window(window)
    
    # Configure webview settings to prevent auto-opening devtools on start but keep right-click inspect
    webview.settings['OPEN_DEVTOOLS_IN_DEBUG'] = False
    
    # Specify persistent storage path inside application config directory
    storage_path = os.path.expanduser("~/.aqw_bot/webview")
    os.makedirs(storage_path, exist_ok=True)
    
    webview.start(debug=True, private_mode=False, storage_path=storage_path)

# --- Icon Generator ---
def generate_icons():
    system = platform.system()
    png_path = os.path.join(project_root, "app", "web_dashboard", "aqw_icon.png")
    if not os.path.exists(png_path):
        return
        
    print("Generating application icons from aqw_icon.png...")
    if system == "Darwin":
        try:
            iconset_dir = "app.iconset"
            os.makedirs(iconset_dir, exist_ok=True)
            
            # macOS icon standard sizes
            sizes = [16, 32, 64, 128, 256, 512, 1024]
            for size in sizes:
                out_path1 = os.path.join(iconset_dir, f"icon_{size}x{size}.png")
                subprocess.run(["sips", "-z", str(size), str(size), png_path, "--out", out_path1], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
                if size * 2 in sizes:
                    out_path2 = os.path.join(iconset_dir, f"icon_{size}x{size}@2x.png")
                    subprocess.run(["sips", "-z", str(size*2), str(size*2), png_path, "--out", out_path2], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            
            subprocess.run(["iconutil", "-c", "icns", iconset_dir], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            shutil.rmtree(iconset_dir)
            print("Successfully generated app.icns on macOS.")
        except Exception as e:
            print(f"Failed to generate macOS app.icns: {e}")
            
    elif system == "Windows":
        try:
            from PIL import Image
            img = Image.open(png_path)
            img.save("app.ico", format="ICO", sizes=[(16, 16), (32, 32), (48, 48), (64, 64), (128, 128), (256, 256)])
            print("Successfully generated app.ico on Windows.")
        except Exception as e:
            print(f"Failed to generate Windows app.ico: {e}")

# --- Packager (Build) ---
def build_app():
    system = platform.system()
    app_name = "AQW_Bot_Hub"
    entrypoint = os.path.join("app", "build_hub_app.py")
    
    generate_icons()
    print(f"Building AQW Bot Hub for {system}...")
    
    # Define outputs to clean depending on the OS
    if system == "Windows":
        outputs_to_clean = [
            os.path.join("build", app_name),
            os.path.join("dist", app_name),
            os.path.join("dist", f"{app_name}.exe")
        ]
    else:  # macOS / Linux
        outputs_to_clean = [
            os.path.join("build", app_name),
            os.path.join("dist", f"{app_name}.app"),
            os.path.join("dist", app_name)
        ]
        
    for path in outputs_to_clean:
        if os.path.exists(path):
            try:
                if os.path.isdir(path):
                    shutil.rmtree(path)
                else:
                    os.remove(path)
                print(f"Cleaned existing {path}.")
            except Exception as e:
                print(f"Failed to clean {path}: {e}")
                
    data_folders = [
        ("app/web_dashboard", "web_dashboard"),
        ("bot", "bot")
    ]
    
    icon_file = "app.icns" if system == "Darwin" else "app.ico"
    separator = ";" if system == "Windows" else ":"
    
    pyinstaller_bin = "pyinstaller"
    venv_pyinstaller = os.path.join("venv", "bin", "pyinstaller")
    if system == "Windows":
        venv_pyinstaller = os.path.join("venv", "Scripts", "pyinstaller.exe")
    if os.path.exists(venv_pyinstaller):
        pyinstaller_bin = venv_pyinstaller

    cmd = [
        pyinstaller_bin,
        f"--name={app_name}",
        "--noconfirm",
        "--clean",
        "--windowed",
        "--hidden-import=psutil",
        f"--paths={project_root}"
    ]
    
    for src, dest in data_folders:
        cmd.append(f"--add-data={src}{separator}{dest}")
        
    if os.path.exists(icon_file):
        cmd.append(f"--icon={icon_file}")
    else:
        print(f"Warning: Icon file '{icon_file}' not found. Building without icon.")
        
    cmd.append(entrypoint)
    
    print("\nExecuting command:\n" + " ".join(cmd) + "\n")
    result = subprocess.run(cmd)
    
    if result.returncode == 0:
        print("\n" + "="*60)
        output_file_desc = os.path.join("dist", f"{app_name}.app" if system == "Darwin" else f"{app_name}.exe")
        print("SUCCESS! Standing app bundle built successfully.")
        print(f"You can find the standalone client at: {os.path.abspath(output_file_desc)}")
        print("="*60 + "\n")
    else:
        print("\nERROR! PyInstaller build failed.")
        sys.exit(result.returncode)

# --- Main Routing Entrypoint ---
def main():
    if len(sys.argv) > 1 and sys.argv[1] in ("build", "--build"):
        build_app()
    else:
        run_gui()

if __name__ == "__main__":
    main()
