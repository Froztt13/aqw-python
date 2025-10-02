import socket
from core.command import Command
from core.player import Player
from core.utils import normalize
import json
import time
from typing import Awaitable, Callable, List, Optional
from xml.etree import ElementTree
import xml.etree.ElementTree as ET
from datetime import datetime, timedelta
from colorama import Fore, Back, Style, init
import inspect
import asyncio
from model import Shop
from model import Monster
from model import ItemInventory, ItemType, Faction, PlayerArea
from handlers import register_quest_task, death_handler_task, aggro_handler_task
import time
import traceback
    
class Bot:

    def __init__(
            self, 
            roomNumber: Optional[int] = None, 
            itemsDropWhiteList = [],
            cmdDelay: int = 1000,
            showLog: bool = True, 
            showDebug: bool = False,
            showChat: bool = True,
            autoRelogin: bool = False,
            followPlayer: str = "",
            slavesPlayer: List[str] = [],
            isScriptable: bool = False,
            farmClass: Optional[str] = None,
            soloClass: Optional[str] = None,
            restartOnAFK: bool = True,
            autoAdjustSkillDelay: bool = False,
            respawnCellPad: List[str] = [],
            muteSpamWarning: bool = False,
            antiMod: bool = True
            ):
        self.roomNumber = roomNumber
        self.showLog = showLog
        self.cmdDelay = cmdDelay
        self.showDebug = showDebug
        self.showChat = showChat
        self.items_drop_whitelist: list[str] = itemsDropWhiteList
        self.auto_relogin = autoRelogin
        self.follow_player = followPlayer
        self.slaves_player = slavesPlayer
        self.isScriptable = isScriptable
        self.farmClass = farmClass
        self.soloClass = soloClass
        self.restart_on_afk = restartOnAFK
        self.respawn_cell_pad = respawnCellPad
        self.mute_spam_warning = muteSpamWarning
        self.anti_mod = antiMod

        self.auto_relogin = False # sementara diset ke False untuk cegah stop_bot() di function read_server_in_background()
        
        self.is_char_load_complete= False
        self.is_joining_map = False
        self.is_client_connected = False
        
        self.wait_ms = 0
        self.player = Player()
        self.cmds = []
        self.index = 0
        self.areaId = None
        self.canuseskill = True
        self.skillAnim = None
        self.username = ""
        self.password = ""
        self.server = ""
        self.server_info: List[str] = []
        self.client_socket = None
        self.users_id_in_cell = []
        self.users_name_in_cell = []
        self.loaded_quest_datas = []
        self.failed_get_quest_datas = []
        self.aggro_mons_id = []
        self.aggro_delay_ms = 500
        self.loaded_shop_datas: List[Shop] = []
        self.registered_auto_quest_ids = []
        self.is_register_quest_task_running = False
        self.is_aggro_handler_task_running = False
        self.followed_player_cell = None
        self.subscribers = []
        self.scroll_id: str = ""
        self.battle_analyzer: bool = False

        self.auto_adjust_skill_delay = autoAdjustSkillDelay
        self.skill_delay_ms = 1300
        self.adjust_skill_delay_by_ms = 500
        self.check_spam_time = None

        self.missing_turn_in_item_questid: list[int] = [] # this mean quest is unlocked (green quest)
        self.missing_quest_progress_questid: list[int] = [] # this mean quest is locked (red quest)

        self.player_in_area: list[PlayerArea] = []

        self.bot_main = None
        self.command = Command(self, init_handler=True)

    def subscribe(self, callback):
        """Subscribe to messages."""
        if callable(callback):
            if callback not in self.subscribers:
                self.subscribers.append(callback)

    def unsubscribe(self, callback):
        """Unsubscribe from messages."""
        if callback in self.subscribers:
            self.subscribers.remove(callback)

    def notify_subscribers(self, message):
        """Notify all subscribers."""
        for subscriber in self.subscribers:
            subscriber(message)
        
    def set_login_info(self, username, password, server):
        self.username = username
        self.password = password
        self.server = server
        
    async def start_bot(self, botMain: Optional[Callable[[Command], Awaitable[None]]] = None):
        self.login(self.username, self.password, self.server)
        if self.server_info:
            await self.connect_client()
            if self.isScriptable and botMain:
                self.bot_main = botMain
                asyncio.create_task(self.read_server_in_background())

                while self.is_client_connected:
                    while self.is_char_load_complete is False:
                        await asyncio.sleep(0.01)
                    
                    if not self.is_register_quest_task_running:
                        self.run_register_quest_task()
                        self.is_register_quest_task_running = True
                    
                    await botMain(self.command)
                    self.stop_bot()
                if self.auto_relogin:
                    print("Relogin from start bot")
                    await self.relogin_and_restart(async_bot=self.bot_main)
            else:
                await self.run_commands()
        return
            
    def run_register_quest_task(self):
        asyncio.create_task(register_quest_task(self))  
    
    def run_death_hanlder_task(self):
        asyncio.create_task(death_handler_task(self))  

    def run_aggro_hadler_task(self):
        asyncio.create_task(aggro_handler_task(self))
    
    def stop_bot(self):
        print(f"[{datetime.now().strftime('%H:%M:%S')}] Stopping bot...")
        self.client_socket.close()
        self.is_client_connected = False

    def debug(self, *args):
        if not self.showDebug:
            return
        caller_frame = inspect.currentframe().f_back
        caller_name = caller_frame.f_code.co_name
        combined_message = ' '.join(map(str, args))
        print(f"[{datetime.now().strftime('%H:%M:%S')}] [{caller_name}] {combined_message}")

    def login(self, username, password, server):
        if self.player.login(username, password):
            self.server_info = self.player.getServerInfo(server)
            
    async def relogin_and_restart(self, async_bot= None):
        self.stop_bot()
        self.index = 0
        self.is_char_load_complete = False
        self.is_joining_map = False
        self.is_register_quest_task_running = False
        self.loaded_quest_datas = []
        self.loaded_shop_datas: List[Shop] = []
        self.registered_auto_quest_ids = []
        self.skill_delay_ms = 1500
        self.adjust_skill_delay_by_ms = 500
        self.check_spam_time = None
        try:
            print("Restarting bot in 35 secs...")
            await asyncio.sleep(35)
            if self.isScriptable and async_bot and self.auto_relogin:
                await self.start_bot(async_bot)
            else:
                await self.start_bot()
        except Exception as e:
            print(f"Error during restarting bot: {e}")
        
    async def connect_client(self):
        hostname = self.server_info[0] 
        port = self.server_info[1]
        self.debug(hostname, port)
        host_ip = socket.gethostbyname(hostname)
        print(f"Connecting to {Fore.BLUE + self.server.upper() + Fore.RESET} server...")
        self.client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.client_socket.connect((host_ip, port))
        self.is_client_connected = True

    async def run_commands(self):    
        if self.is_client_connected:
            # self.print_commands()
            print("Running bot commands...")
        while self.is_client_connected:
            if self.registered_auto_quest_ids and not self.is_register_quest_task_running:
                self.run_register_quest_task()
                self.is_register_quest_task_running = True
            messages = self.read_batch(self.client_socket)
            if messages:
                for msg in messages:
                    try:
                        await self.handle_server_response(msg)
                    except Exception as e:
                        print(f"err: {e}")
                    
            # do wait if any,its different than cmdDelay
            await asyncio.sleep(self.wait_ms)
            self.wait_ms = 0
            
            if self.player.ISDEAD:
                self.debug(Fore.MAGENTA + "respawned" + Fore.WHITE)
                self.write_message(f"%xt%zm%resPlayerTimed%{self.areaId}%{self.username_id}%")
                self.jump_cell(self.player.CELL, self.player.PAD)
                self.player.ISDEAD = False
                self.player.MANA = 100
                continue
            # Execute a command
            if self.is_char_load_complete:
                if self.is_joining_map:
                    continue
                if self.follow_player and self.followed_player_cell != self.player.CELL:
                    await self.goto_player(self.follow_player)
                    await asyncio.sleep(1)
                    continue                
                if self.index >= len(self.cmds):
                    self.index = 0                
                cmd = self.cmds[self.index]
                await self.handle_command(cmd)
                self.index += 1
        print('BOT STOPPED\n')
        if self.auto_relogin:
            print("relogin from run commands")
            await self.relogin_and_restart()
        
    def print_commands(self):
        print("Index\tCommand")
        print("------------------------------")
        for i, cmd in enumerate(self.cmds):
            print(cmd.to_string())
        print("------------------------------")

    async def handle_command(self, command):
        if command.skip_delay: # when skip_delay, we execute the cmd first before print its text
            await command.execute(self, self.command)
        if self.showLog: # print text
            cmd_string = command.to_string()
            if cmd_string:
                cmd_string = cmd_string.split(':')
                if len(cmd_string) > 1:
                    print(Fore.BLUE + f"[{datetime.now().strftime('%H:%M:%S')}] [{self.index}] {cmd_string[0]}:" + Fore.RESET + cmd_string[1])
                else:
                    print(Fore.BLUE + f"[{datetime.now().strftime('%H:%M:%S')}] [{self.index}] {cmd_string[0]}" + Fore.RESET)
        if not command.skip_delay:  # when not skip delay, execute cmd after print its text
            await command.execute(self, self.command)
            await asyncio.sleep(self.cmdDelay/1000)
    
    def check_user_access_level(self, username: str, access_level: int):
        if access_level >= 30 and self.anti_mod:
            print(Fore.RED + f"[{datetime.now().strftime('%H:%M:%S')}] You meet {username}, a staff!")
            self.auto_relogin = False
            self.stop_bot()

    async def handle_server_response(self, msg):
        if self.auto_adjust_skill_delay and self.check_spam_time:
            if (time.time() - self.check_spam_time) > 300 and self.skill_delay_ms > 1500:
                # self.check_spam_time = None
                self.skill_delay_ms -= self.adjust_skill_delay_by_ms
                print(f"set skill delay to: {self.skill_delay_ms}")
        self.notify_subscribers(msg)
        if "counter" in msg.lower():
            self.debug(Fore.RED + msg + Fore.WHITE)

        if self.is_valid_json(msg):
            data = json.loads(msg)
            try:
                data = data["b"]["o"]
            except:
                return
            cmd = data["cmd"]
            if cmd == "moveToArea":
                uo_branch = data.get("uoBranch")
                mon_branch = data.get("monBranch")
                mon_def = data.get("mondef")
                mon_map = data.get("monmap")
                self.areaName = data["areaName"] #"yulgar-99999"
                self.areaId = data["areaId"]
                self.strMapName: str = data["strMapName"] #"yulgar"
                self.monsters: list[Monster] = []
                self.player_in_area: list[PlayerArea] = []
                for i_uo_branch in uo_branch:
                    if (i_uo_branch["uoName"].lower() == self.player.USER.lower()):
                        self.player.PAD = i_uo_branch["strPad"]
                        self.player.CELL = i_uo_branch["strFrame"]
                    if (i_uo_branch["uoName"].lower() == self.follow_player.lower()):
                        self.followed_player_cell = i_uo_branch["strFrame"]
                    if (i_uo_branch["uoName"].lower() == self.player.USER.lower()):
                        self.player.setIsInCombat(i_uo_branch["intState"])
                    self.player_in_area.append(PlayerArea(i_uo_branch))
                if mon_def and mon_branch and mon_map:
                    for i_mon_branch in mon_branch:
                        self.monsters.append(Monster(i_mon_branch))
                    for i_mon_def in mon_def:
                        for mon in self.monsters:
                            if i_mon_def["MonID"] == mon.mon_id:
                                mon.mon_name = i_mon_def["strMonName"]
                    for i_mon_map in mon_map:
                        for mon in self.monsters:
                            if i_mon_map["MonMapID"] == mon.mon_map_id:
                                mon.frame = i_mon_map["strFrame"]
            elif cmd == "initUserDatas":
                try:
                    for i in data["a"]:
                        username = i["data"]["strUsername"]
                        access_level = int(i["data"]["intAccessLevel"])
                        if username.lower() == self.username.lower() and self.player.CHARID == 0:
                            self.player.CHARID = i["data"]["CharID"]
                            self.player.GOLD = int(i["data"]["intGold"])
                        self.check_user_access_level(username, access_level)
                    if not self.player.BANK:
                        # print("Load bank and inventory...")
                        self.player.loadBank()
                        self.write_message(f"%xt%zm%retrieveInventory%{self.areaId}%{self.username_id}%")
                except Exception as e:
                    print(f"initUserDatas err: {e}")
            elif cmd == "initUserData":
                username = data["data"]["strUsername"]
                access_level = int(data["data"]["intAccessLevel"])
                self.check_user_access_level(username, access_level)
            elif cmd == "equipItem":
                pass
            elif cmd == "loadInventoryBig":
                self.is_char_load_complete = True
                for item in data["items"]:
                    self.player.INVENTORY.append(ItemInventory(item))
                for faction in data.get("factions", []):
                    self.player.addFaction(Faction(faction))

            # on monster spwaned in map
            elif cmd == "mtls":
                for mon in self.monsters:
                    if mon.mon_map_id == str(data["id"]):
                        mon.is_alive = int(data["o"].get("intState", mon.is_alive)) > 0
                        mon.current_hp = int(data["o"].get("intHP", mon.current_hp))
                        break
            # on player spwaned in map
            elif cmd == "uotls":
                if str(data['unm']) == str(self.player.USER):
                    self.player.MAX_HP = int(data['o'].get('intHPMax', self.player.MAX_HP))
                    self.player.MANA = int(data['o'].get('intMP', self.player.MANA))
                    self.player.setIsInCombat(data["o"].get("intState"))
                    if self.player.IS_IN_COMBAT == False:
                        self.player.setLastTarget(None)
                else:
                    player_name: str = data['unm']
                    player_found = False
                    for player in self.player_in_area:
                        if player_name.lower() == player.str_username.lower():
                            player_found = True
                            player.updateDataPlayer(data["o"])
                            break
                    if not player_found:
                        self.player_in_area.append(PlayerArea(data["o"]))
                    
            elif cmd == "sAct":
                self.player.SKILLS = data["actions"]["active"]
                # print(self.player.SKILLS)
                count_skill = 0
                for skill in self.player.SKILLS:
                    anim_strl = {
                        "anim" : skill.get("anim", ""),
                        "strl" : skill.get("strl", "")
                    }
                    self.player.skills_ref[skill["ref"]] = anim_strl
                    self.player.SKILLS[count_skill]["nextUse"] = datetime.now()
                    count_skill += 1
                # print(self.player.skills_ref)
            elif cmd == "stu":
                if data["sta"].get("$tha"):
                    self.player.CDREDUCTION = data["sta"].get("$tha")
                if data["sta"].get("$cmc"):
                    self.player.ManaCost = data["sta"].get("$cmc")    
            elif cmd == "ct":
                anims = data.get("anims")
                a = data.get("a")
                m = data.get("m")
                p = data.get("p")
                sarsa = data.get("sarsa")
                sara = data.get("sara")
                if anims:
                    for anim in anims:
                        if anim["cInf"] == f"p:{self.username_id}":
                            animStr: str = anim.get("animStr")
                            strl: str = anim.get("strl", "")
                            
                # update player status
                if p:
                    player = p.get(self.username)
                    if player:
                        self.player.CURRENT_HP = player.get("intHP", self.player.CURRENT_HP)
                        self.player.MANA = player.get("intMP", self.player.MANA)
                        # self.player.IS_IN_COMBAT = int(player.get("intState", self.player.IS_IN_COMBAT)) == 2
                        self.player.setIsInCombat(player.get("intState"))
                
                # update monsters status
                if m:
                    for mon_map_id, mon_condition in m.items():
                        for mon in self.monsters:
                            if mon.mon_map_id == mon_map_id:
                                mon.current_hp = int(mon_condition.get("intHP", mon.current_hp))
                                mon.is_alive = mon.current_hp > 0
                                # print(f"[{datetime.now().strftime('%H:%M:%S')}] Monster {mon.mon_name} ({mon.mon_map_id}) HP: {mon.current_hp}, Alive: {mon.is_alive}")
                            
                # update auras
                if a:
                    for action in a:
                        tInf = action.get('tInf')
                        action_cmd = action.get('cmd')

                        # update aura for monster
                        if tInf.startswith('m'):
                            for mon in self.monsters:
                                if f"m:{mon.mon_map_id}" == tInf:
                                    if 'aura+' in action_cmd:
                                        mon.addAura(action.get('auras', []))
                                    elif 'aura-' in action_cmd:
                                        removed_aura = action.get('aura', {}).get('nam')
                                        mon.removeAura(removed_aura) 
                        
                        # update aura for player
                        if self.username_id in tInf:
                            if 'aura+' in action_cmd:
                                self.player.addAura(action.get('auras', []))
                            elif 'aura' in action_cmd:
                                removed_aura = action.get('aura', {}).get('nam')
                                self.player.removeAura(removed_aura)
                if sarsa:
                    for sarsaElm in sarsa:
                        if sarsaElm["cInf"] == f"p:{self.username_id}":
                            for aSarsa in sarsaElm["a"]:
                                sarsaType = aSarsa["type"]
                                sarsaTarget = aSarsa["tInf"]
                                sarsaActRef = aSarsa["actRef"]
                                self.debug(Fore.GREEN + "skill casted: " + sarsaActRef + Fore.WHITE)
                                if "m" in sarsaTarget:
                                    self.debug(Fore.BLUE + f"[SARSA] [{sarsaType.upper()}] {aSarsa['hp']} DMG to {sarsaTarget}" + Fore.WHITE)
                                    if self.battle_analyzer:
                                        self.battle_analyzer_total_damage += aSarsa['hp']
                                        now = datetime.now()
                                        if (now - self.battle_analyzer_last_print) >= timedelta(seconds=5):
                                            self.debug(Fore.RED + f"DPS: {self.battle_analyzer_total_damage / int((datetime.now() - self.battle_analyzer_time_start).total_seconds())}" + Fore.WHITE)
                                            self.battle_analyzer_last_print = now
                                else:
                                    if aSarsa['hp'] < 0:
                                        self.debug(Fore.BLUE + f"[SARSA] [HEAL] {abs(aSarsa['hp'])} HP to {sarsaTarget}" + Fore.WHITE)
                                    else:
                                        self.debug(Fore.BLUE + f"[SARSA] [{sarsaType.upper()}] to {sarsaTarget}" + Fore.WHITE)
                if sara:
                    for saraElm in sara:
                        actionResult = saraElm["actionResult"]
                        saraCInf = actionResult["cInf"]
                        saraTInf = actionResult["tInf"]
                        if saraCInf == f"p:{self.username_id}" and saraTInf == f"p:{self.username_id}":
                            saraType = actionResult["typ"]
                            if saraType == "d":
                                self.debug(Fore.CYAN + f"[SARA] [HOT] {abs(actionResult['hp'])} HOT to {saraTInf}" + Fore.WHITE)
                            else:
                                self.debug(Fore.CYAN + f"[SARA] [{saraType.upper()}] to {saraTInf}" + Fore.WHITE)
                        elif saraCInf.startswith("m") and saraTInf == f"p:{self.username_id}":
                            saraType = actionResult.get("type", "")
                            self.debug(Fore.CYAN + f"[SARA] [{saraType.upper()}] {actionResult['hp']} DMG to {saraTInf}" + Fore.WHITE)
            elif cmd == "seia":
                self.player.SKILLS[5]["anim"] = data["o"]["anim"]
                self.player.SKILLS[5]["strl"] = data["o"]["strl"]
                self.player.SKILLS[5]["cd"] = data["o"]["cd"]
                self.player.SKILLS[5]["tgt"] = data["o"]["tgt"]
                anim_strl = {
                        "anim" : self.player.SKILLS[5]["anim"],
                        "strl" : self.player.SKILLS[5]["strl"]
                    }
                self.player.SKILLS[5]["ref"] = "i1"
                self.player.SKILLS[5]["nextUse"] = datetime.now()
                self.player.skills_ref["i1"] = anim_strl
                # print(self.player.skills_ref)
                # print(f"Skills: {self.player.SKILLS}")
            elif cmd == "playerDeath":
                if int(data["userID"]) == self.player.LOGINUSERID:
                    print(Fore.RED + "DEATH" + Fore.WHITE)
                    self.player.ISDEAD = True
                    if self.isScriptable:
                        self.run_death_hanlder_task()
            elif cmd == "getQuests":
                for quest_id, quest_data in data.get("quests").items():
                    self.loaded_quest_datas.append(quest_data)
            elif cmd == "loadShop":
                shop = Shop(data["shopinfo"])
                found = False
                for loaded_shop in self.loaded_shop_datas:
                    if str(loaded_shop.shop_id) == str(shop.shop_id):
                        found = True
                        break
                if found == False:
                    self.loaded_shop_datas.append(Shop(data["shopinfo"]))
            elif cmd == "buyItem":
                if data["bitSuccess"] == 1:
                    for loaded_shop in self.loaded_shop_datas:
                        for shop_item in loaded_shop.items:
                            if str(shop_item.item_id) == str(data["ItemID"]):
                                bought = ItemInventory({
                                    "sName": shop_item.item_name,
                                    "ItemID": data["ItemID"],
                                    "CharItemID": data["CharItemID"],
                                    "iQty": data["iQty"]
                                })
                                print(f"bought {bought.item_name} {bought.qty}")
                                player_item = self.player.get_item_inventory_by_id(bought.item_id)
                                if player_item:
                                    player_item.qty += bought.qty
                                else:
                                    self.player.INVENTORY.append(bought)
                                return
            elif cmd == "sellItem":
                # {"t":"xt","b":{"r":-1,"o":{"iQtyNow":230,"cmd":"sellItem","intAmount":43750,"CharItemID":8.3779747E8,"bCoins":0,"iQty":7}}}
                for item in self.player.INVENTORY:
                    if int(item.char_item_id) == int(data["CharItemID"]):
                        self.player.GOLD += int(data["intAmount"])
                        self.player.GOLDFARMED += int(data["intAmount"])
                        debug_data_gold = {
                            "gold_added": int(data["intAmount"]),
                            "gold_now": self.player.GOLD,
                            "gold_farmed": self.player.GOLDFARMED
                        }
                        print(Fore.YELLOW + str(debug_data_gold) + Fore.WHITE)
                        if data["iQtyNow"] == 0:
                            self.player.INVENTORY.remove(item)
                            print(f"sold {data['iQty']}x {item.item_name}. qty now: 0")
                        else:
                            item.qty = data["iQtyNow"]
                            print(f"sold {data['iQty']}x {item.item_name}. qty now: {item.qty}")
                        break
            elif cmd == "addGoldExp":
                self.player.GOLD += data["intGold"]
                self.player.GOLDFARMED += data["intGold"]
                gold_added = data["intGold"]
                debug_data_gold = {
                    "gold_added": gold_added,
                    "gold_farmed": self.player.GOLDFARMED,
                    "gold_now": self.player.GOLD
                }
                intExp = data.get("intExp", 0)
                if intExp > 0:
                    self.player.EXPFARMED += intExp
                    debug_data_exp = {
                        "exp_added": intExp,
                        "exp_farmed": self.player.EXPFARMED
                    }
                    self.debug(Fore.BLUE + str(debug_data_exp) + Fore.WHITE)
                intRep = data.get("iRep", 0)
                if intRep > 0:
                    # {"t":"xt","b":{"r":-1,"o":{"FactionID":75,"cmd":"addGoldExp","intGold":0,"intExp":0,"typ":"q","bonusRep":1000,"iRep":3000}}}
                    self.player.addRepToFaction(data.get('FactionID', 0), data.get('iRep', 0))
                self.debug(Fore.YELLOW + str(debug_data_gold) + Fore.WHITE)
            elif cmd == "dropItem":
                dropItems = data.get('items')
                lowered_droplist= [item.lower() for item in self.items_drop_whitelist]
                for itemDrop in dropItems.values():
                    itemDrop: ItemInventory = ItemInventory(itemDrop)
                    if itemDrop.item_name.lower() in lowered_droplist:
                        print(f"get drop {itemDrop.item_name}")
                        self.get_drop(self.username_id, itemDrop.item_id)
                        self.player.INVENTORY.append(itemDrop)
                        break
            elif cmd == "addItems":
                dropItems = data.get('items')
                for itemId, dropItem in dropItems.items():
                    dropItem: ItemInventory = ItemInventory(dropItem)
                    # Item inventory
                    if dropItem.char_item_id:
                        playerItem = self.player.get_item_inventory_by_id(itemId)
                        playerBankItem = self.player.get_item_bank_by_id(itemId)
                        item_name = dropItem.item_name
                        if playerItem:
                            playerItem.qty = dropItem.qty_now
                            playerItem.char_item_id = dropItem.char_item_id
                            # await self.check_registered_quest_completion(itemId)
                            item_name = playerItem.item_name
                        else:
                            self.player.INVENTORY.append(dropItem)
                        if playerBankItem:
                            playerBankItem.qty = dropItem.qty_now
                            playerBankItem.char_item_id = dropItem.char_item_id
                            item_name = playerBankItem.item_name
                        print(f"[{datetime.now().strftime('%H:%M:%S')}] add items {item_name}. qty now {dropItem.qty_now}")
                    # Item temp inventory
                    else:
                        playerItem = self.player.get_item_temp_inventory_by_id(itemId)
                        if playerItem:
                            playerItem.qty += dropItem.qty
                            print(f"[{datetime.now().strftime('%H:%M:%S')}] add temp items {playerItem.item_name}. qty now {playerItem.qty}")
                        else:
                            self.player.TEMPINVENTORY.append(dropItem)
                        
            elif cmd == "turnIn":
                sItems = data.get("sItems").split(',')
                for s_item in sItems:
                    itemId = s_item.split(':')[0]
                    iQty = int(s_item.split(':')[1])
                    playerItem = self.player.get_item_inventory_by_id(itemId)
                    if playerItem:
                        if playerItem.qty - iQty == 0:
                            self.player.INVENTORY.remove(playerItem)
                        else:
                            playerItem.qty -= iQty
                    playerTempItem = self.player.get_item_temp_inventory_by_id(itemId)
                    if playerTempItem:
                        if playerTempItem.qty - iQty == 0:
                            self.player.TEMPINVENTORY.remove(playerTempItem)
                        else:
                            playerTempItem.qty -= iQty
            elif cmd == "event":
                pass
                # print(Fore.GREEN + data["args"]["zoneSet"] + Fore.WHITE)
                # if data["args"]["zoneSet"]  == "A":
                #     if self.strMapName.lower() == "ultraspeaker":
                #         await self.walk_to(100, 321)
            elif cmd == "ccqr":
                quest_id = data.get('QuestID', None)
                s_name = data.get('sName', None)
                faction_id = data.get('rewardObj', {}).get('FactionID', None)
                i_rep = data.get('rewardObj', {}).get('iRep', 0)
                is_success = data.get('bSuccess', 0)
                ccqr_msg = data.get('msg', '')
                if is_success == 1:
                    for loaded_quest in self.loaded_quest_datas:
                        if str(loaded_quest["QuestID"]) == str(quest_id) and int(quest_id) not in self.registered_auto_quest_ids:
                            self.loaded_quest_datas.remove(loaded_quest)
                            break
                    print(Fore.YELLOW + f"ccqr: [{datetime.now().strftime('%H:%M:%S')}] {quest_id} - {s_name} - {i_rep} rep" + Fore.WHITE)
                else:
                    print(Fore.RED + f"ccqr: [{datetime.now().strftime('%H:%M:%S')}] {quest_id} - {s_name} | {ccqr_msg}" + Fore.WHITE)
                    if "Missing Turn In Item" in ccqr_msg:
                        self.missing_turn_in_item_questid.append(int(quest_id))
                    if "Missing Quest Progress" in ccqr_msg:
                        self.missing_quest_progress_questid.append(int(quest_id))
                    if "One Time Quest Only" in ccqr_msg:
                        pass
            elif cmd == "Wheel":
                dropItems = data.get('dropItems')
                dropItemsName = [item["sName"] for item in dropItems.values() if "sName" in item]
                print(Fore.YELLOW + f"Wheel: {dropItemsName}" + Fore.WHITE)
            elif cmd == "acceptQuest":
                quest_id = data["QuestID"]
                if data["bSuccess"] == 1:
                    loaded_quest_ids = [loaded_quest["QuestID"] for loaded_quest in self.loaded_quest_datas]
                    if not str(quest_id) in str(loaded_quest_ids):
                        self.write_message(f"%xt%zm%getQuests%{self.areaId}%{quest_id}%")
                        self.do_wait(500)
                elif data["bSuccess"] == 0:
                    if quest_id not in self.failed_get_quest_datas:
                        self.failed_get_quest_datas.append(quest_id)
            elif cmd == "addFaction":
                # {"t":"xt","b":{"r":-1,"o":{"cmd":"addFaction","faction":{"FactionID":"75","bitSuccess":"1","CharFactionID":"48707365","sName":"Yew Mountains","iRep":"0"}}}}
                self.player.addFaction(Faction(data["faction"]))
            elif cmd == "clearAuras":
                self.player.removeAllAuras()
        elif self.is_valid_xml(msg):
            if ("<cross-domain-policy><allow-access-from domain='*'" in msg):
                self.write_message(f"<msg t='sys'><body action='login' r='0'><login z='zone_master'><nick><![CDATA[SPIDER#0001~{self.player.USER}~3.012]]></nick><pword><![CDATA[{self.player.TOKEN}]]></pword></login></body></msg>")
            elif "joinOK" in msg:
                self.extract_user_ids(msg)
            elif "userGone" in msg:
                self.extract_remove_user(msg)
            elif "uER" in msg:
                self.extract_new_user(msg)
                root = ET.fromstring(msg)
                newId = root.find(".//u").get("i")
                msg = f"%xt%zm%retrieveUserData%{self.areaId}%{newId}%"
                self.write_message(msg)
            elif "logout" in msg:
                print("Client logged out.")
                self.is_client_connected = False
                return
        elif msg.startswith("%") and msg.endswith("%"):
            if f"%server%" in msg:
                print(Fore.MAGENTA + f"[{datetime.now().strftime('%H:%M:%S')}] {msg.split('%')[4]}" + Fore.RESET)
            if f"%xt%loginResponse%" in msg:
                self.write_message(f"%xt%zm%firstJoin%1%")
                self.write_message(f"%xt%zm%cmd%1%ignoreList%$clearAll%")
            elif "You joined" in msg:
                self.write_message(f"%xt%zm%retrieveUserDatas%{self.areaId}%{self.username_id}%")
                self.is_joining_map = False
            elif "warning" in msg:
                msg = msg.split('%')
                text = msg[4]
                if "Please slow down" in text:
                    if self.mute_spam_warning == False:
                        print(Fore.RED + f"[{datetime.now().strftime('%H:%M:%S')}] server warning: {text}" + Fore.WHITE)
                else:
                    print(Fore.RED + f"[{datetime.now().strftime('%H:%M:%S')}] server warning: {text}" + Fore.WHITE)                    
                if "spamming the server" in text:
                    if self.auto_adjust_skill_delay:
                        self.skill_delay_ms += self.adjust_skill_delay_by_ms
                        self.check_spam_time = time.time()
                        print(f"set skill delay to: {self.skill_delay_ms}")
            elif "exitArea" in msg:
                if msg.split('%')[5].lower() == self.follow_player.lower():
                    self.followed_player_cell = None
                    await self.ensure_leave_from_combat(always=True)
                for player in self.player_in_area[:]:
                    if player.str_username.lower() == msg.split('%')[5].lower():
                        # print(f"{player.str_username} has left the area")
                        self.player_in_area.remove(player)
                        break
            elif "uotls" in msg:
                username = msg.split('%')[4]
                movement = msg.split('%')[5]
                cell = None
                pad = None
                for m in movement.split(','):
                    key, value = m.split(':')
                    if key == "strFrame":
                        cell = value
                    elif key == "strPad":
                        pad = value
                if username == self.follow_player:
                    if cell != self.player.CELL:
                        self.followed_player_cell = cell
                for player in self.player_in_area[:]:
                    if player.str_username.lower() == username.lower():
                        player.str_frame = cell
                        if pad != None:
                            player.str_pad = pad
                        break
                        # self.jump_cell(cell, pad)
            elif "respawnMon" in msg:
                pass
            elif "chatm" in msg:
                if self.showChat:
                    msg = msg.split('%')
                    text = msg[4].replace("zone~", ": ").replace("guild~", "[GUILD]: ").replace("party~", "[PARTY]: ")
                    sender = msg[5]
                    print(Fore.MAGENTA + f"[{datetime.now().strftime('%H:%M:%S')}] {sender} {text}" + Fore.WHITE)
            elif "whisper" in msg:
                if self.showChat:
                    msg = msg.split('%')
                    text = msg[4]
                    sender = msg[5]
                    print(Fore.MAGENTA + f"[{datetime.now().strftime('%H:%M:%S')}] {sender} [WHISPER] : {text}" + Fore.WHITE)
            elif f"Your status is now Away From Keyboard" in msg:
                if self.isScriptable and self.auto_relogin:
                    print("Relogin and restart bot on AFK...")
                    await self.relogin_and_restart(async_bot=self.bot_main)
                elif not self.isScriptable and self.restart_on_afk:
                    print("Restart cmds on AFK...")
                    self.index = 0
                    pass
            elif "invalid session" in msg:
                if self.isScriptable and self.auto_relogin:
                    print("Relogin and restart bot on invalid session...")
                    await self.relogin_and_restart(async_bot=self.bot_main)

    async def check_registered_quest_completion(self, item_id, is_temp: bool = False):
        for registered_quest_id in self.registered_auto_quest_ids:
            if self.can_turn_in_quest(registered_quest_id):
                self.turn_in_quest(registered_quest_id)

    async def read_server_in_background(self):
        """Background task to read and handle messages."""
        while self.is_client_connected:
            try:
                messages = await self.read_batch_async(self.client_socket)
                if messages:
                    for msg in messages:
                        await self.handle_server_response(msg)
                if messages is None:
                    if self.isScriptable and self.auto_relogin:
                        self.stop_bot()
                        # print("Relogin and restart bot on timeout...")
                        # await self.relogin_and_restart(async_bot=self.bot_main)
                    
            except CustomError as e:
                print(f"Critical error encountered: {e}")
                self.run = False  # Stop the bot
            except Exception as e:
                print(f"Unexpected error in testasync: {e}")
                tb_str = ''.join(traceback.format_exception(type(e), e, e.__traceback__))
                print(tb_str)
                if self.is_client_connected == False and self.auto_relogin == False:
                    raise Exception("Connection closed by the server.")
        if self.client_socket:
            self.client_socket.close()
    
    async def read_batch_async(self, conn):
        """
        Asynchronous version of read_batch to avoid blocking.
        """
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(None, self.read_batch, conn)

    def read_batch(self, conn):
        message_builder = ""
        complete_messages = []
        last_received_time = time.time()
        while True:
            try:
                conn.settimeout(0.5)
                buf = conn.recv(1024) 
                if not buf:
                    print("Connection closed by the server.")
                    self.is_client_connected = False
                    break
                message_builder += buf.decode('utf-8')
                last_received_time = time.time()  # Update last activity
                if not message_builder.endswith("\x00"):
                    continue
                messages = message_builder.split("\x00")
                for i, msg in enumerate(messages):
                    msg = msg.strip()
                    if self.is_valid_json(msg):
                        complete_messages.append(msg)
                    elif self.is_valid_xml(msg):
                        complete_messages.append(msg)
                    elif msg.startswith("%") and msg.endswith("%"):
                        complete_messages.append(msg)
                if complete_messages:
                    return complete_messages
            except Exception as e:
                return None
            finally:
                if self.is_client_connected == False and self.auto_relogin == False:
                    raise Exception("Connection closed by the server.")
        return complete_messages
    
    def write_message(self, message):
        # print(f"[{datetime.now().strftime('%H:%M:%S')}] {message}")
        if self.client_socket is None:
            return "Error: Connection is not established"
        try:
            self.client_socket.sendall((message + "\u0000").encode('utf-8'))
        except socket.error as e:
            return f"Error writing to the connection: {e}"
        return None

    def is_valid_json(self, s):
        try:
            json.loads(s)
            return True
        except json.JSONDecodeError:
            return False

    def is_valid_xml(self, s):
        try:
            ElementTree.fromstring(s)
            return True
        except ElementTree.ParseError:
            return False
    
    async def goto_player(self, player_name):
        player_found = next((p for p in self.player_in_area if p.str_username.lower() == player_name.lower()), None)
        if player_found:
            self.jump_cell(player_found.str_frame, player_found.str_pad)
        else:
            self.write_message(f"%xt%zm%cmd%1%goto%{player_name}%")
        
    def get_drop(self, user_id, item_id):
        packet = f"%xt%zm%getDrop%{user_id}%{item_id}%"
        self.write_message(packet)
    
    def accept_quest(self, quest_id: int):
        self.write_message(f"%xt%zm%acceptQuest%{self.areaId}%{quest_id}%")
        self.do_wait(500)
        
    def turn_in_quest(self, quest_id: int, item_id: int = -1, qty: int = 1):
        packet = f"%xt%zm%tryQuestComplete%{self.areaId}%{quest_id}%{item_id}%false%{qty}%wvz%"
        self.write_message(packet)
        self.do_wait(500)

    def use_scroll(self, monsterid, max_target):
        self.target = [f"i1>m:{i}" for i in monsterid][:max_target]
        self.write_message(f"%xt%zm%gar%1%0%{','.join(self.target)}%{self.scroll_id}%wvz%")
        
    def use_potion(self, potion_id):
        self.write_message(f"%xt%zm%gar%1%0%i1>p:{self.user_id}%{potion_id}%wvz%")

    def use_skill_to_monster(self, skill, monsters_id, max_target):
        if not monsters_id:
            return
        for mon in self.monsters:
            if mon.mon_map_id == str(monsters_id[0]):
                self.player.setLastTarget(mon)
                break
        self.target = [f"a{skill}>m:{i}" for i in monsters_id][:max_target]
        self.write_message(f"%xt%zm%gar%1%0%{','.join(self.target)}%wvz%")
        # print(f"[{datetime.now().strftime('%H:%M:%S')}] tgt_mon: {self.target}")

    def use_skill_to_player(self, skill, max_target):
        self.target = [f"a{skill}>p:{i}" for i in self.user_ids][:max_target-1]
        self.target.insert(0, f"a{skill}>p:{self.username_id}")
        final_target = []
        for tgt in self.target:
            if tgt not in final_target:
                final_target.append(tgt)
        self.write_message(f"%xt%zm%gar%1%0%{','.join(final_target)}%wvz%")
        # print(f"[{datetime.now().strftime('%H:%M:%S')}] tgt_p: {','.join(final_target)}")
    
    def use_skill_to_myself(self, skill):
        self.write_message(f"%xt%zm%gar%1%0%a{skill}>p:{self.username_id}%wvz%")

    def do_wait(self, wait_ms: int):
        self.wait_ms = wait_ms/1000

    def extract_user_ids(self, xml_message: str):
        root = ET.fromstring(xml_message)
        self.user_ids = []
        self.username_id = None
        for user in root.findall(".//u"):
            self.user_id = user.get("i")  # Get the id
            self.user_ids.append(self.user_id)  # Append to the list
            name: str = user.find("n").text  # Get the username
            if name.lower() == self.player.USER.lower():
                self.username_id = self.user_id  # Store the ID of the target username

    def extract_new_user(self, xml_message: str):
        root = ET.fromstring(xml_message)
        newId = root.find(".//u").get("i")
        self.user_ids.append(newId)
    
    def extract_remove_user(self, xml_message: str):
        root = ET.fromstring(xml_message)
        toRemove = root.find(".//user").get("id")
        for i in self.user_ids:
            if i == toRemove:
                self.user_ids.remove(i)
                break
        
    async def ensure_leave_from_combat(self, sleep_ms: int = 2000, always: bool = False):
        if self.player.IS_IN_COMBAT or always:
            self.jump_cell(self.player.CELL, self.player.PAD)
            await asyncio.sleep(sleep_ms/1000)
        
    def jump_cell(self, cell: str, pad: str = "Left"):
        msg = f"%xt%zm%moveToCell%{self.areaId}%{cell}%{pad}%"
        self.player.CELL = cell
        self.player.PAD = pad
        self.player.setPlayerPositionXY(0,0)
        self.write_message(msg)

    async def walk_to(self, x: int, y: int, speed = 8):
        self.write_message(f"%xt%zm%mv%{self.areaId}%{x}%{y}%{speed}%")
        self.player.setPlayerPositionXY(x, y)
    
    def find_best_cell(self, monster_name, byMostMonster: bool = True, byAliveMonster: bool = False):
        if monster_name.startswith('id.'):
            monster_name = monster_name.split('.')[1]
        if byMostMonster:
            filtered_monsters = [mon for mon in self.monsters if mon.mon_name.lower() == monster_name.lower() or mon.mon_map_id == monster_name]
        if byAliveMonster:
            filtered_monsters = [mon for mon in self.monsters if (mon.mon_name.lower() == monster_name.lower() or mon.mon_map_id == monster_name) and mon.is_alive]

        if not filtered_monsters:
            return None

        cell_counts = {}
        for mon in filtered_monsters:
            cell_counts[mon.frame] = cell_counts.get(mon.frame, 0) + 1

        best_cell = max(cell_counts, key=cell_counts.get)
        return best_cell

    def can_turn_in_quest(self, questId: int) -> bool:
        for loaded_quest in self.loaded_quest_datas:
            if str(loaded_quest.get("QuestID", 0))  == str(questId):
                return self._check_req_inventory(loaded_quest["turnin"])
        return False

    def _check_req_inventory(self, quest_data) -> bool:
        all_items_met = True
        for req_item in quest_data:
            required_item_id = req_item["ItemID"]
            required_qty = req_item["iQty"]

            item = self.player.get_item_inventory_by_id(required_item_id) or \
                self.player.get_item_temp_inventory_by_id(required_item_id)
            if not item or int(item.qty) < int(required_qty):
                all_items_met = False
        return all_items_met
    
    def quest_not_in_progress(self, quest_id: int) -> bool:
        loaded_quest_ids = [loaded_quest["QuestID"] for loaded_quest in self.loaded_quest_datas]
        return str(quest_id) not in str(loaded_quest_ids)

    def reset_cmds(self):
        self.index = 0
        self.cmds = []
        
    def add_cmd(self, cmd):
        self.cmds.append(cmd)
        
    def add_cmds(self, cmds):
        self.cmds.extend(cmds)
    
    def start_battle_analyzer(self):
        self.battle_analyzer: bool = True
        self.battle_analyzer_time_start: datetime = datetime.now()
        self.battle_analyzer_total_damage: int = 0
        self.battle_analyzer_last_print: datetime = self.battle_analyzer_time_start
    
    def stop_battle_analyzer(self):
        self.battle_analyzer: bool = False
        self.battle_analyzer_time_start: datetime = None
        self.battle_analyzer_total_damage: int = 0
    
    def get_player_in_area(self, player_name: str) -> Optional[PlayerArea]:
        for player in self.player_in_area:
            if player_name.lower() == player.str_username.lower():
                return player
        return None

    def is_player_hp_below(self, player_name: str, percent: float) -> bool:
        player = self.get_player_in_area(player_name)
        if player is None:
            return False
        return player.is_hp_below(percent)

class CustomError(Exception):
    """Exception raised for custom error in the application."""

    def __init__(self, message):
        super().__init__(message)
        self.message = message
    
    def get_message(self):
        return self.message
