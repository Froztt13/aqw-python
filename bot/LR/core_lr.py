from core.bot import Bot
from core.command import Command
from templates.hunt import hunt_item

async def revenant_spellscroll(cmd: Command, qty: int = 20):
    item_name = "Revenant's Spellscroll"

    list_items = [
        "Aeacus Empowered",
        "Tethered Soul",
        "Darkened Essence",
        "Dracolich Contract",
        "Revenant's Spellscroll"
    ]

    await cmd.bank_to_inv(list_items)
    cmd.add_drop(list_items)

    cmd.farming_logger(item_name, qty)

    item_to_farm = [
        {"item_name": "Aeacus Empowered", "qty": 50, "map_name": "judgement", "cell": "r10a", "pad": "Left", "is_solo": True},
        {"item_name": "Tethered Soul", "qty": 300, "map_name": "revenant","cell": "r2", "pad": "Left", "is_solo" : False},
        {"item_name": "Darkened Essence", "qty": 500,"map_name": "shadowrealmpast", "cell": "Enter", "pad": "Spawn", "is_solo": False},
        {"item_name": "Dracolich Contract", "qty": 1000,"map_name": "necrodungeon", "cell": "r22", "pad": "Down", "is_solo": False},
    ]


    while cmd.is_still_connected():
        if cmd.is_in_inventory(item_name, qty, ">="):
            break

        await cmd.ensure_accept_quest(6897)

        await farm_mats(cmd, item_to_farm)

        await cmd.ensure_turn_in_quest(6897)

    await cmd.inv_to_bank(list_items)

async def conquest_wreath(cmd: Command, qty: int = 6):
    item_name = "Conquest Wreath"

    list_items = [
        "Grim Cohort Conquered",
        "Ancient Cohort Conquered",
        "Pirate Cohort Conquered",
        "Battleon Cohort Conquered",
        "Mirror Cohort Conquered",
        "Darkblood Cohort Conquered",
        "Vampire Cohort Conquered",
        "Spirit Cohort Conquered",
        "Dragon Cohort Conquered",
        "Doomwood Cohort Conquered",
        "Conquest Wreath"
      ]

    await cmd.bank_to_inv(list_items)
    cmd.add_drop(list_items)

    cmd.farming_logger(item_name, qty)

    item_to_farm = [
        {"item_name": "Ancient Cohort Conquered", "qty": 400, "map_name": "mummies", "cell": "Enter", "pad": "Spawn", "is_solo": False},
        {"item_name": "Grim Cohort Conquered", "qty": 400, "map_name": "doomvault", "cell": "r1", "pad": "Right", "is_solo": False},
        {"item_name": "Pirate Cohort Conquered", "qty": 400, "map_name": "wrath", "cell": "r5", "pad": "Left", "is_solo": False},
        {"item_name": "Battleon Cohort Conquered", "qty": 400, "map_name": "doomwar", "cell": "r6", "pad": "Left", "is_solo": False},
        {"item_name": "Mirror Cohort Conquered", "qty": 400, "map_name": "overworld", "cell": "Enter", "pad": "Spawn", "is_solo": False},
        {"item_name": "Darkblood Cohort Conquered", "qty": 400, "map_name": "deathpits", "cell": "r1", "pad": "Left", "is_solo": False},
        {"item_name": "Vampire Cohort Conquered", "qty": 400, "map_name": "maxius", "cell": "r2", "pad": "Left", "is_solo": False},
        {"item_name": "Spirit Cohort Conquered", "qty": 400, "map_name": "curseshore", "cell": "Enter", "pad": "Spawn", "is_solo": False},
        {"item_name": "Dragon Cohort Conquered", "qty": 400, "map_name": "dragonbone", "cell": "Enter", "pad": "Spawn", "is_solo": False},
        {"item_name": "Doomwood Cohort Conquered", "qty": 400, "map_name": "doomwood", "cell": "r6", "pad": "Right", "is_solo": False},
    ]

    while cmd.is_still_connected():
        if cmd.is_in_inventory(item_name, qty, ">="):
            break

        await cmd.ensure_accept_quest(6898)

        await farm_mats(cmd, item_to_farm)

        await cmd.ensure_turn_in_quest(6898)
    
    await cmd.inv_to_bank(list_items)

async def exalted_crown(cmd: Command, qty: int = 10):
    # not finished yet
    item_name = "Exalted Crown"

    list_items = [
        "Dage's Favor",
        "Diamond Token of Dage",
        "Emblem of Dage",
        "Dark Token",
        "Exalted Crown",
        "Legion Seal",
        "Gem of Mastery",
        "Defeated Makai",
        "Legion Token"
        "Legion Round 4 Medal"
      ]

    await cmd.bank_to_inv(list_items)
    cmd.add_drop(list_items)

    cmd.farming_logger(item_name, qty)

    while cmd.is_still_connected():
        if cmd.is_in_inventory(item_name, qty, ">="):
            break

        await cmd.ensure_accept_quest(6899)

        await get_hooded_legion_cowl(cmd)
        await get_leto_ssp(cmd)
        await get_dages_favor(cmd)
        await get_emblem_of_dage(cmd)
        await get_diamond_token_of_dage(cmd)
        await get_dark_token(cmd)

        await cmd.ensure_turn_in_quest(6899)
    await cmd.inv_to_bank(list_items)

async def get_hooded_legion_cowl(cmd: Command):
    item = "Hooded Legion Cowl"
    await cmd.bank_to_inv(item)

    if cmd.is_in_inventory(item):
        return
    
    cmd.farming_logger(item)
    await cmd.join_map("underworld")
    await cmd.ensure_load_shop(216)
    await cmd.buy_item(216, item, 1)

async def get_dages_favor(cmd: Command, qty: int = 300):
    await hunt_item(
            cmd = cmd,
            item_name = "Dage's Favor",
            item_qty = qty,
            cell = "r8",
            pad = "Left",
            map_name = "underworld",
            farming_logger=True,
            is_temp=False
        )
    
async def get_emblem_of_dage(cmd: Command, qty: int = 1):
    item = "Emblem of Dage"
    await cmd.bank_to_inv(item)
    if cmd.is_in_inventory(item, qty):
        return
    await cmd.bank_to_inv("Legion Round 4 Medal")
    if not cmd.is_in_inventory("Legion Round 4 Medal"):
        cmd.stop_bot("Required : Legion Round 4 Medal in inventory")
    
    cmd.add_drop(item)
    cmd.farming_logger(item, qty)
    await cmd.ensure_accept_quest(4742)
    await hunt_item(
            cmd = cmd,
            item_name = "Legion Seal",
            item_qty = 25,
            cell = "r10",
            pad = "Left",
            map_name = "shadowblast",
            farming_logger=True,
            is_temp=False
        )
    await hunt_item(
            cmd = cmd,
            item_name = "Gem of Mastery",
            item_qty = 1,
            cell = "r10",
            pad = "Left",
            map_name = "shadowblast",
            farming_logger=True,
            is_temp=False
        )
    await cmd.ensure_turn_in_quest(4742)
    await cmd.inv_to_bank(["Legion Seal", "Gem of Mastery"])
    await cmd.sleep(1000)

async def get_diamond_token_of_dage(cmd: Command, qty: int = 30):
    item = "Diamond Token of Dage"
    await cmd.bank_to_inv(item)
    if cmd.is_in_inventory(item, qty):
        return
    
    cmd.add_drop(item)
    cmd.farming_logger(item, qty)

    item_to_farm = [
        {"item_name": "Defeated Makai", "qty": 25, "map_name": "tercessuinotlim", "cell": "Enter", "pad": "Spawn", "is_solo": False},
        {"item_name": "Carnax Eye", "qty": 1, "map_name": "aqlesson","cell": "Frame9", "pad": "Right", "is_solo" : True},
        {"item_name": "Red Dragon's Fang", "qty": 1,"map_name": "lair", "cell": "End", "pad": "Left", "is_solo": True},
        {"item_name": "Kathool Tentacle", "qty": 1,"map_name": "deepchaos", "cell": "Frame4", "pad": "Left", "is_solo": True},
        {"item_name": "Fluffy's Bones", "qty": 1,"map_name": "dflesson", "cell": "r12", "pad": "Right", "is_solo": True},
        {"item_name": "Blood Titan's Blade", "qty": 1,"map_name": "bloodtitan", "cell": "Enter", "pad": "Spawn", "is_solo": True},
    ]

    cmd.farming_logger(item, qty)

    while cmd.is_still_connected():
        if cmd.is_in_inventory(item, qty, ">="):
            break

        await cmd.ensure_accept_quest(4743)

        await farm_mats(cmd, item_to_farm)

        await cmd.ensure_turn_in_quest(4743)

async def get_dark_token(cmd: Command, qty: int = 100):
    item = "Dark Token"
    await cmd.bank_to_inv(item)
    if cmd.is_in_inventory(item, qty):
        return
    
    cmd.add_drop(item)
    cmd.farming_logger(item, qty)

    await cmd.join_map("seraphicwardage")
    await cmd.jump_cell("Enter", "Spawn")

    skill_index = 0
    skill_list = [0,1,2,0,3,4]

    while cmd.is_still_connected():
        if cmd.is_in_inventory(item, qty, ">="):
            break

        for q in [6248, 6249]:
            if cmd.quest_not_in_progress(q):
                await cmd.accept_quest(q)
            if cmd.can_turnin_quest(q):
                await cmd.turn_in_quest(q)
        
        await cmd.use_skill(skill_list[skill_index])
        skill_index += 1
        if skill_index >= len(skill_index):
            skill_index = 0
        await cmd.sleep(100)

async def get_leto_ssp(cmd: Command, qty: int = 4000):
    item_name = "Legion Token"

    await cmd.bank_to_inv("Shogun Paragon Pet")
    await cmd.bank_to_inv(item_name)

    cmd.add_drop(item_name)
    cmd.farming_logger(item_name, qty)

    await cmd.join_map("fotia")

    skill_index = 0
    skill_list = [0,1,2,0,3,4]

    while cmd.is_still_connected():
        if cmd.is_in_inventory(item_name, qty, ">="):
            break

        if cmd.quest_not_in_progress(5755):
            await cmd.accept_quest(5755)
        if cmd.can_turnin_quest(5755):
            await cmd.turn_in_quest(5755)
        
        await cmd.use_skill(skill_list[skill_index])
        skill_index += 1
        if skill_index >= len(skill_list):
            skill_index = 0
        await cmd.sleep(100)


async def farm_mats(cmd: Command, item_to_farm: list[dict]):
    for item in item_to_farm:
        if not cmd.is_still_connected():
            return
        is_solo = item.get("is_solo", False)
        if is_solo:
            solo_class = cmd.get_solo_class()
            if solo_class:
                await cmd.equip_item(solo_class)
        else:
            farm_class = cmd.get_farm_class()
            if farm_class:
                await cmd.equip_item(farm_class)
        if item["map_name"] == "revenant":
            await cmd.join_map("revenant", 999999)
        await hunt_item(
            cmd = cmd,
            item_name = item["item_name"],
            item_qty = item["qty"],
            cell = item["cell"],
            pad = item["pad"],
            map_name = item["map_name"],
            farming_logger=True,
            is_temp=False
        )