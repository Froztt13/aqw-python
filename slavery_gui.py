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
import asyncio
import threading
import socket
import re
import html
import importlib
import webview

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

# Setup global redirectors
global_redirector_out = ThreadAwareLogRedirector(sys.stdout, lambda x: None)
global_redirector_err = ThreadAwareLogRedirector(sys.stderr, lambda x: None)
sys.stdout = global_redirector_out
sys.stderr = global_redirector_err

class SlaveBotThread(threading.Thread):
    def __init__(self, username, password, char_class, config, callback):
        super().__init__()
        self.username = username
        self.password = password
        self.char_class = char_class
        self.config = config
        self.callback = callback
        self.bot_instance = None
        self.loop = None
        self.daemon = True

    def run(self):
        thread_id = threading.get_ident()
        global_redirector_out.register_thread(thread_id, self.username, self.callback)
        global_redirector_err.register_thread(thread_id, self.username, self.callback)
        
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
            
            bot_module = importlib.import_module("bot.slavery.bot_slave")
            
            print(f"[{self.username}] Bot client launching...")
            self.loop.run_until_complete(self.bot_instance.start_bot(bot_module.main))
        except Exception as e:
            print(f"[{self.username}] Thread Exception: {e}")
        finally:
            print(f"[{self.username}] Thread terminated.")
            global_redirector_out.unregister_thread(thread_id)
            global_redirector_err.unregister_thread(thread_id)
            self.loop.close()

def find_free_port():
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.bind(('127.0.0.1', 0))
    port = s.getsockname()[1]
    s.close()
    return port

def start_local_server(web_dir):
    from bottle import Bottle, static_file
    app = Bottle()

    @app.route('/')
    def serve_index():
        return static_file('index.html', root=web_dir)

    @app.route('/<path:path>')
    def serve_files(path):
        return static_file(path, root=web_dir)

    port = find_free_port()
    t = threading.Thread(target=lambda: app.run(host='127.0.0.1', port=port, quiet=True))
    t.daemon = True
    t.start()
    return f"http://127.0.0.1:{port}"

APP_VERSION = "v1.0.0"

class SlaveryApi:
    def __init__(self):
        self.window = None
        if getattr(sys, 'frozen', False):
            config_dir = os.path.expanduser("~/.aqw_bot")
            os.makedirs(config_dir, exist_ok=True)
            self.config_path = os.path.join(config_dir, "slavery_config.json")
        else:
            self.config_path = os.path.join(get_project_root(), "slavery_config.json")
        self.active_threads = {} # username -> SlaveBotThread
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
            except Exception:
                pass

    def load_config(self):
        default_config = {
            "server": "Artix",
            "room_number": 9099,
            "follow_player": "",
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
            "slaves": []
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
            with open(self.config_path, "w") as f:
                json.dump(config, f, indent=4)
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
                
                thread = SlaveBotThread(
                    username=username,
                    password=password,
                    char_class=char_class,
                    config=config,
                    callback=self.handle_slave_log
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
        # Close sockets to interrupt recv loops
        for username, thread in self.active_threads.items():
            if thread.bot_instance:
                try:
                    thread.bot_instance.stop_bot(user_triggered=True)
                except Exception as e:
                    print(f"Error stopping bot {username}: {e}")
        
        # Wait for threads to terminate
        for username, thread in list(self.active_threads.items()):
            thread.join(timeout=1.0)
            
        self.active_threads.clear()
        return {"success": True}

    def get_version(self):
        return APP_VERSION

    def get_status(self):
        statuses = {}
        for username, thread in list(self.active_threads.items()):
            running = thread.is_alive()
            if thread.bot_instance:
                bot = thread.bot_instance
                try:
                    player = bot.player
                    hp = player.CURRENT_HP if player else 0
                    max_hp = player.MAX_HP if player else 0
                    mp = player.MANA if player else 0
                    max_mp = player.MAX_MP if player else 0
                    cell = player.CELL if player else "-"
                    pad = player.PAD if player else "-"
                    map_name = getattr(bot, "strMapName", "-")
                    
                    statuses[username] = {
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
                        "gold": player.GOLD if player else 0,
                        "index": bot.index
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

def main():
    api = SlaveryApi()
    
    if getattr(sys, 'frozen', False):
        web_dir = os.path.join(getattr(sys, '_MEIPASS', ''), 'web_slavery')
    else:
        web_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'web_slavery')

    print(f"Loading GUI assets from: {web_dir}")
    url = start_local_server(web_dir)
    
    window = webview.create_window(
        f'AQW Maid Slavery {APP_VERSION}',
        url,
        js_api=api,
        width=1200,
        height=800,
        min_size=(900, 600)
    )
    def on_loaded():
        api.set_window(window)
        print("[System] GUI loaded and ready")

    window.events.loaded += on_loaded
    webview.start(debug=False)

if __name__ == '__main__':
    main()
