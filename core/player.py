import requests
from typing import List, Optional
import random
from datetime import datetime, timedelta
from .utils import checkOperator
from colorama import Fore
import json
from core.utils import normalize
from model.inventory import ItemInventory, ItemType
from model.aura import Aura
from model.faction import Faction
from model.monster import Monster

class Player:    
    # Player intState
    # 0 = dead
    # 1 = alive, not in combat
    # 2 = alive, in combat

    def __init__(self):
        self.USER: str = ""
        self.PASS: str = ""
        self.TOKEN = ""
        self.SERVERS = []
        self.SKILLS = []
        self.SKILLUSED = {}
        self.CELL: str = ""
        self.PAD: str = ""
        self.CDREDUCTION = 0
        self.ManaCost = 1.0
        self.LOGINUSERID = 0
        self.INVENTORY: List[ItemInventory] = []
        self.TEMPINVENTORY: List[ItemInventory] = []
        self.BANK: List[ItemInventory] = []
        self.FACTIONS: list[Faction] = []
        self.CHARID: int = 0
        self.GOLD: int = 0
        self.GOLDFARMED: int = 0
        self.EXPFARMED: int = 0
        self.ISDEAD: bool = False
        self.MAX_HP: int = 9999
        self.MAX_MP: int = 100
        self.CURRENT_HP: int = 9999
        self.MANA: int = 100
        self.IS_IN_COMBAT: bool = False
        self.X: int = 0
        self.Y: int= 0
        self.AURAS: list[Aura] = []
        self.skills_ref: dict = {}
        self.last_target: Optional[Monster] = None
        self.is_member: bool = False

    def login(self, username: str, password: str):
        self.USER = username
        self.PASS = password
        url = "https://game.aq.com/game/api/login/now?"

        data = {
            "user": self.USER,
            "option": 1,
            "pass": self.PASS
        }

        print(f'Login {Fore.BLUE + self.USER.upper() + Fore.RESET}...')
        response = requests.post(url, json=data)
        response_json = response.json()
        # print(json.dumps(response_json))
        if response_json.get("login", None):
            self.SERVERS = response_json["servers"]
            self.TOKEN = response_json["login"]["sToken"]
            self.LOGINUSERID = response_json["login"]["userid"]
            self.is_member = response_json["login"]["iUpg"] == 1
            return response
        if response_json.get("bSuccess", 0) == 0:
            print(f"Login {self.USER} failed... {Fore.RED + response_json['sMsg'] + Fore.RESET}")
            return None
        return None

    def loadBank(self):
        random_v = f"0.{random.randint(10**16, 10**17 - 1)}"
        url = f"https://game.aq.com/game/api/char/bank?v={random_v}"

        data = {
            "layout": {
                "cat": "all"
            }
        }

        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Safari/537.36',
            'Content-Type': 'application/x-www-form-urlencoded',
            'ccid': self.CHARID,
            'token': self.TOKEN,
            'artixmode': 'launcher',
            'X-Requested-With': 'ShockwaveFlash/32.0.0.371'
        }

        response = requests.request("POST", url, headers=headers, data=data)
        for item in response.json():
            self.BANK.append(ItemInventory(item))
    
    def getServerInfo(self, serverName):
        for server in self.SERVERS:
            if server["sName"].lower() == serverName.lower():
                return [server["sIP"], server["iPort"]]
        return ["", 0]
    
    def canUseSkill(self, skillNumber: int):
        if skillNumber >= len(self.SKILLS):
            return False
        skills = self.SKILLS[skillNumber]
        
        # Mana check 
        current_mana = self.MANA
        skillCost = skills["mp"]*self.ManaCost
        if current_mana < skillCost:
            print(f"skill:{skillNumber} cost:{skillCost} current_mp:{current_mana}")
            return False
        
        # Cooldown check 
        if skills["nextUse"] > datetime.now():
            return False
        
        return True

    def updateNextUse(self, skillNumber: int) -> None:
        skill = self.SKILLS[skillNumber]
        
        # set maximum CDR to 50%
        cdr = min(self.CDREDUCTION, 0.5)
        cd = skill["cd"]
        effective_cd = cd * (1 - cdr)
        
        resultNextUse = (datetime.now() + timedelta(milliseconds=effective_cd))
        skill["nextUse"] = resultNextUse
        
        # print(f"skill:{skillNumber} cd:{cd} cdr:{cdr * 100:.2f}% => result:{effective_cd:.2f}ms")

    def get_equipped_item(self, item_type: ItemType) -> Optional[ItemInventory]:
        for item in self.INVENTORY:
            if item.s_es == item_type.value and item.is_equipped:
                return item
        return None

    def get_item_inventory(self, itemName: str) -> Optional[ItemInventory]:
        for item in self.INVENTORY:
            if item.item_name == normalize(itemName):
                return item
        return None
    
    def get_item_temp_inventory(self, itemName: str):
        for item in self.TEMPINVENTORY:
            if item.item_name == normalize(itemName):
                return item
        return None
    
    def get_item_inventory_by_id(self, itemId):
        for item in self.INVENTORY:
            if item.item_id == str(itemId):
                return item
        return None

    def get_item_inventory_by_enhance_id(self, enh_id: int) -> Optional[ItemInventory]:
        for item in self.INVENTORY:
            if item.enh_pattern_id == enh_id:
                return item
        return None
    
    def get_item_temp_inventory_by_id(self, itemId):
        for item in self.TEMPINVENTORY:
            if item.item_id == str(itemId):
                return item
        return None
    
    def get_item_bank(self, itemName: str):
        for item in self.BANK:
            if item.item_name == normalize(itemName):
                return item
        return None
        
    def get_item_bank_by_id(self, itemId):
        for item in self.BANK:
            if item.item_id == str(itemId):
                return item
        return None

    def isInBank(self, itemName: str, qty: int = 1, operator: str = ">="):
        inv = self.BANK
        invItemQty = 0
        for item in inv:
            if item.item_name == normalize(itemName):
                invItemQty = item.qty
                break
        return [checkOperator(invItemQty, qty, operator), invItemQty]
    
    def isInInventory(self, itemName: str, qty: int = 1, operator: str = ">=", isTemp: bool = False):
        inv = self.INVENTORY
        invItemQty = 0
        if isTemp:
            inv = self.TEMPINVENTORY
        for item in inv:
            if normalize(item.item_name) == normalize(itemName):
                invItemQty = item.qty
                break
        return [checkOperator(invItemQty, qty, operator), invItemQty]
    
    def getPlayerPositionXY(self) -> list[int]:
        return [self.X, self.Y]
    
    def setPlayerPositionXY(self, X: int, Y: int):
        self.X = X
        self.Y = Y

    def getPlayerCell(self) -> list[str]:
        return [self.CELL, self.PAD]

    def addAura(self, auras:list):
        for aura in auras:
            is_new = aura.get('isNew', False)
            name = normalize(aura.get('nam'))
            if is_new:
                self.AURAS.append(Aura(aura))
            else:
                for existing_aura in self.AURAS:
                    if existing_aura.name == name:
                        existing_aura.refresh(aura.get('dur', 0))
    
    def removeAura(self, auraName: str):
        normalized_name = normalize(auraName)
        for aura in self.AURAS[:]:
            if aura.name == normalized_name:
                self.AURAS.remove(aura)
                break
    
    def removeAllAuras(self):
        self.AURAS: list[Aura] = []

    def getAura(self, auraName: str) -> Optional[Aura]:
        normalized_name = normalize(auraName)
        for aura in self.AURAS:
            if aura.name == normalized_name and not aura.is_expired():
                return aura
        return None
    
    def hasAura(self, auraName: str) -> bool:
        normalized_name = normalize(auraName)
        for aura in self.AURAS:
            if aura.name == normalized_name and not aura.is_expired():
                return True
        return False
    
    def setLastTarget(self, monster: Optional[Monster]):
        if monster == None:
            self.last_target = None
            return
        self.last_target = monster
    
    def getLastTarget(self) -> Optional[Monster]:
        return self.last_target
    
    def setIsInCombat(self, player_state: int):
        self.IS_IN_COMBAT = True if player_state == 2 else False
    
    def addFaction(self, faction: Faction) -> None:
        already_exists = False
        for fac in self.FACTIONS:
            if fac.faction_name.lower() == faction.faction_name.lower():
                already_exists = True
                return
        if already_exists == False:
            self.FACTIONS.append(faction)
    
    def addRepToFaction(self, faction_id: int, faction_rep: int) -> None:
        for fac in self.FACTIONS:
            if fac.faction_id == faction_id:
                fac.add_rep(faction_rep)
                return
    
    def getFactionRank(self, faction_name: str) -> int:
        normalized_faction = normalize(faction_name)
        for fac in self.FACTIONS:
            if fac.faction_name == normalized_faction:
                return fac.get_rank()
        return 0
    
    def printAllAura(self):
        for aur in self.AURAS:
            print(aur.name)