from typing import Optional, List, Dict, Any
from core.command import Command
from templates.hunt import hunt_item
from colorama import Fore

VA_QUEST_ID = 4432

VA_DROP_LIST = [
    "Astral Ephemerite Essence",
    "Belrot the Fiend Essence",
    "Black Knight Essence",
    "Tiger Leech Essence",
    "Carnax Essence",
    "Chaos Vordred Essence",
    "Dai Tengu Essence",
    "Unending Avatar Essence",
    "Void Dragon Essence",
    "Creature Creation Essence",
    "Void Aura"
]

VA_ESSENCES: List[Dict[str, Any]] = [
    {
        "item_name": "Astral Ephemerite Essence",
        "qty": 100,
        "map_name": "timespace",
        "room_number": 999999,
        "cell": "Frame1",
        "pad": "Spawn",
        "monster_name": "*",
        "is_solo": False
    },
    {
        "item_name": "Belrot the Fiend Essence",
        "qty": 100,
        "map_name": "citadel",
        "room_number": 999999,
        "cell": "m13",
        "pad": "Left",
        "monster_name": "*",
        "is_solo": True
    },
    {
        "item_name": "Black Knight Essence",
        "qty": 100,
        "map_name": "greenguardwest",
        "room_number": None,
        "cell": "BKWest15",
        "pad": "Left",
        "monster_name": "*",
        "is_solo": True
    },
    {
        "item_name": "Tiger Leech Essence",
        "qty": 100,
        "map_name": "mudluk",
        "room_number": 999999,
        "cell": "Boss",
        "pad": "Down",
        "monster_name": "*",
        "is_solo": True
    },
    {
        "item_name": "Carnax Essence",
        "qty": 100,
        "map_name": "aqlesson",
        "room_number": None,
        "cell": "Frame9",
        "pad": "Right",
        "monster_name": "*",
        "is_solo": True
    },
    {
        "item_name": "Chaos Vordred Essence",
        "qty": 100,
        "map_name": "necrocavern",
        "room_number": None,
        "cell": "r16",
        "pad": "Down",
        "monster_name": "*",
        "is_solo": True
    },
    {
        "item_name": "Dai Tengu Essence",
        "qty": 100,
        "map_name": "hachiko",
        "room_number": 999999,
        "cell": "Roof",
        "pad": "Left",
        "monster_name": "*",
        "is_solo": True
    },
    {
        "item_name": "Unending Avatar Essence",
        "qty": 100,
        "map_name": "timevoid",
        "room_number": None,
        "cell": "Frame8",
        "pad": "Left",
        "monster_name": "*",
        "is_solo": True
    },
    {
        "item_name": "Void Dragon Essence",
        "qty": 100,
        "map_name": "dragonchallenge",
        "room_number": None,
        "cell": "r4",
        "pad": "Left",
        "monster_name": "*",
        "is_solo": True
    },
    {
        "item_name": "Creature Creation Essence",
        "qty": 100,
        "map_name": "maul",
        "room_number": 999999,
        "cell": "r3",
        "pad": "Down",
        "monster_name": "*",
        "is_solo": True
    }
]

async def turn_in_va_quest(cmd: Command):
    """Turns in Quest 4432 (Retrieve Void Auras) for sets of 20 essences available in inventory."""
    while cmd.is_still_connected():
        min_mats = min([cmd.get_quant_item(item["item_name"]) for item in VA_ESSENCES])
        possible_turn_ins = min_mats // 20
        if possible_turn_ins <= 0:
            break

        turn_in_batch = min(possible_turn_ins, 5)
        print(Fore.CYAN + f"=== [Void Aura] Turning in Quest {VA_QUEST_ID} ({turn_in_batch}x)... ===" + Fore.RESET)

        await cmd.ensure_accept_quest(VA_QUEST_ID)
        await cmd.sleep(1000)

        await cmd.leave_combat()
        cmd.bot.turn_in_quest(VA_QUEST_ID, item_id=-1, qty=turn_in_batch)
        await cmd.sleep(2000)

        cmd.bot.general_turn_in_count = getattr(cmd.bot, "general_turn_in_count", 0) + turn_in_batch
        current_va = cmd.get_quant_item("Void Aura")
        print(Fore.GREEN + f"=== [Void Aura] Turn-in complete! Total turn-ins: {cmd.bot.general_turn_in_count} | Void Aura: {current_va} ===" + Fore.RESET)

async def farm_void_aura(cmd: Command, target_qty: int = 100):
    item_name = "Void Aura"

    cmd.add_drop(VA_DROP_LIST)
    await cmd.bank_to_inv(VA_DROP_LIST)
    await cmd.sleep(500)

    cmd.farming_logger(item_name, target_qty)

    print(Fore.CYAN + f"=== [Void Aura] Starting Retrieve Void Auras farm (Quest {VA_QUEST_ID}) ===" + Fore.RESET)
    if target_qty > 0:
        print(Fore.CYAN + f"Target: {target_qty} Void Auras" + Fore.RESET)
    else:
        print(Fore.CYAN + "Mode: Infinite Loop" + Fore.RESET)

    # Initial turn-in check if player already has materials
    await turn_in_va_quest(cmd)

    while cmd.is_still_connected():
        if target_qty > 0 and cmd.is_in_inventory(item_name, target_qty, operator=">="):
            print(Fore.GREEN + f"=== [Void Aura] Target {target_qty} reached! Current: {cmd.get_quant_item(item_name)} ===" + Fore.RESET)
            break

        await cmd.ensure_accept_quest(VA_QUEST_ID)
        await cmd.sleep(1000)

        for item in VA_ESSENCES:
            if not cmd.is_still_connected():
                return
            if target_qty > 0 and cmd.is_in_inventory(item_name, target_qty, operator=">="):
                break

            # Skip if already reached 100 for this essence
            if cmd.is_in_inventory(item["item_name"], item["qty"], operator=">="):
                continue

            # Equip appropriate class
            if item.get("is_solo", False):
                solo_class = cmd.get_solo_class()
                if solo_class:
                    await cmd.equip_item(solo_class)
            else:
                farm_class = cmd.get_farm_class()
                if farm_class:
                    await cmd.equip_item(farm_class)

            # Determine room number
            room_num = None
            if item.get("room_number") is not None:
                bot_room = getattr(cmd.bot, "roomNumber", None)
                room_num = bot_room if (bot_room and bot_room > 0) else item["room_number"]

            await hunt_item(
                cmd=cmd,
                item_name=item["item_name"],
                item_qty=item["qty"],
                cell=item["cell"],
                pad=item["pad"],
                map_name=item["map_name"],
                room_number=room_num,
                monster_name=item.get("monster_name", "*"),
                farming_logger=True,
                is_temp=False
            )

        # Batch turn-in after cycle
        await turn_in_va_quest(cmd)

async def farm_single_essence(cmd: Command, essence_name: str, qty: int = 100):
    essence_info = next((e for e in VA_ESSENCES if e["item_name"] == essence_name), None)
    if not essence_info:
        print(Fore.RED + f"Unknown essence: {essence_name}" + Fore.RESET)
        return

    cmd.add_drop([essence_name])
    await cmd.bank_to_inv([essence_name])
    cmd.farming_logger(essence_name, qty)

    if essence_info.get("is_solo", False):
        solo_class = cmd.get_solo_class()
        if solo_class:
            await cmd.equip_item(solo_class)
    else:
        farm_class = cmd.get_farm_class()
        if farm_class:
            await cmd.equip_item(farm_class)

    room_num = None
    if essence_info.get("room_number") is not None:
        bot_room = getattr(cmd.bot, "roomNumber", None)
        room_num = bot_room if (bot_room and bot_room > 0) else essence_info["room_number"]

    await hunt_item(
        cmd=cmd,
        item_name=essence_name,
        item_qty=qty,
        cell=essence_info["cell"],
        pad=essence_info["pad"],
        map_name=essence_info["map_name"],
        room_number=room_num,
        monster_name=essence_info.get("monster_name", "*"),
        farming_logger=True,
        is_temp=False
    )
