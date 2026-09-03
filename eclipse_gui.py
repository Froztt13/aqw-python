import os
import sys

# Patch certifi path inside frozen app bundles before other imports
if getattr(sys, 'frozen', False):
    try:
        import certifi
        import certifi.core
        def patched_where():
            meipass_cacert = os.path.join(getattr(sys, '_MEIPASS', ''), 'certifi', 'cacert.pem')
            if os.path.exists(meipass_cacert):
                return meipass_cacert
            resources_cacert = os.path.join(os.path.dirname(sys.executable), '..', 'Resources', 'certifi', 'cacert.pem')
            if os.path.exists(resources_cacert):
                return os.path.abspath(resources_cacert)
            # Try Frameworks folder if that's where certifi looks
            frameworks_cacert = os.path.join(os.path.dirname(sys.executable), '..', 'Frameworks', 'certifi', 'cacert.pem')
            if os.path.exists(frameworks_cacert):
                return os.path.abspath(frameworks_cacert)
            return meipass_cacert
        certifi.core.where = patched_where
        certifi.where = patched_where
        os.environ['SSL_CERT_FILE'] = patched_where()
        os.environ['REQUESTS_CA_BUNDLE'] = patched_where()
    except Exception as e:
        print(f"Warning: certifi patch failed: {e}")

import json
import re
import html
import threading
import asyncio
import webview
from bottle import Bottle, static_file, request

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
        return os.path.dirname(os.path.abspath(__file__))

project_root = get_project_root()
if project_root not in sys.path:
    sys.path.insert(0, project_root)

if getattr(sys, 'frozen', False):
    resources_dir = getattr(sys, '_MEIPASS', None)
    if resources_dir and resources_dir not in sys.path:
        sys.path.insert(0, resources_dir)

from core.bot import Bot
from bot.templeshrine.eclipse.core.config import SlaveConfig
from bot.templeshrine.eclipse.core.core_eclipse import EclipseMasterBot, EclipseSlaveBot

# ANSI color helper
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

class ThreadAwareLogRedirector:
    def __init__(self, original_stream, default_callback):
        self.original_stream = original_stream
        self.default_callback = default_callback
        self.thread_callbacks = {}

    def register_thread(self, thread_id, username, callback):
        self.thread_callbacks[thread_id] = (username, callback)

    def unregister_thread(self, thread_id):
        if thread_id in self.thread_callbacks:
            del self.thread_callbacks[thread_id]

    def write(self, message):
        self.original_stream.write(message)
        if message:
            current_thread_id = threading.get_ident()
            if current_thread_id in self.thread_callbacks:
                username, callback = self.thread_callbacks[current_thread_id]
                callback(username, message)
            else:
                self.default_callback(message)

    def flush(self):
        self.original_stream.flush()

global_redirector_out = ThreadAwareLogRedirector(sys.stdout, lambda x: None)
global_redirector_err = ThreadAwareLogRedirector(sys.stderr, lambda x: None)
sys.stdout = global_redirector_out
sys.stderr = global_redirector_err

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
        global_redirector_out.register_thread(thread_id, self.username, self.callback)
        global_redirector_err.register_thread(thread_id, self.username, self.callback)

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
            global_redirector_out.unregister_thread(thread_id)
            global_redirector_err.unregister_thread(thread_id)

app = Bottle()

@app.route('/')
def serve_index():
    return static_file('index.html', root=app.resources_dir)

@app.route('/<filename:path>')
def serve_static(filename):
    return static_file(filename, root=app.resources_dir)

def find_free_port():
    import socket
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.bind(('127.0.0.1', 0))
    port = s.getsockname()[1]
    s.close()
    return port

def start_local_server(web_dir):
    app.resources_dir = web_dir
    port = find_free_port()
    t = threading.Thread(target=lambda: app.run(host='127.0.0.1', port=port, quiet=True))
    t.daemon = True
    t.start()
    return f"http://127.0.0.1:{port}"

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
        global_redirector_out.default_callback = lambda msg: self.handle_slave_log("System", msg)
        global_redirector_err.default_callback = lambda msg: self.handle_slave_log("System", msg)
        
        import psutil
        try:
            self.process = psutil.Process(os.getpid())
            self.process.cpu_percent(interval=None)
        except Exception:
            self.process = None

    def set_window(self, window):
        self.window = window

    def validate_password(self, password):
        import hashlib
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
                
                # Duplicate raid performance statistics to the System logs tab
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
                    # Deep update config dict
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
            
        server = config.get("server", "Alteon")
        room_number = 99999
        slots = config.get("slots", {})
        
        # Verify credentials
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
        
        # Stop bot loops
        for slot_id, thread in self.active_threads.items():
            if thread.bot_instance:
                try:
                    thread.bot_instance.stop_bot()
                except Exception:
                    pass
                    
        # Force terminate connection threads
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
                    hp = player.CURRENT_HP if player else 0
                    max_hp = player.MAX_HP if player else 0
                    mp = player.MANA if player else 0
                    max_mp = player.MAX_MP if player else 0
                    cell = player.CELL if player else "-"
                    pad = player.PAD if player else "-"
                    map_name = getattr(bot, "strMapName", "-")
                    
                    statuses[slot_id] = {
                        "running": running,
                        "hp": hp,
                        "max_hp": max_hp,
                        "mp": mp,
                        "max_mp": max_mp,
                        "cell": cell,
                        "pad": pad,
                        "map": map_name,
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
        
        # Fill in inactive slots
        for s_id in ["slot1", "slot2", "slot3", "slot4"]:
            if s_id not in statuses:
                statuses[s_id] = {"running": False}

        # Collect monsters HP info from the first active bot that has monsters in the current cell
        monsters_info = []
        for slot_id, thread in list(self.active_threads.items()):
            if thread.is_alive() and thread.bot_instance:
                bot = thread.bot_instance
                player = bot.player
                current_cell = player.CELL if player else None
                if current_cell and hasattr(bot, "monsters") and bot.monsters:
                    for mon in bot.monsters:
                        # Only show monsters in the current cell frame and that are alive
                        if mon.frame == current_cell and mon.current_hp > 0:
                            monsters_info.append({
                                "name": mon.mon_name,
                                "id": mon.mon_map_id,
                                "hp": mon.current_hp,
                                "max_hp": mon.max_hp
                            })
                    if monsters_info:
                        break

        # Fetch CPU & memory stats for this app process using self.process
        mem_mb = 0.0
        cpu_pct = 0.0
        if hasattr(self, "process") and self.process:
            try:
                mem_mb = round(self.process.memory_info().rss / (1024 * 1024), 1)
                cpu_pct = round(self.process.cpu_percent(interval=None), 1)
            except Exception:
                pass

        return {
            "statuses": statuses,
            "monsters": monsters_info,
            "system_stats": {
                "cpu": cpu_pct,
                "memory": mem_mb
            }
        }

def main():
    api = EclipseApi()
    
    if getattr(sys, 'frozen', False):
        web_dir = os.path.join(getattr(sys, '_MEIPASS', ''), 'web_eclipse')
    else:
        web_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'app', 'web_eclipse')

    print(f"Loading GUI assets from: {web_dir}")
    url = start_local_server(web_dir)
    
    window = webview.create_window(
        'Maid Eclipse - AQW Temple Shrine Manager',
        url,
        js_api=api,
        width=1200,
        height=850,
        min_size=(950, 650)
    )
    def on_loaded():
        api.set_window(window)
        print("[System] GUI loaded and ready")

    window.events.loaded += on_loaded
    webview.start(debug=False)

if __name__ == '__main__':
    main()
