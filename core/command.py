import asyncio
import json
import time
from datetime import datetime
from functools import wraps
from inspect import iscoroutinefunction
from typing import List, Optional, Union
from colorama import Fore
from enum import Enum

from core.player import Player
from core.utils import normalize
from model.inventory import ItemInventory, ItemType, ScrollType
from model.monster import Monster
from model.player_area import PlayerArea
from model.shop import Shop

def check_alive(func):
    """Wait for the player to come back, then run the function.

    Respawn is owned by ``handlers.death_handler`` (fired on ``playerDeath``)
    and by the queue loop.  This decorator must never respawn and must never
    block:

    * the old **sync** path looped on ``time.sleep(1)`` inside the event loop,
      so a dead player hitting a sync method (``get_monster_hp`` is called on
      every fight tick) froze the whole bot -- the async death handler could not
      tick and the respawn looked "stopped";
    * both paths also sent their own ``resPlayerTimed``, racing that handler.
    """

    @wraps(func)
    def sync_wrapper(self: 'Command', *args, **kwargs):
        if not self.is_still_connected():
            return
        return func(self, *args, **kwargs)

    @wraps(func)
    async def async_wrapper(self: 'Command', *args, **kwargs):
        start_time = time.time()
        while (not self.is_player_alive() and self.is_still_connected()
               and time.time() - start_time <= 11):
            await asyncio.sleep(0.2)   # non-blocking; the death handler respawns
        if not self.is_still_connected():
            return
        return await func(self, *args, **kwargs)

    # Check if the function is async and use the appropriate wrapper
    return async_wrapper if iscoroutinefunction(func) else sync_wrapper

class SkillMode(Enum):
    BUFF_ONLY = 1    # using buff type skill only 
    ATTACK_ONLY = 2  # using attack type skill only
    ALL = 3    # using both type skills
    NONE = 4    # pause attack
    
class Command:
    """Facade that exposes quest, item, map, combat, player, and utility helpers."""
        
    quest_to_check: Optional[int] = None
    is_green_quest_var: Optional[bool] = None
    is_completed_before_var: Optional[bool] = None

    # Pacing floors between two consecutive skill packets, in ms, measured from
    # the previous packet of ANY kind.
    #
    # These are not arbitrary: they reproduce the envelope the original code was
    # implicitly testing for, which the baseline capture proved safe (2 warnings
    # / 803 casts / 605 s). Flattening them to a single 300 ms floor was tried
    # and measured to fail badly (SKILL_ANALYSIS.md 3.6):
    #
    #   transition   baseline      flat 300 ms floor
    #   nz  -> nz    0.5% reject   42.3% reject
    #   aa  -> nz    0%            11.1%
    #   nz  -> aa    0.4%          11.1%
    #   aa  -> aa    0%            0%
    #
    # So a real skill needs ~700 ms of clearance after the previous action,
    # while the auto-attack ("aa", slot 0) only needs the ~300 ms the old code
    # produced via its 200 ms sleep + 100 ms loop sleep. Slot 0's own 1161 ms
    # cooldown is the real constraint on it, not pacing.
    MIN_SKILL_GAP_MS: int = 700
    AUTO_ATTACK_MIN_GAP_MS: int = 300
    # Latency allowance handed to Player.updateNextUse -- see its docstring.
    CD_START_DELAY_MS: int = 200

    def __init__(self, bot, init_handler = False):
        from core.bot import Bot
        self.bot: Bot = bot
        self.last_skill_cast_ms: int = 0

        if init_handler:
            self.bot.subscribe(self._message_handler)

    def is_still_connected(self) -> bool:
        """Check whether the client connection is still active."""
        self.bot.accept_quest
        return self.bot.is_client_connected

    def is_valid_json(self, s: str) -> bool:
        """Return True when the provided string parses as JSON."""
        try:
            json.loads(s)
            return True
        except json.JSONDecodeError:
            return False

    @check_alive
    async def ensure_accept_quest(self, quest_id: int) -> None:
        """Keep accepting a quest until it is in progress or the client disconnects.

        Args:
            quest_id (int): Identifier of the quest to accept.

        Returns:
            None: Exits once the quest is tracked or a failure is recorded."""
        while self.quest_not_in_progress(quest_id) and self.is_still_connected():
            await self.accept_quest(quest_id)
            await self.sleep(1000)
            if quest_id in self.bot.failed_get_quest_datas:
                return

    @check_alive
    async def ensure_turn_in_quest(self, quest_id: int, item_id = -1, amount = 1) -> None:
        """Attempt to turn in a quest until it completes or the client disconnects.

        Args:
            quest_id (int): Identifier of the quest to complete.
            item_id (int): Required item id for turn-in when applicable.
            amount (int): Quantity of the required item.

        Returns:
            None: Stops when the quest leaves the progress list or fails."""
        while self.quest_in_progress(quest_id) and self.is_still_connected():
            await self.turn_in_quest(quest_id, item_id,amount)
            await self.sleep(1000)
            if quest_id in self.bot.failed_get_quest_datas:
                return
        print("quest turned in:", quest_id, item_id)

    @check_alive
    async def accept_quest(self, quest_id: int) -> None:
        """Send a single quest accept packet and wait briefly for the response.

        Args:
            quest_id (int): Identifier of the quest to accept.

        Returns:
            None: The coroutine simply delays to allow server processing."""
        self.bot.accept_quest(quest_id)
        print("trying accept quest:", quest_id)
        await asyncio.sleep(1)

    @check_alive
    async def turn_in_quest(self, quest_id: int, item_id: int = -1, qty: int = 1) -> None:
        """Submit quest completion requirements and leave combat if needed.

        Args:
            quest_id (int): Identifier of the quest to turn in.
            item_id (int): Required item id for the submission.
            qty (int): Quantity of the required item.

        Returns:
            None: Updates quest tracking state and delays for server processing."""
        self.quest_to_check = quest_id
        await self.bot.ensure_leave_from_combat()
        self.bot.turn_in_quest(quest_id, item_id, qty)
        await asyncio.sleep(1)

    def quest_not_in_progress(self, quest_id: int) -> bool:
        """Return True when the quest is not currently tracked in progress."""
        loaded_quest_ids = [loaded_quest["QuestID"] for loaded_quest in self.bot.loaded_quest_datas]
        return str(quest_id) not in str(loaded_quest_ids)

    def quest_in_progress(self, quest_id: int) -> bool:
        """Return True when the quest is present in the in-progress list."""
        loaded_quest_ids = [loaded_quest["QuestID"] for loaded_quest in self.bot.loaded_quest_datas]
        return str(quest_id) in str(loaded_quest_ids)

    def can_turnin_quest(self, questId: int) -> bool:
        """Delegate to the bot helper that checks quest completion requirements."""
        return self.bot.can_turn_in_quest(questId)

    @check_alive
    async def is_green_quest(self, quest_id: int, timeout_sec: float = 3.0) -> bool:
        """Check whether a quest is marked green (ready to turn in).

        Args:
            quest_id (int): Identifier of the quest to inspect.
            timeout_sec (float): Maximum wait time for server response in seconds.

        Returns:
            bool: True when the server reports the quest as green."""
        self.is_green_quest_var = None
        await self.turn_in_quest(quest_id)
        start_time = time.time()
        while(self.is_still_connected()):
            if self.is_green_quest_var is not None:
                output = self.is_green_quest_var
                # print(f"{quest_id} is {self.is_green_quest_var}")
                self.is_green_quest_var = None
                return output
            if time.time() - start_time > timeout_sec:
                self.is_green_quest_var = None
                return False
            await self.sleep(100)
        return False

    @check_alive
    async def is_completed_before(self, quest_id: int, timeout_sec: float = 3.0) -> bool:
        """Determine whether the quest has been completed previously.

        Args:
            quest_id (int): Identifier of the quest to inspect.
            timeout_sec (float): Maximum wait time for server response in seconds.

        Returns:
            bool: True when the server indicates prior completion."""
        if hasattr(self.bot, "one_time_questid") and int(quest_id) in self.bot.one_time_questid:
            return True

        self.is_completed_before_var = None
        await self.turn_in_quest(quest_id)
        start_time = time.time()
        while(self.is_still_connected()):
            if hasattr(self.bot, "one_time_questid") and int(quest_id) in self.bot.one_time_questid:
                self.is_completed_before_var = None
                return True
            if self.is_completed_before_var is not None:
                output = self.is_completed_before_var
                self.is_completed_before_var = None
                return output
            if time.time() - start_time > timeout_sec:
                self.is_completed_before_var = None
                return False
            await self.sleep(100)
        return False

    @check_alive
    async def accept_quest_bulk(self, quest_id: int, increment: int, ensure:bool = False):
        """Accept a range of quests sequentially.

        Args:
            quest_id (int): Starting quest identifier.
            increment (int): Number of consecutive quest ids to process.
            ensure (bool): Use ensure-accept logic for each quest when True."""
        print(f"accepting quest from {quest_id} to {quest_id + increment}")
        for i in range(increment):
            if ensure:
                await self.ensure_accept_quest(quest_id + i)
            elif not ensure:
                await self.accept_quest(quest_id + i)

    @check_alive
    async def register_quest(self, questId: int):
        """Register a quest for auto accept and complete system.

        Args:
            questId (int): Identifier of the quest to register."""
        if questId not in self.bot.registered_auto_quest_ids:
            self.bot.registered_auto_quest_ids.append(questId)
            await self.ensure_accept_quest(questId)

    async def buy_item_cmd(self, item_name: str, shop_id: int, qty: int = 1) -> None:
        """Buy an item from a shop, loading data when necessary.

        Args:
            item_name (str): Name of the shop item to purchase.
            shop_id (int): Identifier of the shop to query.
            qty (int): Quantity to purchase in a single request.

        Returns:
            None: The coroutine sends the purchase packet asynchronously.
        """
        await self.bot.ensure_leave_from_combat()
        shop = None
        for loaded_shop in self.bot.loaded_shop_datas:
            if str(loaded_shop.shop_id) == str(shop_id):
                shop = loaded_shop
                break
        if shop:
            for shop_item in shop.items:
                if shop_item.item_name == item_name.lower():
                    packet = f"%xt%zm%buyItem%{self.bot.areaId}%{shop_item.item_id}%{shop.shop_id}%{shop_item.shop_item_id}%{qty}%"
                    self.bot.write_message(packet)
                    await asyncio.sleep(0.5)
                    break
        else:
            packet = f"%xt%zm%loadShop%{self.bot.areaId}%{shop_id}%"
            self.bot.write_message(packet)
            await asyncio.sleep(1)
            self.bot.index -= 1

    def is_in_bank(self, itemName: str, itemQty: int = 1, operator: str = ">=") -> bool:
        """Check whether the bank holds a given quantity of an item.

        Args:
            itemName (str): Name of the item to inspect.
            itemQty (int): Quantity threshold to test.
            operator (str): Comparison operator understood by the bot API.

        Returns:
            bool: True when the bank fulfils the requested quantity test.
        """
        inBank = self.bot.player.isInBank(itemName, itemQty, operator)
        return inBank[0]

    def is_in_inventory(self, itemName: str, itemQty: int = 1, operator: str = ">=", isTemp: bool = False) -> bool:
        """Check whether the inventory (temp or permanent) has enough items.

        Args:
            itemName (str): Name of the item to inspect.
            itemQty (int): Quantity threshold to test.
            operator (str): Comparison operator understood by the bot API.
            isTemp (bool): When True, inspect the temporary inventory.

        Returns:
            bool: True when the inventory satisfies the quantity requirement.
        """
        inInv = self.bot.player.isInInventory(itemName, itemQty, operator, isTemp)
        return inInv[0]

    def is_in_inventory_or_bank(self, itemName: str, itemQty: int = 1, operator: str = ">=", isTemp: bool = False) -> bool:
        """Check whether an item is available in bank or inventory.

        Args:
            itemName (str): Name of the item to inspect.
            itemQty (int): Quantity threshold to test.
            operator (str): Comparison operator understood by the bot API.
            isTemp (bool): When True, include the temporary inventory.

        Returns:
            bool: True when either storage location satisfies the check.
        """
        return self.is_in_bank(itemName, itemQty, operator) or self.is_in_inventory(itemName, itemQty, operator, isTemp)

    def get_quant_item(self, itemName: str) -> int:
        """Return the current quantity of an item in the inventory.

        Args:
            itemName (str): Name of the inventory item.

        Returns:
            int: Quantity of the item, or 0 when the item is missing.
        """
        # get item quant from inventory
        item_inventory = self.bot.player.get_item_inventory(itemName)
        if item_inventory:
            return item_inventory.qty
        return 0

    def farming_logger(self, item_name: str, item_qty: int = 1, is_temp: bool = False) -> None:
        """Log farming progress for a specific item.

        Args:
            item_name (str): Name of the item being farmed.
            item_qty (int): Target quantity for the farming session.
            is_temp (bool): Whether to read from the temporary inventory.

        Returns:
            None: Prints progress information to the console.
        """
        # Determine inventory type and fetch the item
        inventory_type = "temp" if is_temp else "inv"
        get_inventory = (
            self.bot.player.get_item_temp_inventory
            if is_temp else self.bot.player.get_item_inventory
        )

        # Fetch the item
        item = get_inventory(item_name)
        inv_item_qty = item.qty if item else 0

        # Prepare log message
        current_time = datetime.now().strftime('%H:%M:%S')
        message = (
            f"{Fore.CYAN}[{current_time}] [{inventory_type}] {item_name} "
            f"{inv_item_qty}/{item_qty}{Fore.RESET}"
        )

        # Print log message
        print(message)

    @check_alive
    async def bank_to_inv(self, itemNames: Union[str, List[str]]) -> None:
        """Move items from the bank to the inventory.

        Args:
            itemNames (Union[str, List[str]]): Single name or list of names to transfer.

        Returns:
            None: The coroutine issues move requests for each item.
        """
        itemNames = itemNames if isinstance(itemNames, list) else [itemNames]
        for item in itemNames:
            if not self.is_still_connected():
                return
            item = self.bot.player.get_item_bank(item)        
            if item:
                packet = f"%xt%zm%bankToInv%{self.bot.areaId}%{item.item_id}%{item.char_item_id}%"
                self.bot.write_message(packet)
                is_exist = False
                for itemInv in self.bot.player.INVENTORY:
                    if itemInv.item_name == item.item_name:
                        self.bot.player.INVENTORY.remove(itemInv)
                        self.bot.player.INVENTORY.append(item)
                        is_exist = True
                        break
                if not is_exist:
                    self.bot.player.INVENTORY.append(item)
                for itemBank in self.bot.player.BANK:
                    if itemBank.item_name == item.item_name:
                        self.bot.player.BANK.remove(itemBank)
                        break
                await asyncio.sleep(1)

    @check_alive
    async def inv_to_bank(self, itemNames: Union[str, List[str]]) -> None:
        """Move items from the inventory to the bank.

        Args:
            itemNames (Union[str, List[str]]): Single name or list of names to transfer.

        Returns:
            None: The coroutine issues transfer packets for each item.
        """
        await self.leave_combat()
        itemNames = itemNames if isinstance(itemNames, list) else [itemNames]
        for item in itemNames:
            if not self.is_still_connected():
                return
            item = self.bot.player.get_item_inventory(item)        
            if item:
                packet = f"%xt%zm%bankFromInv%{self.bot.areaId}%{item.item_id}%{item.char_item_id}%"
                self.bot.write_message(packet)
                is_exist = False
                for itemBank in self.bot.player.BANK:
                    if itemBank.item_name == item.item_name:
                        self.bot.player.BANK.remove(itemBank)
                        self.bot.player.BANK.append(item)
                        is_exist = True
                        break
                if not is_exist:
                    self.bot.player.BANK.append(item)
                for itemInv in self.bot.player.INVENTORY:
                    if itemInv.item_name == item.item_name:
                        self.bot.player.INVENTORY.remove(itemInv)
                        break
                await asyncio.sleep(1)

    @check_alive
    async def equip_item(self, item_name: str) -> bool:
        """Equip an inventory item, withdrawing it from the bank if needed.

        Lookup order is deliberate, and is what a caller relies on to decide
        whether to abort:

        1. in inventory and already equipped -> True, nothing sent;
        2. in inventory -> equip it, True;
        3. in the **bank** only -> withdraw it (``bank_to_inv``), then equip,
           True -- classes are commonly banked, so this stops "the class is
           owned but not worn" from looking like a missing item;
        4. in neither -> False, with a message saying which was checked.

        Args:
            item_name (str): Name of the item to equip.

        Returns:
            bool: True when the item is equipped afterwards, False when it is
            in neither inventory nor bank.  Callers that must not run with the
            wrong gear (see ``bot.ultra.core_ultra.CoreUltra.apply_loadout``)
            stop the bot on False instead of fighting in whatever was on.
        """
        await self.bot.ensure_leave_from_combat()

        if await self._equip_held_item(item_name):
            return True

        if self.is_in_bank(item_name):
            print(Fore.CYAN +
                  f"[equip_item] {item_name!r} is in the bank -- withdrawing it"
                  + Fore.RESET)
            await self.bank_to_inv(item_name)
            if await self._equip_held_item(item_name):
                return True

        print(Fore.YELLOW +
              f"[equip_item] {item_name!r} is in neither inventory nor bank "
              f"({len(self.bot.player.INVENTORY)} in inventory, "
              f"{len(self.bot.player.BANK)} in bank)." + Fore.RESET)
        return False

    async def _equip_held_item(self, item_name: str) -> bool:
        """Equip from ``INVENTORY`` only; False when the name matches nothing.

        Split out so ``equip_item`` can retry it after withdrawing from the
        bank rather than duplicating the match-and-packet logic.
        """
        is_equipped = False
        s_type = None
        for item in self.bot.player.INVENTORY:
            if normalize(item.item_name.lower()) == normalize(item_name.lower()):
                if item.is_equipped:
                    return True
                print(f"equipping {item_name}")
                packet = f"%xt%zm%equipItem%{self.bot.areaId}%{item.item_id}%"
                self.bot.write_message(packet)
                is_equipped = True
                s_type = item.s_type
                item.is_equipped = is_equipped
                await asyncio.sleep(1)
                break
        # Update unequip previous item
        if is_equipped and s_type:
            for item in self.bot.player.INVENTORY:
                if item.s_type == s_type and item.is_equipped and not item.item_name == item_name.lower():
                    item.is_equipped = False
                    break
        return is_equipped

    @check_alive
    async def equip_scroll(self, item_name: str, item_type: ScrollType = ScrollType.SCROLL) -> bool:
        """Equip a scroll or potion from the player's inventory.

        Args:
            item_name (str): Name of the scroll or potion to equip.
            item_type (ScrollType): Scroll category to include in the packet.

        Returns:
            bool: True when the scroll was found and its packet sent, False
            when inventory has no item by that name -- so a caller can refuse
            to start a fight that depends on the scroll.
        """
        for item in self.bot.player.INVENTORY:
            if item.item_name.lower() == item_name.lower():
                packet = f"%xt%zm%geia%{self.bot.areaId}%{item_type.value}%{item.s_meta}%{item.item_id}%"
                self.bot.scroll_id = item.item_id
                self.bot.write_message(packet)
                await asyncio.sleep(1)
                return True
        print(Fore.YELLOW +
              f"[equip_scroll] {item_name!r} is not in inventory "
              f"({len(self.bot.player.INVENTORY)} items checked)." + Fore.RESET)
        return False

    @check_alive
    async def equip_item_by_enhancement(self, enh_id: int) -> bool:
        """Equip the first item carrying a given enhancement.

        Backwards-compatible wrapper over :meth:`equip_enhancement`.

        Args:
            enh_id (int): Prefer an ``EnhID`` (the enhancement's unique item
                id, e.g. 70752 = Valiance R7).  An ``EnhPatternID`` is still
                accepted for old call sites, but patterns are ambiguous --
                pattern 10 covers seven different weapon enhancements -- so
                prefer the name (``equip_enhancement("Valiance")``) or the id.

        Returns:
            bool: True when an item was found and equip was attempted.
        """
        return await self.equip_enhancement(enh_id)

    @check_alive
    async def equip_enhancement(self, enhancement: Union[int, str],
                                slot: Optional[str] = None, *,
                                level: Optional[int] = None,
                                rarity: Optional[int] = None) -> bool:
        """Equip whatever item has a given enhancement socketed.

        This is the "which weapon do I want" selector: pick the enhancement and
        the item carrying it gets equipped, rather than naming the item.

        An enhancement only fits one slot -- Valiance a weapon, Penitence a
        cape, Vim a helm -- so when a name maps to a single slot the filter is
        applied automatically and you do not need to repeat it.

        Args:
            enhancement: An enhancement name (``"Valiance"``), an ``EnhID``
                (70752), a numeric string (``"70752"``), or an ``EnhPatternID``
                (legacy; see the ambiguity note below).
            slot (str): Overrides the slot inferred from the enhancement.
                Accepts readable names (``"weapon"``, ``"helm"``, ``"cape"``,
                ``"class"``, ``"armor"``) or raw ``sES`` codes (``"Weapon"``,
                ``"he"``, ``"ba"``, ``"ar"``, ``"co"``).
            level (int): Only meaningful for a *basic* enhancement named as
                text.  Those shops sell one name at every level 51..100, so
                the name is a family and ``level`` picks the tier.  Ignored
                when ``enhancement`` is an id, since an id is already unique.
            rarity (int): Further narrows a ``level`` lookup.  Needed only at
                the cap, where level 100 exists at both rarity 5 and 6.

        Returns:
            bool: True when a matching item was found and the equip packet was
                sent.  False means *nothing matched* -- unknown name, empty
                inventory, ambiguous target with no slot, a ``level`` the shop
                does not sell, or no owned item -- and prints why, so callers
                fail loudly instead of silently doing nothing.

        Example::

            await cmd.equip_enhancement("Valiance")      # equips a weapon
            await cmd.equip_enhancement("Penitence")     # equips a cape
            await cmd.equip_enhancement("Forge", slot="he")
            await cmd.equip_enhancement(70752)           # Valiance R7 by id
            await cmd.equip_enhancement("Wizard Armor Enhancement",
                                        level=100)       # basic, by tier
            await cmd.equip_enhancement("Wizard Armor Enhancement",
                                        level=100, rarity=6)  # -> 52276

        Note:
            Passing a raw pattern id (the old ``enh_pattern_id=`` style) is
            ambiguous for pattern 10, which seven weapon enhancements share --
            "equip pattern 10" has no single right answer.  A warning names the
            candidates and asks for ``slot=``; every other pattern maps to one
            enhancement and resolves cleanly.  Pattern 6 became shared too
            once the basic file was added: forge *Elysium* and basic *Wizard*
            both report it, so prefer a name or an EnhID there as well.
        """
        from model import enhancement as enh

        # --- normalise / validate the slot -----------------------------
        try:
            wanted_slot = enh.slot_code(slot)
        except ValueError as exc:
            print(Fore.YELLOW + f"[equip_enhancement] {exc}" + Fore.RESET)
            return False

        # --- resolve the enhancement itself ----------------------------
        records: List = []
        # What we ultimately match inventory against.  A `level` lookup
        # narrows a *name* to a set of EnhIDs, so the name is matched first
        # and then filtered down to `tier_ids`.
        target: Union[int, str] = enhancement
        tier_ids: Optional[set] = None
        tier_by_id: dict = {}
        named = isinstance(enhancement, str) and not enhancement.strip().isdigit()
        if named:
            records = enh.find(enhancement)
            if not records:
                known = ", ".join(enh.names()) or "(no enhancement data loaded)"
                print(Fore.YELLOW +
                      f"[equip_enhancement] no enhancement named "
                      f"{enhancement!r}. Known: {known}." + Fore.RESET)
                return False
            if level is not None:
                # Basic shops sell one name at every level 51..100, so the
                # name is a family and level picks the tier out of it.
                narrowed = enh.by_name_level(enhancement, level,
                                             slot=wanted_slot, rarity=rarity)
                if not narrowed:
                    tiers = sorted({r.level for r in records})
                    print(Fore.YELLOW +
                          f"[equip_enhancement] {enhancement!r} has no tier at "
                          f"level {level}{' rarity ' + str(rarity) if rarity is not None else ''} "
                          f"(shop sells levels {tiers[0]}..{tiers[-1]})."
                          + Fore.RESET)
                    return False
                # Keep every tier at this level and let inventory decide:
                # level 100 exists at rarity 5 and 6, and committing to one
                # up front fails when the account only owns the other.
                # `target` stays the name so the match is broad, then the
                # filter below restricts it to exactly these ids.
                records = narrowed
                tier_ids = {r.item_id for r in narrowed}
                tier_by_id = {r.item_id: r for r in narrowed}
        else:
            enh_id = int(enhancement)
            rec = enh.get(enh_id)
            records = [rec] if rec else enh.by_pattern(enh_id)
            if not records:
                # No name for this id -- it came from a shop we never
                # captured.  The id itself is still unique, so match
                # inventory on it directly (this is what the old
                # equip_item_by_by_enhancement(enh_id) did).  Slot stays
                # unknown: pass slot= if the enhancement could span slots.
                target = enh_id
                print(Fore.CYAN +
                      f"[equip_enhancement] EnhID {enh_id} is not in "
                      f"forge_enhancement.jsonl or basic_enhancement.jsonl; "
                      f"matching it by raw id." + Fore.RESET)

        # --- infer the slot when the enhancement implies exactly one ----
        implied = {r.slot for r in records}
        if wanted_slot is None and len(implied) == 1:
            wanted_slot = implied.pop()
        elif wanted_slot is None and len(implied) > 1:
            labels = ", ".join(sorted(enh.SLOT_LABELS.get(s, s)
                                      for s in implied))
            print(Fore.YELLOW +
                  f"[equip_enhancement] {enhancement!r} fits more than one "
                  f"slot ({labels}); pass slot= to choose." + Fore.RESET)
            return False

        # --- warn when the target is a pattern shared by several names ---
        # Only meaningful when the id actually resolved through the pattern
        # table.  An id in neither capture leaves `records` empty and takes
        # the raw-id path above, where there is nothing shared to warn about.
        if records and (isinstance(enhancement, (int,)) or
                        str(enhancement).isdigit()):
            pattern_id = int(enhancement)
            if not enh.get(pattern_id) and not enh.is_pattern_unique(pattern_id):
                labels = ", ".join(sorted({r.name for r in records}))
                print(Fore.YELLOW +
                      f"[equip_enhancement] pattern {pattern_id} is shared by "
                      f"{len(records)} enhancements ({labels}); matching all "
                      f"of them. Prefer the name or an EnhID." + Fore.RESET)

        if not self.bot.player.INVENTORY:
            print(Fore.YELLOW +
                  "[equip_enhancement] inventory is empty, cannot select an "
                  "item. Load it first." + Fore.RESET)
            return False

        items = self.bot.player.get_items_by_enhancement(target,
                                                         slot=wanted_slot)
        if tier_ids is not None:
            # Keep only the tiers this level actually sells.  Among them prefer
            # the highest rarity: at level 100 both cost the same, so the
            # rarity-6 one is simply the better item.
            items = [i for i in items if i.enh_id in tier_ids]
            items.sort(key=lambda i: (
                tier_by_id[i.enh_id].rarity, i.enh_id), reverse=True)
        if not items:
            label = records[0].name if len(records) == 1 else str(enhancement)
            tier = f" (level {level})" if level is not None else ""
            scope = (f" in slot "
                     f"{enh.SLOT_LABELS.get(wanted_slot, wanted_slot)}"
                     if wanted_slot else "")
            owned = sum(1 for i in self.bot.player.INVENTORY
                        if i.enh_id or i.enh_pattern_id)
            want = ""
            if tier_ids:
                want = (f"; shop tiers for this level are "
                        f"{', '.join(str(i) for i in sorted(tier_ids))}")
            print(Fore.YELLOW +
                  f"[equip_enhancement] no owned item carries {label}{tier}"
                  f"{scope} ({owned} enhancements in inventory){want}."
                  + Fore.RESET)
            return False

        if len(items) > 1:
            names = ", ".join(i.item_name for i in items[:4])
            more = "" if len(items) <= 4 else f", +{len(items) - 4} more"
            if tier_ids:
                # Sorted best-first by rarity; say which one won.
                top = items[0]
                print(Fore.CYAN +
                      f"[equip_enhancement] {len(items)} owned items carry "
                      f"this enhancement ({names}{more}); using the "
                      f"highest-rarity one -- {top.item_name} (EnhID "
                      f"{top.enh_id}). Pass rarity= to choose." + Fore.RESET)
            else:
                print(Fore.YELLOW +
                      f"[equip_enhancement] {len(items)} items carry this "
                      f"enhancement ({names}{more}); equipping the first. Pass "
                      f"slot= or name the item directly to choose." + Fore.RESET)

        chosen = items[0]
        label = records[0].name if len(records) == 1 else str(enhancement)
        slot_label = (enh.SLOT_LABELS.get(wanted_slot, wanted_slot)
                      if wanted_slot else "any slot")
        tier = f" level {level}" if level is not None else ""
        print(Fore.CYAN +
              f"[equip_enhancement] equipping {chosen.item_name!r} for "
              f"enhancement {label}{tier} in {slot_label} "
              f"(EnhID {chosen.enh_id})" + Fore.RESET)

        await self.equip_item(chosen.item_name)
        return True

    def add_drop(self, itemName: Union[str, List[str]]) -> None:
        """Add items to the drop whitelist handled by the bot.

        Args:
            itemName (Union[str, List[str]]): Single name or list of names to whitelist.

        Returns:
            None: Extends the whitelist in place.
        """
        if isinstance(itemName, str):
            itemName = [itemName]

        for item in itemName:
            if item not in self.bot.items_drop_whitelist:
                self.bot.items_drop_whitelist.append(item)

    @check_alive
    async def get_map_item(self, map_item_id: int, qty: int = 1, item_name: Optional[str] = None) -> None:
        """Collect a map item until target quantity is reached.

        Args:
            map_item_id (int): Map item identifier to pick up.
            qty (int): Target quantity to collect.
            item_name (str, optional): Expected temp item name to verify quantity.
        """
        if item_name:
            attempts = 0
            while self.is_still_connected() and not self.is_in_inventory(item_name, qty, isTemp=True) and attempts < qty * 3 + 6:
                self.bot.write_message(f"%xt%zm%getMapItem%{self.bot.areaId}%{map_item_id}%")
                await asyncio.sleep(1.2)
                attempts += 1
            return

        initial_counts = {item.item_id: item.qty for item in self.bot.player.TEMPINVENTORY}
        detected_item_name = None
        attempts = 0
        max_attempts = qty * 3 + 6

        while self.is_still_connected() and attempts < max_attempts:
            if detected_item_name and self.is_in_inventory(detected_item_name, qty, isTemp=True):
                break

            self.bot.write_message(f"%xt%zm%getMapItem%{self.bot.areaId}%{map_item_id}%")
            await asyncio.sleep(1.2)
            attempts += 1

            if not detected_item_name:
                for item in self.bot.player.TEMPINVENTORY:
                    old_qty = initial_counts.get(item.item_id, 0)
                    if item.qty > old_qty:
                        detected_item_name = item.item_name
                        break

            if detected_item_name and self.is_in_inventory(detected_item_name, qty, isTemp=True):
                break

            if attempts >= qty and not detected_item_name:
                break

    @check_alive
    async def load_shop(self, shop_id: int) -> None:
        """Request shop data from the server and wait for the response.

        Args:
            shop_id (int): Identifier of the shop to load.

        Returns:
            None: Awaits for a short delay to let the data load.
        """
        msg = f"%xt%zm%loadShop%{self.bot.areaId}%{shop_id}%"
        self.bot.write_message(msg)
        await self.sleep(1000)

    @check_alive
    def get_loaded_shop(self, shop_id: int) -> Optional[Shop]:
        """Return a loaded shop instance when available.

        Args:
            shop_id (int): Identifier of the shop to look up.

        Returns:
            Shop | None: Cached shop instance, or None if it has not been loaded.
        """
        for loaded_shop in self.bot.loaded_shop_datas:
            if str(loaded_shop.shop_id) == str(shop_id): 
                return loaded_shop
        return None

    @check_alive
    async def sell_item(self, item_name: str, qty: int = 1) -> None:
        """Sell an item from the inventory.

        Args:
            item_name (str): Name of the item to sell.
            qty (int): Quantity to sell in a single transaction.

        """
        # %xt%zm%sellItem%374121%87406%1%950679343%
        item = self.bot.player.get_item_inventory(item_name)
        if item:
            self.bot.debug(f"Selling {qty}x {item_name}...")
            self.bot.write_message(f"%xt%zm%sellItem%{self.bot.areaId}%{item.item_id}%{qty}%{item.char_item_id}%")
            await self.sleep(500)

    @check_alive
    async def buy_item(self, shop_id: int, item_name: str, qty: int = 1) -> None:
        """Buy an item, loading the shop if it is not cached.

        Args:
            shop_id (int): Identifier of the shop containing the item.
            item_name (str): Name of the item to purchase.
            qty (int): Quantity to purchase in a single request.

        Returns:
            None: Sends the buy packet once the shop data is available.
        """
        print(f"buying {qty} {item_name}")
        shop: Optional[Shop] = None
        for loaded_shop in self.bot.loaded_shop_datas:
            if str(loaded_shop.shop_id) == str(shop_id):
                shop = loaded_shop
                break
        if shop:
            for shop_item in shop.items:
                if shop_item.item_name.lower() == item_name.lower():
                    packet = f"%xt%zm%buyItem%{self.bot.areaId}%{shop_item.item_id}%{shop.shop_id}%{shop_item.shop_item_id}%{qty}%"
                    self.bot.write_message(packet)
                    await asyncio.sleep(1)
                    break
        else:
            packet = f"%xt%zm%loadShop%{self.bot.areaId}%{shop_id}%"
            self.bot.write_message(packet)
            await asyncio.sleep(1)
            # await self.buy_item(shop_id, item_name, qty)

    @check_alive
    async def ensure_load_shop(self, shop_id: int) -> None:
        """Keep loading a shop until it is present in the cache.

        Args:
            shop_id (int): Identifier of the shop to ensure.
        """
        await self.leave_combat()
        while True:
            for loaded_shop in self.bot.loaded_shop_datas:
                if str(loaded_shop.shop_id) == str(shop_id): 
                    print("loaded_Shop", loaded_shop.shop_id)
                    return
            packet = f"%xt%zm%loadShop%{self.bot.areaId}%{shop_id}%"
            self.bot.write_message(packet)
            await asyncio.sleep(1)

    def wait_count_player(self, player_count: int) -> bool:
        """Check if the current map has at least the requested player count."""
        return len(self.bot.user_ids) >= player_count

    def wait_count_player_in_cell(self, cell: str, player_count: int) -> bool:
        """Check if a cell hosts at least the requested number of players."""
        count = 0
        cell = cell.lower()
        for player in self.bot.player_in_area:
            print(player.str_username, player.str_frame, cell)
            if player.str_frame.lower() == cell:
                count += 1

        if self.bot.player.CELL.lower() == cell:
            count += 1
        return count >= player_count

    def get_player_in_map(self, name: str) -> Optional[PlayerArea]:
        """Return the area record for a player in the current map, if present."""
        for player in self.bot.player_in_area:
            if player.str_username.lower() == name.lower():
                return player
        return None

    def is_player_in_cell(self, name: str, cell: str) -> bool:
        """Return True when a named player is currently in the given cell."""
        player = self.get_player_in_map(name)
        if player and player.str_frame and player.str_frame.lower() == cell.lower():
            return True
        return False

    @check_alive
    async def goto_player(self, player_name: str) -> None:
        """Jump to another player on the current server.

        Args:
            player_name (str): Target player name to follow.
        """
        player_in_map = self.get_player_in_map(player_name)
        if player_in_map:
            self.bot.jump_cell(player_in_map.str_frame, player_in_map.str_pad)
        else:
            await self.bot.ensure_leave_from_combat(always=True)
            self.bot.write_message(f"%xt%zm%cmd%1%goto%{player_name}%")
            await self.sleep(1000)

    @check_alive
    async def join_house(self, houseName: str, safeLeave: bool = True) -> None:
        """Join a player house while optionally leaving combat safely.

        Args:
            houseName (str): Name of the house to join.
            safeLeave (bool): Leave combat via spawn before issuing the join request.
        """
        self.stop_aggro()
        if self.bot.strMapName.lower() == houseName.lower():
            return
        self.bot.is_joining_map = True
        await self.leave_combat(safeLeave)
        msg = f"%xt%zm%house%1%{houseName}%"
        self.bot.write_message(msg)

    @check_alive
    async def join_map(self, mapName: str, roomNumber: Optional[int] = None, safeLeave: bool = True) -> None:
        """Join a map instance, picking the appropriate room.

        Args:
            mapName (str): Map identifier to join.
            roomNumber (int | None): Specific room number to target when provided.
            safeLeave (bool): Leave combat before transferring maps.

        Returns:
            None: Records join state and sends the transfer packet.
        """
        self.stop_aggro()
        if self.bot.strMapName.lower() == mapName.lower():
            return
        self.bot.is_joining_map = True
        await self.leave_combat(safeLeave)

        if roomNumber != None:
            msg = f"%xt%zm%cmd%1%tfer%{self.bot.player.USER}%{mapName}-{roomNumber}%"
        elif self.bot.roomNumber != None:
            msg = f"%xt%zm%cmd%1%tfer%{self.bot.player.USER}%{mapName}-{self.bot.roomNumber}%"
        else:
            msg = f"%xt%zm%cmd%1%tfer%{self.bot.player.USER}%{mapName}%"
        self.bot.write_message(msg)

    def is_not_in_map(self, mapName: str) -> bool:
        """Return True when the player is not currently in the given map.

        Args:
            mapName (str): Map identifier to compare.

        Returns:
            bool: True when the current map differs from ``mapName``.
        """
        return mapName.lower() != self.bot.strMapName.lower()
    
    def is_in_map(self, mapName: str) -> bool:
        """Return True when the player is currently in the given map.
        
        Args:
            mapName (str): Map identifier to compare.
            
        Returns:
            bool: True when the current map matches ``mapName``.
        """
        return mapName.lower() == self.bot.strMapName.lower()

    @check_alive
    async def jump_cell(self, cell: str, pad: str) -> None:
        """Jump to a specific cell and pad if not already positioned there.

        Args:
            cell (str): Cell name to move to.
            pad (str): Pad identifier within the cell.

        Returns:
            None: Executes a jump command and waits briefly for sync.
        """
        if str(self.bot.player.CELL or "").lower() != str(cell or "").lower() or str(self.bot.player.PAD or "").lower() != str(pad or "").lower():
            self.bot.jump_cell(cell, pad)
            #print(f"jump cell: {cell} {pad}")
            await asyncio.sleep(1)

    def is_not_in_cell(self, cell: str) -> bool:
        """Check whether the player is standing in a different cell.

        Args:
            cell (str): Cell name to compare with the current position.

        Returns:
            bool: True when the active cell does not match ``cell``.
        """
        return str(self.bot.player.CELL or "").lower() != str(cell or "").lower()

    @check_alive
    async def walk_to(self, X: int, Y: int, speed: int = 8) -> None:
        """Walk to a coordinate within the current map.

        Args:
            X (int): Target X coordinate.
            Y (int): Target Y coordinate.
            speed (int): Movement speed for the walk animation."""
        await self.bot.walk_to(X, Y, speed)
        await self.sleep(200)

    def start_aggro_by_cell(self, cells: list[str], delay_ms : int = 500) -> None:
        """Start aggroing every monster found in the provided cells.

        Args:
            cells (list[str]): Cell names to scan for monsters.
            delay_ms (int): Delay between aggro commands in milliseconds.

        Returns:
            None: Delegates to start_aggro when monsters are present.
        """
        mons_id: list[str] = []
        for monster in self.bot.monsters:
            if monster.frame in cells:
                mons_id.append(str(monster.mon_map_id))

        if len(mons_id) == 0:
            return

        self.start_aggro(mons_id, delay_ms)

    def start_aggro(self, mons_id: list[str], delay_ms: int = 500) -> None:
        """Enable the aggro handler for the supplied monster identifiers.

        Args:
            mons_id (list[str]): Monster identifiers to keep aggroed.
            delay_ms (int): Delay between aggro ticks in milliseconds.

        Returns:
            None: Updates the bot state and starts the aggro task.
        """
        self.stop_aggro()
        self.bot.is_aggro_handler_task_running = True
        self.bot.aggro_mons_id = mons_id
        self.bot.aggro_delay_ms = delay_ms
        self.bot.run_aggro_hadler_task()

    def stop_aggro(self) -> None:
        """Stop the aggro handler and clear tracked monsters.

        Returns:
            None: Clears aggro state without returning a value.
        """
        self.bot.is_aggro_handler_task_running = False
        self.bot.aggro_mons_id = []

    @check_alive
    async def leave_combat(self, safeLeave: bool = True) -> None:
        """Leave combat and optionally jump back to spawn.

        Args:
            safeLeave (bool): Jump to the Enter/Spawn cell after leaving combat when True.

        Returns:
            None: Always returns None; the bot actions run asynchronously.
        """
        await self.bot.ensure_leave_from_combat(always=True)
        if safeLeave:
            await self.jump_cell("Enter", "Spawn")

    @check_alive
    async def jump_to_monster(self, monsterName: str, byMostMonster: bool = True, byAliveMonster: bool = False) -> None:
        """Jump to the cell that currently hosts the requested monster.

        Args:
            monsterName (str): Display name, comma-separated names, or ``id.X`` identifier for the monster.
            byMostMonster (bool): Prefer the cell with the highest monster population when True.
            byAliveMonster (bool): Prefer a cell that still has the monster alive when True.

        Returns:
            None: The coroutine adjusts player position and exits.
        """
        # Wait briefly if map transfer is in progress or monster definitions haven't loaded yet
        for _ in range(15):
            if not self.bot.is_joining_map and self.bot.monsters:
                break
            await asyncio.sleep(0.2)

        if not self.bot.monsters:
            return

        targets = [t.strip().lower() for t in str(monsterName or "*").split(',') if t.strip()]
        if not targets:
            targets = ["*"]

        def _is_match(mon: Monster) -> bool:
            if not mon.frame:
                return False
            if "*" in targets:
                return True
            m_name = (mon.mon_name or "").lower()
            m_id = str(mon.mon_map_id)
            for t in targets:
                if t.startswith("id.") and t.split(".")[1] == m_id:
                    return True
                if t == m_id or t == m_name:
                    return True
            return False

        matching_monsters = [m for m in self.bot.monsters if _is_match(m)]
        if not matching_monsters:
            return

        player_cell = str(self.bot.player.CELL or "").lower()
        current_cell_monsters = [m for m in matching_monsters if str(m.frame or "").lower() == player_cell]
        current_cell_alive = [m for m in current_cell_monsters if m.is_alive and m.current_hp > 0]

        # Case 1: If searching for alive monsters and an alive monster is already in our cell, stay.
        if byAliveMonster and current_cell_alive:
            return

        # Case 2: If alive monster preferred and there are alive monsters in other cells, pick the best one.
        target_cell = None
        if byAliveMonster:
            alive_other = [m for m in matching_monsters if m.is_alive and m.current_hp > 0 and str(m.frame or "").lower() != player_cell]
            if alive_other:
                cell_counts = {}
                for m in alive_other:
                    cell_counts[m.frame] = cell_counts.get(m.frame, 0) + 1
                target_cell = max(cell_counts, key=cell_counts.get)

        # Case 3: If target_cell not determined yet (or not byAliveMonster):
        if not target_cell:
            if current_cell_monsters and not byMostMonster:
                return

            cell_counts = {}
            for m in matching_monsters:
                cell_counts[m.frame] = cell_counts.get(m.frame, 0) + 1

            if cell_counts:
                best_cell = max(cell_counts, key=cell_counts.get)
                if str(best_cell).lower() == player_cell:
                    return
                target_cell = best_cell

        if not target_cell:
            return

        if str(target_cell).lower() == player_cell:
            return

        self.bot.jump_cell(target_cell, "Left")
        await asyncio.sleep(1)

    @check_alive
    async def wait_use_skill(self, index: int, target_monsters: str = "*") -> None:
        """Wait until a skill is ready before casting it.

        Args:
            index (int): Skill slot to trigger.
            target_monsters (str): Comma-separated monster names or ``id.X`` identifiers to focus.

        Returns:
            None: The coroutine finishes once the skill has been used.
        """
        while self.is_still_connected() and not self.bot.player.canUseSkill(int(index)):
            await self.sleep(100)
        if not self.is_still_connected():
            return
        await self.use_skill(index, target_monsters)

    def check_is_skill_safe(self, skill: int) -> bool:
        """Return whether a skill is safe to use at the current HP threshold.

        Args:
            skill (int): Skill slot that is about to be executed.

        Returns:
            bool: True when the skill can be used safely for the equipped class.
        """
        
        conditions = {
            "void highlord": {
                "hp_threshold": 50, 
                "skills_to_check": [1, 3],
                "condition": lambda hp, threshold: hp > threshold
            },
            "scarlet sorceress": {
                "hp_threshold": 50,
                "skills_to_check": [1, 4],
                "condition": lambda hp, threshold: hp > threshold
            },
            "dragon of time": {
                "hp_threshold": 40,
                "skills_to_check": [1, 3],
                "condition": lambda hp, threshold: hp > threshold
            },
            "healer": {
                "hp_threshold": 70,
                "skills_to_check": [2],
                "condition": lambda hp, threshold: hp < threshold
            },
            # "archpaladin": {
            #     "hp_threshold": 70,
            #     "skills_to_check": [2],
            #     "condition": lambda hp, threshold: hp < threshold
            # },
        }

        equipped_class = self.bot.player.get_equipped_item(ItemType.CLASS)
        
        if equipped_class:
            class_name = equipped_class.item_name.lower()
            
            if class_name in conditions:
                condition_data = conditions[class_name]
                
                if skill in condition_data["skills_to_check"]:
                    current_hp_pct = (self.bot.player.CURRENT_HP / self.bot.player.MAX_HP) * 100
                    return condition_data["condition"](current_hp_pct, condition_data["hp_threshold"])
        return True

    @check_alive
    async def use_skill(self,  
                        index: int = 0, 
                        target_monsters: str = "*", 
                        hunt: bool = False, 
                        skill_mode: SkillMode = SkillMode.ALL,
                        reload_delay: int = MIN_SKILL_GAP_MS,
                        *,
                        buff_only: bool = False,
        ) -> bool:
        """Execute a skill with optional hunting, targeting, and cooldown handling.

        Args:
            index (int): Skill slot that should be triggered. ``5`` is the
                scroll/potion slot: call ``equip_scroll(...)`` once first so
                ``bot.scroll_id`` is set, then ``use_skill(5, ...)``. There is
                no per-call scroll id -- the equipped scroll is the scroll.
            target_monsters (str): Target filter, ``*`` for any or comma-separated list.
            hunt (bool): When True, jump to the monster before casting.
            skill_mode (SkillType): Defines which types of skills (buff, attack, all, none) can be used.
            reload_delay (int): Pacing floor in milliseconds before a non-zero
                slot may fire again after the previous packet. This used to be a
                global "reload gate" armed by every cast and read only by
                non-zero slots; it is kept, because removing it was measured to
                get 42% of casts rejected as "too soon" (see class constants).
                Slot 0 ignores it and uses AUTO_ATTACK_MIN_GAP_MS instead.
            buff_only (bool): Shorthand for ``skill_mode=SkillMode.BUFF_ONLY``.
                When True it wins over ``skill_mode``.

        Keyword-only after ``reload_delay``:
            ``buff_only`` is keyword-only, so no positional caller -- existing
            or new -- can shift into it. ``scroll_id`` used to sit here too and
            has been removed: every caller passes ``index == 5`` and lets the
            scroll come from ``bot.scroll_id``.

        Returns:
            bool: True if the skill was successfully executed, False otherwise.
        """
        if buff_only:
            skill_mode = SkillMode.BUFF_ONLY
        if skill_mode == SkillMode.NONE:
            return False
        index = int(index)
        if not self.bot.player.canUseSkill(index) or not self.check_is_skill_safe(index):
            return False

        skill = self.bot.player.SKILLS[index]
        self.bot.skillAnim = skill.get("anim", None)
        # skill.max_targets coerces the payload's `tgtMax: null` (which the
        # item/scroll slot sends) to 1 instead of raising int(None).
        max_target = skill.max_targets
        # Which pacing floor governs this slot -- see the class constants for
        # why slot 0 (auto-attack) gets a much shorter one than real skills.
        gap_ms = self.AUTO_ATTACK_MIN_GAP_MS if index == 0 else reload_delay

        packet_sent = False

        if skill.target == "h" and skill_mode in (SkillMode.ALL, SkillMode.ATTACK_ONLY): 
            priority_monsters_id = []
            if hunt and len(target_monsters.split(",")) == 1 and target_monsters != "*":
                await self.jump_to_monster(target_monsters, byAliveMonster=True)
            player_cell = str(self.bot.player.CELL or "").lower()
            cell_monsters_id = [mon.mon_map_id for mon in self.bot.monsters if str(mon.frame or "").lower() == player_cell and mon.is_alive and mon.current_hp > 0]
            cell_monsters = [mon for mon in self.bot.monsters if str(mon.frame or "").lower() == player_cell and mon.is_alive and mon.current_hp > 0]
            final_ids = []
            if target_monsters != "*":
                # Mapping priority_monsters_id
                target_ids = []
                target_names = []
                for target_monster in target_monsters.split(','):
                    if target_monster.startswith('id.'):
                        target_ids.append(target_monster.split('.')[1])
                    else:
                        target_names.append(target_monster.lower())

                # Step 1: build a map of alive monsters in current cell
                alive_monsters = {mon.mon_map_id: mon for mon in self.bot.monsters if str(mon.frame or "").lower() == player_cell and mon.is_alive and mon.current_hp > 0}

                priority_monsters_id = []

                # Step 2: follow *input* order strictly
                for target in target_monsters.split(','):
                    if target.startswith("id."):
                        mon_id = target.split(".")[1]
                        if mon_id in alive_monsters:
                            priority_monsters_id.append(mon_id)
                    else:
                        name = target.lower()
                        for mon in self.bot.monsters:
                            if str(mon.frame or "").lower() == player_cell and mon.is_alive and mon.current_hp > 0 and mon.mon_name.lower() == name:
                                priority_monsters_id.append(mon.mon_map_id)

                # Step 3: merge into cell_monsters_id (dedup, keep priority first)
                final_ids = []
                seen = set()

                # First: priority in order
                for mon_id in priority_monsters_id:
                    if mon_id not in seen:
                        final_ids.append(mon_id)
                        seen.add(mon_id)

                # Then: the rest
                for mon_id in cell_monsters_id:
                    if mon_id not in seen:
                        final_ids.append(mon_id)
                        seen.add(mon_id)

            else:
                cell_monsters.sort(key=lambda m: m.current_hp)
                final_ids = [mon.mon_map_id for mon in cell_monsters]
            
            if not final_ids:
                return False

            await self._pace_skill_cast(gap_ms)
            if index == 5:
                # The scroll id comes from bot.scroll_id, set by equip_scroll().
                self.bot.use_scroll(final_ids, max_target)
            if index < 5:
                self.bot.use_skill_to_monster("a" if index == 0 else index, final_ids, max_target)
            packet_sent = True
        
        if skill_mode in (SkillMode.ALL, SkillMode.BUFF_ONLY):
            if skill.target == "f":
                await self._pace_skill_cast(gap_ms)
                self.bot.use_skill_to_player(index, max_target)
                packet_sent = True
            if skill.target == "s":
                await self._pace_skill_cast(gap_ms)
                self.bot.use_skill_to_myself(index)
                packet_sent = True

        if not packet_sent:
            # skill_mode filtered this slot out, so nothing went on the wire.
            # Previously this still armed the cooldown and returned True, which
            # locked a slot for a full cooldown without ever casting it.
            return False

        # Arm the cooldown at the moment the packet goes out. The 200 ms the old
        # code spent sleeping here is now the explicit start_delay_ms inside
        # updateNextUse, so server-side timing is unchanged but this coroutine
        # returns immediately and the scheduler can line up the next cast.
        self._mark_skill_cast()
        self.bot.player.updateNextUse(index, start_delay_ms=self.CD_START_DELAY_MS)
        return True

    async def _pace_skill_cast(self, min_gap_ms: int) -> None:
        """Hold the loop until ``min_gap_ms`` elapsed since the previous cast.

        This is a *floor*, not a fixed delay: if the last cast was already long
        ago the coroutine returns immediately. The server's backoff
        (``Bot.spam_backoff_ms``) is added on top so a "slow down" warning
        actually slows the bot down -- the old ``skill_delay_ms`` counter was
        incremented but never read by anything, so it never could.
        """
        now = int(round(datetime.now().timestamp() * 1000))
        wait = min_gap_ms + max(0, getattr(self.bot, "spam_backoff_ms", 0)) \
               - (now - self.last_skill_cast_ms)
        if wait > 0:
            await self.sleep(wait)

    def _mark_skill_cast(self) -> None:
        """Record the moment the most recent skill packet went out."""
        self.last_skill_cast_ms = int(round(datetime.now().timestamp() * 1000))

    @check_alive
    async def use_next_skill(self,
                             skill_list: list[int],
                             target_monsters: str = "*",
                             hunt: bool = False,
                             skill_mode: SkillMode = SkillMode.ALL,
                             reload_delay: int = MIN_SKILL_GAP_MS) -> bool:
        """Cast whichever listed skill is ready, instead of round-robining.

        The old templates advanced one position per iteration no matter what,
        so 1096 of 1899 attempts in the baseline run bounced off a cooldown and
        the 1.5 s skill was starved by 6-12 s skills holding rotation slots.
        This picks from the ready set instead, and when *nothing* is ready it
        sleeps exactly until the earliest cooldown expires rather than polling
        on a blind delay.

        Args:
            skill_list (list[int]): Candidate slots. Duplicates such as the
                ``[0,1,2,0,3,4]`` rotation are collapsed on the way in.

        Returns:
            bool: True only when a packet was actually sent.
        """
        ready: list[int] = []
        soonest: Optional[float] = None
        for slot in dict.fromkeys(skill_list):
            if not self.check_is_skill_safe(slot):
                continue
            wait = self.bot.player.skill_ready_in_ms(slot)
            if wait <= 0:
                ready.append(slot)
            elif soonest is None or wait < soonest:
                soonest = wait

        if not ready:
            await self.sleep(max(20, min(soonest if soonest is not None else 100.0, 500.0)))
            return False

        # Rarest cooldown first: a long-cooldown skill starts its long timer as
        # early as possible, and the short-cooldown slot fills the gaps left.
        slot = max(ready, key=lambda s: self.bot.player.effective_cd_ms(s))
        if await self.use_skill(slot, target_monsters, hunt, skill_mode, reload_delay):
            return True

        # Ready but refused (no target in the cell, filtered by skill_mode, or
        # the player died mid-call): back off so the same slot cannot spin the
        # caller's loop at full speed.
        await self.sleep(100)
        return False

    @check_alive
    def do_pwd(self, monster_id: str) -> None:
        """Send a raw PWD packet to the server for a specific monster.

        Args:
            monster_id (str): Monster identifier to include in the packet payload.

        Returns:
            None: The message is sent and no value is returned.
        """
        # %xt%zm%gar%1%3%p6>m:1%wvz%
        self.bot.write_message(f"%xt%zm%gar%1%3%p6>m:{monster_id}%wvz%")

    def is_monster_alive(self, monster: str = "*") -> bool:
        """Check whether a monster is alive in the player's current cell.

        Args:
            monster (str): Name or ``id.X`` identifier of the monster, ``*`` for any.

        Returns:
            bool: True when a matching live monster is found in the cell.
        """
        if monster.startswith('id.'):
            monster = monster.split('.')[1]
        player_cell = str(self.bot.player.CELL or "").lower()
        for mon in self.bot.monsters:
            if mon.is_alive and mon.current_hp > 0 and str(mon.frame or "").lower() == player_cell:
                if monster == "*":
                    return True
                elif mon.mon_name and mon.mon_name.lower() == monster.lower():
                    return True
                elif mon.mon_map_id == monster:
                    return True
        return False

    @check_alive
    def get_monster_hp(self, monster: str) -> int:
        """Get the current HP of the requested monster.

        Args:
            monster (str): Name or ``id.X`` identifier of the monster, ``*`` for any.

        Returns:
            int: Current HP, or -1 when the monster is not found.
        """
        if monster == None:
            return -1
        if monster.startswith('id.'):
            monster = monster.split('.')[1]
        for mon in self.bot.monsters:
            if mon.mon_name.lower() == monster.lower() or mon.mon_map_id == monster and mon.is_alive:
                return mon.current_hp
            elif monster == "*":
                return mon.current_hp
        # this mean not get the desired monster
        return -1

    def get_monster_hp_percentage(self, monster: str) -> int:
        """Get the remaining HP of a monster as a percentage.

        Args:
            monster (str): Name or ``id.X`` identifier of the monster, ``*`` for any.

        Returns:
            int: Rounded HP percentage, or -1 when the monster is missing.
        """
        if monster.startswith("id."):
            monster = monster.split(".")[1]

        for mon in self.bot.monsters:
            if mon.mon_name.lower() == monster.lower() or mon.mon_map_id == monster or monster == "*":
                return round((mon.current_hp / mon.max_hp) * 100)
        # this mean not get the desired monster
        return -1


    def get_monster(self, monster: str) -> Optional[Monster]:
        """Return the monster object that matches the provided identifier.

        Args:
            monster (str): Name or ``id.X`` identifier of the monster.

        Returns:
            Monster or None: Monster instance when found, otherwise None.
        """
        if monster.startswith('id.'):
            monster = monster.split('.')[1]
        for mon in self.bot.monsters:
            if mon.mon_name.lower() == monster.lower() or mon.mon_map_id == monster:
                return mon
        return None

    @check_alive
    def hp_below_percentage(self, percent: int) -> bool:
        """Check if the player HP is below the requested percentage.

        Args:
            percent (int): HP threshold to compare against.

        Returns:
            bool: True when the player HP percentage is lower than the threshold.
        """
        return ((self.bot.player.CURRENT_HP / self.bot.player.MAX_HP) * 100) < percent

    def get_user_id(self) -> str:
        """Return current player user ID."""
        return self.bot.user_id

    def get_player(self) -> Player:
        """Return current player instance."""
        return self.bot.player
    
    def get_followed_player(self) -> str:
        """Return username of registered followed player username."""
        return self.bot.follow_player
    
    def get_slaves(self) -> List[str]:
        """Return list of registered Slaves username"""
        return self.bot.slaves_player

    def is_player_alive(self) -> bool:
        """Return True when the local player is not dead."""
        return not self.bot.player.ISDEAD

    def get_farm_class(self) -> Optional[str]:
        """Return the configured farming class name, or None when unset."""
        return None if self.bot.farmClass == "" else self.bot.farmClass

    def get_solo_class(self) -> Optional[str]:
        """Return the configured solo class name, or None when unset."""
        return None if self.bot.soloClass == "" else self.bot.soloClass

    def get_equipped_class(self) -> Optional[ItemInventory]:
        """Return the currently equipped class inventory item, or None."""
        equipped_class = self.bot.player.get_equipped_item(ItemType.CLASS)
        return equipped_class if equipped_class else None

    def get_player_cell(self) -> str:
        """Return the local player's current cell name."""
        return self.bot.player.getPlayerCell()[0]

    def get_player_pad(self) -> str:
        """Return the local player's current pad identifier."""
        return self.bot.player.getPlayerCell()[1]

    def get_player_position_xy(self) -> list[int]:
        """Return the local player's map coordinates as an [x, y] list."""
        return self.bot.player.getPlayerPositionXY()

    def stop_bot(self, msg: str = "") -> None:
        """Print a stop message and terminate the bot session."""
        print(Fore.RED + msg + Fore.RESET)
        print(Fore.RED + "stop bot: " + self.bot.player.USER + Fore.RESET)
        self.bot.stop_bot()

    async def send_chat(self, message: str) -> None:
        """Send a zone chat message through the server packet API."""
        await self.send_packet(f"%xt%zm%message%{self.bot.areaId}%{message}%zone%")

    async def rest(self) -> None:
        """Request the rest action."""
        await self.send_packet(f"%xt%zm%restRequest%1%%")

    @check_alive
    async def sleep(self,  milliseconds: int) -> None:
        """Asynchronously sleep for the requested number of milliseconds."""
        await asyncio.sleep(milliseconds/1000)
        
    def subscribe(self, callback):
        """Register a server message/response handler."""
        self.bot.subscribe(callback)

    def unsubscribe(self, callback):
        """Remove server message/response handler."""
        self.bot.unsubscribe(callback)

    async def send_packet(self, packet: str) -> None:
        """Send a raw packet to the server after validating connectivity."""
        if not self.is_still_connected():
            return
        self.bot.write_message(packet)
        await asyncio.sleep(0.5)

    def _message_handler(self, message: str) -> None:
        """Handle server messages to update quest status flags."""
        if not message:
            return
        if self.is_valid_json(message):
            data = json.loads(message)
        else:
            return
        try:
            data = data["b"]["o"]
        except Exception:
            return
        cmd = data.get("cmd")
        if cmd != "ccqr":
            return
        quest_id = data.get('QuestID')
        ccqr_msg = data.get('msg', '')
        if data.get('bSuccess', 0) == 1:
            if quest_id is not None and int(quest_id) == self.quest_to_check:
                self.is_green_quest_var = True
                self.is_completed_before_var = True
            return
        if quest_id is None or int(quest_id) != self.quest_to_check:
            return
        if "Missing Turn In Item" in ccqr_msg:
            self.is_green_quest_var = True
            self.is_completed_before_var = False
        if "Missing Quest Progress" in ccqr_msg:
            self.is_green_quest_var = False
            self.is_completed_before_var = False
        if "One Time Quest Only" in ccqr_msg:
            self.is_green_quest_var = False
            self.is_completed_before_var = True
            if hasattr(self.bot, "one_time_questid") and int(quest_id) not in self.bot.one_time_questid:
                self.bot.one_time_questid.append(int(quest_id))
