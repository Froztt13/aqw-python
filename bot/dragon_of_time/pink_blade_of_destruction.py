import asyncio
from datetime import datetime
from colorama import Fore
from core.bot import Bot
from core.command import Command
from templates.hunt import hunt_item, kill_quest, attack_script

PBOD_ITEM_NAME = "Pink Blade of Destruction"
PBOD_ITEM_ID = 55884

PBOD_DROPS = [
    # Final item
    "Pink Blade of Destruction",

    # Fuchsia Dye requirements
    "Fuchsia Dye",
    "Pink Coral",
    "Amaranth Flower",

    # Spirit Orb requirements
    "Spirit Orb",
    "Bone Dust",
    "Undead Essence",

    # Zealous Badge requirements
    "Zealous Badge",
    "Immutable Dedication",
    "Paladin Armor Scraps",

    # Boss drops
    "Unicorn Essence",
    "Gem Power",
]


def log_info(msg: str):
    print(Fore.MAGENTA + f"[{datetime.now().strftime('%H:%M:%S')}][PBoD] " + Fore.WHITE + msg + Fore.RESET)


def log_success(msg: str):
    print(Fore.GREEN + f"[{datetime.now().strftime('%H:%M:%S')}][PBoD] " + msg + Fore.RESET)


def log_warning(msg: str):
    print(Fore.YELLOW + f"[{datetime.now().strftime('%H:%M:%S')}][PBoD] " + msg + Fore.RESET)


def log_error(msg: str):
    print(Fore.RED + f"[{datetime.now().strftime('%H:%M:%S')}][PBoD] " + msg + Fore.RESET)


async def check_and_transfer_bank(cmd: Command, items: list[str]):
    """Check items in bank and move them to inventory if found."""
    for item in items:
        if cmd.is_in_bank(item):
            log_info(f"Moving '{item}' from Bank to Inventory...")
            await cmd.bank_to_inv(item)
            await cmd.sleep(300)


# =========================================================================
# Story Helper: Doomwood Part 3 (Quests 7589 -> 7653)
# =========================================================================
async def kill_monsters_for_quest(cmd: Command, quest_id: int, map_name: str, monsters: list[str]):
    """Helper to defeat one or more monster types until quest is turn-in ready."""
    await cmd.ensure_accept_quest(quest_id)
    if cmd.can_turnin_quest(quest_id):
        await cmd.ensure_turn_in_quest(quest_id)
        return

    if cmd.is_not_in_map(map_name):
        await cmd.join_map(map_name)
        await cmd.sleep(1000)

    while cmd.is_still_connected() and not cmd.can_turnin_quest(quest_id):
        for m in monsters:
            if cmd.can_turnin_quest(quest_id):
                break
            await cmd.jump_to_monster(m)
            for _ in range(5):
                if cmd.can_turnin_quest(quest_id):
                    break
                await attack_script(cmd, m)
                await cmd.sleep(200)

    await cmd.leave_combat()
    await cmd.ensure_turn_in_quest(quest_id)


async def is_quest_completed(cmd: Command, quest_id: int) -> bool:
    """Return True if a one-time story quest is already completed before."""
    return await cmd.is_completed_before(quest_id)


async def map_item_quest(
    cmd: Command,
    quest_id: int,
    map_name: str,
    map_item_ids: list,
    extra_monsters: list[str] = None
):
    """Helper to collect map items and optionally defeat monsters to complete a quest."""
    await cmd.ensure_accept_quest(quest_id)
    if cmd.can_turnin_quest(quest_id):
        await cmd.ensure_turn_in_quest(quest_id)
        return

    if cmd.is_not_in_map(map_name):
        await cmd.join_map(map_name)
        await cmd.sleep(1000)

    for item_entry in map_item_ids:
        item_id = item_entry[0]
        qty = item_entry[1]
        item_name = item_entry[2] if len(item_entry) > 2 else None
        await cmd.get_map_item(item_id, qty, item_name)
        await cmd.sleep(500)

    if extra_monsters:
        while cmd.is_still_connected() and not cmd.can_turnin_quest(quest_id):
            for m in extra_monsters:
                if cmd.can_turnin_quest(quest_id):
                    break
                await cmd.jump_to_monster(m)
                for _ in range(5):
                    if cmd.can_turnin_quest(quest_id):
                        break
                    await attack_script(cmd, m)
                    await cmd.sleep(200)
        await cmd.leave_combat()

    await cmd.ensure_turn_in_quest(quest_id)


async def complete_doomwood_part_3(cmd: Command):
    """Ensure Doomwood Part 3 (Quests 7589 -> 7653) is completed."""
    if await is_quest_completed(cmd, 7653):
        log_info("Doomwood Part 3 is already completed (Quest 7653 is completed).")
        return

    log_info("Doomwood Part 3 not yet finished. Checking progression...")

    # Equip farm class by default for story trash mobs
    farm_class = cmd.get_farm_class()
    solo_class = cmd.get_solo_class()
    if farm_class:
        await cmd.equip_item(farm_class)

    # ----------------- Part 3.1: Thorngarde (7589 - 7601) -----------------
    if not await is_quest_completed(cmd, 7589):
        log_info("Doing Quest 7589: Bullies...")
        await kill_monsters_for_quest(cmd, 7589, "thorngarde", ["CryptHacker", "NecroDrone", "NecroMech"])

    if not await is_quest_completed(cmd, 7590):
        log_info("Doing Quest 7590: Free the People...")
        await map_item_quest(cmd, 7590, "thorngarde", [(7485, 5, "Villager Released")], extra_monsters=["NecroMech"])

    if not await is_quest_completed(cmd, 7591):
        log_info("Doing Quest 7591: Sample It...")
        await kill_monsters_for_quest(cmd, 7591, "thorngarde", ["NecroMech"])

    if not await is_quest_completed(cmd, 7592):
        log_info("Doing Quest 7592: Swat the Flies...")
        await kill_monsters_for_quest(cmd, 7592, "thorngarde", ["CryptHacker"])

    if not await is_quest_completed(cmd, 7593):
        log_info("Doing Quest 7593: Reclaim the Supplies...")
        await cmd.ensure_accept_quest(7593)
        await hunt_item(cmd=cmd, item_name="Cured Meat", item_qty=3, map_name="thorngarde", monster_name="CryptHacker", is_temp=True)
        await hunt_item(cmd=cmd, item_name="Bag of Grain", item_qty=3, map_name="thorngarde", monster_name="NecroMech", is_temp=True)
        await hunt_item(cmd=cmd, item_name="Jug of Water", item_qty=5, map_name="thorngarde", monster_name="NecroDrone", is_temp=True)
        await cmd.ensure_turn_in_quest(7593)

    if not await is_quest_completed(cmd, 7594):
        log_info("Doing Quest 7594: Who's That?...")
        await map_item_quest(cmd, 7594, "thorngarde", [(7486, 1)])

    if not await is_quest_completed(cmd, 7595):
        log_info("Doing Quest 7595: Find my Stuff...")
        await map_item_quest(cmd, 7595, "thorngarde", [(7487, 1), (7488, 1)], extra_monsters=["NecroDrone"])

    if not await is_quest_completed(cmd, 7596):
        log_info("Doing Quest 7596: Save my Friends...")
        await map_item_quest(cmd, 7596, "thorngarde", [(7489, 1), (7490, 1), (7491, 1)], extra_monsters=["NecroMech"])

    if not await is_quest_completed(cmd, 7597):
        log_info("Doing Quest 7597: Pull the Wires...")
        await kill_monsters_for_quest(cmd, 7597, "thorngarde", ["CryptHacker"])

    if not await is_quest_completed(cmd, 7598):
        log_info("Doing Quest 7598: Dress-up Time!...")
        await kill_monsters_for_quest(cmd, 7598, "thorngarde", ["CryptHacker", "NecroDrone"])

    if not await is_quest_completed(cmd, 7599):
        log_info("Doing Quest 7599: I Need a Distraction...")
        await cmd.ensure_accept_quest(7599)
        await hunt_item(cmd=cmd, item_name="NecroMech Slain", item_qty=5, map_name="thorngarde", monster_name="NecroMech", is_temp=True)
        await hunt_item(cmd=cmd, item_name="CryptHacker Slain", item_qty=5, map_name="thorngarde", monster_name="CryptHacker", is_temp=True)
        await hunt_item(cmd=cmd, item_name="NecroDrone Slain", item_qty=5, map_name="thorngarde", monster_name="NecroDrone", is_temp=True)
        await cmd.ensure_turn_in_quest(7599)

    if not await is_quest_completed(cmd, 7600):
        log_info("Doing Quest 7600: Zyrus is Lost...")
        if solo_class:
            await cmd.equip_item(solo_class)
        await kill_monsters_for_quest(cmd, 7600, "thorngarde", ["Zyrus the BioKnight"])
        if farm_class:
            await cmd.equip_item(farm_class)

    if not await is_quest_completed(cmd, 7601):
        log_info("Doing Quest 7601: Investigate the Tech...")
        await cmd.ensure_accept_quest(7601)
        await hunt_item(cmd=cmd, item_name="Deadtech Power Core", item_qty=7, map_name="thorngarde", monster_name="NecroDrone", is_temp=True)
        await hunt_item(cmd=cmd, item_name="NecroMech Targeting Systems", item_qty=5, map_name="thorngarde", monster_name="NecroMech", is_temp=True)
        await hunt_item(cmd=cmd, item_name="CryptHacker Circuitry", item_qty=15, map_name="thorngarde", monster_name="CryptHacker", is_temp=True)
        if solo_class:
            await cmd.equip_item(solo_class)
        await hunt_item(cmd=cmd, item_name="BioKnight Engine", item_qty=3, map_name="thorngarde", monster_name="Zyrus the BioKnight", is_temp=True)
        if farm_class:
            await cmd.equip_item(farm_class)
        await cmd.ensure_turn_in_quest(7601)

    # ----------------- Part 3.2: Stonewood (7603 - 7608) -----------------
    if not await is_quest_completed(cmd, 7603):
        log_info("Doing Quest 7603: Defeat the Deadtech...")
        await kill_monsters_for_quest(cmd, 7603, "stonewood", ["NecroDrone"])

    if not await is_quest_completed(cmd, 7604):
        log_info("Doing Quest 7604: Gather Spell Components...")
        await map_item_quest(cmd, 7604, "stonewood", [(7510, 6)], extra_monsters=["Doomwood Treeant"])

    if not await is_quest_completed(cmd, 7605):
        log_info("Doing Quest 7605: A Few Things More...")
        await kill_monsters_for_quest(cmd, 7605, "stonewood", ["NecroDrone", "NecroMech"])

    if not await is_quest_completed(cmd, 7606):
        log_info("Doing Quest 7606: Search for the Axe...")
        await map_item_quest(cmd, 7606, "stonewood", [(7511, 4), (7512, 1)])

    if not await is_quest_completed(cmd, 7607):
        log_info("Doing Quest 7607: Defeat the BioKnight...")
        if solo_class:
            await cmd.equip_item(solo_class)
        await kill_monsters_for_quest(cmd, 7607, "stonewood", ["BioKnight"])
        if farm_class:
            await cmd.equip_item(farm_class)

    if not await is_quest_completed(cmd, 7608):
        log_info("Doing Quest 7608: Take the Axe!...")
        await map_item_quest(cmd, 7608, "stonewood", [(7513, 1)])

    # ----------------- Part 3.3: TechDungeon (7609 - 7615) -----------------
    if not await is_quest_completed(cmd, 7609):
        log_info("Doing Quest 7609: Find the Keys...")
        await kill_monsters_for_quest(cmd, 7609, "techdungeon", ["NecroMech"])

    if not await is_quest_completed(cmd, 7610):
        log_info("Doing Quest 7610: Ew, Rats...")
        await map_item_quest(cmd, 7610, "techdungeon", [(7515, 6)], extra_monsters=["Rotting Rat"])

    if not await is_quest_completed(cmd, 7611):
        log_info("Doing Quest 7611: Grab Their Gear...")
        await cmd.ensure_accept_quest(7611)
        await hunt_item(cmd=cmd, item_name="Guard Armor Piece", item_qty=5, map_name="techdungeon", monster_name="DoomBorg Guard", is_temp=True)
        await hunt_item(cmd=cmd, item_name="Guard Helm", item_qty=1, map_name="techdungeon", monster_name="DoomBorg Guard", is_temp=True)
        await hunt_item(cmd=cmd, item_name="Deadtech Polearm", item_qty=1, map_name="techdungeon", monster_name="DoomBorg Guard", is_temp=True)
        await cmd.ensure_turn_in_quest(7611)

    if not await is_quest_completed(cmd, 7612):
        log_info("Doing Quest 7612: Talk to the Guard...")
        await map_item_quest(cmd, 7612, "techdungeon", [(7514, 1)])

    if not await is_quest_completed(cmd, 7613):
        log_info("Doing Quest 7613: Let Them Out!...")
        await map_item_quest(cmd, 7613, "techdungeon", [(7516, 1)])

    if not await is_quest_completed(cmd, 7614):
        log_info("Doing Quest 7614: Head on Out...")
        await map_item_quest(cmd, 7614, "techdungeon", [(7517, 1)], extra_monsters=["DoomBorg Guard"])

    if not await is_quest_completed(cmd, 7615):
        log_info("Doing Quest 7615: Take Him Down...")
        if solo_class:
            await cmd.equip_item(solo_class)
        await kill_monsters_for_quest(cmd, 7615, "techdungeon", ["Kalron the Cryptborg"])
        if farm_class:
            await cmd.equip_item(farm_class)

    # ----------------- Part 3.4: StonewoodForest (7623 - 7636) -----------------
    if not await is_quest_completed(cmd, 7623):
        log_info("Doing Quest 7623: Cat Ears?...")
        await map_item_quest(cmd, 7623, "stonewooddeep", [(7528, 1)])
        await cmd.sleep(2000)
        await cmd.jump_cell("Enter", "Spawn")

    if not await is_quest_completed(cmd, 7624):
        log_info("Doing Quest 7624: EN GARDE!...")
        if solo_class:
            await cmd.equip_item(solo_class)
        await kill_monsters_for_quest(cmd, 7624, "stonewooddeep", ["Asherion"])
        if farm_class:
            await cmd.equip_item(farm_class)

    if not await is_quest_completed(cmd, 7625):
        log_info("Doing Quest 7625: The Light Of Destiny...")
        await map_item_quest(cmd, 7625, "stonewooddeep", [(7529, 1)])
        await cmd.sleep(2000)
        await cmd.jump_cell("Enter", "Spawn")

    if not await is_quest_completed(cmd, 7626):
        log_info("Doing Quest 7626: Stuff for Dummies...")
        await cmd.ensure_accept_quest(7626)
        await hunt_item(cmd=cmd, item_name="Sturdy Wood", item_qty=8, map_name="stonewooddeep", monster_name="Doomwood Treeant", is_temp=True)
        await cmd.get_map_item(7530, 8)
        await cmd.ensure_turn_in_quest(7626)

    if not await is_quest_completed(cmd, 7627):
        log_info("Doing Quest 7627: Build the Dummies...")
        await cmd.ensure_accept_quest(7627)
        await hunt_item(cmd=cmd, item_name="Area Cleared", item_qty=10, map_name="stonewooddeep", monster_name="Doomwood Treeant", is_temp=True)
        await cmd.get_map_item(7531, 6)
        await cmd.ensure_turn_in_quest(7627)

    if not await is_quest_completed(cmd, 7628):
        log_info("Doing Quest 7628: Battle the Dummies...")
        await kill_monsters_for_quest(cmd, 7628, "stonewooddeep", ["Target Dummy"])

    if not await is_quest_completed(cmd, 7629):
        log_info("Doing Quest 7629: Lesson 1: Bravery...")
        await kill_monsters_for_quest(cmd, 7629, "stonewooddeep", ["Doomwood Slime"])

    if not await is_quest_completed(cmd, 7630):
        log_info("Doing Quest 7630: Lesson 2: Armor...")
        await cmd.ensure_accept_quest(7630)
        await hunt_item(cmd=cmd, item_name="Stolen Armor", item_qty=7, map_name="stonewooddeep", monster_name="Doomwood Slime", is_temp=True)
        await cmd.ensure_turn_in_quest(7630)

    if not await is_quest_completed(cmd, 7631):
        log_info("Doing Quest 7631: Lesson 3: Protection...")
        await cmd.ensure_accept_quest(7631)
        await hunt_item(cmd=cmd, item_name="Crypthacker Slain", item_qty=10, map_name="stonewooddeep", monster_name="CryptHacker", is_temp=True)
        await hunt_item(cmd=cmd, item_name="Unidentified Clue", item_qty=1, map_name="stonewooddeep", monster_name="CryptHacker", is_temp=True)
        await cmd.ensure_turn_in_quest(7631)

    if not await is_quest_completed(cmd, 7632):
        log_info("Doing Quest 7632: Lesson 4: Gather Intelligence...")
        await kill_monsters_for_quest(cmd, 7632, "stonewooddeep", ["CryptHacker"])

    if not await is_quest_completed(cmd, 7633):
        log_info("Doing Quest 7633: Lesson 5: Demolition...")
        await cmd.ensure_accept_quest(7633)
        await hunt_item(cmd=cmd, item_name="Acid Ooze", item_qty=6, map_name="stonewooddeep", monster_name="Doomwood Slime", is_temp=True)
        await hunt_item(cmd=cmd, item_name="Explosive Tech", item_qty=6, map_name="stonewooddeep", monster_name="NecroDrone", is_temp=True)
        await cmd.ensure_turn_in_quest(7633)

    if not await is_quest_completed(cmd, 7634):
        log_info("Doing Quest 7634: Lesson 6: Searching...")
        await map_item_quest(cmd, 7634, "stonewooddeep", [(7532, 1)])

    if not await is_quest_completed(cmd, 7635):
        log_info("Doing Quest 7635: Get the Axe...")
        await map_item_quest(cmd, 7635, "stonewooddeep", [(7533, 1)])
        await cmd.sleep(2000)
        await cmd.jump_cell("Enter", "Spawn")

    if not await is_quest_completed(cmd, 7636):
        log_info("Doing Quest 7636: Never Give Up...")
        if solo_class:
            await cmd.equip_item(solo_class)
        await kill_monsters_for_quest(cmd, 7636, "stonewooddeep", ["Sir Kut"])
        if farm_class:
            await cmd.equip_item(farm_class)

    # ----------------- Part 3.5: TechFortress (7637 - 7653) -----------------
    if not await is_quest_completed(cmd, 7637):
        log_info("Doing Quest 7637: I CPU U!...")
        await kill_monsters_for_quest(cmd, 7637, "techfortress", ["CryptHacker"])

    if not await is_quest_completed(cmd, 7638):
        log_info("Doing Quest 7638: Keep Droning On...")
        await kill_monsters_for_quest(cmd, 7638, "techfortress", ["NecroDrone"])

    if not await is_quest_completed(cmd, 7639):
        log_info("Doing Quest 7639: Gathering Data...")
        await kill_monsters_for_quest(cmd, 7639, "techfortress", ["CryptHacker"])

    if not await is_quest_completed(cmd, 7640):
        log_info("Doing Quest 7640: Signal Flare...")
        await map_item_quest(cmd, 7640, "techfortress", [(7561, 1)], extra_monsters=["NecroDrone"])

    if not await is_quest_completed(cmd, 7641):
        log_info("Doing Quest 7641: Medal Time...")
        await cmd.ensure_accept_quest(7641)
        await hunt_item(cmd=cmd, item_name="NecroMedals", item_qty=5, map_name="techfortress", monster_name="NecroDrone", is_temp=True)
        await cmd.ensure_turn_in_quest(7641)

    if not await is_quest_completed(cmd, 7642):
        log_info("Doing Quest 7642: Hidden Data...")
        await kill_monsters_for_quest(cmd, 7642, "techfortress", ["NecroMech"])

    if not await is_quest_completed(cmd, 7643):
        log_info("Doing Quest 7643: Pass the CPU...")
        await kill_monsters_for_quest(cmd, 7643, "techfortress", ["CPU"])

    if not await is_quest_completed(cmd, 7644):
        log_info("Doing Quest 7644: The Guards...")
        await kill_monsters_for_quest(cmd, 7644, "techfortress", ["DoomBorg Guard"])

    if not await is_quest_completed(cmd, 7645):
        log_info("Doing Quest 7645: Circui-try This...")
        await kill_monsters_for_quest(cmd, 7645, "techfortress", ["DoomBorg Guard"])

    if not await is_quest_completed(cmd, 7646):
        log_info("Doing Quest 7646: The Thing...")
        if solo_class:
            await cmd.equip_item(solo_class)
        await kill_monsters_for_quest(cmd, 7646, "techfortress", ["Vortrix"])
        if farm_class:
            await cmd.equip_item(farm_class)

    if not await is_quest_completed(cmd, 7653):
        log_info("Doing Quest 7653: The Final Form...")
        if solo_class:
            await cmd.equip_item(solo_class)
        await kill_monsters_for_quest(cmd, 7653, "techfortress", ["MechaVortrix"])
        if farm_class:
            await cmd.equip_item(farm_class)

    log_success("Doomwood Part 3 story completion confirmed!")


# =========================================================================
# Item 1: Fuchsia Dye x50 (Quest 1487)
# =========================================================================
async def farm_fuchsia_dye(cmd: Command, target_qty: int = 50):
    """Farm Fuchsia Dye x50 via Quest 1487."""
    log_info(f"Checking Fuchsia Dye (Target: {target_qty})...")
    if cmd.is_in_bank("Fuchsia Dye"):
        await cmd.bank_to_inv("Fuchsia Dye")
        await cmd.sleep(300)

    if cmd.is_in_inventory("Fuchsia Dye", target_qty):
        log_info(f"Fuchsia Dye x{target_qty} already satisfied.")
        return

    cmd.add_drop(["Fuchsia Dye", "Pink Coral", "Amaranth Flower"])
    farm_class = cmd.get_farm_class()
    if farm_class:
        await cmd.equip_item(farm_class)

    while cmd.is_still_connected() and not cmd.is_in_inventory("Fuchsia Dye", target_qty):
        log_info(f"Farming Fuchsia Dye (Target: {target_qty})...")
        await cmd.ensure_accept_quest(1487)

        # Pink Coral x3 from Anglerfish at /natatorium
        await hunt_item(
            cmd=cmd,
            item_name="Pink Coral",
            item_qty=3,
            map_name="natatorium",
            monster_name="Anglerfish",
            is_temp=True,
            farming_logger=False
        )

        # Amaranth Flower x5 from Chaotic Vulture at /bloodtuskwar
        await hunt_item(
            cmd=cmd,
            item_name="Amaranth Flower",
            item_qty=5,
            map_name="bloodtuskwar",
            monster_name="Chaotic Vulture",
            is_temp=True,
            farming_logger=False
        )

        await cmd.ensure_turn_in_quest(1487)
        await cmd.sleep(500)

    log_success(f"Fuchsia Dye x{target_qty} obtained!")


# =========================================================================
# Item 2: Spirit Orb x500 (Quests 2082 & 2083)
# =========================================================================
async def unlock_spirit_orb_quests(cmd: Command):
    """Ensure Quests 2082 & 2083 are unlocked via Artix's quests 2066 & 2067 if needed."""
    if await cmd.is_green_quest(2082) or await cmd.is_green_quest(2083):
        return

    # Check Quest 2066: Reforging the Blinding Light
    if not await is_quest_completed(cmd, 2066):
        log_info("Unlocking Quest 2066 (Reforging the Blinding Light)...")
        if cmd.is_not_in_map("doomwood"):
            await cmd.join_map("doomwood")
            await cmd.sleep(1000)
        if not cmd.is_in_inventory("Blinding Light of Destiny Handle"):
            await cmd.buy_item(276, "Blinding Light of Destiny Handle")
            await cmd.sleep(500)
        await cmd.ensure_accept_quest(2066)
        await cmd.ensure_turn_in_quest(2066)

    # Check Quest 2067: Secret Order of Undead Slayers
    if not await is_quest_completed(cmd, 2067):
        log_info("Unlocking Quest 2067 (Secret Order of Undead Slayers)...")
        if cmd.is_not_in_map("doomwood"):
            await cmd.join_map("doomwood")
            await cmd.sleep(1000)
        if not cmd.is_in_inventory("Bonegrinder Medal"):
            await cmd.buy_item(276, "Bonegrinder Medal")
            await cmd.sleep(500)
        await cmd.ensure_accept_quest(2067)
        await cmd.ensure_turn_in_quest(2067)


async def farm_spirit_orbs(cmd: Command, target_qty: int = 500):
    """Farm Spirit Orb x500 at /battleunderb using Quests 2082 & 2083."""
    log_info(f"Checking Spirit Orb (Target: {target_qty})...")
    if cmd.is_in_bank("Spirit Orb"):
        await cmd.bank_to_inv("Spirit Orb")
        await cmd.sleep(300)

    if cmd.is_in_inventory("Spirit Orb", target_qty):
        log_info(f"Spirit Orb x{target_qty} already satisfied.")
        return

    cmd.add_drop(["Spirit Orb", "Bone Dust", "Undead Essence"])
    await unlock_spirit_orb_quests(cmd)

    farm_class = cmd.get_farm_class()
    if farm_class:
        await cmd.equip_item(farm_class)

    if cmd.is_not_in_map("battleunderb"):
        await cmd.join_map("battleunderb")
        await cmd.sleep(1000)

    await cmd.jump_to_monster("Skeleton Warrior")

    while cmd.is_still_connected() and not cmd.is_in_inventory("Spirit Orb", target_qty):
        if cmd.quest_not_in_progress(2082):
            await cmd.ensure_accept_quest(2082)
        if cmd.quest_not_in_progress(2083):
            await cmd.ensure_accept_quest(2083)

        await attack_script(cmd, "Skeleton Warrior")

        if cmd.is_in_inventory("Undead Essence", 25):
            await cmd.leave_combat()
            await cmd.ensure_turn_in_quest(2082)
            await cmd.ensure_accept_quest(2082)

        if cmd.is_in_inventory("Bone Dust", 40):
            await cmd.leave_combat()
            await cmd.ensure_turn_in_quest(2083)
            await cmd.ensure_accept_quest(2083)

    await cmd.leave_combat()
    log_success(f"Spirit Orb x{target_qty} obtained!")


# =========================================================================
# Item 3: Zealous Badge x5 (Quest 7616)
# =========================================================================
async def farm_zealous_badges(cmd: Command, target_qty: int = 5):
    """Farm Zealous Badge x5 via Quest 7616."""
    log_info(f"Checking Zealous Badge (Target: {target_qty})...")
    if cmd.is_in_bank("Zealous Badge"):
        await cmd.bank_to_inv("Zealous Badge")
        await cmd.sleep(300)

    if cmd.is_in_inventory("Zealous Badge", target_qty):
        log_info(f"Zealous Badge x{target_qty} already satisfied.")
        return

    cmd.add_drop(["Zealous Badge", "Immutable Dedication", "Paladin Armor Scraps"])
    solo_class = cmd.get_solo_class()
    farm_class = cmd.get_farm_class()

    while cmd.is_still_connected() and not cmd.is_in_inventory("Zealous Badge", target_qty):
        log_info(f"Farming Zealous Badge (Target: {target_qty})...")
        await cmd.ensure_accept_quest(7616)

        # 1. Immutable Dedication x7 from Kalron the Cryptborg (Solo class)
        if solo_class:
            await cmd.equip_item(solo_class)
        await hunt_item(
            cmd=cmd,
            item_name="Immutable Dedication",
            item_qty=7,
            map_name="techdungeon",
            monster_name="Kalron the Cryptborg",
            is_temp=True,
            farming_logger=False
        )

        # 2. Paladin Armor Scraps x30 from DoomBorg Guard (Farm class)
        if farm_class:
            await cmd.equip_item(farm_class)
        await hunt_item(
            cmd=cmd,
            item_name="Paladin Armor Scraps",
            item_qty=30,
            map_name="techdungeon",
            monster_name="DoomBorg Guard",
            is_temp=True,
            farming_logger=False
        )

        await cmd.ensure_turn_in_quest(7616)
        await cmd.sleep(500)

    log_success(f"Zealous Badge x{target_qty} obtained!")


# =========================================================================
# Items 4 & 5: Unicorn Essence x5 and Gem Power x5 (/undergroundlabb)
# =========================================================================
async def farm_boss_materials(cmd: Command):
    """Farm Unicorn Essence x5 and Gem Power x5 from /undergroundlabb."""
    for item in ["Unicorn Essence", "Gem Power"]:
        if cmd.is_in_bank(item):
            await cmd.bank_to_inv(item)
            await cmd.sleep(300)

    cmd.add_drop(["Unicorn Essence", "Gem Power"])
    solo_class = cmd.get_solo_class()
    if solo_class:
        await cmd.equip_item(solo_class)

    if not cmd.is_in_inventory("Unicorn Essence", 5):
        log_info("Farming Unicorn Essence x5 from Ultra BrutalCorn at /undergroundlabb...")
        await hunt_item(
            cmd=cmd,
            item_name="Unicorn Essence",
            item_qty=5,
            map_name="undergroundlabb",
            monster_name="Ultra BrutalCorn",
            is_temp=False,
            farming_logger=True
        )

    if not cmd.is_in_inventory("Gem Power", 5):
        log_info("Farming Gem Power x5 from Ultra Battle Gem at /undergroundlabb...")
        await hunt_item(
            cmd=cmd,
            item_name="Gem Power",
            item_qty=5,
            map_name="undergroundlabb",
            monster_name="Ultra Battle Gem",
            is_temp=False,
            farming_logger=True
        )

    log_success("Unicorn Essence and Gem Power farming complete!")


# =========================================================================
# Turn in: Quest 7650 (Forging a Friendship) -> Pink Blade of Destruction
# =========================================================================
async def complete_forging_a_friendship(cmd: Command):
    """Accept Quest 7650, turn in, and choose Pink Blade of Destruction (item id: 55884)."""
    quest_id = 7650
    log_info("=== [Quest 7650] Forging a Friendship ===")
    cmd.add_drop([PBOD_ITEM_NAME])

    if cmd.is_in_inventory_or_bank(PBOD_ITEM_NAME):
        if cmd.is_in_bank(PBOD_ITEM_NAME):
            await cmd.bank_to_inv(PBOD_ITEM_NAME)
        log_success(f"'{PBOD_ITEM_NAME}' is already in inventory!")
        return

    if cmd.is_not_in_map("techfortress"):
        await cmd.join_map("techfortress")
        await cmd.sleep(1000)

    await cmd.ensure_accept_quest(quest_id)

    log_info(f"Turning in Quest 7650 for '{PBOD_ITEM_NAME}' (Reward ID: {PBOD_ITEM_ID})...")
    await cmd.ensure_turn_in_quest(quest_id, item_id=PBOD_ITEM_ID)

    for _ in range(15):
        if cmd.is_in_inventory(PBOD_ITEM_NAME):
            break
        await cmd.sleep(1000)

    if cmd.is_in_inventory(PBOD_ITEM_NAME):
        log_success(f"Successfully obtained '{PBOD_ITEM_NAME}'!")
    else:
        log_warning(f"Turned in Quest 7650. Please check your inventory for '{PBOD_ITEM_NAME}'.")


# =========================================================================
# Main Entry Point
# =========================================================================
async def main(cmd: Command):
    log_info("Starting Pink Blade of Destruction farm bot...")

    # Whitelist all required drops
    cmd.add_drop(PBOD_DROPS)

    # Check bank and transfer if found
    await check_and_transfer_bank(cmd, PBOD_DROPS)

    # Check if target item is already owned
    if cmd.is_in_inventory(PBOD_ITEM_NAME):
        log_success(f"'{PBOD_ITEM_NAME}' is already in inventory! Nothing to do.")
        return

    # Step 1: Ensure Doomwood Part 3 is completed
    log_info("Checking Doomwood Part 3 story prerequisites...")
    await complete_doomwood_part_3(cmd)

    # Step 2: Ensure Quest 7650 is accepted
    await cmd.ensure_accept_quest(7650)

    # Step 3: Farm Fuchsia Dye x50
    await farm_fuchsia_dye(cmd, target_qty=50)

    # Step 4: Farm Spirit Orb x500
    await farm_spirit_orbs(cmd, target_qty=500)

    # Step 5: Farm Zealous Badge x5
    await farm_zealous_badges(cmd, target_qty=5)

    # Step 6: Farm Unicorn Essence x5 and Gem Power x5
    await farm_boss_materials(cmd)

    # Step 7: Turn in Quest 7650 for Pink Blade of Destruction
    await complete_forging_a_friendship(cmd)

    if cmd.is_in_inventory(PBOD_ITEM_NAME):
        log_success("Pink Blade of Destruction bot completed successfully!")
    else:
        log_warning("Bot finished execution. Please verify your inventory.")


if __name__ == "__main__":
    username = input("Username: ")
    password = input("Password: ")
    server = input("Server: ")

    b = Bot(
        roomNumber=9099,
        itemsDropWhiteList=PBOD_DROPS,
        showLog=True,
        showDebug=False,
        showChat=True,
        isScriptable=True,
        autoRelogin=True,
        muteSpamWarning=True
    )
    b.set_login_info(username, password, server)
    asyncio.run(b.start_bot(main))
