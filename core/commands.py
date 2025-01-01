from core.bot import Bot
import asyncio
from typing import List, Union
import time
from functools import wraps
from inspect import iscoroutinefunction
from datetime import datetime
from colorama import Fore

def check_alive(func):
    @wraps(func)
    def sync_wrapper(self, *args, **kwargs):
        if self.isPlayerAlive():
            return func(self, *args, **kwargs)
        start_time = time.time()
        timeout = 11  # Maximum time to wait (in seconds)

        while self.isStillConnected():
            if self.isPlayerAlive():
                break
            if time.time() - start_time > timeout:
                self.stopBot()
            time.sleep(1)  # Avoid busy-waiting

        return func(self, *args, **kwargs)

    @wraps(func)
    async def async_wrapper(self, *args, **kwargs):
        if self.isPlayerAlive():
            return await func(self, *args, **kwargs)
        start_time = time.time()
        timeout = 11  # Maximum time to wait (in seconds)

        while self.isStillConnected():
            if self.isPlayerAlive():
                break
            if time.time() - start_time > timeout:
                self.stopBot()
            await asyncio.sleep(1)  # Non-blocking wait

        return await func(self, *args, **kwargs)

    # Check if the function is async and use the appropriate wrapper
    return async_wrapper if iscoroutinefunction(func) else sync_wrapper

class Command:
    def __init__(self, bot: Bot):
        self.bot = bot

    def isPlayerAlive(self) -> bool:
        return not self.bot.player.ISDEAD

    def isStillConnected(self) -> bool:
        return self.bot.is_client_connected

    def stopBot(self):
        self.bot.stop_bot()
    
    @check_alive
    async def leave_combat(self, safeLeave: bool = True) -> bool:
        await self.bot.ensure_leave_from_combat(always=True)
        if safeLeave:
            await self.jump_cell("Enter", "Spawn")
    
    @check_alive
    async def ensure_accept_quest(self, quest_id: int) -> None:
        while self.quest_not_in_progress(quest_id):
            await self.accept_quest(quest_id)
            await self.sleep(1000)
            if quest_id in self.bot.failed_get_quest_datas:
                return
        print("quest accepted:", quest_id)
    
    @check_alive
    async def ensure_turn_in_quest(self, quest_id: int) -> None:
        while self.quest_in_progress(quest_id):
            await self.turn_in_quest(quest_id)
            await self.sleep(1000)
            if quest_id in self.bot.failed_get_quest_datas:
                return
        print("quest turned in:", quest_id)

    @check_alive
    async def join_map(self, mapName: str, roomNumber: int = None, safeLeave: bool = True) -> None:
        self.stop_aggro()
        if self.bot.strMapName.lower() == mapName.lower():
            return
        self.bot.is_joining_map = True
        await self.leave_combat(safeLeave)

        if roomNumber != None:
            msg = f"%xt%zm%cmd%1%tfer%{self.bot.player.USER}%{mapName}-{roomNumber}%"
        elif self.bot.roomNumber != None:
            roomNumber = self.bot.roomNumber
            msg = f"%xt%zm%cmd%1%tfer%{self.bot.player.USER}%{mapName}-{self.bot.roomNumber}%"
        else:
            msg = f"%xt%zm%cmd%1%tfer%{self.bot.player.USER}%{mapName}%"
        self.bot.write_message(msg)
        count = 0
        while self.bot.is_joining_map:
            await asyncio.sleep(0.5)
            count += 1
            if count % 5 == 0 and self.is_not_in_map(mapName):
                self.bot.write_message(msg)
    
    def is_not_in_map(self, mapName: str) -> bool:
        return mapName.lower() != self.bot.strMapName.lower()

    @check_alive
    async def jump_cell(self, cell: str, pad: str) -> None:
        if self.bot.player.CELL.lower() != cell or self.bot.player.PAD.lower() != pad:
            self.bot.jump_cell(cell, pad)
        await asyncio.sleep(1)
    
    @check_alive
    async def jump_to_monster(self, monsterName: str, byMostMonster: bool = True, byAliveMonster: bool = False) -> None:
        for monster in self.bot.monsters:
            if monster.mon_name.lower() == monsterName.lower() \
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
            if monster.mon_name.lower() == monsterName.lower() \
                    and monster.is_alive \
                    and self.bot.player.CELL != monster.frame:
                # TODO need to handle the rigth pad
                self.bot.jump_cell(monster.frame, "Left")
                await asyncio.sleep(1)
                return
        
    @check_alive
    async def use_skill(self,  index: int = 0, target_monsters: str = "*", hunt: bool = False, scroll_id: int = 0) -> None:
        if not self.bot.player.canUseSkill(int(index)) and not self.bot.canuseskill:
            self.bot.debug(f"Skill {index} not ready yet")
            return

        skill = self.bot.player.SKILLS[int(index)]
        self.bot.skillAnim = skill["anim"]
        self.bot.skillNumber = index
        max_target = int(skill.get("tgtMax", 1))

        if skill["tgt"] == "h": 
            priority_monsters_id = []
            if hunt and len(target_monsters.split(",")) == 1 and target_monsters != "*":
                await self.hunt_monster(target_monsters, byAliveMonster=True)
            cell_monsters_id = [mon.mon_map_id for mon in self.bot.monsters if mon.frame == self.bot.player.CELL and mon.is_alive]
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

                # Mapping priority_monsters_id
                for mon in self.bot.monsters:
                    if mon.frame != self.bot.player.CELL or not mon.is_alive:
                        continue

                    # Check by ID
                    if mon.mon_map_id in target_ids:
                        priority_monsters_id.append(mon.mon_map_id)
                        continue

                    # Check by name
                    if mon.mon_name.lower() in target_names:
                        priority_monsters_id.append(mon.mon_map_id)
                # Check if the first index is one of the priority targets
                if len(priority_monsters_id) > 0:
                    if not cell_monsters_id[0] in priority_monsters_id:
                        cell_monsters_id.pop(0)
                        cell_monsters_id.insert(0, priority_monsters_id[0])
                # Remove duplicate monster id and keep the order
                seen = set()
                for monster_id in cell_monsters_id:
                    if monster_id not in seen:
                        final_ids.append(monster_id)
                        seen.add(monster_id)
            else:
                final_ids = cell_monsters_id
            # print(f"tgt: {final_ids}")
            self.bot.use_skill_to_monster("a" if self.bot.skillNumber == 0 else self.bot.skillNumber, final_ids, max_target)
        elif skill["tgt"] == "f":
            self.bot.use_skill_to_player(self.bot.skillNumber, max_target)
        self.bot.canuseskill = False
        await asyncio.sleep(1)
        # self.bot.player.delayAllSkills(except_skill = index)

    @check_alive
    async def sleep(self,  milliseconds: int) -> None:
        await asyncio.sleep(milliseconds/1000)

    @check_alive
    async def accept_quest(self, quest_id: int) -> None:
        self.bot.accept_quest(quest_id)
        await asyncio.sleep(1)

    def quest_not_in_progress(self, quest_id: int) -> bool:
        loaded_quest_ids = [loaded_quest["QuestID"] for loaded_quest in self.bot.loaded_quest_datas]
        return str(quest_id) not in str(loaded_quest_ids)
    
    def quest_in_progress(self, quest_id: int) -> bool:
        loaded_quest_ids = [loaded_quest["QuestID"] for loaded_quest in self.bot.loaded_quest_datas]
        return str(quest_id) in str(loaded_quest_ids)

    def can_turnin_quest(self, questId: int) -> bool:
        return self.bot.can_turn_in_quest(questId)
    
    @check_alive
    async def turn_in_quest(self, quest_id: int, item_id: int = -1) -> None:
        await self.bot.ensure_leave_from_combat()
        self.bot.turn_in_quest(quest_id, item_id)
        await asyncio.sleep(1)

    def is_in_bank(self, itemName: str, itemQty: int = 1, operator: str = ">=") -> bool:
        inBank = self.bot.player.isInBank(itemName, itemQty, operator)
        return inBank[0]
    
    def is_in_inventory(self, itemName: str, itemQty: int = 1, operator: str = ">=", isTemp: bool = False) -> bool:
        inInv = self.bot.player.isInInventory(itemName, itemQty, operator, isTemp)
        return inInv[0]
    
    def farming_logger(self, item_name: str, item_qty: int = 1, is_temp: bool = False) -> None:
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
        for item in itemNames:
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
    async def equip_item(self, item_name: str) -> None:
        await self.bot.ensure_leave_from_combat()
        
        is_equipped = False
        s_type = None
        for item in self.bot.player.INVENTORY:
            if item.item_name == item_name.lower():
                packet = f"%xt%zm%equipItem%{self.bot.areaId}%{item.item_id}%"
                self.bot.write_message(packet)
                is_equipped = True
                s_type = item.s_type
                item.is_equipped = is_equipped
                await asyncio.sleep(0.5)
                break
        # Update unequip previous item
        if is_equipped and s_type:
            for item in self.bot.player.INVENTORY:
                if item.s_type == s_type and item.is_equipped and not item.item_name == item_name.lower():
                    item.is_equipped = False
                    break

    def add_drop(self, itemName: Union[str, List[str]]) -> None:
        if isinstance(itemName, str):
            itemName = [itemName]

        for item in itemName:
            if item not in self.bot.items_drop_whitelist:
                self.bot.items_drop_whitelist.append(item)

    def is_monster_alive(self, monster: str = "*") -> bool:
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
    async def get_map_item(self, map_item_id: int, qty: int = 1):
        for _ in range(qty):
            self.bot.write_message(f"%xt%zm%getMapItem%{self.bot.areaId}%{map_item_id}%")
            await asyncio.sleep(1)

    @check_alive
    async def accept_quest_bulk(self, quest_id: int, increament: int):
        for i in range(increament):
            await self.ensure_accept_quest(quest_id + i)

    @check_alive
    async def register_quest(self, questId: int):
        if questId not in self.bot.registered_auto_quest_ids:
            self.bot.registered_auto_quest_ids.append(questId)
            await self.ensure_accept_quest(questId)

    def wait_count_player(self, player_count: int):
        return len(self.bot.user_ids) >= player_count
    
    def get_player_cell(self) -> list[str]:
        return self.bot.player.getPlayerCell()
    
    def get_player_position_xy(self) -> list[int]:
        return self.bot.player.getPlayerPositionXY()
    
    @check_alive
    async def walk_to(self, X: int, Y: int, speed: int = 8):
        await self.bot.walk_to(X, Y, speed)
        await self.sleep(200)

    def start_aggro(self, mons_id: list[str], delay_ms: int = 500):
        self.stop_aggro()
        self.bot.is_aggro_handler_task_running = True
        self.bot.aggro_mons_id = mons_id
        self.bot.aggro_delay_ms = delay_ms
        self.bot.run_aggro_hadler_task()

    def stop_aggro(self):
        self.bot.is_aggro_handler_task_running = False
        self.bot.aggro_mons_id = []