import os
import sys
import time
import json
import asyncio
import threading
from typing import Dict, Any, Optional

from core.bot import Bot
from core.command import Command
from bot.general.registry import REGISTRY, get_submodules_list

class GeneralBotManager:
    def __init__(self, redirector_out=None, redirector_err=None, get_config_dir_fn=None):
        self.redirector_out = redirector_out
        self.redirector_err = redirector_err
        self.get_config_dir_fn = get_config_dir_fn

        self.runner_thread: Optional[threading.Thread] = None
        self.current_bot: Optional[Bot] = None
        self.is_running = False
        self.stop_requested = False
        self.start_time: Optional[float] = None

        self.current_username = ""
        self.current_sub_module = "lr"
        self.current_task = "spellscroll"
        self.current_target_qty = 20
        self.current_status = "Idle"
        self.current_message = ""
        self.tracked_item = "Revenant's Spellscroll"

    def get_config_path(self) -> str:
        if self.get_config_dir_fn:
            base = self.get_config_dir_fn()
        else:
            base = os.path.expanduser("~/.aqw_bot")
        return os.path.join(base, "general_bot_config.json")

    def load_config(self) -> Dict[str, Any]:
        default_config = {
            "server": "Alteon",
            "room_number": 9099,
            "username": "",
            "password": "",
            "sub_module": "lr",
            "task": "spellscroll",
            "target_qty": 20,
            "solo_class": "Void Highlord",
            "farm_class": "Legion Revenant"
        }
        cfg_path = self.get_config_path()
        if os.path.exists(cfg_path):
            try:
                with open(cfg_path, "r") as f:
                    user_conf = json.load(f)
                    default_config.update(user_conf)
            except Exception as e:
                print(f"[GeneralBotManager] load_config error: {e}")
        return default_config

    def save_config(self, config: Dict[str, Any]) -> Dict[str, Any]:
        cfg_path = self.get_config_path()
        try:
            with open(cfg_path, "w") as f:
                json.dump(config, f, indent=4)
            return {"success": True}
        except Exception as e:
            return {"success": False, "error": str(e)}

    def reset_config(self) -> Dict[str, Any]:
        cfg_path = self.get_config_path()
        if os.path.exists(cfg_path):
            try:
                os.remove(cfg_path)
            except Exception:
                pass
        return self.load_config()

    def get_submodules(self) -> Dict[str, Any]:
        return {
            "success": True,
            "submodules": get_submodules_list()
        }

    def start(self, config: Dict[str, Any]) -> Dict[str, Any]:
        if self.is_running:
            return {"success": False, "error": "General Bot is already running"}

        username = config.get("username", "").strip()
        password = config.get("password", "").strip()
        server = config.get("server", "Alteon").strip()
        room_number = int(config.get("room_number", 9099))
        sub_module_id = config.get("sub_module", "lr").strip()
        task_id = config.get("task", "spellscroll").strip()
        target_qty = int(config.get("target_qty", 20))
        solo_class = config.get("solo_class", "Void Highlord").strip()
        farm_class = config.get("farm_class", "Legion Revenant").strip()

        if not username:
            return {"success": False, "error": "Username is required"}
        if not password:
            return {"success": False, "error": "Password is required"}

        submodule = REGISTRY.get(sub_module_id)
        if not submodule:
            return {"success": False, "error": f"Unknown sub-module: {sub_module_id}"}

        task = submodule.get_task(task_id)
        if not task:
            return {"success": False, "error": f"Unknown task: {task_id} in sub-module {sub_module_id}"}

        self.save_config(config)

        self.is_running = True
        self.stop_requested = False
        self.start_time = time.time()
        self.current_username = username
        self.current_sub_module = sub_module_id
        self.current_task = task_id
        self.current_target_qty = target_qty
        self.current_status = "Starting"
        self.current_message = f"Starting {submodule.name} ({task.name})..."
        self.tracked_item = task.tracked_item

        self.runner_thread = threading.Thread(
            target=self._run_bot,
            args=(server, room_number, username, password, sub_module_id, task_id, target_qty, solo_class, farm_class),
            daemon=True
        )
        self.runner_thread.start()
        return {"success": True}

    def stop(self) -> Dict[str, Any]:
        self.stop_requested = True
        self.current_status = "Stopping"
        self.current_message = "Stop requested by user..."
        if self.current_bot:
            try:
                self.current_bot.stop_bot(user_triggered=True)
            except Exception:
                pass
        return {"success": True}

    def reset_state(self) -> Dict[str, Any]:
        self.stop_requested = True
        self.is_running = False
        self.current_status = "Idle"
        self.current_message = "State reset by user"
        self.start_time = 0.0
        if self.current_bot:
            try:
                self.current_bot.stop_bot(user_triggered=True)
            except Exception:
                pass
            try:
                if hasattr(self.current_bot, "disconnect"):
                    self.current_bot.disconnect()
            except Exception:
                pass
            self.current_bot = None
        print(f"=== [General Bot] State reset by user ===")
        return {"success": True}

    def get_status(self) -> Dict[str, Any]:
        time_running = int(time.time() - self.start_time) if self.start_time and self.is_running else 0
        b = self.current_bot
        p = getattr(b, "player", None) if b else None

        current_qty = 0
        if p and hasattr(p, "get_item_inventory") and self.tracked_item:
            item_inv = p.get_item_inventory(self.tracked_item)
            if item_inv:
                current_qty = getattr(item_inv, "qty", 0)
        elif not self.tracked_item and b:
            current_qty = getattr(b, "general_turn_in_count", 0)

        sub_info = REGISTRY.get(self.current_sub_module)
        sub_name = sub_info.name if sub_info else self.current_sub_module
        task_info = sub_info.get_task(self.current_task) if sub_info else None
        task_name = task_info.name if task_info else self.current_task

        from datetime import datetime
        now = datetime.now()
        cooldowns = {0: 0.0, 1: 0.0, 2: 0.0, 3: 0.0, 4: 0.0, 5: 0.0}
        if p and hasattr(p, "SKILLS") and isinstance(p.SKILLS, list):
            for i in range(0, 6):
                if i < len(p.SKILLS):
                    skill_data = p.SKILLS[i]
                    if isinstance(skill_data, dict):
                        next_use = skill_data.get("nextUse")
                        if next_use and next_use > now:
                            cooldowns[i] = round((next_use - now).total_seconds(), 1)

        return {
            "running": self.is_running,
            "is_connected": getattr(b, "is_client_connected", False) if b else False,
            "username": self.current_username,
            "sub_module": self.current_sub_module,
            "sub_module_name": sub_name,
            "task": self.current_task,
            "task_name": task_name,
            "tracked_item": self.tracked_item,
            "current_qty": current_qty,
            "target_qty": self.current_target_qty,
            "status": self.current_status,
            "message": self.current_message,
            "map": getattr(b, "strMapName", "-") if b else "-",
            "cell": p.CELL if (p and getattr(p, "CELL", None)) else "-",
            "pad": p.PAD if (p and getattr(p, "PAD", None)) else "-",
            "hp": p.CURRENT_HP if p else 0,
            "max_hp": p.MAX_HP if p else 0,
            "mp": p.MANA if p else 0,
            "max_mp": p.MAX_MP if p else 0,
            "is_dead": p.ISDEAD if p else False,
            "cooldowns": cooldowns,
            "time_running": time_running
        }

    def _run_bot(
        self,
        server: str,
        room_number: int,
        username: str,
        password: str,
        sub_module_id: str,
        task_id: str,
        target_qty: int,
        solo_class: str,
        farm_class: str
    ):
        thread_id = threading.get_ident()

        if self.redirector_out:
            self.redirector_out.register_thread(thread_id, "general", username)
        if self.redirector_err:
            self.redirector_err.register_thread(thread_id, "general", username)

        submodule = REGISTRY.get(sub_module_id)
        task = submodule.get_task(task_id) if submodule else None

        print(f"=== [General Bot] Launching Sub-Module '{submodule.name if submodule else sub_module_id}' ===")
        print(f"=== [General Bot] Task: {task.name if task else task_id} | Target Qty: {target_qty} ===")
        print(f"=== [General Bot] Solo Class: '{solo_class}' | Farm Class: '{farm_class}' | Server: {server} | Room: {room_number} ===")

        self.current_status = "Connecting"
        self.current_message = f"Connecting to {server}..."

        bot = Bot(
            cmdDelay=1000,
            showLog=True,
            showDebug=False,
            autoRelogin=False,
            isScriptable=True,
            soloClass=solo_class,
            farmClass=farm_class,
            roomNumber=room_number if room_number > 0 else None
        )
        bot.set_login_info(username, password, server)
        bot.general_turn_in_count = 0
        self.current_bot = bot

        async def bot_main(cmd: Command):
            if self.stop_requested:
                return

            self.current_status = "Running"
            self.current_message = f"Farming {task.name if task else task_id}..."

            try:
                if task and task.runner_fn:
                    await task.runner_fn(cmd, target_qty)
                else:
                    print(f"[{username}] Error: No runner function found for task {task_id}")
            except Exception as ex:
                print(f"[{username}] Task exception: {ex}")
                raise

        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        try:
            loop.run_until_complete(bot.start_bot(bot_main))
        except Exception as e:
            print(f"[{username}] Error during bot execution: {e}")
            self.current_status = "Error"
            self.current_message = str(e)
        finally:
            if self.redirector_out:
                self.redirector_out.unregister_thread(thread_id)
            if self.redirector_err:
                self.redirector_err.unregister_thread(thread_id)
            loop.close()
            self.current_bot = None

        if self.stop_requested:
            self.current_status = "Stopped"
            self.current_message = "Stopped by user"
            print(f"=== [General Bot] Stopped by user ===")
        elif self.current_status != "Error":
            self.current_status = "Finished"
            self.current_message = "Task completed successfully"
            print(f"=== [General Bot] Completed successfully ===")

        self.is_running = False
        print(f"=== [General Bot] Execution finished. ===")
