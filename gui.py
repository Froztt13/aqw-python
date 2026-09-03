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
import queue
import html
import re
import importlib
import socket
import webview

def get_project_root():
    if getattr(sys, 'frozen', False):
        # sys.executable is dist/AQW_Bot.app/Contents/MacOS/AQW_Bot
        contents_dir = os.path.dirname(os.path.dirname(sys.executable))
        app_dir = os.path.dirname(contents_dir)  # AQW_Bot.app
        parent_dir = os.path.dirname(app_dir)  # dist/
        grandparent_dir = os.path.dirname(parent_dir)  # project root (aqw-python)
        
        # Check where 'bot' folder exists to find the true root
        for path in [grandparent_dir, parent_dir, os.getcwd()]:
            if os.path.exists(os.path.join(path, "bot")):
                return os.path.abspath(path)
        return os.path.abspath(grandparent_dir)
    else:
        return os.path.dirname(os.path.abspath(__file__))

# Add the project root to Python search path so dynamic imports can find bot modules
project_root = get_project_root()
if project_root not in sys.path:
    sys.path.insert(0, project_root)

from core.bot import Bot

# Helper to strip/convert ANSI codes from colorama to HTML classes
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
    # Strip any remaining raw ANSI codes
    text = ansi_escape.sub('', text)
    return text

class LogRedirector:
    def __init__(self, original_stream, callback):
        self.original_stream = original_stream
        self.callback = callback

    def write(self, message):
        self.original_stream.write(message)
        if message:
            self.callback(message)

    def flush(self):
        self.original_stream.flush()

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
    
    # Start Bottle server in a background daemon thread
    t = threading.Thread(target=lambda: app.run(host='127.0.0.1', port=port, quiet=True))
    t.daemon = True
    t.start()
    return f"http://127.0.0.1:{port}"

class Api:
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

        # Support external directories for dynamic python imports
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
            player = self.bot_instance.player
            inv_count = len(player.INVENTORY) if player.INVENTORY else 0
            bank_count = len(player.BANK) if player.BANK else 0
            
            return {
                "running": True,
                "is_connected": self.bot_instance.is_client_connected,
                "username": player.USER or "Unknown",
                "gold": player.GOLD,
                "gold_farmed": player.GOLDFARMED,
                "exp_farmed": player.EXPFARMED,
                "hp": player.CURRENT_HP,
                "max_hp": player.MAX_HP,
                "mp": player.MANA,
                "max_mp": player.MAX_MP,
                "cell": player.CELL or "Unknown",
                "pad": player.PAD or "Unknown",
                "is_dead": player.ISDEAD,
                "in_combat": player.IS_IN_COMBAT,
                "inventory_count": inv_count,
                "bank_count": bank_count,
                "current_script": self.bot_thread.bot_path,
                "index": self.bot_instance.index
            }
        
        return {"running": False}

def main():
    api = Api()
    
    # Redirect stdout and stderr
    sys.stdout = LogRedirector(sys.stdout, api.handle_log)
    sys.stderr = LogRedirector(sys.stderr, api.handle_log)

    # Determine resources base directory
    if getattr(sys, 'frozen', False):
        web_dir = os.path.join(getattr(sys, '_MEIPASS', ''), 'web')
    else:
        web_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'app', 'web')

    print(f"Loading GUI assets from: {web_dir}")
    
    # Start custom local web server to serve the frontend files
    # This bypasses WKWebView file security and handles pywebview's frozen path overrides
    url = start_local_server(web_dir)
    print(f"Custom HTTP server running at: {url}")

    # Create the pywebview desktop window
    window = webview.create_window(
        title='AQW Python Bot Client',
        url=url,
        js_api=api,
        width=1000,
        height=700,
        min_size=(900, 600),
        resizable=True
    )
    
    api.set_window(window)
    webview.start(debug=False)

if __name__ == '__main__':
    main()
