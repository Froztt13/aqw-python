import asyncio
from datetime import datetime
from colorama import Fore
from core.bot import Bot
from core.command import Command
from templates.hunt import hunt_item, kill_quest
from bot.darkon_mats.core_darkon_mats import darkons_receipts_arcangrove

DOT_CLASS_NAME = "Dragon of Time"

ALL_DOT_DROPS = [
    # Rewards
    "Dragon of Time",
    "Dragon of Time Helm",
    "Dragon of Time Ponytail",
    "Dragon of Time Runes",
    "Dragon of Time Wings",
    "Dragon of Time Tail",
    "Dragon of Time FangBlade",
    "Dual Dragon of Time FangBlades",
    "Dragon of Time Armor",
    "Dragon of Time Daggers",
    "Dragon of Time Cleaver",
    "Ascended Dragon of Time Runes",
    "Runes Of Time",
    "Dragon of Time Reaper",
    "Dragon of Time WingBlade",
    "Ascended Dragon of Time",
    "Ascended Dragon of Time Morph",
    "Ascended Dragon of Time Wings",

    # Quest 7716: Acquiring Ancient Secrets
    "Lost Hieroglyphic",
    "Myths of Lore",
    "Historia Page",
    "Frost King's Story",
    "Your Own Memories",

    # Quest 7717: Time to Train Yourself
    "Desoloth's Destructive Aura",
    "Nythera's Patience",
    "Goregold's Luck",
    "Victorious's Dignity",
    "Trigoras's Tenacity",
    "Key of Greed",

    # Quest 7718: Do You Have the Time?
    "Golden Blade of Fate",
    "Pink Blade of Destruction",
    "Cross-Era Stabilizer",
    "Dragonoid of Hours",
    "Chronomancer's Codex",
    "Timestream String",

    # Quest 7719: Through the Wormhole
    "Time Loop Broken",
    "Anomaly Silenced",
    "Chronolord Stopped",
    "Is This a Wormhole?",

    # Quest 7720: Rend
    "Dimensional Dragon Portal",
    "Brutal Slash Studied",
    "Epic Hydra Fang",

    # Quest 7721: Confluence of Fates
    "Sword of Voids",
    "Darkon's Receipt",
    "Banana",
    "Semiramis Feather",
    "Cross-Dimensional Weapons",
    "Starlight Singularity",
    "Unidentified 34",

    # Quest 7722: Dragon's Will
    "Unyielding Slime",
    "Omnipotent Cells",
    "Dragon's Plasma",
    "Chaotic Invertebrae",
    "Cryostatic Essence",
    "Salvaged Chaos Dragon Biomass",

    # Quest 7723: Burning Fates
    "Fire Essence",
    "Akriloth's Flametongue",
    "Immortal Embers",
    "Ashes from the Void Realm",

    # Quest 7724: Hero's Heartbeat
    "Mysterious Egg",
    "Blade of Awe",
    "Conquered Past",
    "Slugbutter Trophy",
    "Icewing's Laurel",
    "Key of Pride",
    "Key of Gluttony",
    "Key of Sloth",
    "Key of Lust",
    "Key of Envy",
    "Key of Wrath",
]


def log_info(msg: str):
    print(Fore.CYAN + f"[{datetime.now().strftime('%H:%M:%S')}][DoT] " + Fore.WHITE + msg + Fore.RESET)


def log_success(msg: str):
    print(Fore.GREEN + f"[{datetime.now().strftime('%H:%M:%S')}][DoT] " + msg + Fore.RESET)


def log_warning(msg: str):
    print(Fore.YELLOW + f"[{datetime.now().strftime('%H:%M:%S')}][DoT] " + msg + Fore.RESET)


def log_error(msg: str):
    print(Fore.RED + f"[{datetime.now().strftime('%H:%M:%S')}][DoT] " + msg + Fore.RESET)


async def check_and_transfer_bank(cmd: Command, items: list[str]):
    """Mengecek item di bank dan memindahkannya ke inventory jika ditemukan."""
    for item in items:
        if cmd.is_in_bank(item):
            log_info(f"Mengambil '{item}' dari Bank ke Inventory...")
            await cmd.bank_to_inv(item)
            await cmd.sleep(300)


# =========================================================================
# QUEST 1: Acquiring Ancient Secrets (Quest 7716)
# =========================================================================
async def quest_1_ancient_secrets(cmd: Command):
    quest_id = 7716
    log_info("=== [Quest 1/9] Acquiring Ancient Secrets (7716) ===")

    if await cmd.is_completed_before(quest_id):
        log_success("Quest 7716 sudah selesai.")
        return

    req_items = [
        "Lost Hieroglyphic",
        "Myths of Lore",
        "Historia Page",
        "Frost King's Story",
        "Your Own Memories"
    ]
    await check_and_transfer_bank(cmd, req_items)
    cmd.add_drop(req_items)

    await cmd.ensure_accept_quest(quest_id)

    farm_class = cmd.get_farm_class()
    solo_class = cmd.get_solo_class()

    # 1. Lost Hieroglyphic x30 (/mummies)
    if not cmd.is_in_inventory("Lost Hieroglyphic", 30):
        log_info("Farming Lost Hieroglyphic x30 di /mummies...")
        if farm_class:
            await cmd.equip_item(farm_class)
        await hunt_item(
            cmd=cmd,
            item_name="Lost Hieroglyphic",
            item_qty=30,
            map_name="mummies",
            cell="Enter",
            pad="Spawn",
            monster_name="Mummy",
            farming_logger=True
        )

    # 2. Myths of Lore x1 (Shop 651 di /librarium)
    if not cmd.is_in_inventory("Myths of Lore"):
        log_info("Membeli Myths of Lore dari /librarium (Shop 651)...")
        if cmd.is_not_in_map("librarium"):
            await cmd.join_map("librarium")
            await cmd.sleep(1000)
        await cmd.ensure_load_shop(651)
        await cmd.buy_item(651, "Myths of Lore", 1)
        await cmd.sleep(500)

    # 3. Historia Page x100 (/timelibrary)
    if not cmd.is_in_inventory("Historia Page", 100):
        log_info("Farming Historia Page x100 di /timelibrary...")
        if farm_class:
            await cmd.equip_item(farm_class)
        await hunt_item(
            cmd=cmd,
            item_name="Historia Page",
            item_qty=100,
            map_name="timelibrary",
            cell="FrameAQ",
            pad="Left",
            monster_name="*",
            farming_logger=True
        )

    # 4. Frost King's Story x1 (/kingcoal)
    if not cmd.is_in_inventory("Frost King's Story"):
        log_info("Farming Frost King's Story di /kingcoal...")
        if solo_class:
            await cmd.equip_item(solo_class)
        await hunt_item(
            cmd=cmd,
            item_name="Frost King's Story",
            item_qty=1,
            map_name="kingcoal",
            monster_name="Frost King",
            farming_logger=True
        )

    # 5. Your Own Memories x1 (/baconcatyou)
    if not cmd.is_in_inventory("Your Own Memories"):
        log_info("Farming Your Own Memories di /baconcatyou...")
        if farm_class:
            await cmd.equip_item(farm_class)
        await hunt_item(
            cmd=cmd,
            item_name="Your Own Memories",
            item_qty=1,
            map_name="baconcatyou",
            cell="Enter",
            pad="Spawn",
            monster_name="*",
            farming_logger=True
        )

    print('try to completing quest...')
    await cmd.ensure_turn_in_quest(quest_id)
    log_success("Quest 7716 Selesai!")


# =========================================================================
# QUEST 2: Time to Train Yourself (Quest 7717)
# =========================================================================
async def quest_2_train_yourself(cmd: Command):
    quest_id = 7717
    log_info("=== [Quest 2/9] Time to Train Yourself (7717) ===")

    if await cmd.is_completed_before(quest_id):
        log_success("Quest 7717 sudah selesai.")
        return

    req_items = [
        "Desoloth's Destructive Aura",
        "Nythera's Patience",
        "Goregold's Luck",
        "Victorious's Dignity",
        "Trigoras's Tenacity"
    ]
    await check_and_transfer_bank(cmd, req_items)
    cmd.add_drop(req_items)

    await cmd.ensure_accept_quest(quest_id)

    solo_class = cmd.get_solo_class()
    if solo_class:
        await cmd.equip_item(solo_class)

    # 1. Desoloth's Destructive Aura (/dragonchallenge)
    if not cmd.is_in_inventory("Desoloth's Destructive Aura"):
        log_info("Farming Desoloth's Destructive Aura di /dragonchallenge...")
        await hunt_item(
            cmd=cmd,
            item_name="Desoloth's Destructive Aura",
            item_qty=1,
            map_name="dragonchallenge",
            monster_name="Desoloth the Final",
            farming_logger=True
        )

    # 2. Nythera's Patience (/blindingsnow)
    if not cmd.is_in_inventory("Nythera's Patience"):
        log_info("Farming Nythera's Patience di /blindingsnow...")
        await hunt_item(
            cmd=cmd,
            item_name="Nythera's Patience",
            item_qty=1,
            map_name="blindingsnow",
            monster_name="Nythera",
            farming_logger=True
        )

    # 3. Goregold's Luck (/greed)
    if not cmd.is_in_inventory("Goregold's Luck"):
        log_info("Farming Goregold's Luck di /greed...")
        await hunt_item(
            cmd=cmd,
            item_name="Goregold's Luck",
            item_qty=1,
            map_name="greed",
            monster_name="Goregold",
            farming_logger=True
        )

    # 4. Victorious's Dignity (/darkplane)
    if not cmd.is_in_inventory("Victorious's Dignity"):
        log_info("Farming Victorious's Dignity di /darkplane...")
        await hunt_item(
            cmd=cmd,
            item_name="Victorious's Dignity",
            item_qty=1,
            map_name="darkplane",
            monster_name="Victorious",
            farming_logger=True
        )

    # 5. Trigoras's Tenacity x3 (/trigoras)
    if not cmd.is_in_inventory("Trigoras's Tenacity", 3):
        log_info("Farming Trigoras's Tenacity x3 di /trigoras...")
        await hunt_item(
            cmd=cmd,
            item_name="Trigoras's Tenacity",
            item_qty=3,
            map_name="trigoras",
            monster_name="Trigoras",
            farming_logger=True
        )

    await cmd.ensure_turn_in_quest(quest_id)
    log_success("Quest 7717 Selesai!")


# =========================================================================
# QUEST 3: Do You Have the Time? (Quest 7718)
# =========================================================================
async def quest_3_do_you_have_the_time(cmd: Command):
    quest_id = 7718
    log_info("=== [Quest 3/9] Do You Have the Time? (7718) ===")

    if await cmd.is_completed_before(quest_id):
        log_success("Quest 7718 sudah selesai.")
        return

    req_items = [
        "Golden Blade of Fate",
        "Pink Blade of Destruction",
        "Cross-Era Stabilizer",
        "Dragonoid of Hours",
        "Chronomancer's Codex",
        "Timestream String"
    ]
    await check_and_transfer_bank(cmd, req_items)
    cmd.add_drop(req_items)

    solo_class = cmd.get_solo_class()
    farm_class = cmd.get_farm_class()

    # Cek Golden Blade of Fate & Pink Blade of Destruction
    if not cmd.is_in_inventory("Golden Blade of Fate"):
        log_warning("Item 'Golden Blade of Fate' belum ada di inventory/bank. Pastikan Anda telah menyelesaikan questline Golden Blade of Fate.")
    if not cmd.is_in_inventory("Pink Blade of Destruction"):
        log_warning("Item 'Pink Blade of Destruction' belum ada di inventory/bank. Pastikan Anda telah menyelesaikannya di /doomwood (Quest 7650).")

    await cmd.ensure_accept_quest(quest_id)

    # 1. Cross-Era Stabilizer (/underworld - Laken)
    if not cmd.is_in_inventory("Cross-Era Stabilizer"):
        log_info("Farming Cross-Era Stabilizer dari Laken di /underworld...")
        if solo_class:
            await cmd.equip_item(solo_class)
        await hunt_item(
            cmd=cmd,
            item_name="Cross-Era Stabilizer",
            item_qty=1,
            map_name="underworld",
            monster_name="Laken",
            farming_logger=True
        )

    # 2. Chronomancer's Codex (/timespace - Chaos Lord Iadoa)
    if not cmd.is_in_inventory("Chronomancer's Codex"):
        log_info("Farming Dragonoid of Hours di /mqlesson...")
        if solo_class:
            await cmd.equip_item(solo_class)
        await hunt_item(
            cmd=cmd,
            item_name="Dragonoid of Hours",
            item_qty=1,
            map_name="mqlesson",
            monster_name="Dragonoid",
            farming_logger=True
        )
        log_info("Farming Chronomancer's Codex di /timespace...")
        await hunt_item(
            cmd=cmd,
            item_name="Chronomancer's Codex",
            item_qty=1,
            map_name="timespace",
            monster_name="Chaos Lord Iadoa",
            farming_logger=True
        )

    # 3. Timestream String x100 (/arena)
    if not cmd.is_in_inventory("Timestream String", 100):
        log_info("Farming Timestream String x100 di /arena...")
        if farm_class:
            await cmd.equip_item(farm_class)
        await hunt_item(
            cmd=cmd,
            item_name="Timestream String",
            item_qty=100,
            map_name="arena",
            monster_name="Timestream Rider",
            farming_logger=True
        )

    if cmd.is_in_inventory("Golden Blade of Fate") and cmd.is_in_inventory("Pink Blade of Destruction"):
        await cmd.ensure_turn_in_quest(quest_id)
        log_success("Quest 7718 Selesai!")
    else:
        log_warning("Quest 7718 belum bisa di-turn in karena Golden Blade of Fate atau Pink Blade of Destruction belum ada.")


# =========================================================================
# QUEST 4: Through the Wormhole (Quest 7719)
# =========================================================================
async def quest_4_through_the_wormhole(cmd: Command):
    quest_id = 7719
    log_info("=== [Quest 4/9] Through the Wormhole (7719) ===")

    if await cmd.is_completed_before(quest_id):
        log_success("Quest 7719 sudah selesai.")
        return

    req_items = [
        "Time Loop Broken",
        "Anomaly Silenced",
        "Chronolord Stopped",
        "Is This a Wormhole?"
    ]
    await check_and_transfer_bank(cmd, req_items)
    cmd.add_drop(req_items)

    await cmd.ensure_accept_quest(quest_id)

    solo_class = cmd.get_solo_class()
    farm_class = cmd.get_farm_class()

    # 1. Time Loop Broken (/cathedral - Incarnation of Time)
    if not cmd.is_in_inventory("Time Loop Broken"):
        log_info("Farming Time Loop Broken di /cathedral...")
        if solo_class:
            await cmd.equip_item(solo_class)
        await hunt_item(
            cmd=cmd,
            item_name="Time Loop Broken",
            item_qty=1,
            map_name="cathedral",
            monster_name="Incarnation of Time",
            farming_logger=True
        )

    # 2. Anomaly Silenced x100 (/portalwar)
    if not cmd.is_in_inventory("Anomaly Silenced", 100):
        log_info("Farming Anomaly Silenced x100 di /portalwar...")
        if farm_class:
            await cmd.equip_item(farm_class)
        await hunt_item(
            cmd=cmd,
            item_name="Anomaly Silenced",
            item_qty=100,
            map_name="portalwar",
            cell="r4",
            pad="Right",
            monster_name="*",
            farming_logger=True
        )

    # 3. Chronolord Stopped x50 (/portalmaze)
    if not cmd.is_in_inventory("Chronolord Stopped", 50):
        log_info("Farming Chronolord Stopped x50 di /portalmaze...")
        if farm_class:
            await cmd.equip_item(farm_class)
        await hunt_item(
            cmd=cmd,
            item_name="Chronolord Stopped",
            item_qty=50,
            map_name="portalmaze",
            monster_name="ChronoLord",
            farming_logger=True
        )

    # 4. Is This a Wormhole? (/ubear - Cornholio)
    if not cmd.is_in_inventory("Is This a Wormhole?"):
        log_info("Farming Is This a Wormhole? di /ubear...")
        if solo_class:
            await cmd.equip_item(solo_class)
        await hunt_item(
            cmd=cmd,
            item_name="Is This a Wormhole?",
            item_qty=1,
            map_name="ubear",
            monster_name="Cornholio",
            farming_logger=True
        )

    await cmd.ensure_turn_in_quest(quest_id)
    log_success("Quest 7719 Selesai! (Dragon of Time Armor unlocked)")


# =========================================================================
# QUEST 5: Rend (Quest 7720)
# =========================================================================
async def quest_5_rend(cmd: Command):
    quest_id = 7720
    log_info("=== [Quest 5/9] Rend (7720) ===")

    if await cmd.is_completed_before(quest_id):
        log_success("Quest 7720 sudah selesai.")
        return

    req_items = [
        "Dimensional Dragon Portal",
        "Brutal Slash Studied",
        "Epic Hydra Fang"
    ]
    await check_and_transfer_bank(cmd, req_items)
    cmd.add_drop(req_items)

    await cmd.ensure_accept_quest(quest_id)

    solo_class = cmd.get_solo_class()
    farm_class = cmd.get_farm_class()

    # 1. Dimensional Dragon Portal x2 (/lairdefend)
    if not cmd.is_in_inventory("Dimensional Dragon Portal", 2):
        log_info("Farming Dimensional Dragon Portal x2 di /lairdefend...")
        if solo_class:
            await cmd.equip_item(solo_class)
        await hunt_item(
            cmd=cmd,
            item_name="Dimensional Dragon Portal",
            item_qty=2,
            map_name="lairdefend",
            monster_name="Dragon Summoner",
            farming_logger=True
        )

    # 2. Brutal Slash Studied x10 (/bosschallenge - Grievous Inbunche)
    if not cmd.is_in_inventory("Brutal Slash Studied", 10):
        log_info("Farming Brutal Slash Studied x10 di /bosschallenge...")
        if solo_class:
            await cmd.equip_item(solo_class)
        await hunt_item(
            cmd=cmd,
            item_name="Brutal Slash Studied",
            item_qty=10,
            map_name="bosschallenge",
            monster_name="Grievous Inbunche",
            farming_logger=True
        )

    # 3. Epic Hydra Fang x125 (/hydrachallenge)
    if not cmd.is_in_inventory("Epic Hydra Fang", 125):
        log_info("Farming Epic Hydra Fang x125 di /hydrachallenge...")
        if farm_class:
            await cmd.equip_item(farm_class)
        await hunt_item(
            cmd=cmd,
            item_name="Epic Hydra Fang",
            item_qty=125,
            map_name="hydrachallenge",
            cell="h90",
            pad="Left",
            monster_name="*",
            farming_logger=True
        )

    await cmd.ensure_turn_in_quest(quest_id)
    log_success("Quest 7720 Selesai!")


# =========================================================================
# QUEST 6: Confluence of Fates (Quest 7721)
# =========================================================================
async def quest_6_confluence_of_fates(cmd: Command):
    quest_id = 7721
    log_info("=== [Quest 6/9] Confluence of Fates (7721) ===")

    if await cmd.is_completed_before(quest_id):
        log_success("Quest 7721 sudah selesai.")
        return

    req_items = [
        "Sword of Voids",
        "Darkon's Receipt",
        "Semiramis Feather",
        "Cross-Dimensional Weapons",
        "Starlight Singularity",
        "Unidentified 34"
    ]
    await check_and_transfer_bank(cmd, req_items)
    cmd.add_drop(req_items)

    solo_class = cmd.get_solo_class()
    farm_class = cmd.get_farm_class()

    # 1. Sword of Voids (/ivoliss)
    if not cmd.is_in_inventory("Sword of Voids"):
        log_info("Farming Sword of Voids di /ivoliss...")
        if solo_class:
            await cmd.equip_item(solo_class)
        await hunt_item(
            cmd=cmd,
            item_name="Sword of Voids",
            item_qty=1,
            map_name="ivoliss",
            monster_name="Ivoliss",
            farming_logger=True
        )

    # 2. Darkon's Receipt x100 (via bot.darkon_mats)
    if not cmd.is_in_inventory("Darkon's Receipt", 100):
        log_info(f"Farming Darkon's Receipt ({cmd.get_quant_item('Darkon\'s Receipt')}/100)...")
        await darkons_receipts_arcangrove(cmd, 100)

    # 3. Semiramis Feather (/guardiantree - Quest 6286)
    if not cmd.is_in_inventory("Semiramis Feather"):
        log_info("Farming Semiramis Feather di /guardiantree (Quest 6286)...")
        if solo_class:
            await cmd.equip_item(solo_class)
        await cmd.ensure_accept_quest(6286)
        await hunt_item(
            cmd=cmd,
            item_name="Semiramis Feather",
            item_qty=1,
            map_name="guardiantree",
            cell="r12",
            pad="Left",
            monster_name="Terrane",
            farming_logger=True
        )
        await cmd.ensure_turn_in_quest(6286)

    # 4. Cross-Dimensional Weapons x300 (/aqw3d)
    if not cmd.is_in_inventory("Cross-Dimensional Weapons", 300):
        log_info("Farming Cross-Dimensional Weapons x300 di /aqw3d...")
        if farm_class:
            await cmd.equip_item(farm_class)
        await hunt_item(
            cmd=cmd,
            item_name="Cross-Dimensional Weapons",
            item_qty=300,
            map_name="aqw3d",
            cell="r13",
            pad="Bottom",
            monster_name="*",
            farming_logger=True
        )

    # 5. Starlight Singularity (/whitehole - Quest 5186)
    if not cmd.is_in_inventory("Starlight Singularity"):
        log_info("Farming Starlight Singularity di /whitehole (Quest 5186)...")
        if solo_class:
            await cmd.equip_item(solo_class)
        await cmd.ensure_accept_quest(5186)
        await hunt_item(
            cmd=cmd,
            item_name="Mehen Slain",
            item_qty=1,
            map_name="whitehole",
            monster_name="Mehensi Serpent",
            is_temp=True,
            farming_logger=True
        )
        await cmd.ensure_turn_in_quest(5186)

    # 6. Unidentified 34 (Shop 325 di /collection)
    if not cmd.is_in_inventory("Unidentified 34"):
        log_info("Membeli Unidentified 34 di /collection (Shop 325)...")
        if cmd.is_not_in_map("collection"):
            await cmd.join_map("collection")
            await cmd.sleep(1000)
        await cmd.ensure_load_shop(325)
        await cmd.buy_item(325, "Unidentified 34", 1)
        await cmd.sleep(500)

    await cmd.ensure_accept_quest(quest_id)
    await cmd.ensure_turn_in_quest(quest_id)
    log_success("Quest 7721 Selesai!")


# =========================================================================
# QUEST 7: Dragon's Will (Quest 7722)
# =========================================================================
async def quest_7_dragons_will(cmd: Command):
    quest_id = 7722
    log_info("=== [Quest 7/9] Dragon's Will (7722) ===")

    if await cmd.is_completed_before(quest_id):
        log_success("Quest 7722 sudah selesai.")
        return

    req_items = [
        "Unyielding Slime",
        "Omnipotent Cells",
        "Dragon's Plasma",
        "Chaotic Invertebrae",
        "Cryostatic Essence",
        "Salvaged Chaos Dragon Biomass"
    ]
    await check_and_transfer_bank(cmd, req_items)
    cmd.add_drop(req_items)

    await cmd.ensure_accept_quest(quest_id)

    solo_class = cmd.get_solo_class()
    farm_class = cmd.get_farm_class()

    # 1. Unyielding Slime x300 (/moonlab)
    if not cmd.is_in_inventory("Unyielding Slime", 300):
        log_info("Farming Unyielding Slime x300 di /moonlab...")
        if farm_class:
            await cmd.equip_item(farm_class)
        await hunt_item(
            cmd=cmd,
            item_name="Unyielding Slime",
            item_qty=300,
            map_name="moonlab",
            monster_name="Slime Mold",
            farming_logger=True
        )

    # 2. Omnipotent Cells x20 (/bosschallenge - Mutated Void Dragon)
    if not cmd.is_in_inventory("Omnipotent Cells", 20):
        log_info("Farming Omnipotent Cells x20 di /bosschallenge...")
        if solo_class:
            await cmd.equip_item(solo_class)
        await hunt_item(
            cmd=cmd,
            item_name="Omnipotent Cells",
            item_qty=20,
            map_name="bosschallenge",
            monster_name="Mutated Void Dragon",
            farming_logger=True
        )

    # 3. Dragon's Plasma x20 (/underlair - ArchFiend Dragonlord)
    if not cmd.is_in_inventory("Dragon's Plasma", 20):
        log_info("Farming Dragon's Plasma x20 di /underlair...")
        if solo_class:
            await cmd.equip_item(solo_class)
        await hunt_item(
            cmd=cmd,
            item_name="Dragon's Plasma",
            item_qty=20,
            map_name="underlair",
            monster_name="ArchFiend Dragonlord",
            farming_logger=True
        )

    # 4. Chaotic Invertebrae x20 (/chaoskraken)
    if not cmd.is_in_inventory("Chaotic Invertebrae", 20):
        log_info("Farming Chaotic Invertebrae x20 di /chaoskraken...")
        if solo_class:
            await cmd.equip_item(solo_class)
        await hunt_item(
            cmd=cmd,
            item_name="Chaotic Invertebrae",
            item_qty=20,
            map_name="chaoskraken",
            monster_name="Chaos Kraken",
            farming_logger=True
        )

    # 5. Cryostatic Essence x20 (/towerofdoom9 - Dread Fang)
    if not cmd.is_in_inventory("Cryostatic Essence", 20):
        log_info("Farming Cryostatic Essence x20 di /towerofdoom9...")
        if solo_class:
            await cmd.equip_item(solo_class)
        await hunt_item(
            cmd=cmd,
            item_name="Cryostatic Essence",
            item_qty=20,
            map_name="towerofdoom9",
            monster_name="Dread Fang",
            farming_logger=True
        )

    # 6. Salvaged Chaos Dragon Biomass x20 (/castleroof - Ultra Chaos Dragon)
    if not cmd.is_in_inventory("Salvaged Chaos Dragon Biomass", 20):
        log_info("Farming Salvaged Chaos Dragon Biomass x20 di /castleroof...")
        if solo_class:
            await cmd.equip_item(solo_class)
        await hunt_item(
            cmd=cmd,
            item_name="Salvaged Chaos Dragon Biomass",
            item_qty=20,
            map_name="castleroof",
            monster_name="Ultra Chaos Dragon",
            farming_logger=True
        )

    await cmd.ensure_turn_in_quest(quest_id)
    log_success("Quest 7722 Selesai!")


# =========================================================================
# QUEST 8: Burning Fates (Quest 7723)
# =========================================================================
async def quest_8_burning_fates(cmd: Command):
    quest_id = 7723
    log_info("=== [Quest 8/9] Burning Fates (7723) ===")

    if await cmd.is_completed_before(quest_id):
        log_success("Quest 7723 sudah selesai.")
        return

    req_items = [
        "Fire Essence",
        "Akriloth's Flametongue",
        "Immortal Embers",
        "Ashes from the Void Realm"
    ]
    await check_and_transfer_bank(cmd, req_items)
    cmd.add_drop(req_items)

    await cmd.ensure_accept_quest(quest_id)

    solo_class = cmd.get_solo_class()
    farm_class = cmd.get_farm_class()

    # 1. Fire Essence x3000 (/volcano)
    if not cmd.is_in_inventory("Fire Essence", 3000):
        log_info("Farming Fire Essence x3000 di /volcano...")
        if farm_class:
            await cmd.equip_item(farm_class)
        await hunt_item(
            cmd=cmd,
            item_name="Fire Essence",
            item_qty=3000,
            map_name="volcano",
            cell="r10",
            pad="Left",
            monster_name="Fire Imp",
            farming_logger=True
        )

    # 2. Akriloth's Flametongue x100 (/charredplains - Akriloth)
    if not cmd.is_in_inventory("Akriloth's Flametongue", 100):
        log_info("Farming Akriloth's Flametongue x100 di /charredplains...")
        if solo_class:
            await cmd.equip_item(solo_class)
        await hunt_item(
            cmd=cmd,
            item_name="Akriloth's Flametongue",
            item_qty=100,
            map_name="charredplains",
            monster_name="Akriloth",
            farming_logger=True
        )

    # 3. Immortal Embers x50 (/ultraphedra - Ultra Phedra)
    if not cmd.is_in_inventory("Immortal Embers", 50):
        log_info("Farming Immortal Embers x50 di /ultraphedra...")
        if solo_class:
            await cmd.equip_item(solo_class)
        await hunt_item(
            cmd=cmd,
            item_name="Immortal Embers",
            item_qty=50,
            map_name="ultraphedra",
            monster_name="Ultra Phedra",
            farming_logger=True
        )

    # 4. Ashes from the Void Realm x50 (/thevoid - Reaper)
    if not cmd.is_in_inventory("Ashes from the Void Realm", 50):
        log_info("Farming Ashes from the Void Realm x50 di /thevoid...")
        if solo_class:
            await cmd.equip_item(solo_class)
        await hunt_item(
            cmd=cmd,
            item_name="Ashes from the Void Realm",
            item_qty=50,
            map_name="thevoid",
            monster_name="Reaper",
            farming_logger=True
        )

    await cmd.ensure_turn_in_quest(quest_id)
    log_success("Quest 7723 Selesai!")


# =========================================================================
# QUEST 9: Hero's Heartbeat (Quest 7724) -> DRAGON OF TIME CLASS!
# =========================================================================
async def quest_9_heros_heartbeat(cmd: Command):
    quest_id = 7724
    log_info("=== [Quest 9/9] Hero's Heartbeat (7724) -> DRAGON OF TIME! ===")

    if cmd.is_in_inventory_or_bank(DOT_CLASS_NAME):
        await check_and_transfer_bank(cmd, [DOT_CLASS_NAME])
        log_success("Class 'Dragon of Time' sudah ada di inventory!")
        return

    req_items = [
        "Mysterious Egg",
        "Blade of Awe",
        "Conquered Past",
        "Slugbutter Trophy",
        "Icewing's Laurel"
    ]
    await check_and_transfer_bank(cmd, req_items)
    cmd.add_drop(req_items + [DOT_CLASS_NAME])

    solo_class = cmd.get_solo_class()
    if solo_class:
        await cmd.equip_item(solo_class)

    # Cek Blade of Awe
    if not cmd.is_in_inventory("Blade of Awe"):
        log_warning("Item 'Blade of Awe' belum ada di inventory. Diperlukan untuk menyelesaikan quest ini.")

    # Cek Mysterious Egg
    if not cmd.is_in_inventory("Mysterious Egg"):
        log_info("Mengecek Mysterious Egg (Quest 6171)...")
        egg_keys = [
            "Key of Pride",
            "Key of Gluttony",
            "Key of Greed",
            "Key of Sloth",
            "Key of Lust",
            "Key of Envy",
            "Key of Wrath"
        ]
        cmd.add_drop(egg_keys)
        await cmd.ensure_accept_quest(6171)

        # 7 Deadly Dragons keys
        if not cmd.is_in_inventory("Key of Pride"):
            await hunt_item(cmd, "Key of Pride", 1, "pride", "r13", "Left", monster_name="Valsarian", farming_logger=True)
        if not cmd.is_in_inventory("Key of Gluttony"):
            await hunt_item(cmd, "Key of Gluttony", 1, "gluttony", "Enter2", "Top", monster_name="Deflated Glutus", farming_logger=True)
        if not cmd.is_in_inventory("Key of Greed"):
            await hunt_item(cmd, "Key of Greed", 1, "greed", "r16", "Left", monster_name="Goregold", farming_logger=True)
        if not cmd.is_in_inventory("Key of Sloth"):
            await hunt_item(cmd, "Key of Sloth", 1, "sloth", monster_name="Phlegnn", farming_logger=True)
        if not cmd.is_in_inventory("Key of Lust"):
            await hunt_item(cmd, "Key of Lust", 1, "lust", monster_name="Lascivia", farming_logger=True)
        if not cmd.is_in_inventory("Key of Envy"):
            await hunt_item(cmd, "Key of Envy", 1, "maloth", monster_name="Maloth", farming_logger=True)
        if not cmd.is_in_inventory("Key of Wrath"):
            await hunt_item(cmd, "Key of Wrath", 1, "wrath", monster_name="Gorgorath", farming_logger=True)

        if cmd.can_turnin_quest(6171):
            await cmd.ensure_turn_in_quest(6171)
            await cmd.sleep(1000)

    await cmd.ensure_accept_quest(quest_id)

    # 1. Conquered Past (/chaoslord)
    if not cmd.is_in_inventory("Conquered Past"):
        log_info("Farming Conquered Past di /chaoslord...")
        await hunt_item(
            cmd=cmd,
            item_name="Conquered Past",
            item_qty=1,
            map_name="chaoslord",
            cell="r2",
            pad="Left",
            monster_name="*",
            farming_logger=True
        )

    # 2. Slugbutter Trophy x100 (/towerofdoom10 - Slugbutter)
    if not cmd.is_in_inventory("Slugbutter Trophy", 100):
        log_info("Farming Slugbutter Trophy x100 di /towerofdoom10...")
        await hunt_item(
            cmd=cmd,
            item_name="Slugbutter Trophy",
            item_qty=100,
            map_name="towerofdoom10",
            monster_name="Slugbutter",
            farming_logger=True
        )

    # 3. Icewing's Laurel x30 (/icewing - Warlord Icewing)
    if not cmd.is_in_inventory("Icewing's Laurel", 30):
        log_info("Farming Icewing's Laurel x30 di /icewing...")
        await hunt_item(
            cmd=cmd,
            item_name="Icewing's Laurel",
            item_qty=30,
            map_name="icewing",
            monster_name="Warlord Icewing",
            farming_logger=True
        )

    await cmd.ensure_turn_in_quest(quest_id)
    await cmd.sleep(1500)

    if cmd.is_in_inventory(DOT_CLASS_NAME):
        print(Fore.GREEN + "\n========================================================")
        print("  CONGRATULATIONS! CLASS UNLOCKED: DRAGON OF TIME!")
        print("========================================================\n" + Fore.RESET)
    else:
        log_warning("Quest 7724 telah selesai diproses. Periksa inventory Anda untuk class Dragon of Time.")


# =========================================================================
# MAIN ENTRYPOINT
# =========================================================================
async def main(cmd: Command):
    log_info("Memulai Scriptable Bot: Dragon of Time Class...")

    # Cek apakah sudah punya Dragon of Time
    if cmd.is_in_inventory_or_bank(DOT_CLASS_NAME):
        await check_and_transfer_bank(cmd, [DOT_CLASS_NAME])
        log_success(f"Class '{DOT_CLASS_NAME}' sudah dimiliki di inventory!")
        return

    # Whitelist all drops
    cmd.add_drop(ALL_DOT_DROPS)

    # Jalankan rangkaian Quest 1 - 9 secara berurutan
    await quest_1_ancient_secrets(cmd)
    await quest_2_train_yourself(cmd)
    await quest_3_do_you_have_the_time(cmd)
    await quest_4_through_the_wormhole(cmd)
    await quest_5_rend(cmd)
    await quest_6_confluence_of_fates(cmd)
    await quest_7_dragons_will(cmd)
    await quest_8_burning_fates(cmd)
    await quest_9_heros_heartbeat(cmd)

    if cmd.is_in_inventory(DOT_CLASS_NAME):
        log_success("Bot Dragon of Time selesai dengan sukses!")
    else:
        log_warning("Bot telah mengeksekusi semua langkah. Pastikan item pendukung (Golden Blade of Fate, Pink Blade of Destruction, Blade of Awe) sudah dimiliki.")


if __name__ == "__main__":
    username = input("Username: ")
    password = input("Password: ")
    server = input("Server: ")

    b = Bot(
        roomNumber=1,
        itemsDropWhiteList=ALL_DOT_DROPS,
        showLog=True,
        showDebug=False,
        showChat=True,
        isScriptable=True,
        autoRelogin=True,
        muteSpamWarning=True
    )
    b.set_login_info(username, password, server)
    asyncio.run(b.start_bot(main))
