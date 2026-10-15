import asyncio
from datetime import datetime
from colorama import Fore
from core.bot import Bot
from core.command import Command
from templates.hunt import hunt_item, kill_quest

GBOF_ITEM_NAME = "Golden Blade of Fate"

GBOF_DROPS = [
    "Golden Blade of Fate",
    "Blade Fragments",
    "Big Gold Coin",
    "A Feather",
    "Armor Fragment",
    "White Scales",
    "Necrotic Shard",
    "Purification Dust",
    "Dark Spirit",
]


def log_info(msg: str):
    print(Fore.CYAN + f"[{datetime.now().strftime('%H:%M:%S')}][GBoF] " + Fore.WHITE + msg + Fore.RESET)


def log_success(msg: str):
    print(Fore.GREEN + f"[{datetime.now().strftime('%H:%M:%S')}][GBoF] " + msg + Fore.RESET)


def log_warning(msg: str):
    print(Fore.YELLOW + f"[{datetime.now().strftime('%H:%M:%S')}][GBoF] " + msg + Fore.RESET)


def log_error(msg: str):
    print(Fore.RED + f"[{datetime.now().strftime('%H:%M:%S')}][GBoF] " + msg + Fore.RESET)


async def check_and_transfer_bank(cmd: Command, items: list[str]):
    """Check items in bank and move them to inventory if found."""
    for item in items:
        if cmd.is_in_bank(item):
            log_info(f"Moving '{item}' from Bank to Inventory...")
            await cmd.bank_to_inv(item)
            await cmd.sleep(300)


# =========================================================================
# Quest 1: The Lost Teacher (5669)
# =========================================================================
async def quest_1_the_lost_teacher(cmd: Command, check_green: bool = False):
    quest_id = 5669
    log_info("=== [Quest 1/11] The Lost Teacher (5669) ===")

    if check_green and not await cmd.is_green_quest(quest_id):
        log_info(f"Quest {quest_id} is not green. Skipping.")
        return

    farm_class = cmd.get_farm_class()
    if farm_class:
        await cmd.equip_item(farm_class)

    cmd.add_drop(["Blade Fragments"])
    log_info("Farming Blade Fragments from Horc Tutor Trainer at /tutor...")
    await kill_quest(cmd, quest_id, "tutor", "Horc Tutor Trainer")
    log_success("Quest 5669 Completed!")


# =========================================================================
# Quest 2: Big Gold Coins (5670)
# =========================================================================
async def quest_2_big_gold_coins(cmd: Command, check_green: bool = False):
    quest_id = 5670
    log_info("=== [Quest 2/11] Big Gold Coins (5670) ===")

    if check_green and not await cmd.is_green_quest(quest_id):
        log_info(f"Quest {quest_id} is not green. Skipping.")
        return

    farm_class = cmd.get_farm_class()
    if farm_class:
        await cmd.equip_item(farm_class)

    cmd.add_drop(["Big Gold Coin"])
    log_info("Farming Big Gold Coin from Piggy Drake at /prison...")
    await kill_quest(cmd, quest_id, "prison", "Piggy Drake")
    log_success("Quest 5670 Completed!")


# =========================================================================
# Quest 3: Light as a Feather (5671)
# =========================================================================
async def quest_3_light_as_a_feather(cmd: Command, check_green: bool = False):
    quest_id = 5671
    log_info("=== [Quest 3/11] Light as a Feather (5671) ===")

    if check_green and not await cmd.is_green_quest(quest_id):
        log_info(f"Quest {quest_id} is not green. Skipping.")
        return

    solo_class = cmd.get_solo_class()
    if solo_class:
        await cmd.equip_item(solo_class)

    cmd.add_drop(["A Feather"])
    log_info("Farming A Feather from Phedra at /lavarun...")
    await kill_quest(cmd, quest_id, "lavarun", "Phedra")
    log_success("Quest 5671 Completed!")


# =========================================================================
# Quest 4: Shard Shard Shard (5672)
# =========================================================================
async def quest_4_shard_shard_shard(cmd: Command, check_green: bool = False):
    quest_id = 5672
    log_info("=== [Quest 4/11] Shard Shard Shard (5672) ===")

    if check_green and not await cmd.is_green_quest(quest_id):
        log_info(f"Quest {quest_id} is not green. Skipping.")
        return

    solo_class = cmd.get_solo_class()
    if solo_class:
        await cmd.equip_item(solo_class)

    cmd.add_drop(["Armor Fragment"])
    log_info("Farming Armor Fragment from Chaorrupted Armor at /chaoscrypt...")
    await kill_quest(cmd, quest_id, "chaoscrypt", "Chaorrupted Armor")
    log_success("Quest 5672 Completed!")


# =========================================================================
# Quest 5: White Scales, Light Scales (5673)
# =========================================================================
async def quest_5_white_scales(cmd: Command, check_green: bool = False):
    quest_id = 5673
    log_info("=== [Quest 5/11] White Scales, Light Scales (5673) ===")

    if check_green and not await cmd.is_green_quest(quest_id):
        log_info(f"Quest {quest_id} is not green. Skipping.")
        return

    farm_class = cmd.get_farm_class()
    if farm_class:
        await cmd.equip_item(farm_class)

    cmd.add_drop(["White Scales"])
    log_info("Farming White Scales from Sketchy Frogzard at /j6...")
    await kill_quest(cmd, quest_id, "j6", "Sketchy Frogzard")
    log_success("Quest 5673 Completed!")


# =========================================================================
# Quest 6: The Stench of Defeat (5674)
# =========================================================================
async def quest_6_the_stench_of_defeat(cmd: Command, check_green: bool = False):
    quest_id = 5674
    log_info("=== [Quest 6/11] The Stench of Defeat (5674) ===")

    if check_green and not await cmd.is_green_quest(quest_id):
        log_info(f"Quest {quest_id} is not green. Skipping.")
        return

    await cmd.ensure_accept_quest(quest_id)
    if cmd.is_not_in_map("orcpath"):
        await cmd.join_map("orcpath")
        await cmd.sleep(1000)

    log_info("Collecting Strong Scent x3 (Map Item 5143) at /orcpath...")
    await cmd.get_map_item(5143, 3)
    await cmd.sleep(500)

    await cmd.ensure_turn_in_quest(quest_id)
    log_success("Quest 5674 Completed!")


# =========================================================================
# Quest 7: If you can't stand the heat... (5675)
# =========================================================================
async def quest_7_if_you_cant_stand_the_heat(cmd: Command, check_green: bool = False):
    quest_id = 5675
    log_info("=== [Quest 7/11] If you can't stand the heat... (5675) ===")

    if check_green and not await cmd.is_green_quest(quest_id):
        log_info(f"Quest {quest_id} is not green. Skipping.")
        return

    solo_class = cmd.get_solo_class()
    if solo_class:
        await cmd.equip_item(solo_class)

    cmd.add_drop(["Necrotic Shard"])
    log_info("Farming Necrotic Shard from Red Dragon at /lair...")
    await kill_quest(cmd, quest_id, "lair", "Red Dragon")
    log_success("Quest 5675 Completed!")


# =========================================================================
# Quest 8: The Depths of Despair (5676)
# =========================================================================
async def quest_8_the_depths_of_despair(cmd: Command, check_green: bool = False):
    quest_id = 5676
    log_info("=== [Quest 8/11] The Depths of Despair (5676) ===")

    if check_green and not await cmd.is_green_quest(quest_id):
        log_info(f"Quest {quest_id} is not green. Skipping.")
        return

    await cmd.ensure_accept_quest(quest_id)
    if cmd.is_not_in_map("well"):
        await cmd.join_map("well")
        await cmd.sleep(1000)

    log_info("Collecting Ancient Skull (Map Item 5144) at /well...")
    await cmd.get_map_item(5144, 1)
    await cmd.sleep(500)

    await cmd.ensure_turn_in_quest(quest_id)
    log_success("Quest 5676 Completed!")


# =========================================================================
# Quest 9: All Things Green and Small... (5677)
# =========================================================================
async def quest_9_all_things_green_and_small(cmd: Command, check_green: bool = False):
    quest_id = 5677
    log_info("=== [Quest 9/11] All Things Green and Small... (5677) ===")

    if check_green and not await cmd.is_green_quest(quest_id):
        log_info(f"Quest {quest_id} is not green. Skipping.")
        return

    farm_class = cmd.get_farm_class()
    if farm_class:
        await cmd.equip_item(farm_class)

    cmd.add_drop(["Purification Dust"])
    log_info("Farming Purification Dust from GreenRat at /cellar...")
    await kill_quest(cmd, quest_id, "cellar", "GreenRat")
    log_success("Quest 5677 Completed!")


# =========================================================================
# Quest 10: Doom... Or Redemption? (5678)
# =========================================================================
async def quest_10_doom_or_redemption(cmd: Command, check_green: bool = False):
    quest_id = 5678
    log_info("=== [Quest 10/11] Doom... Or Redemption? (5678) ===")

    if check_green and not await cmd.is_green_quest(quest_id):
        log_info(f"Quest {quest_id} is not green. Skipping.")
        return

    solo_class = cmd.get_solo_class()
    if solo_class:
        await cmd.equip_item(solo_class)

    await cmd.ensure_accept_quest(quest_id)
    cmd.add_drop(["Dark Spirit"])

    if not cmd.is_in_inventory("Dark Spirit"):
        log_info("Farming Dark Spirit from Dark Sepulchure at /sepulchure...")
        await hunt_item(
            cmd=cmd,
            item_name="Dark Spirit",
            item_qty=1,
            map_name="sepulchure",
            monster_name="Dark Sepulchure",
            farming_logger=True
        )

    await cmd.ensure_turn_in_quest(quest_id)
    log_success("Quest 5678 Completed!")


# =========================================================================
# Quest 11: The Mysterious Reward (5679) -> GOLDEN BLADE OF FATE!
# =========================================================================
async def quest_11_the_mysterious_reward(cmd: Command, check_green: bool = False):
    quest_id = 5679
    log_info("=== [Quest 11/11] The Mysterious Reward (5679) -> GOLDEN BLADE OF FATE! ===")

    if cmd.is_in_inventory_or_bank(GBOF_ITEM_NAME):
        await check_and_transfer_bank(cmd, [GBOF_ITEM_NAME])
        log_success(f"Item '{GBOF_ITEM_NAME}' is already owned in inventory!")
        return

    if check_green and not await cmd.is_green_quest(quest_id):
        log_info(f"Quest {quest_id} is not green. Skipping.")
        return

    cmd.add_drop([GBOF_ITEM_NAME])
    await cmd.ensure_accept_quest(quest_id)

    if cmd.is_not_in_map("yulgar"):
        await cmd.join_map("yulgar")
        await cmd.sleep(1000)

    log_info("Interacting with Mysterious Stranger (Map Item 5145) at /yulgar...")
    await cmd.get_map_item(5145, 1)
    await cmd.sleep(500)

    await cmd.ensure_turn_in_quest(quest_id)
    await cmd.sleep(1500)

    if cmd.is_in_inventory(GBOF_ITEM_NAME):
        print(Fore.GREEN + "\n========================================================")
        print("  CONGRATULATIONS! ITEM UNLOCKED: GOLDEN BLADE OF FATE!")
        print("========================================================\n" + Fore.RESET)
    else:
        log_warning("Quest 5679 completed. Please verify your inventory for Golden Blade of Fate.")


GBOF_QUESTS = [
    (5669, "The Lost Teacher", quest_1_the_lost_teacher),
    (5670, "Big Gold Coins", quest_2_big_gold_coins),
    (5671, "Light as a Feather", quest_3_light_as_a_feather),
    (5672, "Shard Shard Shard", quest_4_shard_shard_shard),
    (5673, "White Scales, Light Scales", quest_5_white_scales),
    (5674, "The Stench of Defeat", quest_6_the_stench_of_defeat),
    (5675, "If you can't stand the heat...", quest_7_if_you_cant_stand_the_heat),
    (5676, "The Depths of Despair", quest_8_the_depths_of_despair),
    (5677, "All Things Green and Small...", quest_9_all_things_green_and_small),
    (5678, "Doom... Or Redemption?", quest_10_doom_or_redemption),
    (5679, "The Mysterious Reward", quest_11_the_mysterious_reward),
]


async def find_active_gbof_quest_index(cmd: Command) -> int | None:
    """Check quests from LARGEST ID (5679) down to SMALLEST (5669).

    Searching backwards from the largest ID finds the latest active green quest
    in the linear progression chain.
    """
    for index in range(len(GBOF_QUESTS) - 1, -1, -1):
        qid, qname, _ = GBOF_QUESTS[index]
        log_info(f"Checking status of Quest {qid} ({qname})...")
        if await cmd.is_green_quest(qid):
            log_success(f"Latest green quest found: [{index + 1}/11] {qname} (ID: {qid})")
            return index
        await cmd.sleep(200)
    return None


# =========================================================================
# MAIN ENTRYPOINT
# =========================================================================
async def main(cmd: Command):
    log_info("Starting Scriptable Bot: Golden Blade of Fate...")

    # Check if already owned
    if cmd.is_in_inventory_or_bank(GBOF_ITEM_NAME):
        await check_and_transfer_bank(cmd, [GBOF_ITEM_NAME])
        log_success(f"Item '{GBOF_ITEM_NAME}' is already owned in inventory!")
        return

    # Whitelist all drops
    cmd.add_drop(GBOF_DROPS)

    # Detect the latest green quest to determine the starting point
    log_info("Detecting active green quest...")
    start_index = await find_active_gbof_quest_index(cmd)

    if start_index is None:
        log_warning("No green quest found on initial check. Retrying in 1s...")
        await cmd.sleep(1000)
        start_index = await find_active_gbof_quest_index(cmd)

    if start_index is None:
        if cmd.is_in_inventory_or_bank(GBOF_ITEM_NAME):
            await check_and_transfer_bank(cmd, [GBOF_ITEM_NAME])
            log_success(f"Item '{GBOF_ITEM_NAME}' is already owned in inventory!")
            return
        log_error("Could not find any active (green) quest for Golden Blade of Fate.")
        return

    log_success(
        f"Bot will start from Quest {start_index + 1}/11: "
        f"{GBOF_QUESTS[start_index][1]} (ID: {GBOF_QUESTS[start_index][0]})"
    )

    # Run quests sequentially starting from the latest green quest
    for index in range(start_index, len(GBOF_QUESTS)):
        qid, qname, quest_func = GBOF_QUESTS[index]

        # For subsequent quests after the start quest, verify green status
        if index > start_index:
            log_info(f"Verifying status for Quest {qid} ({qname})...")
            if not await cmd.is_green_quest(qid):
                log_error(f"Quest {qid} ({qname}) is not green after previous quest. Stopping bot.")
                return

        log_info(f"\n========================================================")
        log_info(f"  Running [{index + 1}/11] {qname} (ID: {qid})")
        log_info(f"========================================================")
        await quest_func(cmd)
        await cmd.sleep(1000)

    if cmd.is_in_inventory(GBOF_ITEM_NAME):
        log_success("Golden Blade of Fate bot completed successfully!")
    else:
        log_warning("Bot has executed all steps. Please check your inventory for Golden Blade of Fate.")


if __name__ == "__main__":
    username = input("Username: ")
    password = input("Password: ")
    server = input("Server: ")

    b = Bot(
        roomNumber=9099,
        itemsDropWhiteList=GBOF_DROPS,
        showLog=True,
        showDebug=False,
        showChat=True,
        isScriptable=True,
        autoRelogin=True,
        muteSpamWarning=True
    )
    b.set_login_info(username, password, server)
    asyncio.run(b.start_bot(main))
