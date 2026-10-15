import requests
from typing import List, Optional
import random
import time
from datetime import datetime, timedelta
from .utils import checkOperator
from colorama import Fore
import json
from core.utils import normalize
from model.inventory import ItemInventory, ItemType
from model.aura import Aura
from model.faction import Faction
from model.monster import Monster
from model.stats import MAX_COOLDOWN_REDUCTION, PlayerStats

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
        # Full `stu` stat block.  CDREDUCTION/ManaCost above are kept in sync
        # from it so existing readers keep working; prefer STATS for new code
        # (STATS.cooldown_reduction applies the verified 0.5 cap -- the raw
        # $tha can reach 0.8444 and would recast ~2.8x too early).
        self.STATS = PlayerStats()
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
        response = None
        for attempt in range(3):
            try:
                response = requests.post(url, json=data, timeout=15)
                break
            except requests.exceptions.RequestException as error:
                if attempt == 2:
                    print(f"Login request failed after 3 tries: {error}")
                    return None
                time.sleep(2 * (attempt + 1))
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
            'ccid': str(self.CHARID),
            'token': self.TOKEN,
            'artixmode': 'launcher',
            'X-Requested-With': 'ShockwaveFlash/32.0.0.371'
        }

        # The bank POST is the request that resets (10054) on a busy login.  One
        # reset used to leave BANK empty for the whole session, which then looks
        # like "class not in bank" to equip_item.  Retry a couple of times.
        for attempt in range(3):
            try:
                response = requests.request("POST", url, headers=headers,
                                            data=data, timeout=15)
                for item in response.json():
                    self.BANK.append(ItemInventory(item))
                return True
            except (requests.exceptions.RequestException, ValueError) as error:
                if attempt == 2:
                    print(f"loadBank failed after 3 tries: {error}")
                    return False
                time.sleep(2 * (attempt + 1))
    
    def getServerInfo(self, serverName):
        for server in self.SERVERS:
            if server["sName"].lower() == serverName.lower():
                return [server["sIP"], server["iPort"]]
        return ["", 0]
    
    def canUseSkill(self, skillNumber: int):
        if skillNumber >= len(self.SKILLS):
            return False
        skill = self.SKILLS[skillNumber]

        # Mana check. `mana` is signed: the auto-attack reports -15 because it
        # *returns* mana, so `MANA < -15` is never true and it stays castable.
        # The accessor also tolerates the scroll slot, which omits `mp`.
        skillCost = skill.mana * self.ManaCost
        if self.MANA < skillCost:
            # print(f"skill:{skillNumber} cost:{skillCost} current_mp:{self.MANA}")
            return False

        # Cooldown check. `nextUse` is armed by updateNextUse; a slot the
        # server has just replaced via sAct starts ready rather than blocking.
        deadline = skill.next_use
        if deadline is not None and deadline > datetime.now():
            return False

        return True

    def updateNextUse(self, skillNumber: int, start_delay_ms: int = 200) -> None:
        """Arm this slot's cooldown.

        Args:
            skillNumber (int): Skill slot that was just cast.
            start_delay_ms (int): Latency allowance. The server starts its own
                cooldown when the packet *arrives*, not when we send it, so the
                local timer has to start that much later -- otherwise we recast
                early and the server answers "Please slow down. Last action was
                too soon!". Keeping this as an explicit argument (rather than a
                side effect of sleeping before the call) makes the compensation
                visible and lets the caller stop blocking its loop to apply it.

        Returns:
            None: mutates ``SKILLS[skillNumber]["nextUse"]`` in place.
        """
        skill = self.SKILLS[skillNumber]

        # Cap the cooldown reduction the server actually honours.  Raw $tha
        # reaches 0.8444 but observed recasts only ever match a 50% reduction --
        # verified slot-by-slot in tools/verify_cdr_cap.py (obs min 3202 ms vs
        # 3200 ms predicted at 0.5, versus 1134 ms if uncapped).  Using the raw
        # value would recast ~2.8x early and draw "too soon" rejections.
        cdr = min(self.CDREDUCTION, MAX_COOLDOWN_REDUCTION)
        effective_cd = skill.effective_cooldown_ms(cdr)

        resultNextUse = (datetime.now()
                         + timedelta(milliseconds=effective_cd + start_delay_ms))
        skill.next_use = resultNextUse

        # print(f"skill:{skillNumber} cd:{skill.cooldown_ms} cdr:{cdr * 100:.2f}% => result:{effective_cd:.2f}ms")

    def effective_cd_ms(self, skillNumber: int) -> float:
        """Cooldown this slot actually runs for, in milliseconds."""
        if skillNumber >= len(self.SKILLS):
            return float("inf")
        return self.SKILLS[skillNumber].effective_cooldown_ms(self.CDREDUCTION)

    def skill_ready_in_ms(self, skillNumber: int) -> float:
        """Milliseconds until this slot can be cast again.

        Returns ``0.0`` when it is ready now and ``float("inf")`` when the slot
        does not exist, so callers can ``min()``/``max()`` across a skill list
        without bounds checks. Mana starvation reads as a short wait rather than
        "ready" so the scheduler retries after regeneration instead of spinning.
        """
        if skillNumber >= len(self.SKILLS):
            return float("inf")
        skill = self.SKILLS[skillNumber]
        if self.MANA < skill.mana * self.ManaCost:
            # Mana regeneration is not modelled; retry shortly rather than spin.
            return 250.0
        return skill.ready_in_ms()

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

    def get_item_inventory_by_enhance_id(self, enh_id: int,
                                         slot: Optional[str] = None
                                         ) -> Optional[ItemInventory]:
        """First inventory item carrying a given enhancement.

        Args:
            enh_id: Either an ``EnhID`` (the enhancement's unique id, e.g.
                70752 = Valiance R7) or, for backwards compatibility, an
                ``EnhPatternID``.  Prefer ``EnhID``: a pattern can cover
                several enhancements (pattern 10 covers seven weapon ones),
                so a pattern-only target is inherently ambiguous and can be
                narrowed with ``slot``.
            slot (str): Optional equipment slot filter -- ``"Weapon"``,
                ``"he"``, ``"ba"``, or a readable name like ``"cape"``.
                Without it the first match in inventory order wins, which may
                be a helm when you meant the weapon.

        Returns:
            ItemInventory | None: the match, or ``None`` if nothing has it.
        """
        for item in self.get_items_by_enhancement(enh_id, slot=slot):
            return item
        return None

    def get_items_by_enhancement(self, enh_id,
                                 slot: Optional[str] = None) -> List[ItemInventory]:
        """Every inventory item carrying enhancement ``enh_id``.

        ``enh_id`` may be an ``EnhID``, a pattern id, or an enhancement name.
        Matching prefers the item's unique ``enh_id`` and only falls back to
        ``enh_pattern_id`` when the item reports no id -- see
        :func:`model.enhancement.item_matches`.
        """
        from model import enhancement as _enh
        matches: List[ItemInventory] = []
        try:
            for item in self.INVENTORY:
                if _enh.item_matches(item, enh_id, slot=slot):
                    matches.append(item)
        except ValueError as exc:          # unknown slot string
            raise ValueError(str(exc)) from exc
        return matches

    def items_by_enhancement_name(self, name: str,
                                  slot: Optional[str] = None) -> List[ItemInventory]:
        """Every inventory item carrying the enhancement called ``name``.

        Example::

            player.items_by_enhancement_name("Valiance")          # must be a weapon
            player.items_by_enhancement_name("Forge", slot="ba")  # cape only
        """
        return self.get_items_by_enhancement(name, slot=slot)

    def inventory_by_slot(self, slot: str) -> List[ItemInventory]:
        """Every inventory item that belongs in equipment slot ``slot``."""
        from model import enhancement as _enh
        code = _enh.slot_code(slot)
        return [item for item in self.INVENTORY if item.s_es == code]
    
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