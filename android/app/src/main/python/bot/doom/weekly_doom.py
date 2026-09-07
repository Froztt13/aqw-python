import os
import sys
import time
import json
import asyncio
import threading
from typing import List, Dict, Any, Optional

from core.bot import Bot
import commands as cmd

def get_weekly_doom_commands():
    return [
        cmd.IsInInvCmd("Epic Item of Digital Awesomeness"),
        cmd.MessageCmd(msg="You have \"Epic Item of Digital Awesomeness\" in your inventory!!"),
        cmd.IsInBankCmd("Gear of Doom"),
        cmd.BankToInvCmd("Gear of Doom"),
        cmd.IsInInvCmd("Gear of Doom", 3, operator="<"),
        cmd.StopBotCmd(msg="Not enough Gear of Doom."),
        cmd.JoinMapCmd("doom"),
        cmd.AcceptQuestCmd(3076),
        cmd.TurnInQuestCmd(3076),
        cmd.SleepCmd(1000),
        cmd.StopBotCmd(msg="Bot Finished.")
    ]

class WeeklyDoomManager:
    def __init__(self, redirector_out=None, redirector_err=None, get_config_dir_fn=None):
        self.redirector_out = redirector_out
        self.redirector_err = redirector_err
        self.get_config_dir_fn = get_config_dir_fn
        self.runner_thread = None
        self.current_bot = None
        self.is_running = False
        self.stop_requested = False
        self.start_time = None
        self.current_index = 0
        self.current_username = ""
        self.current_account_id = None
        self.total_accounts = 0
        self.completed_accounts = 0
        self.account_statuses: Dict[str, Dict[str, Any]] = {}

    def get_config_path(self):
        if self.get_config_dir_fn:
            base = self.get_config_dir_fn()
        else:
            base = os.path.expanduser("~/.aqw_bot")
        return os.path.join(base, "weekly_doom_config.json")

    def load_config(self):
        default_config = {
            "server": "Alteon",
            "accounts": [
                {
                    "id": "acc-1",
                    "username": "",
                    "password": "",
                    "enabled": True
                }
            ]
        }
        cfg_path = self.get_config_path()
        if os.path.exists(cfg_path):
            try:
                with open(cfg_path, "r") as f:
                    user_conf = json.load(f)
                    if "server" in user_conf:
                        default_config["server"] = user_conf["server"]
                    if "accounts" in user_conf and isinstance(user_conf["accounts"], list):
                        default_config["accounts"] = user_conf["accounts"]
            except Exception as e:
                print(f"[WeeklyDoomManager] load_config error: {e}")
        return default_config

    def save_config(self, config):
        cfg_path = self.get_config_path()
        try:
            with open(cfg_path, "w") as f:
                json.dump(config, f, indent=4)
            return {"success": True}
        except Exception as e:
            return {"success": False, "error": str(e)}

    def reset_config(self):
        cfg_path = self.get_config_path()
        if os.path.exists(cfg_path):
            try:
                os.remove(cfg_path)
            except Exception:
                pass
        return self.load_config()

    def start(self, config):
        if self.is_running:
            return {"success": False, "error": "Weekly Doom Bot is already running"}

        server = config.get("server", "Alteon")
        accounts = config.get("accounts", [])
        enabled_accounts = [
            a for a in accounts
            if a.get("enabled", True) and a.get("username", "").strip()
        ]

        if not enabled_accounts:
            return {"success": False, "error": "No enabled accounts configured with a username"}

        self.save_config(config)

        # Initialize status for each account
        self.account_statuses.clear()
        for acc in accounts:
            a_id = acc.get("id", "")
            if not a_id:
                continue
            is_enabled = acc.get("enabled", True) and bool(acc.get("username", "").strip())
            self.account_statuses[a_id] = {
                "id": a_id,
                "username": acc.get("username", "").strip(),
                "status": "Pending" if is_enabled else "Disabled",
                "message": "Waiting in queue..." if is_enabled else "Disabled",
                "has_eioda": False,
                "wheel_drops": []
            }

        self.is_running = True
        self.stop_requested = False
        self.start_time = time.time()
        self.total_accounts = len(enabled_accounts)
        self.completed_accounts = 0
        self.current_index = 0
        self.current_username = ""

        self.runner_thread = threading.Thread(
            target=self._run_accounts,
            args=(server, enabled_accounts),
            daemon=True
        )
        self.runner_thread.start()
        return {"success": True}

    def stop(self):
        self.stop_requested = True
        if self.current_bot:
            try:
                self.current_bot.stop_bot(user_triggered=True)
            except Exception:
                pass
        return {"success": True}

    def get_status(self):
        time_running = int(time.time() - self.start_time) if self.start_time and self.is_running else 0
        return {
            "running": self.is_running,
            "current_index": self.current_index,
            "current_username": self.current_username,
            "total_accounts": self.total_accounts,
            "completed_accounts": self.completed_accounts,
            "time_running": time_running,
            "accounts": self.account_statuses
        }

    def _run_accounts(self, server: str, accounts: List[Dict[str, Any]]):
        thread_id = threading.get_ident()

        for idx, acc in enumerate(accounts):
            if self.stop_requested:
                break

            acc_id = acc.get("id", "")
            username = acc.get("username", "").strip()
            password = acc.get("password", "").strip()

            self.current_index = idx + 1
            self.current_username = username
            self.current_account_id = acc_id

            if acc_id in self.account_statuses:
                self.account_statuses[acc_id]["status"] = "Running"
                self.account_statuses[acc_id]["message"] = "Logging in..."

            if self.redirector_out:
                self.redirector_out.register_thread(thread_id, "doom", username)
            if self.redirector_err:
                self.redirector_err.register_thread(thread_id, "doom", username)

            print(f"=== [Weekly Doom] Starting account {idx + 1}/{len(accounts)}: {username} ===")

            bot = Bot(
                cmdDelay=1000,
                showLog=True,
                showDebug=False,
                autoRelogin=False,
                isScriptable=False
            )
            bot.set_login_info(username, password, server)
            bot.cmds = get_weekly_doom_commands()
            self.current_bot = bot

            def on_packet(msg):
                if not msg:
                    return
                try:
                    # Capture Wheel drops if packet arrives
                    if '"cmd":"Wheel"' in msg or '"cmd":"wheel"' in msg:
                        data = json.loads(msg)
                        obj = data.get("b", {}).get("o", {})
                        drop_items = obj.get("dropItems", {})
                        drops = [item["sName"] for item in drop_items.values() if "sName" in item]
                        if drops and acc_id in self.account_statuses:
                            existing = self.account_statuses[acc_id].setdefault("wheel_drops", [])
                            for d in drops:
                                if d not in existing:
                                    existing.append(d)
                except Exception:
                    pass

            bot.subscribe(on_packet)

            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            try:
                loop.run_until_complete(bot.start_bot())
            except Exception as e:
                print(f"[{username}] Error during bot execution: {e}")
                if acc_id in self.account_statuses:
                    self.account_statuses[acc_id]["status"] = "Error"
                    self.account_statuses[acc_id]["message"] = str(e)
            finally:
                if self.redirector_out:
                    self.redirector_out.unregister_thread(thread_id)
                if self.redirector_err:
                    self.redirector_err.unregister_thread(thread_id)
                loop.close()
                self.current_bot = None

            # Check if player has EIODA
            try:
                eioda_check = bot.player.isInInventory("Epic Item of Digital Awesomeness")
                if eioda_check and eioda_check[0]:
                    if acc_id in self.account_statuses:
                        self.account_statuses[acc_id]["has_eioda"] = True
                    print(f"[{username}] *** EPIC ITEM OF DIGITAL AWESOMENESS IN INVENTORY! ***")
            except Exception:
                pass

            # Outcome determination
            stop_msg = getattr(bot, "last_stop_msg", None)
            if self.stop_requested:
                if acc_id in self.account_statuses:
                    self.account_statuses[acc_id]["status"] = "Stopped"
                    self.account_statuses[acc_id]["message"] = "Stopped by user"
                break
            elif stop_msg:
                if "Not enough Gear of Doom" in stop_msg:
                    if acc_id in self.account_statuses:
                        self.account_statuses[acc_id]["status"] = "Not enough Gear"
                        self.account_statuses[acc_id]["message"] = "Not enough Gear of Doom (< 3)"
                elif "Bot Finished" in stop_msg:
                    if acc_id in self.account_statuses:
                        self.account_statuses[acc_id]["status"] = "Finished"
                        self.account_statuses[acc_id]["message"] = "Completed successfully"
                else:
                    if acc_id in self.account_statuses:
                        self.account_statuses[acc_id]["status"] = "Stopped"
                        self.account_statuses[acc_id]["message"] = stop_msg
            else:
                if not bot.server_info:
                    if acc_id in self.account_statuses:
                        self.account_statuses[acc_id]["status"] = "Failed"
                        self.account_statuses[acc_id]["message"] = "Login failed / check credentials"
                else:
                    if acc_id in self.account_statuses:
                        self.account_statuses[acc_id]["status"] = "Finished"
                        self.account_statuses[acc_id]["message"] = "Completed"

            self.completed_accounts += 1
            print(f"=== [Weekly Doom] Account {username} result: {self.account_statuses[acc_id]['status']} ({self.account_statuses[acc_id]['message']}) ===")

            if not self.stop_requested and idx < len(accounts) - 1:
                print(f"Waiting 3 seconds before next account...")
                time.sleep(3.0)

        self.is_running = False
        self.current_bot = None
        self.current_username = ""
        self.current_account_id = None
        print("=== [Weekly Doom] All accounts processed. Runner finished. ===")
