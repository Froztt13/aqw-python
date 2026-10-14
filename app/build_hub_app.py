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
        if hasattr(sys, '_MEIPASS'):
            return sys._MEIPASS
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
    def __init__(self, original_stream, log_file=None):
        self.original_stream = original_stream
        self.log_file = log_file
        self.thread_callbacks = {}  # thread_id -> (username, callback)
        self.combined_api = None
        self.standalone_callback = None
        self.default_callback = lambda x: None

    def register_thread(self, thread_id, username, callback):
        self.thread_callbacks[thread_id] = (username, callback)

    def unregister_thread(self, thread_id):
        if thread_id in self.thread_callbacks:
            del self.thread_callbacks[thread_id]

    def write(self, message):
        if self.original_stream and hasattr(self.original_stream, 'write'):
            try:
                self.original_stream.write(message)
            except Exception:
                pass
        if self.log_file:
            try:
                self.log_file.write(message)
                self.log_file.flush()
            except Exception:
                pass
        if not message or not message.strip():
            return
            
        current_thread_id = threading.get_ident()
        if current_thread_id in self.thread_callbacks:
            username, callback = self.thread_callbacks[current_thread_id]
            callback(username, message)
        elif self.standalone_callback:
            try:
                self.standalone_callback("System", message)
            except Exception:
                pass
        else:
            # Route output from threads that never registered a callback to
            # whichever menu is currently on screen.  This deliberately avoids
            # window.get_current_url(): that call blocks (~20 s) and can wedge
            # or crash the GUI thread when it fires during a stop/teardown.
            api = getattr(self, 'combined_api', None)
            if api is None:
                return
            try:
                api.route_system_log(message)
            except Exception:
                pass

    def flush(self):
        if self.original_stream and hasattr(self.original_stream, 'flush'):
            try:
                self.original_stream.flush()
            except Exception:
                pass
        if hasattr(self, 'log_file') and self.log_file:
            try:
                self.log_file.flush()
            except Exception:
                pass

# Setup unified global redirectors with persistent file log
try:
    _log_dir = os.path.expanduser("~/.aqw_bot")
    os.makedirs(_log_dir, exist_ok=True)
    _hub_log_file = open(os.path.join(_log_dir, "hub_app.log"), "a", encoding="utf-8", errors="replace")
except Exception:
    _hub_log_file = None

unified_redirector_out = UnifiedThreadRedirector(sys.stdout, _hub_log_file)
unified_redirector_err = UnifiedThreadRedirector(sys.stderr, _hub_log_file)

# Assign global overrides
sys.stdout = unified_redirector_out
sys.stderr = unified_redirector_err

# --- Thread Classes for Sub-Bots ---
# Calling evaluate_js once per log line from four bot threads floods WebView2
# (it wedges / the control can get disposed mid-teardown).  All log lines are
# queued and flushed in ONE evaluate_js call every ~250 ms instead.
_JS_LOCK = threading.Lock()


def _eval_js(window, script):
    if window is None:
        return
    try:
        events = getattr(window, "events", None)
        closed = getattr(events, "closed", None)
        if closed is not None and hasattr(closed, "is_set") and closed.is_set():
            return
    except Exception:
        pass
    try:
        with _JS_LOCK:
            window.evaluate_js(script)
    except Exception:
        pass


class _LogFlusher:
    def __init__(self, interval=0.25, max_batch=300):
        self._queue = []
        self._lock = threading.Lock()
        self._interval = interval
        self._max_batch = max_batch
        self._window = None
        self._thread = None

    def set_window(self, window):
        self._window = window
        if self._thread is None:
            self._thread = threading.Thread(target=self._run, daemon=True,
                                            name="log-flusher")
            self._thread.start()

    def push(self, script):
        with self._lock:
            self._queue.append(script)
            if len(self._queue) > 3000:
                del self._queue[:1000]

    def _run(self):
        while True:
            time.sleep(self._interval)
            if self._window is None:
                continue
            with self._lock:
                if not self._queue:
                    continue
                batch = self._queue[-self._max_batch:]
                self._queue = []
            _eval_js(self._window, ";".join(batch))


_log_flusher = _LogFlusher()


def _drain_loop(loop):
    """Cancel and await pending tasks so closing the loop is clean.

    Without this, closing a loop that still has ``read_server_in_background`` /
    ``register_quest_task`` pending prints ``Task was destroyed but it is
    pending!`` and can abort the process.
    """
    try:
        pending = [t for t in asyncio.all_tasks(loop) if not t.done()]
    except Exception:
        pending = []
    for task in pending:
        task.cancel()
    if pending:
        try:
            loop.run_until_complete(asyncio.gather(*pending, return_exceptions=True))
        except Exception:
            pass


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
            _drain_loop(self.loop)
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
            self.bot_instance.set_login_info(self.username, self.password, self.config.get("server", "Alteon"))
            self.bot_instance.is_script_paused = False
            self.bot_instance.is_paused = False
            self.bot_instance.was_paused = False
            self.bot_instance.taunt_error = False
            
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
            _drain_loop(self.loop)
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
        self.bot_core = None
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
            self.bot_core = bot_inst
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
        self.bot_core = None
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
            self.bot_core = bot_inst
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

class UltraBotThread(threading.Thread):
    """One pane of an ultra party (daily or speaker) run inside the hub.

    Mirrors what ``ultra_daily_pane.bat`` / ``ultra_speaker_pane.bat`` do per
    window: build a ``Bot`` for one account, then run the shared ultra runner.
    The party file sync works because every pane shares one ``AQW_RUN_ID`` set
    by the API before the threads start.
    """

    def __init__(self, slot, kind, username, password, server, room_number,
                 leader, slaves, role, callback, missing_policy="stop"):
        super().__init__()
        self.slot = slot
        self.kind = kind                    # "daily" | "speaker"
        self.username = username
        self.password = password
        self.server = server
        self.room_number = room_number
        self.leader = leader
        self.slaves = slaves or []
        self.role = role                    # speaker: class name; daily: ""
        self.callback = callback
        self.missing_policy = missing_policy
        self.bot_instance = None
        self.daemon = True

    def run(self):
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        thread_id = threading.get_ident()
        unified_redirector_out.register_thread(thread_id, self.username, self.callback)
        unified_redirector_err.register_thread(thread_id, self.username, self.callback)

        telemetry = None
        b = Bot(
            roomNumber=self.room_number,
            showLog=True,
            showDebug=False,
            showChat=True,
            isScriptable=True,
            followPlayer=(self.leader or "").lower(),
            slavesPlayer=self.slaves,
            soloClass=self.role or None,
            muteSpamWarning=True,
        )
        b.set_login_info(self.username, self.password, self.server)
        self.bot_instance = b

        try:
            try:
                from bot.ultra.telemetry import install_from_env
                telemetry = install_from_env(b, self.slot, self.username)
            except Exception as exc:
                print(f"[ultra slot {self.slot}] telemetry off: {exc}")

            if self.kind == "speaker":
                from bot.ultra.core_ultra import UltraSpeaker
                runner = UltraSpeaker(b.command, self.slot)
            else:
                from bot.ultra.daily import DailyUltra
                runner = DailyUltra(b.command, self.slot)
            runner.missing_policy = self.missing_policy

            async def run_bot(cmd):
                await runner.run()

            loop.run_until_complete(b.start_bot(run_bot))
        except Exception as e:
            print(f"[ultra slot {self.slot}] execution stopped or error occurred: {e}")
        finally:
            if telemetry is not None:
                try:
                    telemetry.close()
                except Exception:
                    pass
            unified_redirector_out.unregister_thread(thread_id)
            unified_redirector_err.unregister_thread(thread_id)
            _drain_loop(loop)
            loop.close()

class WeeklyDoomThread(threading.Thread):
    """Runs the Weekly Doom queue for one account.

    Weekly Doom is a queue-mode script (``bot_cmds/weekly_doom.py``), so this
    builds a non-scriptable ``Bot`` and runs ``start_bot()`` (the command loop).
    """

    def __init__(self, username, password, server, room_number, callback):
        super().__init__()
        self.username = username
        self.password = password
        self.server = server
        self.room_number = room_number
        self.callback = callback
        self.bot_instance = None
        self.daemon = True

    def run(self):
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        thread_id = threading.get_ident()
        unified_redirector_out.register_thread(thread_id, self.username, self.callback)
        unified_redirector_err.register_thread(thread_id, self.username, self.callback)
        try:
            import commands as botcmd
            b = Bot(roomNumber=self.room_number, showLog=True, showDebug=True, cmdDelay=500)
            b.set_login_info(self.username, self.password, self.server)
            self.bot_instance = b
            b.add_cmds([
                botcmd.IsInInvCmd("Epic Item of Digital Awesomeness"),
                botcmd.MessageCmd(msg="You have \"Epic Item of Digital Awesomeness\" in your inventory!!"),
                botcmd.IsInBankCmd("Gear of Doom"),
                botcmd.BankToInvCmd("Gear of Doom"),
                botcmd.IsInInvCmd("Gear of Doom", 3, operator="<"),
                botcmd.StopBotCmd(msg="Not enough Gear of Doom."),
                botcmd.JoinMapCmd("doom"),
                botcmd.AcceptQuestCmd(3076),
                botcmd.TurnInQuestCmd(3076),
                botcmd.SleepCmd(1000),
                botcmd.StopBotCmd(msg="Bot Finished."),
            ])
            loop.run_until_complete(b.start_bot())
        except Exception as e:
            print(f"[weekly doom {self.username}] execution stopped: {e}")
        finally:
            unified_redirector_out.unregister_thread(thread_id)
            unified_redirector_err.unregister_thread(thread_id)
            _drain_loop(loop)
            try:
                loop.close()
            except Exception:
                pass

# --- Sub-GUI API Implementations (Standalone-Compatible) ---
class PlayersApi:
    """Saved player list for the Config Player menu.

    This is the only place the app persists credentials.  The file is a plain
    list of ``{"user", "pass"}`` objects so it can also be filled in by hand.
    It starts empty: nothing is seeded from any script or from
    ``bot/ultra/config.py``.
    """

    def __init__(self):
        self._window = None
        if getattr(sys, 'frozen', False):
            config_dir = os.path.expanduser("~/.aqw_bot")
            os.makedirs(config_dir, exist_ok=True)
            self.config_path = os.path.join(config_dir, "players.json")
        else:
            self.config_path = os.path.join(get_project_root(), "players.json")

    def set_window(self, window):
        self._window = window

    def _read(self):
        if not os.path.exists(self.config_path):
            return []
        try:
            with open(self.config_path, "r", encoding="utf-8") as f:
                data = json.load(f)
            if isinstance(data, list):
                return [p for p in data if isinstance(p, dict)]
        except Exception as e:
            print(f"Failed to load players: {e}")
        return []

    def _write(self, players):
        try:
            temp_path = self.config_path + ".tmp"
            with open(temp_path, "w", encoding="utf-8") as f:
                json.dump(players, f, indent=4)
            os.replace(temp_path, self.config_path)
            return {"success": True, "players": players}
        except Exception as e:
            print(f"Failed to save players: {e}")
            return {"success": False, "error": str(e)}

    def list_players(self):
        return self._read()

    def add_player(self, user, password):
        user = (user or "").strip()
        if not user:
            return {"success": False, "error": "Username is required."}
        players = self._read()
        if any(p.get("user", "").lower() == user.lower() for p in players):
            return {"success": False, "error": f"{user} already exists."}
        players.append({"user": user, "pass": password or ""})
        return self._write(players)

    def update_player(self, index, user, password):
        players = self._read()
        try:
            index = int(index)
        except (TypeError, ValueError):
            return {"success": False, "error": "Invalid index."}
        if index < 0 or index >= len(players):
            return {"success": False, "error": "Player not found."}
        user = (user or "").strip()
        if not user:
            return {"success": False, "error": "Username is required."}
        if any(p.get("user", "").lower() == user.lower()
               for i, p in enumerate(players) if i != index):
            return {"success": False, "error": f"{user} already exists."}
        players[index] = {"user": user, "pass": password or ""}
        return self._write(players)

    def delete_player(self, index):
        players = self._read()
        try:
            index = int(index)
        except (TypeError, ValueError):
            return {"success": False, "error": "Invalid index."}
        if index < 0 or index >= len(players):
            return {"success": False, "error": "Player not found."}
        players.pop(index)
        return self._write(players)


class AqwSoloApi:
    def __init__(self):
        #: username -> {"thread", "instance", "config"}; one bot per account.
        self.bots = {}
        self._window = None
        if getattr(sys, 'frozen', False):
            config_dir = os.path.expanduser("~/.aqw_bot")
            os.makedirs(config_dir, exist_ok=True)
            self.config_path = os.path.join(config_dir, "gui_config.json")
        else:
            self.config_path = os.path.join(get_project_root(), "gui_config.json")

    def set_window(self, window):
        self._window = window

    def handle_log(self, message):
        html_msg = ansi_to_html(message)
        _log_flusher.push(
            f"if(window.addSlaveLog) window.addSlaveLog('System', {json.dumps(html_msg)}, 'aqw');"
        )

    def handle_account_log(self, key, message):
        """Route one line to a single account's log panel in the solo menu."""
        html_msg = ansi_to_html(message)
        _log_flusher.push(
            f"if(window.addSlaveLog) window.addSlaveLog({json.dumps(key)}, "
            f"{json.dumps(html_msg)}, 'aqw');"
        )

    @staticmethod
    def _default_account():
        return {
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
            "anti_mod": True,
            "bot_external": False,
            "bot_parent_dir": ""
        }

    def load_config(self):
        accounts = [self._default_account()]
        if os.path.exists(self.config_path):
            try:
                with open(self.config_path, "r") as f:
                    user_config = json.load(f)
                if isinstance(user_config, dict) and isinstance(user_config.get("accounts"), list):
                    accounts = user_config["accounts"] or [self._default_account()]
                elif isinstance(user_config, dict):
                    # Migrate the old single-account layout into the first row.
                    acc = self._default_account()
                    for key in acc:
                        if key in user_config:
                            acc[key] = user_config[key]
                    accounts = [acc]
            except Exception as e:
                print(f"Failed to load config: {e}")
        return {"accounts": accounts}

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
        if not self._window:
            return None
        file_types = ('Python files (*.py)', 'All files (*.*)')
        result = self._window.create_file_dialog(
            dialog_type=webview.OPEN_DIALOG,
            file_types=file_types
        )
        if result and len(result) > 0:
            return self._resolve_module_path(result[0])
        return None

    def _build_bot_and_thread(self, acc):
        whitelist = acc.get("whitelist", [])
        if isinstance(whitelist, str):
            whitelist = [item.strip() for item in whitelist.split(",") if item.strip()]

        if acc.get("bot_external") and acc.get("bot_parent_dir"):
            ext_path = acc.get("bot_parent_dir")
            if ext_path not in sys.path:
                sys.path.insert(0, ext_path)

        bot = Bot(
            roomNumber=int(acc.get("room_number", 1) or 1),
            itemsDropWhiteList=whitelist,
            showLog=True,
            showDebug=False,
            showChat=acc.get("show_chat", True),
            isScriptable=True,
            followPlayer="",
            slavesPlayer=[],
            farmClass=acc.get("farm_class") or None,
            soloClass=acc.get("solo_class") or None,
            autoRelogin=acc.get("auto_relogin", True),
            muteSpamWarning=acc.get("mute_spam", True),
            antiMod=acc.get("anti_mod", True)
        )
        bot.set_login_info(acc.get("username"), acc.get("password"), acc.get("server", "Artix"))
        return bot, BotThread(bot, acc.get("bot_path"))

    def start_bots(self, config):
        """Start one bot per account, all in parallel."""
        self.save_config(config)
        accounts = config.get("accounts", [])
        started = 0
        errors = []
        for acc in accounts:
            username = (acc.get("username") or "").strip()
            if not username or not acc.get("bot_path"):
                continue
            key = username
            entry = self.bots.get(key)
            if entry and entry["thread"].is_alive():
                continue
            try:
                bot, thread = self._build_bot_and_thread(acc)
                thread.start()
                tid = thread.ident
                if tid:
                    unified_redirector_out.register_thread(
                        tid, key, lambda name, msg, k=key: self.handle_account_log(k, msg))
                    unified_redirector_err.register_thread(
                        tid, key, lambda name, msg, k=key: self.handle_account_log(k, msg))
                self.bots[key] = {"thread": thread, "instance": bot, "config": acc}
                started += 1
            except Exception as e:
                errors.append(f"{username}: {e}")
        if started == 0 and not errors:
            return {"success": False, "error": "Fill at least one account (username + script)."}
        return {"success": True, "started": started, "errors": errors}

    def start_one(self, acc):
        """Start a single account (the per-tab START button)."""
        username = (acc.get("username") or "").strip()
        if not username:
            return {"success": False, "error": "Username is required."}
        if not acc.get("bot_path"):
            return {"success": False, "error": "Pick a script first."}
        entry = self.bots.get(username)
        if entry and entry["thread"].is_alive():
            return {"success": False, "error": f"{username} is already running."}
        try:
            bot, thread = self._build_bot_and_thread(acc)
            thread.start()
            tid = thread.ident
            if tid:
                unified_redirector_out.register_thread(
                    tid, username, lambda name, msg, k=username: self.handle_account_log(k, msg))
                unified_redirector_err.register_thread(
                    tid, username, lambda name, msg, k=username: self.handle_account_log(k, msg))
            self.bots[username] = {"thread": thread, "instance": bot, "config": acc}
            return {"success": True}
        except Exception as e:
            return {"success": False, "error": str(e)}

    def stop_one(self, key):
        """Stop a single account (the per-tab STOP button)."""
        entry = self.bots.pop(key, None)
        if not entry:
            return {"success": False, "error": f"{key} is not running."}
        try:
            tid = entry["thread"].ident
            if tid:
                unified_redirector_out.unregister_thread(tid)
                unified_redirector_err.unregister_thread(tid)
            instance = entry.get("instance")
            if instance:
                instance.stop_bot(user_triggered=True)
            return {"success": True}
        except Exception as e:
            return {"success": False, "error": str(e)}

    def stop_bots(self):
        entries = list(self.bots.items())
        self.bots = {}
        for key, entry in entries:
            try:
                tid = entry["thread"].ident
                if tid:
                    unified_redirector_out.unregister_thread(tid)
                    unified_redirector_err.unregister_thread(tid)
                instance = entry.get("instance")
                if instance:
                    instance.stop_bot(user_triggered=True)
            except Exception as e:
                print(f"Failed to stop {key}: {e}")
        return {"success": True}

    def _account_status(self, entry):
        thread = entry["thread"]
        instance = entry.get("instance")
        if not (thread.is_alive() and instance):
            return {"running": False, "is_connected": False}
        b = instance
        p = b.player
        from datetime import datetime
        now = datetime.now()
        cooldowns = {}
        if p and hasattr(p, "SKILLS"):
            for i in range(6):
                if i < len(p.SKILLS):
                    skill_data = p.SKILLS[i]
                    next_use = skill_data.get("nextUse")
                    cooldowns[i] = (round((next_use - now).total_seconds(), 1)
                                    if next_use and next_use > now else 0.0)
                else:
                    cooldowns[i] = 0.0
        try:
            return {
                "running": True,
                "is_connected": b.is_client_connected,
                "username": p.USER if p else "-",
                "hp": p.CURRENT_HP if p else 0,
                "max_hp": p.MAX_HP if p else 0,
                "mp": p.MANA if p else 0,
                "max_mp": p.MAX_MP if p else 0,
                "is_dead": p.ISDEAD if p else False,
                "map": getattr(b, "strMapName", "") or "-",
                "cell": p.CELL if p else "-",
                "pad": p.PAD if p else "-",
                "cooldowns": cooldowns,
            }
        except Exception as e:
            return {"running": True, "is_connected": False, "error": str(e)}

    def get_statuses(self):
        result = []
        for key, entry in self.bots.items():
            status = self._account_status(entry)
            status["key"] = key
            result.append(status)
        return result

    def get_status(self):
        accounts = self.get_statuses()
        running = [a for a in accounts if a.get("running")]
        base = {"running": bool(running), "accounts": accounts}
        if running:
            # Keep the old single-account dashboard fields at the top level.
            base.update({k: v for k, v in running[0].items() if k != "accounts"})
        return base

    def get_items(self, key):
        """Inventory / bank / temp items for one account (realtime snapshot)."""
        entry = self.bots.get(key)
        if not entry or not entry.get("instance"):
            return {"running": False, "inventory": [], "bank": [], "temp": []}
        player = entry["instance"].player

        def dump(items):
            out = []
            for item in items or []:
                try:
                    out.append({
                        "name": item.s_name or item.item_name,
                        "id": item.item_id,
                        "slot": item.slot,
                        "qty": item.qty_now or item.qty,
                        "level": item.level,
                        "dps": item.dps,
                        "rarity": item.rarity,
                        "enh": item.enhancement_name or "",
                        "equipped": bool(item.is_equipped),
                    })
                except Exception:
                    continue
            return out

        try:
            return {
                "running": entry["thread"].is_alive(),
                "inventory": dump(getattr(player, "INVENTORY", [])),
                "bank": dump(getattr(player, "BANK", [])),
                "temp": dump(getattr(player, "TEMPINVENTORY", [])),
            }
        except Exception as e:
            return {"running": False, "error": str(e),
                    "inventory": [], "bank": [], "temp": []}

class SlaveryApi:
    def __init__(self):
        self._window = None
        if getattr(sys, 'frozen', False):
            config_dir = os.path.expanduser("~/.aqw_bot")
            os.makedirs(config_dir, exist_ok=True)
            self.config_path = os.path.join(config_dir, "slavery_config.json")
        else:
            self.config_path = os.path.join(get_project_root(), "slavery_config.json")
        self.active_threads = {}
        self.taunt_coordinator = TauntCoordinator()

    def set_window(self, window):
        self._window = window

    def handle_slave_log(self, username, message):
        html_msg = ansi_to_html(message)
        if self._window:
            try:
                self._window.evaluate_js(
                    f"if(window.addSlaveLog) window.addSlaveLog({json.dumps(username)}, {json.dumps(html_msg)}, 'slavery');"
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
        state = bool(pause_state)
        for username, thread in self.active_threads.items():
            if thread.bot_instance:
                thread.bot_instance.is_paused = state
                thread.bot_instance.is_script_paused = state
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
        now = datetime.now()
        for username, thread in list(self.active_threads.items()):
            running = thread.is_alive()
            if running and thread.bot_instance:
                bot = thread.bot_instance
                player = getattr(bot, "player", None)
                
                cooldowns = {0: 0.0, 1: 0.0, 2: 0.0, 3: 0.0, 4: 0.0, 5: 0.0}
                if player and hasattr(player, "SKILLS"):
                    try:
                        skills = player.SKILLS
                        if isinstance(skills, (list, tuple)):
                            for i in range(0, 6):
                                if i < len(skills):
                                    skill_data = skills[i]
                                    if isinstance(skill_data, dict):
                                        next_use = skill_data.get("nextUse")
                                        if isinstance(next_use, datetime) and next_use > now:
                                            cooldowns[i] = round((next_use - now).total_seconds(), 1)
                    except Exception:
                        pass

                scroll_qty = 0
                if player and hasattr(player, "get_item_inventory"):
                    try:
                        item_enrage = player.get_item_inventory("Scroll of Enrage")
                        if item_enrage and hasattr(item_enrage, "qty"):
                            scroll_qty = int(item_enrage.qty)
                    except Exception:
                        scroll_qty = 0

                is_active_taunter = False
                if self.taunt_coordinator:
                    try:
                        is_active_taunter = (self.taunt_coordinator.get_active_taunter() == username)
                    except Exception:
                        pass

                try:
                    hp_val = int(player.CURRENT_HP) if player and player.CURRENT_HP is not None else 0
                    max_hp_val = int(player.MAX_HP) if player and player.MAX_HP is not None else 0
                    mp_val = int(player.MANA) if player and player.MANA is not None else 0
                    max_mp_val = int(player.MAX_MP) if player and player.MAX_MP is not None else 0
                    
                    statuses[username] = {
                        "running": True,
                        "is_connected": bool(getattr(bot, "is_client_connected", False)),
                        "hp": hp_val,
                        "max_hp": max_hp_val,
                        "mp": mp_val,
                        "max_mp": max_mp_val,
                        "is_dead": bool(player.ISDEAD) if player else False,
                        "map": str(getattr(bot, "strMapName", "-") or "-"),
                        "cell": str(player.CELL if player and player.CELL else "-"),
                        "pad": str(player.PAD if player and player.PAD else "-"),
                        "is_paused": bool(getattr(bot, "is_paused", False) or getattr(bot, "is_script_paused", False)),
                        "cooldowns": cooldowns,
                        "scroll_enrage_qty": scroll_qty,
                        "taunt_error": bool(getattr(bot, "taunt_error", False)),
                        "is_active_taunter": is_active_taunter
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
        self._window = None
        if getattr(sys, 'frozen', False):
            config_dir = os.path.expanduser("~/.aqw_bot")
            os.makedirs(config_dir, exist_ok=True)
            self.config_path = os.path.join(config_dir, "temple_config.json")
        else:
            self.config_path = os.path.join(get_project_root(), "temple_config.json")
        self.active_threads = {}
        self.start_time = None
        self.cleared_count = 0
        self.taunt_coordinator = TauntCoordinator()
        
        try:
            import psutil
            self._process = psutil.Process(os.getpid())
            self._process.cpu_percent(interval=None)
        except Exception:
            self._process = None

    def set_window(self, window):
        self._window = window

    def handle_slave_log(self, username, message):
        html_msg = ansi_to_html(message)
        if "Dungeon cleared" in message:
            import re
            m = re.search(r"Dungeon cleared (\d+) times", message)
            if m:
                self.cleared_count = int(m.group(1))

        if self._window:
            try:
                self._window.evaluate_js(
                    f"if(window.addSlaveLog) window.addSlaveLog({json.dumps(username)}, {json.dumps(html_msg)}, 'temple');"
                )
                # Duplicate cleared logs (clear time, clear count, total time running) to System logs tab
                if "Finished in" in message or "Total time taken" in message or "Clear time" in message or "Dungeon cleared" in message or "Total time running" in message:
                    sys_msg = f"[{username}] {message}"
                    html_sys_msg = ansi_to_html(sys_msg)
                    self._window.evaluate_js(
                        f"if(window.addSlaveLog) window.addSlaveLog('System', {json.dumps(html_sys_msg)}, 'temple');"
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
        self.cleared_count = 0
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
        for s_id, thread in list(self.active_threads.items()):
            running = thread.is_alive()
            if running and thread.bot_instance:
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
                    try:
                        item_enrage = p.get_item_inventory("Scroll of Enrage")
                        if item_enrage:
                            scroll_qty = item_enrage.qty
                    except Exception:
                        scroll_qty = 0

                try:
                    status_data[s_id] = {
                        "running": running,
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
                except Exception as e:
                    status_data[s_id] = {
                        "running": running,
                        "is_connected": False,
                        "error": str(e)
                    }
            else:
                status_data[s_id] = {"running": False, "is_connected": False}
                
        for s_id in ["slot1", "slot2", "slot3", "slot4"]:
            if s_id not in status_data:
                status_data[s_id] = {"running": False, "is_connected": False}

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
        if hasattr(self, "_process") and self._process:
            try:
                mem_mb = round(self._process.memory_info().rss / (1024 * 1024), 1)
                cpu_pct = round(self._process.cpu_percent(interval=None), 1)
            except Exception:
                pass

        slot_statuses = {s_id: status_data[s_id] for s_id in ["slot1", "slot2", "slot3", "slot4"]}
        time_running = int(time.time() - self.start_time) if getattr(self, "start_time", None) else 0
        active_taunter = self.taunt_coordinator.active_taunter if hasattr(self, "taunt_coordinator") else None

        for thread in self.active_threads.values():
            if hasattr(thread, "bot_core") and thread.bot_core:
                c = getattr(thread.bot_core, "cleared_count", 0)
                if c > self.cleared_count:
                    self.cleared_count = c

        return {
            "statuses": slot_statuses,
            "monsters": monsters_info,
            "_active_taunter": active_taunter,
            "_time_running": time_running,
            "cleared_count": self.cleared_count,
            "system_stats": {
                "cpu": cpu_pct,
                "memory": mem_mb
            },
            **slot_statuses
        }

class EclipseApi:
    def __init__(self):
        self._window = None
        if getattr(sys, 'frozen', False):
            config_dir = os.path.expanduser("~/.aqw_bot")
            os.makedirs(config_dir, exist_ok=True)
            self.config_path = os.path.join(config_dir, "eclipse_config.json")
        else:
            self.config_path = os.path.join(get_project_root(), "eclipse_config.json")
            
        self.active_threads = {}
        self.start_time = None
        self.cleared_count = 0
        
        try:
            import psutil
            self._process = psutil.Process(os.getpid())
            self._process.cpu_percent(interval=None)
        except Exception:
            self._process = None

    def set_window(self, window):
        self._window = window

    def validate_password(self, password):
        target_hash = "080dcf0b2c402cb9ac5be3dc6907f79a3a2b113325755ecdd792bdc6b8c7399e"
        input_hash = hashlib.sha256(password.encode('utf-8')).hexdigest()
        return {"valid": input_hash == target_hash}

    def handle_slave_log(self, username, message):
        html_msg = ansi_to_html(message)
        if "Dungeon cleared" in message:
            import re
            m = re.search(r"Dungeon cleared (\d+) times", message)
            if m:
                self.cleared_count = int(m.group(1))

        if self._window:
            try:
                self._window.evaluate_js(
                    f"if(window.addSlaveLog) window.addSlaveLog({json.dumps(username)}, {json.dumps(html_msg)}, 'eclipse');"
                )
                if "Finished in" in message or "Total time taken" in message or "Clear time" in message or "Dungeon cleared" in message or "Total time running" in message:
                    sys_msg = f"[{username}] {message}"
                    html_sys_msg = ansi_to_html(sys_msg)
                    self._window.evaluate_js(
                        f"if(window.addSlaveLog) window.addSlaveLog('System', {json.dumps(html_sys_msg)}, 'eclipse');"
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
                    "light_gather_taunter": True
                },
                "slot2": {
                    "username": "",
                    "password": "",
                    "char_class": "StoneCrusher",
                    "taunt_parity": "even",
                    "converge_type": "sun",
                    "light_gather_taunter": True
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
        self.cleared_count = 0
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
            "slot_number": 1,
            "light_gather_taunter": bool(s1.get("light_gather_taunter", True))
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
            "slot_number": 2,
            "light_gather_taunter": bool(s2.get("light_gather_taunter", True)),
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
            "slot_number": 3,
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
            "slot_number": 4,
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

    def toggle_pause(self, pause_state):
        state = bool(pause_state)
        for slot_id, thread in self.active_threads.items():
            if thread.bot_instance:
                thread.bot_instance.is_paused = state
                thread.bot_instance.is_script_paused = state
            if thread.bot_core:
                thread.bot_core.is_paused = state
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
                    try:
                        item_enrage = player.get_item_inventory("Scroll of Enrage")
                        if item_enrage:
                            scroll_qty = item_enrage.qty
                    except Exception:
                        scroll_qty = 0

                is_paused = getattr(bot, "is_paused", False) or (getattr(thread.bot_core, "is_paused", False) if thread.bot_core else False)

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
                        "is_paused": is_paused,
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
                statuses[s_id] = {"running": False, "is_connected": False}

        monsters_info = []
        for slot_id, thread in list(self.active_threads.items()):
            if thread.is_alive() and thread.bot_instance:
                bot = thread.bot_instance
                player = bot.player
                current_cell = player.CELL if player else None
                if current_cell and hasattr(bot, "monsters") and bot.monsters:
                    try:
                        for mon in list(bot.monsters):
                            if mon.frame == current_cell and mon.current_hp > 0:
                                monsters_info.append({
                                    "name": mon.mon_name,
                                    "id": mon.mon_map_id,
                                    "hp": mon.current_hp,
                                    "max_hp": mon.max_hp
                                })
                    except Exception:
                        pass
                    if monsters_info:
                        break

        mem_mb = 0.0
        cpu_pct = 0.0
        if hasattr(self, "_process") and self._process:
            try:
                mem_mb = round(self._process.memory_info().rss / (1024 * 1024), 1)
                cpu_pct = round(self._process.cpu_percent(interval=None), 1)
            except Exception:
                pass

        slot_statuses = {s_id: statuses[s_id] for s_id in ["slot1", "slot2", "slot3", "slot4"]}
        time_running = int(time.time() - self.start_time) if getattr(self, "start_time", None) else 0

        for thread in self.active_threads.values():
            if hasattr(thread, "bot_core") and thread.bot_core:
                c = getattr(thread.bot_core, "cleared_count", 0)
                if c > self.cleared_count:
                    self.cleared_count = c

        return {
            "statuses": slot_statuses,
            "monsters": monsters_info,
            "system_stats": {
                "cpu": cpu_pct,
                "memory": mem_mb
            },
            "_time_running": time_running,
            "cleared_count": self.cleared_count,
            **slot_statuses
        }

# --- Combined API class ---
def _spec_name(spec):
    """Enhancement-spec -> display name ('Valiance', 'Awe Blast', ...)."""
    if spec is None:
        return ""
    return getattr(spec, "name", spec)


class UltraApi:
    """Shared plumbing for the Ultra Daily / Ultra Speaker menus.

    Four slots = four panes, exactly like the ``.bat`` launchers.  All four run
    as threads in this process, so they share one ``AQW_RUN_ID`` and the party
    coordination in ``bot/ultra/party.py`` works across them.
    """

    kind = ""
    DEFAULT_SERVER = "Alteon"
    SLOT_IDS = ("slot1", "slot2", "slot3", "slot4")

    def __init__(self, config_name):
        self.active_threads = {}
        self._window = None
        self.start_time = None
        #: Config of the running party, kept so the watchdog can relogin.
        self._party_config = None
        #: Set when the user presses STOP so the watchdog does NOT relogin.
        self._manual_stop = False
        self._watchdog = None
        #: Bumped every start; a stale watchdog exits when it no longer matches.
        self._party_gen = 0
        if getattr(sys, 'frozen', False):
            config_dir = os.path.expanduser("~/.aqw_bot")
            os.makedirs(config_dir, exist_ok=True)
            self.config_path = os.path.join(config_dir, config_name)
        else:
            self.config_path = os.path.join(get_project_root(), config_name)

    def set_window(self, window):
        self._window = window

    # ------------------------------------------------------------------
    # party watchdog: one pane stops -> stop all -> wait -> relogin
    # ------------------------------------------------------------------

    def _start_watchdog(self):
        self._party_gen += 1
        gen = self._party_gen
        self._watchdog = threading.Thread(
            target=self._watch_party, args=(gen,), daemon=True,
            name=f"{self.tab_id()}-watchdog")
        self._watchdog.start()

    def _watch_party(self, gen):
        """Stop the whole party when any pane stops, then relogin after 10 s.

        'Any stop condition' counts: a pane finishing normally, erroring, the
        server dropping it, or a thread ending.  A user STOP sets
        ``_manual_stop`` so this does not fight the button and does not relogin.
        A ``gen`` mismatch means a newer party has started, so this watchdog
        retires instead of watching the wrong run.
        """
        seen_connected = set()
        while gen == self._party_gen and not self._manual_stop:
            threads = list(self.active_threads.items())
            if not threads:
                return
            for s_id, t in threads:
                b = getattr(t, "bot_instance", None)
                if b is not None and getattr(b, "is_client_connected", False):
                    seen_connected.add(s_id)
            stopped = []
            for s_id, t in threads:
                b = getattr(t, "bot_instance", None)
                if not t.is_alive():
                    stopped.append(s_id)
                elif s_id in seen_connected and b is not None and \
                        not getattr(b, "is_client_connected", True):
                    stopped.append(s_id)
            if stopped:
                finished = False
                aborted = None
                try:
                    from bot.ultra import party as ultra_party
                    if ultra_party.enabled():
                        finished = ultra_party.all_done(f"ultra_{self.kind}")
                        aborted = ultra_party.any_abort(f"ultra_{self.kind}")
                except Exception:
                    pass
                print(f"[{self.tab_id()}] {sorted(stopped)} stopped -> stopping whole party")
                self.stop_party()             # not user-triggered
                if aborted and not self._manual_stop:
                    print(f"[{self.tab_id()}] preflight abort: {aborted} (no relogin)")
                    return
                if finished and not self._manual_stop:
                    print(f"[{self.tab_id()}] all panes finished (no relogin)")
                    return
                if gen != self._party_gen or self._manual_stop:
                    return
                print(f"[{self.tab_id()}] waiting 10s before relogin...")
                time.sleep(10)
                if gen != self._party_gen or self._manual_stop:
                    return
                if self._party_config:
                    print(f"[{self.tab_id()}] relogin")
                    self.start_party(self._party_config)   # bumps gen, new watchdog
                return
            time.sleep(1.0)

    def handle_log(self, username, message):
        html_msg = ansi_to_html(message)
        _log_flusher.push(
            f"if(window.addSlaveLog) window.addSlaveLog({json.dumps(username or 'System')}, "
            f"{json.dumps(html_msg)}, {json.dumps(self.tab_id())});"
        )

    def tab_id(self):
        """Hub iframe id for this menu. ``kind`` is 'daily'/'speaker', the tab is
        'ultra_daily'/'ultra_speaker' -- forwarding with the bare kind looked for
        an ``iframe-daily`` that does not exist, so logs were dropped."""
        return f"ultra_{self.kind}"

    def config_key(self):
        return self.kind

    def _default_role(self, slot):
        return ""

    def _default_slots(self):
        return {
            f"slot{i}": {"username": "", "password": "", "role": self._default_role(i)}
            for i in range(1, 5)
        }

    def load_config(self):
        default_config = {
            "server": self.DEFAULT_SERVER,
            "room_number": 9099,
            "missing_policy": "stop",
            "slots": self._default_slots(),
        }
        if os.path.exists(self.config_path):
            try:
                with open(self.config_path, "r") as f:
                    user_config = json.load(f)
                if isinstance(user_config, dict):
                    if isinstance(user_config.get("slots"), dict):
                        for key, val in user_config["slots"].items():
                            if key in default_config["slots"] and isinstance(val, dict):
                                default_config["slots"][key].update(val)
                        user_config = {k: v for k, v in user_config.items() if k != "slots"}
                    default_config.update(user_config)
            except Exception as e:
                print(f"Failed to load {self.kind} config: {e}")
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
        if any(t.is_alive() for t in self.active_threads.values()):
            return {"success": False, "error": "Party is already running!"}
        self.save_config(config)

        slots = config.get("slots", {})
        server = config.get("server", self.DEFAULT_SERVER)
        room_number = int(config.get("room_number", 9099) or 9099)

        for s_id in self.SLOT_IDS:
            slot = slots.get(s_id, {})
            if not slot.get("username") or not slot.get("password"):
                return {"success": False, "error": "Fill username and password for all 4 slots."}
            if self.kind == "speaker" and not slot.get("role"):
                return {"success": False, "error": "Pick a role for all 4 slots."}

        # One run id for the whole party, set before the threads start, so the
        # in-process panes share capture_logs/ultra/<run>/party like the .bat.
        os.environ.setdefault("AQW_TELEMETRY", "1")
        if not os.environ.get("AQW_RUN_ID"):
            os.environ["AQW_RUN_ID"] = time.strftime("%Y%m%d_%H%M%S")

        # Fresh "done" markers so a previous run cannot look finished already.
        try:
            from bot.ultra import party as ultra_party
            if ultra_party.enabled():
                ultra_party.clear_done(f"ultra_{self.kind}")
                ultra_party.clear_abort(f"ultra_{self.kind}")
        except Exception:
            pass

        leader = slots["slot1"]["username"]
        slaves = [slots[s]["username"] for s in ("slot2", "slot3", "slot4")]

        self.active_threads = {}
        self.start_time = time.time()
        for i, s_id in enumerate(self.SLOT_IDS, start=1):
            slot = slots[s_id]
            self.active_threads[s_id] = UltraBotThread(
                slot=i,
                kind=self.kind,
                username=slot["username"],
                password=slot["password"],
                server=server,
                room_number=room_number,
                leader=leader,
                slaves=slaves,
                role=(slot.get("role") or "") if self.kind == "speaker" else "",
                callback=(lambda name, msg, k=self.kind: self.handle_log(name, msg)),
                missing_policy=config.get("missing_policy", "stop"),
            )
        for thread in self.active_threads.values():
            thread.start()
        self._party_config = config
        self._manual_stop = False
        self._start_watchdog()
        return {"success": True}

    def stop_party(self, user_triggered=False):
        if user_triggered:
            self._manual_stop = True
        threads = list(self.active_threads.values())
        self.active_threads = {}
        self.start_time = None
        for thread in threads:
            try:
                if thread.bot_instance:
                    thread.bot_instance.stop_bot()
            except Exception as e:
                print(f"Failed to stop ultra pane: {e}")
        return {"success": True}

    def get_status(self):
        slots = {}
        for s_id, thread in list(self.active_threads.items()):
            slots[s_id] = self._slot_status(thread)
        return {
            "running": any(v.get("running") for v in slots.values()),
            "slots": slots,
        }

    @staticmethod
    def _slot_status(thread):
        b = thread.bot_instance
        if not (thread.is_alive() and b):
            return {"running": False, "username": thread.username, "role": thread.role}
        p = b.player
        try:
            return {
                "running": True,
                "is_connected": b.is_client_connected,
                "username": thread.username,
                "role": thread.role,
                "hp": p.CURRENT_HP,
                "max_hp": p.MAX_HP,
                "mp": p.MANA,
                "max_mp": p.MAX_MP,
                "is_dead": p.ISDEAD,
                "map": getattr(b, "strMapName", "") or "-",
                "cell": p.CELL,
                "pad": p.PAD,
            }
        except Exception as e:
            return {"running": True, "username": thread.username, "role": thread.role, "error": str(e)}


class UltraDailyApi(UltraApi):
    kind = "daily"
    #: The four bosses DailyUltra actually runs (bot/ultra/daily.py).
    BOSSES = ("tyndarius", "engineer", "ezrajal", "warden")

    def __init__(self):
        super().__init__("ultra_daily_config.json")

    def _default_role(self, slot):
        return str(slot)  # daily "role" is just the loadout slot (1-4)

    def get_slots(self):
        """Per loadout slot, the class + enhancements each boss will equip."""
        from bot.ultra import config as ultra_config
        out = {}
        for slot in (1, 2, 3, 4):
            per_boss = {}
            for boss in self.BOSSES:
                loadout = ultra_config.LOADOUTS.get(boss, {}).get(slot)
                if loadout:
                    per_boss[boss] = {
                        "cls": loadout.cls,
                        "weapon": _spec_name(loadout.weapon),
                        "helm": _spec_name(loadout.helm),
                        "cape": _spec_name(loadout.cape),
                        "scroll": loadout.scroll or "",
                    }
            out[str(slot)] = per_boss
        return out


class UltraSpeakerApi(UltraApi):
    kind = "speaker"
    #: Must match bot.ultra.config.SOLO_ROLES order -- pane n wears role n.
    SOLO_ROLES = ("Legion Revenant", "ArchPaladin", "Lord Of Order", "Verus DoomKnight")

    def __init__(self):
        super().__init__("ultra_speaker_config.json")

    def _default_role(self, slot):
        return self.SOLO_ROLES[slot - 1] if 1 <= slot <= len(self.SOLO_ROLES) else ""

    def get_roles(self):
        """Each role with the class + enhancements SOLO_LOADOUTS pairs with it."""
        from bot.ultra import config as ultra_config
        out = []
        for role in self.SOLO_ROLES:
            loadout = ultra_config.SOLO_LOADOUTS.get(role.lower())
            out.append({
                "role": role,
                "cls": loadout.cls if loadout else "",
                "weapon": _spec_name(loadout.weapon) if loadout else "",
                "helm": _spec_name(loadout.helm) if loadout else "",
                "cape": _spec_name(loadout.cape) if loadout else "",
                "scroll": (loadout.scroll if loadout else "") or "",
            })
        return out


class WeeklyDoomApi:
    """Weekly Doom menu: one manual account, or several picked from players.json.

    Each selected account runs the same command queue (``bot_cmds/weekly_doom.py``)
    in its own thread, concurrently.
    """

    def __init__(self):
        self.active_threads = {}
        self._window = None
        if getattr(sys, 'frozen', False):
            config_dir = os.path.expanduser("~/.aqw_bot")
            os.makedirs(config_dir, exist_ok=True)
            self.config_path = os.path.join(config_dir, "weekly_doom_config.json")
        else:
            self.config_path = os.path.join(get_project_root(), "weekly_doom_config.json")

    def set_window(self, window):
        self._window = window

    def handle_log(self, username, message):
        html_msg = ansi_to_html(message)
        _log_flusher.push(
            f"if(window.addSlaveLog) window.addSlaveLog({json.dumps(username or 'System')}, "
            f"{json.dumps(html_msg)}, 'weekly_doom');"
        )

    def load_config(self):
        default_config = {"server": "Swordhaven (EU)", "room_number": 9099}
        if os.path.exists(self.config_path):
            try:
                with open(self.config_path, "r") as f:
                    user_config = json.load(f)
                if isinstance(user_config, dict):
                    default_config.update(user_config)
            except Exception as e:
                print(f"Failed to load weekly doom config: {e}")
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

    def start_bots(self, config):
        self.save_config({"server": config.get("server", "Swordhaven (EU)"),
                          "room_number": config.get("room_number", 9099)})
        server = config.get("server", "Swordhaven (EU)")
        room_number = int(config.get("room_number", 9099) or 9099)
        started, errors = 0, []
        for acc in config.get("accounts", []):
            username = (acc.get("username") or "").strip()
            if not username or not acc.get("password"):
                continue
            existing = self.active_threads.get(username)
            if existing and existing.is_alive():
                continue
            try:
                thread = WeeklyDoomThread(
                    username, acc.get("password", ""), server, room_number,
                    lambda name, msg: self.handle_log(name, msg))
                thread.start()
                self.active_threads[username] = thread
                started += 1
            except Exception as e:
                errors.append(f"{username}: {e}")
        if started == 0 and not errors:
            return {"success": False, "error": "Pick at least one account (username + password)."}
        return {"success": True, "started": started, "errors": errors}

    def stop_bots(self):
        threads = list(self.active_threads.values())
        self.active_threads = {}
        for thread in threads:
            try:
                if thread.bot_instance:
                    thread.bot_instance.stop_bot()
            except Exception as e:
                print(f"Failed to stop weekly doom: {e}")
        return {"success": True}

    def get_statuses(self):
        out = []
        for username, thread in list(self.active_threads.items()):
            running = thread.is_alive()
            status = {"username": username, "running": running}
            if running and thread.bot_instance:
                b = thread.bot_instance
                p = b.player
                try:
                    status.update({
                        "is_connected": b.is_client_connected,
                        "map": getattr(b, "strMapName", "") or "-",
                        "cell": p.CELL, "pad": p.PAD,
                        "hp": p.CURRENT_HP, "max_hp": p.MAX_HP,
                        "mp": p.MANA, "max_mp": p.MAX_MP,
                        "is_dead": p.ISDEAD,
                    })
                except Exception as e:
                    status["error"] = str(e)
            out.append(status)
        return out


class CombinedApi:
    def __init__(self, aqw_api, slavery_api, temple_api, eclipse_api,
                 players_api=None, ultra_daily_api=None, ultra_speaker_api=None,
                 weekly_doom_api=None):
        self._aqw_api = aqw_api
        self._slavery_api = slavery_api
        self._temple_api = temple_api
        self._eclipse_api = eclipse_api
        self._players_api = players_api
        self._ultra_daily_api = ultra_daily_api
        self._ultra_speaker_api = ultra_speaker_api
        self._weekly_doom_api = weekly_doom_api
        self._window = None
        #: Which menu is on screen; used to route unregistered-thread logs.
        self._active_tab = "dashboard"
        
        try:
            import psutil
            self._process = psutil.Process(os.getpid())
            self._process.cpu_percent(interval=None)
        except Exception:
            self._process = None

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
        self._window = window
        _log_flusher.set_window(window)
        self._aqw_api.set_window(window)
        self._slavery_api.set_window(window)
        self._temple_api.set_window(window)
        self._eclipse_api.set_window(window)
        if self._players_api:
            self._players_api.set_window(window)
        if self._ultra_daily_api:
            self._ultra_daily_api.set_window(window)
        if self._ultra_speaker_api:
            self._ultra_speaker_api.set_window(window)
        if self._weekly_doom_api:
            self._weekly_doom_api.set_window(window)

    def set_active_tab(self, tab):
        """Remember which menu is on screen, for unregistered-thread log routing."""
        self._active_tab = tab or "dashboard"
        return {"success": True}

    def route_system_log(self, message):
        """Forward a log line from an unregistered thread to the active menu."""
        tab = getattr(self, "_active_tab", "dashboard")
        try:
            if tab == "slavery":
                self._slavery_api.handle_slave_log("System", message)
            elif tab == "temple":
                self._temple_api.handle_slave_log("System", message)
            elif tab == "eclipse":
                self._eclipse_api.handle_slave_log("System", message)
            elif tab == "aqw":
                self._aqw_api.handle_log(message)
            elif tab == "weekly_doom" and self._weekly_doom_api:
                self._weekly_doom_api.handle_log("System", message)
            elif tab == "ultra_daily" and self._ultra_daily_api:
                self._ultra_daily_api.handle_log("System", message)
            elif tab == "ultra_speaker" and self._ultra_speaker_api:
                self._ultra_speaker_api.handle_log("System", message)
        except Exception:
            pass

    # --- Config Player (shared player list) ---
    def players_list(self):
        return self._players_api.list_players() if self._players_api else []

    def players_add(self, user, password):
        return self._players_api.add_player(user, password)

    def players_update(self, index, user, password):
        return self._players_api.update_player(index, user, password)

    def players_delete(self, index):
        return self._players_api.delete_player(index)

    # --- NAMESPACED API FOR ULTRA DAILY / SPEAKER ---
    def ultra_daily_load_config(self):
        return self._ultra_daily_api.load_config()

    def ultra_daily_save_config(self, config):
        return self._ultra_daily_api.save_config(config)

    def ultra_daily_reset_config(self):
        return self._ultra_daily_api.reset_config()

    def ultra_daily_get_status(self):
        return self._ultra_daily_api.get_status()

    def ultra_daily_get_slots(self):
        return self._ultra_daily_api.get_slots()

    def ultra_daily_start_party(self, config):
        return self._ultra_daily_api.start_party(config)

    def ultra_daily_stop_party(self):
        return self._ultra_daily_api.stop_party(user_triggered=True)

    def ultra_speaker_load_config(self):
        return self._ultra_speaker_api.load_config()

    def ultra_speaker_get_roles(self):
        return self._ultra_speaker_api.get_roles()

    def ultra_speaker_save_config(self, config):
        return self._ultra_speaker_api.save_config(config)

    def ultra_speaker_reset_config(self):
        return self._ultra_speaker_api.reset_config()

    def ultra_speaker_get_status(self):
        return self._ultra_speaker_api.get_status()

    def ultra_speaker_start_party(self, config):
        return self._ultra_speaker_api.start_party(config)

    def ultra_speaker_stop_party(self):
        return self._ultra_speaker_api.stop_party(user_triggered=True)

    # --- NAMESPACED API FOR WEEKLY DOOM ---
    def weekly_doom_load_config(self):
        return self._weekly_doom_api.load_config()

    def weekly_doom_save_config(self, config):
        return self._weekly_doom_api.save_config(config)

    def weekly_doom_start_bots(self, config):
        return self._weekly_doom_api.start_bots(config)

    def weekly_doom_stop_bots(self):
        return self._weekly_doom_api.stop_bots()

    def weekly_doom_get_statuses(self):
        return self._weekly_doom_api.get_statuses()

    # --- NAMESPACED API FOR AQW BOT (IFRAME) ---
    def aqw_load_config(self):
        return self._aqw_api.load_config()

    def aqw_save_config(self, config):
        return self._aqw_api.save_config(config)

    def aqw_get_status(self):
        return self._aqw_api.get_status()

    def aqw_get_statuses(self):
        return self._aqw_api.get_statuses()

    def aqw_get_items(self, key):
        return self._aqw_api.get_items(key)

    def aqw_select_script(self):
        return self._aqw_api.select_script()

    def aqw_start_bots(self, config):
        return self._aqw_api.start_bots(config)

    def aqw_start_one(self, acc):
        return self._aqw_api.start_one(acc)

    def aqw_stop_one(self, key):
        return self._aqw_api.stop_one(key)

    def aqw_stop_bots(self):
        return self._aqw_api.stop_bots()

    # --- NAMESPACED API FOR SLAVERY BOT (IFRAME) ---
    def slavery_load_config(self):
        return self._slavery_api.load_config()

    def slavery_save_config(self, config):
        return self._slavery_api.save_config(config)

    def slavery_get_status(self):
        return self._slavery_api.get_status()

    def start_slaves(self, config, usernames):
        return self._slavery_api.start_slaves(config, usernames)

    def stop_slaves(self):
        return self._slavery_api.stop_slaves()

    def toggle_pause_slaves(self, pause_state):
        return self._slavery_api.toggle_pause_slaves(pause_state)

    def update_slave_taunter(self, username, taunter_state):
        return self._slavery_api.update_slave_taunter(username, taunter_state)

    def get_version(self):
        return self._slavery_api.get_version()

    # --- NAMESPACED API FOR TEMPLE BOT (IFRAME) ---
    def temple_load_config(self):
        return self._temple_api.load_config()

    def temple_save_config(self, config):
        return self._temple_api.save_config(config)

    def temple_get_status(self):
        return self._temple_api.get_status()

    def temple_reset_config(self):
        return self._temple_api.reset_config()

    def temple_start_party(self, config):
        return self._temple_api.start_party(config)

    def temple_stop_party(self):
        return self._temple_api.stop_party()

    # --- NAMESPACED API FOR ECLIPSE BOT (IFRAME) ---
    def eclipse_load_config(self):
        return self._eclipse_api.load_config()

    def eclipse_save_config(self, config):
        return self._eclipse_api.save_config(config)

    def eclipse_get_status(self):
        return self._eclipse_api.get_status()

    def eclipse_reset_config(self):
        return self._eclipse_api.reset_config()

    def eclipse_start_party(self, config):
        return self._eclipse_api.start_party(config)

    def eclipse_stop_party(self):
        return self._eclipse_api.stop_party()

    def eclipse_toggle_pause(self, pause_state):
        return self._eclipse_api.toggle_pause(pause_state)

    def validate_password(self, password):
        return self._eclipse_api.validate_password(password)

    def toggle_debug(self):
        if self._window:
            try:
                self._window.toggle_developer_tools()
                return {"success": True}
            except Exception as e:
                print(f"Error toggling developer tools: {e}")
                return {"success": False, "error": str(e)}

    def stop_all(self):
        try:
            self.aqw_stop_bots()
        except Exception:
            pass
        try:
            self.stop_slaves()
        except Exception:
            pass
        try:
            self.temple_stop_party()
        except Exception:
            pass
        try:
            self.eclipse_stop_party()
        except Exception:
            pass
        try:
            if self._ultra_daily_api:
                self._ultra_daily_api.stop_party(user_triggered=True)
        except Exception:
            pass
        try:
            if self._ultra_speaker_api:
                self._ultra_speaker_api.stop_party(user_triggered=True)
        except Exception:
            pass
        try:
            if self._weekly_doom_api:
                self._weekly_doom_api.stop_bots()
        except Exception:
            pass

    # --- Dashboard Hub Status ---
    def get_hub_status(self):
        # 1. AQW Bot (multi-account)
        aqw_status = {"running": False, "accounts": []}
        try:
            aqw_status = self._aqw_api.get_status()
        except Exception:
            aqw_status = {"running": False, "accounts": []}
        
        # 2. Slavery Bot
        slavery_status = {"running": False}
        active_slaves = [username for username, thread in self._slavery_api.active_threads.items() if thread.is_alive()]
        if active_slaves:
            slavery_status = {
                "running": True,
                "count": len(active_slaves),
                "slaves": active_slaves
            }

        # 3. Temple Bot
        temple_status = {"running": False}
        active_temple = [s_id for s_id, thread in self._temple_api.active_threads.items() if thread.is_alive()]
        if active_temple:
            members = [thread.username for thread in self._temple_api.active_threads.values() if thread.is_alive()]
            elapsed = 0
            if getattr(self._temple_api, "start_time", None):
                elapsed = int(time.time() - self._temple_api.start_time)
            temple_status = {
                "running": True,
                "count": len(active_temple),
                "slots": active_temple,
                "members": members,
                "time_running": elapsed,
                "cleared_count": getattr(self._temple_api, "cleared_count", 0)
            }
        else:
            self._temple_api.start_time = None

        # 4. Eclipse Bot
        eclipse_status = {"running": False}
        active_eclipse = [s_id for s_id, thread in self._eclipse_api.active_threads.items() if thread.is_alive()]
        if active_eclipse:
            members = [thread.username for thread in self._eclipse_api.active_threads.values() if thread.is_alive()]
            elapsed = 0
            if getattr(self._eclipse_api, "start_time", None):
                elapsed = int(time.time() - self._eclipse_api.start_time)
            eclipse_status = {
                "running": True,
                "count": len(active_eclipse),
                "slots": active_eclipse,
                "members": members,
                "time_running": elapsed,
                "cleared_count": getattr(self._eclipse_api, "cleared_count", 0)
            }
        else:
            self._eclipse_api.start_time = None

        mem_mb = 0.0
        cpu_pct = 0.0
        if hasattr(self, "_process") and self._process:
            try:
                mem_mb = round(self._process.memory_info().rss / (1024 * 1024), 1)
                cpu_pct = round(self._process.cpu_percent(interval=None), 1)
            except Exception:
                pass

        ultra_daily_status = {"running": False}
        try:
            if self._ultra_daily_api:
                ultra_daily_status = self._ultra_daily_api.get_status()
        except Exception:
            ultra_daily_status = {"running": False}

        ultra_speaker_status = {"running": False}
        try:
            if self._ultra_speaker_api:
                ultra_speaker_status = self._ultra_speaker_api.get_status()
        except Exception:
            ultra_speaker_status = {"running": False}

        return {
            "aqw": aqw_status,
            "slavery": slavery_status,
            "temple": temple_status,
            "eclipse": eclipse_status,
            "ultra_daily": ultra_daily_status,
            "ultra_speaker": ultra_speaker_status,
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
                            get_statuses: () => topApi.aqw_get_statuses(),
                            get_items: (k) => topApi.aqw_get_items(k),
                            select_script: () => topApi.aqw_select_script(),
                            start_bots: (cfg) => topApi.aqw_start_bots(cfg),
                            start_one: (acc) => topApi.aqw_start_one(acc),
                            stop_one: (k) => topApi.aqw_stop_one(k),
                            stop_bots: () => topApi.aqw_stop_bots(),
                            list_players: () => topApi.players_list()
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
                            get_version: () => topApi.get_version(),
                            list_players: () => topApi.players_list()
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
                            stop_party: () => topApi.temple_stop_party(),
                            list_players: () => topApi.players_list()
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
                            toggle_pause: (p) => topApi.eclipse_toggle_pause(p),
                            validate_password: (pwd) => topApi.validate_password(pwd),
                            list_players: () => topApi.players_list()
                        }
                    };
                }
            })();
            </script>
            """
            
        elif bot_type == "players":
            bridge_js = """
            <script>
            (function() {
                if (window.parent && window.parent.pywebview) {
                    const topApi = window.parent.pywebview.api;
                    window.pywebview = {
                        api: {
                            list_players: () => topApi.players_list(),
                            add_player: (u, p) => topApi.players_add(u, p),
                            update_player: (i, u, p) => topApi.players_update(i, u, p),
                            delete_player: (i) => topApi.players_delete(i)
                        }
                    };
                }
            })();
            </script>
            """
        elif bot_type == "ultra_daily":
            bridge_js = """
            <script>
            (function() {
                if (window.parent && window.parent.pywebview) {
                    const topApi = window.parent.pywebview.api;
                    window.pywebview = {
                        api: {
                            load_config: () => topApi.ultra_daily_load_config(),
                            save_config: (cfg) => topApi.ultra_daily_save_config(cfg),
                            reset_config: () => topApi.ultra_daily_reset_config(),
                            get_status: () => topApi.ultra_daily_get_status(),
                            start_party: (cfg) => topApi.ultra_daily_start_party(cfg),
                            stop_party: () => topApi.ultra_daily_stop_party(),
                            get_slots: () => topApi.ultra_daily_get_slots(),
                            list_players: () => topApi.players_list()
                        }
                    };
                }
            })();
            </script>
            """
        elif bot_type == "ultra_speaker":
            bridge_js = """
            <script>
            (function() {
                if (window.parent && window.parent.pywebview) {
                    const topApi = window.parent.pywebview.api;
                    window.pywebview = {
                        api: {
                            load_config: () => topApi.ultra_speaker_load_config(),
                            save_config: (cfg) => topApi.ultra_speaker_save_config(cfg),
                            reset_config: () => topApi.ultra_speaker_reset_config(),
                            get_status: () => topApi.ultra_speaker_get_status(),
                            get_roles: () => topApi.ultra_speaker_get_roles(),
                            start_party: (cfg) => topApi.ultra_speaker_start_party(cfg),
                            stop_party: () => topApi.ultra_speaker_stop_party(),
                            list_players: () => topApi.players_list()
                        }
                    };
                }
            })();
            </script>
            """

        elif bot_type == "weekly_doom":
            bridge_js = """
            <script>
            (function() {
                if (window.parent && window.parent.pywebview) {
                    const topApi = window.parent.pywebview.api;
                    window.pywebview = {
                        api: {
                            load_config: () => topApi.weekly_doom_load_config(),
                            save_config: (cfg) => topApi.weekly_doom_save_config(cfg),
                            start_bots: (cfg) => topApi.weekly_doom_start_bots(cfg),
                            stop_bots: () => topApi.weekly_doom_stop_bots(),
                            get_statuses: () => topApi.weekly_doom_get_statuses(),
                            list_players: () => topApi.players_list()
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

def start_local_server(web_dashboard_dir, sub_apps):
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

    @app.route('/players_dropdown.js')
    def serve_players_dropdown():
        return static_file('players_dropdown.js', root=web_dashboard_dir)

    @app.route('/cfg.css')
    def serve_cfg_css():
        return static_file('cfg.css', root=web_dashboard_dir)

    @app.route(r'/<filename:re:[^/]+\.(png|jpg|jpeg|gif|ico|svg)>')
    def serve_dashboard_images(filename):
        return static_file(filename, root=web_dashboard_dir)

    # Every sub-app (aqw, slavery, temple, eclipse, players, ultra_daily,
    # ultra_speaker) is served at /<name>/ with the parent bridge injected.
    def _register(name, root):
        def index_view(**_):
            return serve_injected_html(os.path.join(root, 'index.html'), name)

        def files_view(path):
            return static_file(path, root=root)

        app.route(f'/{name}', callback=index_view)
        app.route(f'/{name}/', callback=index_view)
        app.route(f'/{name}/<path:path>', callback=files_view)

    for _name, _root in sub_apps.items():
        _register(_name, _root)

    port = find_free_port()
    t = threading.Thread(target=lambda: app.run(host='127.0.0.1', port=port, quiet=True))
    t.daemon = True
    t.start()
    return f"http://127.0.0.1:{port}"

def cleanup_orphaned_processes():
    """
    Terminates any zombie / orphaned instances of AQW_Bot_Hub or msedgewebview2 processes
    locking the webview UserDataFolder from previous unfinished sessions.
    """
    current_pid = os.getpid()
    protected_pids = {current_pid}
    try:
        import psutil
        curr = psutil.Process(current_pid)
        for parent in curr.parents():
            protected_pids.add(parent.pid)
        for child in curr.children(recursive=True):
            protected_pids.add(child.pid)
    except Exception:
        if hasattr(os, 'getppid'):
            protected_pids.add(os.getppid())

    try:
        import psutil
        for proc in psutil.process_iter(['pid', 'name', 'cmdline']):
            try:
                if proc.info['pid'] in protected_pids:
                    continue
                pname = (proc.info['name'] or '').lower()
                cmdline = ' '.join(proc.info['cmdline'] or []).lower()
                
                # Check for orphaned AQW_Bot_Hub.exe from a previous closed session
                if 'aqw_bot_hub' in pname:
                    print(f"Cleaning up orphaned hub process PID {proc.info['pid']}...")
                    try:
                        proc.kill()
                    except Exception:
                        pass
                # Check for orphaned msedgewebview2 attached to our specific ~/.aqw_bot/webview directory
                elif 'msedgewebview2' in pname and ('.aqw_bot' in cmdline or 'aqw' in cmdline):
                    print(f"Cleaning up orphaned webview process PID {proc.info['pid']}...")
                    try:
                        proc.kill()
                    except Exception:
                        pass
            except (psutil.NoSuchProcess, psutil.AccessDenied):
                pass
    except Exception as e:
        print(f"Process cleanup notice: {e}")

# --- Launcher (Run) ---
def run_gui():
    # Clean up any leftover zombie processes from previous sessions
    cleanup_orphaned_processes()

    # Verify WebView2 Runtime availability on Windows before launching
    if sys.platform == "win32":
        try:
            from webview.platforms import winforms
            if not winforms._is_chromium():
                import ctypes
                msg = (
                    "Aplikasi AQW Multi-Bot Hub memerlukan 'Microsoft Edge WebView2 Runtime' agar dapat berjalan di Windows.\n\n"
                    "Di perangkat ini WebView2 Runtime belum terdeteksi. Silakan unduh dan pasang WebView2 Runtime dari situs resmi Microsoft:\n"
                    "https://developer.microsoft.com/en-us/microsoft-edge/webview2/\n\n"
                    "Klik OK untuk membuka halaman unduhan resmi Microsoft."
                )
                res = ctypes.windll.user32.MessageBoxW(0, msg, "Microsoft Edge WebView2 Diperlukan", 0x30 | 0x1)
                if res == 1:
                    import webbrowser
                    webbrowser.open("https://go.microsoft.com/fwlink/p/?LinkId=2124703")
                sys.exit(1)
        except Exception as e:
            pass

    aqw_api = AqwSoloApi()
    slavery_api = SlaveryApi()
    temple_api = TempleApi()
    eclipse_api = EclipseApi()
    players_api = PlayersApi()
    ultra_daily_api = UltraDailyApi()
    ultra_speaker_api = UltraSpeakerApi()
    weekly_doom_api = WeeklyDoomApi()

    combined_api = CombinedApi(aqw_api, slavery_api, temple_api, eclipse_api,
                               players_api, ultra_daily_api, ultra_speaker_api,
                               weekly_doom_api)
    
    unified_redirector_out.combined_api = combined_api
    unified_redirector_err.combined_api = combined_api

    if getattr(sys, 'frozen', False):
        base_path = getattr(sys, '_MEIPASS', '')
        web_dashboard_dir = os.path.join(base_path, 'web_dashboard')
    else:
        web_dashboard_dir = os.path.join(project_root, 'app', 'web_dashboard')

    sub_apps = {
        name: os.path.join(web_dashboard_dir, name)
        for name in ('aqw', 'slavery', 'temple', 'eclipse',
                     'players', 'ultra_daily', 'ultra_speaker', 'weekly_doom')
    }

    print(f"Loading GUI assets from: {web_dashboard_dir}")
    url = start_local_server(web_dashboard_dir, sub_apps)
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
    
    def on_closed():
        print("Application closing, stopping all bot tasks and background processes...")
        try:
            combined_api.stop_all()
        except Exception:
            pass
        try:
            import psutil
            current_process = psutil.Process(os.getpid())
            for child in current_process.children(recursive=True):
                try:
                    child.kill()
                except Exception:
                    pass
        except Exception:
            pass
        os._exit(0)

    window.events.closed += on_closed

    try:
        webview.start(debug=True, private_mode=False, storage_path=storage_path)
    finally:
        on_closed()

# --- Icon Generator ---
def generate_icons():
    system = platform.system()
    png_path = os.path.join(project_root, "app", "web_dashboard", "temple_icon.png")
    if not os.path.exists(png_path):
        return
        
    print("Generating application icons from temple_icon.png...")
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

# --- Packager (Build macOS App Bundle) ---
def build_app():
    app_name = "AQW_Bot_Hub"
    entrypoint = os.path.join("app", "build_hub_app.py")
    
    generate_icons()
    print("Building AQW Bot Hub macOS app bundle (.app)...")
    
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
        ("bot", "bot"),
        ("commands", "commands"),
        ("abstracts", "abstracts"),
        ("templates", "templates"),
        ("bot_cmds", "bot_cmds")
    ]
    
    icon_file = "app.icns"
    
    pyinstaller_bin = "pyinstaller"
    venv_pyinstaller = os.path.join("venv", "bin", "pyinstaller")
    if os.path.exists(venv_pyinstaller):
        pyinstaller_bin = venv_pyinstaller

    cmd = [
        pyinstaller_bin,
        f"--name={app_name}",
        "--noconfirm",
        "--clean",
        "--windowed",
        "--collect-all=webview",
        "--hidden-import=psutil",
        "--hidden-import=bottle",
        "--hidden-import=webview",
        "--hidden-import=commands",
        "--hidden-import=abstracts",
        "--hidden-import=templates",
        "--hidden-import=bot_cmds",
        "--hidden-import=handlers",
        "--hidden-import=model",
        "--hidden-import=core",
        f"--paths={project_root}"
    ]
    
    for src, dest in data_folders:
        cmd.append(f"--add-data={src}:{dest}")
        
    if os.path.exists(icon_file):
        cmd.append(f"--icon={icon_file}")
    else:
        print(f"Warning: Icon file '{icon_file}' not found. Building without icon.")
        
    cmd.append(entrypoint)
    
    print("\nExecuting command:\n" + " ".join(cmd) + "\n")
    result = subprocess.run(cmd)
    
    if result.returncode == 0:
        print("\n" + "="*60)
        output_file_desc = os.path.join("dist", f"{app_name}.app")
        print("SUCCESS! macOS App bundle built successfully.")
        print(f"You can find the standalone client at: {os.path.abspath(output_file_desc)}")
        print("="*60 + "\n")
    else:
        print("\nERROR! PyInstaller build failed.")
        sys.exit(result.returncode)

# --- Main Routing Entrypoint ---
def main():
    try:
        if len(sys.argv) > 1 and sys.argv[1] in ("build", "--build"):
            build_app()
        else:
            run_gui()
    except Exception as e:
        import traceback
        err_msg = traceback.format_exc()
        print(f"[AQW Hub] Critical startup exception:\n{err_msg}")
        try:
            log_dir = os.path.expanduser("~/.aqw_bot")
            os.makedirs(log_dir, exist_ok=True)
            with open(os.path.join(log_dir, "crash.log"), "w", encoding="utf-8") as f:
                f.write(err_msg)
        except Exception:
            pass
        sys.exit(1)

if __name__ == "__main__":
    main()
