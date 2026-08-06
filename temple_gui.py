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
from bot.templeshrine.temple.core.core_temple import MidnightSunBot, SolsticeMoonBot

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

class TempleBotThread(threading.Thread):
    def __init__(self, slot_id, username, password, char_class, bot_class, role, is_taunter, config, callback):
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
        self.bot_instance = None
        self.daemon = True

    def run(self):
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        
        thread_id = threading.get_ident()
        global_redirector_out.register_thread(thread_id, self.username, self.callback)
        global_redirector_err.register_thread(thread_id, self.username, self.callback)

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
        global_redirector_out.default_callback = lambda msg: self.handle_slave_log("System", msg)
        global_redirector_err.default_callback = lambda msg: self.handle_slave_log("System", msg)

    def set_window(self, window):
        self.window = window

    def handle_slave_log(self, username, message):
        html_msg = ansi_to_html(message)
        if self.window:
            try:
                self.window.evaluate_js(
                    f"if(window.addSlaveLog) window.addSlaveLog({json.dumps(username)}, {json.dumps(html_msg)});"
                )
                
                # Duplicate cleared logs to System logs tab
                if "Dungeon cleared" in message or "Total time taken" in message:
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
            "temple_bot_type": "MidnightSunBot",
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

    def start_party(self, config):
        if self.active_threads:
            return {"success": False, "error": "Party is already running!"}
            
        server = config.get("server", "Alteon")
        room_number = int(config.get("room_number", 9099))
        temple_bot_type = config.get("temple_bot_type", "MidnightSunBot")
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

        # Resolve Bot Class
        bot_class = MidnightSunBot if temple_bot_type == "MidnightSunBot" else SolsticeMoonBot

        # Launch all slots
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
                self.handle_slave_log
            )
            self.active_threads[s_id] = t
            t.start()
            
        return {"success": True}

    def stop_party(self):
        if not self.active_threads:
            return {"success": True}
            
        # Call stop on each bot instance if it has one
        for s_id, thread in self.active_threads.items():
            if thread.bot_instance:
                try:
                    thread.bot_instance.stop_bot()
                except Exception:
                    pass
        self.active_threads = {}
        return {"success": True}

    def get_status(self):
        status_data = {}
        for s_id, thread in self.active_threads.items():
            if thread.bot_instance:
                b = thread.bot_instance
                p = b.player
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
                    "is_dead": p.ISDEAD if p else False
                }
            else:
                status_data[s_id] = {"running": False}
                
        # Fill in inactive slots
        for s_id in ["slot1", "slot2", "slot3", "slot4"]:
            if s_id not in status_data:
                status_data[s_id] = {"running": False}
        return status_data

def main():
    api = TempleApi()
    
    # Locate web folder resources
    if getattr(sys, 'frozen', False):
        web_dir = os.path.join(getattr(sys, '_MEIPASS', ''), 'web_temple')
    else:
        web_dir = os.path.join(get_project_root(), "web_temple")
        
    url = start_local_server(web_dir)
    
    window = webview.create_window(
        'Maid Temple',
        url,
        js_api=api,
        width=1150,
        height=820,
        resizable=True
    )
    api.set_window(window)
    webview.start(debug=False)

if __name__ == '__main__':
    main()
