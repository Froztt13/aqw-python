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
    @wraps(func)
    def sync_wrapper(self: 'Command', *args, **kwargs):
        if self.is_player_alive():
            return func(self, *args, **kwargs)
        start_time = time.time()
        timeout = 11  # Maximum time to wait (in seconds)
        count = 1
        while self.is_still_connected():
            if self.is_player_alive():
                return func(self, *args, **kwargs)
            if time.time() - start_time > timeout:
                print("timeout from @check_alive sync")
                self.bot.debug(Fore.MAGENTA + "respawned: from @check_alive sync" + Fore.WHITE)
                self.bot.write_message(f"%xt%zm%resPlayerTimed%{self.bot.areaId}%{self.bot.user_id}%")
                self.bot.jump_cell(self.bot.player.CELL, self.bot.player.PAD)
                self.bot.player.ISDEAD = False
                print("Spawned at cell:", self.bot.player.CELL, "pad:", self.bot.player.PAD)
                # self.stopBot("from @check_alive sync")
                return func(self, *args, **kwargs)
            time.sleep(1)  # Avoid busy-waiting
            count += 1
        if not self.is_still_connected():
            print("STOPPPPPPPP SYNC")
            return
        self.bot.debug(Fore.MAGENTA + "respawned: from @check_alive sync" + Fore.WHITE)
        self.bot.write_message(f"%xt%zm%resPlayerTimed%{self.bot.areaId}%{self.bot.user_id}%")
        self.bot.jump_cell(self.bot.player.CELL, self.bot.player.PAD)
        self.bot.player.ISDEAD = False
        print("Spawned at cell:", self.bot.player.CELL, "pad:", self.bot.player.PAD)
        return func(self, *args, **kwargs)

    @wraps(func)
    async def async_wrapper(self: 'Command', *args, **kwargs):
        if self.is_player_alive():
            return await func(self, *args, **kwargs)
        start_time = time.time()
        timeout = 11  # Maximum time to wait (in seconds)

        while self.is_still_connected():
            if self.is_player_alive():
                return await func(self, *args, **kwargs)
            if time.time() - start_time > timeout:
                print("timeout from @check_alive async")
                self.bot.debug(Fore.MAGENTA + "respawned: from @check_alive sync" + Fore.WHITE)
                self.bot.write_message(f"%xt%zm%resPlayerTimed%{self.bot.areaId}%{self.bot.user_id}%")
                self.bot.jump_cell(self.bot.player.CELL, self.bot.player.PAD)
                self.bot.player.ISDEAD = False
                print("Spawned at cell:", self.bot.player.CELL, "pad:", self.bot.player.PAD)
                # self.stopBot("from @check_alive async")
                return await func(self, *args, **kwargs)
            await asyncio.sleep(1)  # Non-blocking wait
        if not self.is_still_connected():
            print("STOPPPPPPPP ASYNC")
            return
        self.bot.debug(Fore.MAGENTA + "respawned: from @check_alive async" + Fore.WHITE)
        self.bot.write_message(f"%xt%zm%resPlayerTimed%{self.bot.areaId}%{self.bot.user_id}%")
        self.bot.jump_cell(self.bot.player.CELL, self.bot.player.PAD)
        self.bot.player.ISDEAD = False
        print("Spawned at cell:", self.bot.player.CELL, "pad:", self.bot.player.PAD)
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
    skill_reload_time: int = 0

    def __init__(self, bot, init_handler = False):
        from core.bot import Bot
        self.bot: Bot = bot

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
    async def is_green_quest(self, quest_id: int) -> bool:
        """Check whether a quest is marked green (ready to turn in).

        Args:
            quest_id (int): Identifier of the quest to inspect.

        Returns:
            bool: True when the server reports the quest as green."""
        await self.turn_in_quest(quest_id)
        while(self.is_still_connected()):
            if self.is_green_quest_var is not None:
                output = self.is_green_quest_var
                # print(f"{quest_id} is {self.is_green_quest_var}")
                self.is_green_quest_var = None
                return output
            else:
                await self.sleep(100)
        return False

    @check_alive
    async def is_completed_before(self, quest_id: int) -> bool:
        """Determine whether the quest has been completed previously.

        Args:
            quest_id (int): Identifier of the quest to inspect.

        Returns:
            bool: True when the server indicates prior completion."""
        await self.turn_in_quest(quest_id)
        while(self.is_still_connected()):
            if self.is_completed_before_var is not None:
                output = self.is_completed_before_var
                # print(f"{quest_id} is {self.is_green_quest_var}")
                self.is_completed_before_var = None
                return output
            else:
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
    async def equip_item(self, item_name: str) -> None:
        """Equip an inventory item if it is present and not already equipped.

        Args:
            item_name (str): Name of the item to equip.

        Returns:
            None: Updates the equipped state and sends the equip packet.
        """
        await self.bot.ensure_leave_from_combat()

        is_equipped = False
        s_type = None
        for item in self.bot.player.INVENTORY:
            if normalize(item.item_name.lower()) == normalize(item_name.lower()):
                if item.is_equipped:
                    return
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

    @check_alive
    async def equip_scroll(self, item_name: str, item_type: ScrollType = ScrollType.SCROLL) -> None:
        """Equip a scroll or potion from the player's inventory.

        Args:
            item_name (str): Name of the scroll or potion to equip.
            item_type (ScrollType): Scroll category to include in the packet.

        Returns:
            None: Sends the equip packet when the item is found.
        """
        for item in self.bot.player.INVENTORY:
            if item.item_name.lower() == item_name.lower():
                packet = f"%xt%zm%geia%{self.bot.areaId}%{item_type.value}%{item.s_meta}%{item.item_id}%"
                self.bot.scroll_id = item.item_id
                self.bot.write_message(packet)
                await asyncio.sleep(1)
                break

    @check_alive
    async def equip_item_by_enhancement(self, enh_id: int) -> None:
        """Equip the item that matches a specific enhancement identifier.

        Args:
            enh_id (int): Enhancement identifier bound to the desired item.

        Returns:
            None: Calls :meth:`equip_item` when a matching item exists.
        """
        # TODO: should change the enhance_pattern_id to enhance name
        item = self.bot.player.get_item_inventory_by_enhance_id(enh_id)
        if item:
            await self.equip_item(item.item_name)

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
    async def get_map_item(self, map_item_id: int, qty: int = 1) -> None:
        """Collect a map item multiple times.

        Args:
            map_item_id (int): Map item identifier to pick up.
            qty (int): Number of pickup attempts.

        Returns:
            None: Sends the pickup packet for each requested iteration.
        """
        for _ in range(qty):
            self.bot.write_message(f"%xt%zm%getMapItem%{self.bot.areaId}%{map_item_id}%")
            await asyncio.sleep(1)

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
            await self.buy_item(shop_id, item_name, qty)

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
        if self.bot.player.CELL.lower() != cell.lower() or self.bot.player.PAD.lower() != pad.lower():
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
        return self.bot.player.CELL.lower() != cell.lower()

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
            monsterName (str): Display name or ``id.X`` identifier for the monster.
            byMostMonster (bool): Prefer the cell with the highest monster population when True.
            byAliveMonster (bool): Prefer a cell that still has the monster alive when True.

        Returns:
            None: The coroutine adjusts player position and exits.
        """
        if monsterName.startswith('id.'):
            monsterName = monsterName.split('.')[1]
        for monster in self.bot.monsters:
            if (monster.mon_name.lower() == monsterName.lower() or monster.mon_map_id == monsterName )\
                    and monster.is_alive \
                    and self.bot.player.CELL == monster.frame:
                return

        # Hunt monster in other cell
        if byMostMonster or byAliveMonster:
            cell = self.bot.find_best_cell(monsterName, byMostMonster, byAliveMonster)
            if cell:
                if cell == self.bot.player.CELL:
                    return
                self.bot.jump_cell(cell, "Left")
                await asyncio.sleep(1)
                return
        for monster in self.bot.monsters:
            if (monster.mon_name.lower() == monsterName.lower() or monster.mon_map_id == monsterName )\
                    and monster.is_alive \
                    and self.bot.player.CELL != monster.frame:
                # TODO need to handle the rigth pad
                self.bot.jump_cell(monster.frame, "Left")
                await asyncio.sleep(1)
                return

    @check_alive
    async def wait_use_skill(self, index: int, target_monsters: str = "*") -> None:
        """Wait until a skill is ready before casting it.

        Args:
            index (int): Skill slot to trigger.
            target_monsters (str): Comma-separated monster names or ``id.X`` identifiers to focus.

        Returns:
            None: The coroutine finishes once the skill has been used.
        """
        while not self.bot.player.canUseSkill(int(index)):
            await self.sleep(100)
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
                "hp_threshold": 50, # in percentage of current hp from max hp
                "skills_to_check": [1, 3],
                "condition": lambda hp, threshold: hp < threshold
            },
            "scarlet sorceress": {
                "hp_threshold": 50,
                "skills_to_check": [1, 4],
                "condition": lambda hp, threshold: hp < threshold
            },
            "dragon of time": {
                "hp_threshold": 40,
                "skills_to_check": [1, 3],
                "condition": lambda hp, threshold: hp < threshold
            },
            # "archpaladin": {
            #     "hp_threshold": 70,
            #     "skills_to_check": [2],
            #     "condition": lambda hp, threshold: hp > threshold
            # },
        }
        # Get the class and its conditions
        equipped_class = self.bot.player.get_equipped_item(ItemType.CLASS)
        if equipped_class:
            if equipped_class.item_name in conditions:
                condition = conditions[equipped_class.item_name]
                current_hp = self.bot.player.CURRENT_HP
                max_hp = self.bot.player.MAX_HP
                # Check if the current conditions match
                if skill in condition["skills_to_check"] and condition["condition"]((current_hp / max_hp) * 100, condition["hp_threshold"]):
                    return False
        return True

    @check_alive
    async def use_skill(self,  
                        index: int = 0, 
                        target_monsters: str = "*", 
                        hunt: bool = False, 
                        skill_mode: SkillMode = SkillMode.ALL,
                        reload_delay: int = 500
        ) -> None:
        """Execute a skill with optional hunting, targeting, and cooldown handling.

        Args:
            index (int): Skill slot that should be triggered.
            target_monsters (str): Target filter, ``*`` for any or comma-separated list.
            hunt (bool): When True, jump to the monster before casting.
            skill_mode (SkillType): Defines which types of skills (buff, attack, all, none) can be used.
            reload_delay (int): Cooldown buffer in milliseconds after casting.

        Returns:
            None: The coroutine schedules the skill usage and exits.
        """
        if skill_mode == SkillMode.NONE:
            return
        if not self.bot.player.canUseSkill(int(index)) or not self.check_is_skill_safe(int(index)):
            return

        skill = self.bot.player.SKILLS[int(index)]
        self.bot.skillAnim = skill.get("anim", None)
        max_target = int(skill.get("tgtMax", 1))

        wait_reload_s = (self.skill_reload_time - int(round(datetime.now().timestamp() * 1000))) / 1000
        if wait_reload_s > 0 and index != 0:
            # print(Fore.BLUE + f"[{datetime.now().strftime('%H:%M:%S')}] wait reload skill:{index} cd:{wait_reload_s:.2f} s" + Fore.RESET)
            await self.sleep(wait_reload_s*1000)

        if skill["tgt"] == "h" and skill_mode in (SkillMode.ALL, SkillMode.ATTACK_ONLY): 
            priority_monsters_id = []
            if hunt and len(target_monsters.split(",")) == 1 and target_monsters != "*":
                await self.jump_to_monster(target_monsters, byAliveMonster=True)
            cell_monsters_id = [mon.mon_map_id for mon in self.bot.monsters if mon.frame == self.bot.player.CELL and mon.is_alive]
            cell_monsters = [mon for mon in self.bot.monsters if mon.frame == self.bot.player.CELL and mon.is_alive]
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
                alive_monsters = {mon.mon_map_id: mon for mon in self.bot.monsters if mon.frame == self.bot.player.CELL and mon.is_alive}

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
                            if mon.frame == self.bot.player.CELL and mon.is_alive and mon.mon_name.lower() == name:
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
            if index == 5:
                self.bot.use_scroll(final_ids, max_target)
            if index < 5 and final_ids:
                self.bot.use_skill_to_monster("a" if index == 0 else index, final_ids, max_target)
        
        if skill_mode in (SkillMode.ALL, SkillMode.BUFF_ONLY):
            if skill["tgt"] == "f":
                self.bot.use_skill_to_player(index, max_target)
            if skill["tgt"] == "s":
                self.bot.use_skill_to_myself(index)

        await self.sleep(200)
        self.bot.player.updateNextUse(index) # do this if skills is REALLY exetuced

        self.skill_reload_time = int(round(datetime.now().timestamp() * 1000)) + reload_delay

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
        for mon in self.bot.monsters:
            if mon.is_alive and mon.frame == self.bot.player.CELL:
                if mon.mon_name.lower() == monster.lower() or mon.mon_map_id == monster:
                    return True
                elif monster == "*":
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
            return
        if quest_id is None or int(quest_id) != self.quest_to_check:
            return
        if "Missing Turn In Item" in ccqr_msg:
            self.is_green_quest_var = True
        if "Missing Quest Progress" in ccqr_msg:
            self.is_green_quest_var = False
        if "One Time Quest Only" in ccqr_msg:
            self.is_green_quest_var = False
            self.is_completed_before_var = True
