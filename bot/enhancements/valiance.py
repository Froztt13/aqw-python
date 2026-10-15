import asyncio
from datetime import datetime
from colorama import Fore
from core.bot import Bot
from core.command import Command
from templates.hunt import hunt_item, kill_quest

VALIANCE_QUEST_ID = 8741

# 6 Item utama yang dibutuhkan untuk turn in quest Hero's Valiance (Quest 8741)
REQUIRED_ITEMS = [
    "Fire Champion's Armor",
    "Dragon of Time",
    "Drakath the Eternal",
    "Eternity Blade",
    "ArchPaladin Armor",
    "Gravelyn's DoomFire Token"
]

ALL_DROPS = [
    # Required final items
    "Fire Champion's Armor",
    "Dragon of Time",
    "Drakath the Eternal",
    "Eternity Blade",
    "ArchPaladin Armor",
    "Gravelyn's DoomFire Token",

    # Gravelyn's DoomFire Token mats
    "Empowered Essence",
    "Gravelyn's Blessing",
    "Painful Memory Bubble",
    "Burning Passion Flame",
    "Father's Sorrowful Tear",
    "Essence of the Doomlord",
    "Doomed Memories",
    "Sepulchuroth's Undying Flame",
    "Father's Anger",

    # Fire Champion's Armor mats
    "Flame-Forged Metal",
    "Void Scale",
    "Polished DragonSlayer",
    "Warfury Emblem",
    "Enchanted Scale",
    "Dragon Scale",

    # Blacksmithing
    "Gold Voucher 500k",
    "Hydra Scale Piece",
    "Creature Shard",
    "Monster Trophy",

    # Drakath the Eternal mats
    "Drakath Armor",
    "Drakath's Sword",
    "Reality Shard",
    "Star Fragment",
    "Death's Oversight",
    "Crystallized Chaos"
]


def log_info(msg: str):
    print(Fore.CYAN + f"[{datetime.now().strftime('%H:%M:%S')}][Valiance] " + Fore.WHITE + msg + Fore.RESET)


def log_success(msg: str):
    print(Fore.GREEN + f"[{datetime.now().strftime('%H:%M:%S')}][Valiance] " + msg + Fore.RESET)


def log_warning(msg: str):
    print(Fore.YELLOW + f"[{datetime.now().strftime('%H:%M:%S')}][Valiance] " + msg + Fore.RESET)


def log_error(msg: str):
    print(Fore.RED + f"[{datetime.now().strftime('%H:%M:%S')}][Valiance] " + msg + Fore.RESET)


async def check_and_transfer_bank(cmd: Command, items: list[str]):
    """Mengecek apakah item berada di bank. Jika ya, pindahkan ke inventory."""
    for item in items:
        if cmd.is_in_bank(item):
            log_info(f"Mengambil '{item}' dari Bank ke Inventory...")
            await cmd.bank_to_inv(item)
            await cmd.sleep(400)


async def ensure_blacksmithing_rep(cmd: Command, target_rank: int = 10, use_gold: bool = True):
    """
    Farms Blacksmithing Reputation hingga target_rank (default 10).
    Sesuai Farm.BlacksmithingREP di C#:
    - Jika use_gold=True: Menggunakan Quest 8737 di /alchemyacademy membeli 'Gold Voucher 500k' (Shop 2036).
    - Jika use_gold=False: Menggunakan Quest 8736 di /hydrachallenge, /maul, dan /towerofdoom.
    """
    current_rank = cmd.get_player().getFactionRank("Blacksmithing")
    log_info(f"Status Blacksmithing Reputation: Rank {current_rank}/{target_rank}")

    if current_rank >= target_rank:
        log_success(f"Blacksmithing Reputation sudah Rank {current_rank}.")
        return

    # Equip farm class
    farm_class = cmd.get_farm_class()
    if farm_class:
        await cmd.equip_item(farm_class)

    while cmd.is_still_connected() and cmd.get_player().getFactionRank("Blacksmithing") < target_rank:
        player_gold = cmd.get_player().GOLD

        if use_gold and player_gold >= 500000:
            log_info(f"Farming Blacksmithing REP menggunakan metode Gold Voucher 500k (Quest 8737)... (Gold: {player_gold:,})")
            if cmd.is_not_in_map("alchemyacademy"):
                await cmd.join_map("alchemyacademy")
                await cmd.sleep(1000)

            await cmd.ensure_accept_quest(8737)
            if not cmd.is_in_inventory("Gold Voucher 500k"):
                await cmd.ensure_load_shop(2036)
                await cmd.buy_item(2036, "Gold Voucher 500k", 1)
                await cmd.sleep(500)

            await cmd.ensure_turn_in_quest(8737)
            await cmd.sleep(500)
        else:
            log_info(f"Farming Blacksmithing REP menggunakan metode Monster (Quest 8736)...")
            await cmd.ensure_accept_quest(8736)

            solo_class = cmd.get_solo_class()
            if solo_class:
                await cmd.equip_item(solo_class)

            # Hydra Scale Piece x75
            if not cmd.is_in_inventory("Hydra Scale Piece", 75):
                await hunt_item(
                    cmd=cmd,
                    item_name="Hydra Scale Piece",
                    item_qty=75,
                    map_name="hydrachallenge",
                    monster_name="Hydra Head 25",
                    farming_logger=True
                )

            # Creature Shard x1
            if not cmd.is_in_inventory("Creature Shard", 1):
                await hunt_item(
                    cmd=cmd,
                    item_name="Creature Shard",
                    item_qty=1,
                    map_name="maul",
                    monster_name="Creature Creation",
                    farming_logger=True
                )

            # Monster Trophy x15
            if not cmd.is_in_inventory("Monster Trophy", 15):
                await hunt_item(
                    cmd=cmd,
                    item_name="Monster Trophy",
                    item_qty=15,
                    map_name="towerofdoom",
                    monster_name="Dread Klunk",
                    farming_logger=True
                )

            await cmd.ensure_turn_in_quest(8736)
            await cmd.sleep(500)

    log_success("Blacksmithing Reputation selesai (Rank 10)!")


async def get_eternity_blade(cmd: Command):
    """
    Farms Eternity Blade (ID 23689).
    Sesuai UnlockForgeEnhancements.cs:
    - Quest 3485 (The Final Challenge)
    - Monster Slugbutter di /towerofdoom10
    """
    item_name = "Eternity Blade"

    if cmd.is_in_bank(item_name):
        await cmd.bank_to_inv(item_name)
        return

    if cmd.is_in_inventory(item_name):
        log_success(f"'{item_name}' sudah ada di inventory.")
        return

    log_info(f"Farming '{item_name}' dari Slugbutter di /towerofdoom10 (Quest 3485)...")
    cmd.add_drop(item_name)

    solo_class = cmd.get_solo_class()
    if solo_class:
        await cmd.equip_item(solo_class)

    await kill_quest(
        cmd=cmd,
        quest_id=3485,
        map_name="towerofdoom10",
        monster_name="Slugbutter"
    )

    if cmd.is_in_inventory(item_name):
        log_success(f"Berhasil mendapatkan '{item_name}'!")
    else:
        log_warning(f"Selesai Quest 3485, mengecek pickup '{item_name}'...")
        await cmd.sleep(1000)


async def get_gravelyns_doomfire_token(cmd: Command):
    """
    Farms Gravelyn's DoomFire Token (Quest 5461).
    Sesuai SepulchuresOriginalHelm.GravelynsDoomFireToken():
    - Gravelyn's Blessing (Quest 5455/5456/5457)
    - Painful Memory Bubble (Quest 5458)
    - Burning Passion Flame (Quest 5459)
    - Father's Sorrowful Tear (Quest 5460)
    - Empowered Essence x13 (/shadowrealmpast)
    """
    item_name = "Gravelyn's DoomFire Token"

    if cmd.is_in_bank(item_name):
        await cmd.bank_to_inv(item_name)
        return

    if cmd.is_in_inventory(item_name):
        log_success(f"'{item_name}' sudah ada di inventory.")
        return

    log_info(f"Farming '{item_name}' (Quest 5461)...")

    doomfire_sub_items = [
        "Gravelyn's Blessing",
        "Painful Memory Bubble",
        "Burning Passion Flame",
        "Father's Sorrowful Tear",
        "Empowered Essence",
        "Essence of the Doomlord",
        "Doomed Memories",
        "Sepulchuroth's Undying Flame",
        "Father's Anger",
        item_name
    ]
    await check_and_transfer_bank(cmd, doomfire_sub_items)
    cmd.add_drop(doomfire_sub_items)

    solo_class = cmd.get_solo_class()
    farm_class = cmd.get_farm_class()

    while cmd.is_still_connected() and not cmd.is_in_inventory(item_name):
        await cmd.ensure_accept_quest(5461)

        # 1. Gravelyn's Blessing
        if not cmd.is_in_inventory("Gravelyn's Blessing"):
            if cmd.is_in_inventory_or_bank("Necrotic Sword of Doom"):
                log_info("Menyelesaikan Gravelyn's Blessing via NSoD (Quest 5455)...")
                await check_and_transfer_bank(cmd, ["Necrotic Sword of Doom"])
                await cmd.ensure_accept_quest(5455)
                await cmd.ensure_turn_in_quest(5455)
            elif cmd.is_in_inventory_or_bank("Sepulchure's DoomKnight Armor"):
                log_info("Menyelesaikan Gravelyn's Blessing via SDKA (Quest 5456)...")
                await check_and_transfer_bank(cmd, ["Sepulchure's DoomKnight Armor"])
                await cmd.ensure_accept_quest(5456)
                await cmd.ensure_turn_in_quest(5456)
            else:
                log_info("Farming Gravelyn's Blessing dari Essence of the Doomlord (Quest 5457)...")
                if solo_class:
                    await cmd.equip_item(solo_class)
                await kill_quest(
                    cmd=cmd,
                    quest_id=5457,
                    map_name="necrodungeon",
                    monster_name="Essence of the Doomlord"
                )

        # 2. Painful Memory Bubble (Quest 5458)
        if not cmd.is_in_inventory("Painful Memory Bubble"):
            log_info("Farming Painful Memory Bubble (Quest 5458) di /swordhavenfalls...")
            if solo_class:
                await cmd.equip_item(solo_class)
            await cmd.ensure_accept_quest(5458)
            await hunt_item(
                cmd=cmd,
                item_name="Doomed Memories",
                item_qty=1,
                map_name="swordhavenfalls",
                cell="r10",
                pad="Left",
                monster_name="*",
                is_temp=True,
                farming_logger=True
            )
            await cmd.ensure_turn_in_quest(5458)

        # 3. Burning Passion Flame (Quest 5459)
        if not cmd.is_in_inventory("Burning Passion Flame"):
            log_info("Farming Burning Passion Flame (Quest 5459) di /shadowstrike...")
            if solo_class:
                await cmd.equip_item(solo_class)
            await cmd.ensure_accept_quest(5459)
            await hunt_item(
                cmd=cmd,
                item_name="Sepulchuroth's Undying Flame",
                item_qty=1,
                map_name="shadowstrike",
                monster_name="Sepulchuroth",
                is_temp=True,
                farming_logger=True
            )
            await cmd.ensure_turn_in_quest(5459)

        # 4. Father's Sorrowful Tear (Quest 5460)
        if not cmd.is_in_inventory("Father's Sorrowful Tear"):
            log_info("Farming Father's Sorrowful Tear (Quest 5460) di /shadowfall...")
            if solo_class:
                await cmd.equip_item(solo_class)
            await cmd.ensure_accept_quest(5460)
            await hunt_item(
                cmd=cmd,
                item_name="Father's Anger",
                item_qty=1,
                map_name="shadowfall",
                monster_name="Shadow of the Past",
                is_temp=True,
                farming_logger=True
            )
            await cmd.ensure_turn_in_quest(5460)

        # 5. Empowered Essence x13
        if not cmd.is_in_inventory("Empowered Essence", 13):
            log_info("Farming Empowered Essence x13 di /shadowrealmpast...")
            if farm_class:
                await cmd.equip_item(farm_class)
            await hunt_item(
                cmd=cmd,
                item_name="Empowered Essence",
                item_qty=13,
                map_name="shadowrealmpast",
                cell="Enter",
                pad="Spawn",
                monster_name="*",
                farming_logger=True
            )

        # Turn in 5461
        await cmd.ensure_turn_in_quest(5461)
        await cmd.sleep(1000)

    if cmd.is_in_inventory(item_name):
        log_success(f"Berhasil mendapatkan '{item_name}'!")


async def get_archpaladin_armor(cmd: Command):
    """
    Membeli ArchPaladin Armor dari darkthronehub (Shop 1303).
    Sesuai UnlockForgeEnhancements.cs:
    - Adv.BuyItem("darkthronehub", 1303, "ArchPaladin Armor")
    - Memerlukan Quest 5467 (Sacred Magic: Eden) dan 100,000 Gold.
    """
    item_name = "ArchPaladin Armor"

    if cmd.is_in_bank(item_name):
        await cmd.bank_to_inv(item_name)
        return

    if cmd.is_in_inventory(item_name):
        log_success(f"'{item_name}' sudah ada di inventory.")
        return

    log_info(f"Mengecek pembelian '{item_name}' di /darkthronehub...")

    # Cek apakah quest 5467 sudah pernah diselesaikan
    is_quest_completed = await cmd.is_completed_before(5467)
    if is_quest_completed or cmd.is_in_inventory_or_bank("ArchPaladin"):
        if cmd.is_not_in_map("darkthronehub"):
            await cmd.join_map("darkthronehub")
            await cmd.sleep(1000)

        log_info(f"Membeli '{item_name}' dari Shop 1303 (harga 100,000 gold)...")
        await cmd.ensure_load_shop(1303)
        await cmd.buy_item(1303, item_name, 1)
        await cmd.sleep(1000)

        if cmd.is_in_inventory(item_name):
            log_success(f"Berhasil membeli '{item_name}'!")
        else:
            log_warning(f"Gagal membeli '{item_name}', pastikan gold mencukupi (100k) dan quest 5467 telah selesai.")
    else:
        log_warning(f"Quest 5467 ('Sacred Magic: Eden') belum selesai. '{item_name}' belum bisa dibeli dari Shop 1303.")


async def farm_flame_forged_metal(cmd: Command, qty: int = 10):
    """Farms Flame-Forged Metal (Quest 6975) dari Frozen Pyromancer di /underworld."""
    item_name = "Flame-Forged Metal"
    if cmd.is_in_bank(item_name):
        await cmd.bank_to_inv(item_name)

    if cmd.is_in_inventory(item_name, qty, ">="):
        return

    log_info(f"Farming {item_name} x{qty} di /underworld (Quest 6975)...")
    cmd.add_drop([item_name, "Stolen Flame"])

    solo_class = cmd.get_solo_class()
    if solo_class:
        await cmd.equip_item(solo_class)

    while cmd.is_still_connected() and not cmd.is_in_inventory(item_name, qty, ">="):
        await cmd.ensure_accept_quest(6975)
        await hunt_item(
            cmd=cmd,
            item_name="Stolen Flame",
            item_qty=1,
            map_name="underworld",
            monster_name="Frozen Pyromancer",
            is_temp=True,
            farming_logger=True
        )
        await cmd.ensure_turn_in_quest(6975)
        await cmd.sleep(500)


async def farm_void_scale(cmd: Command, qty: int = 13):
    """Farms Void Scale x13 dari Archfiend Dragonlord di /underlair."""
    item_name = "Void Scale"
    if cmd.is_in_bank(item_name):
        await cmd.bank_to_inv(item_name)

    if cmd.is_in_inventory(item_name, qty, ">="):
        return

    log_info(f"Farming {item_name} x{qty} di /underlair (Archfiend Dragonlord)...")
    cmd.add_drop(item_name)

    solo_class = cmd.get_solo_class()
    if solo_class:
        await cmd.equip_item(solo_class)

    await hunt_item(
        cmd=cmd,
        item_name=item_name,
        item_qty=qty,
        map_name="underlair",
        monster_name="Archfiend Dragonlord",
        farming_logger=True
    )


async def check_fire_champions_armor(cmd: Command) -> bool:
    """
    Mengecek ketersediaan Fire Champion's Armor.
    Jika belum punya, dapat mem-farm bahan Flame-Forged Metal dan Void Scale,
    serta mencoba membelinya di /wartraining (Shop 2035) jika bahan lain lengkap.
    """
    item_name = "Fire Champion's Armor"

    if cmd.is_in_bank(item_name):
        await cmd.bank_to_inv(item_name)
        return True

    if cmd.is_in_inventory(item_name):
        log_success(f"'{item_name}' sudah ada di inventory.")
        return True

    log_info(f"Mengecek material untuk '{item_name}'...")
    mats = [
        "Polished DragonSlayer",
        "Enchanted Scale",
        "Warfury Emblem",
        "Flame-Forged Metal",
        "Void Scale"
    ]
    await check_and_transfer_bank(cmd, mats)
    cmd.add_drop(mats)

    # Farm Flame-Forged Metal x10 & Void Scale x13 jika belum ada
    await farm_flame_forged_metal(cmd, 10)
    await farm_void_scale(cmd, 13)

    # Cek apakah bisa dibeli di wartraining shop 2035
    has_pds = cmd.is_in_inventory("Polished DragonSlayer")
    has_scale = cmd.is_in_inventory("Enchanted Scale", 125, ">=")
    has_wfe = cmd.is_in_inventory("Warfury Emblem", 60, ">=")
    has_ffm = cmd.is_in_inventory("Flame-Forged Metal", 10, ">=")
    has_vs = cmd.is_in_inventory("Void Scale", 13, ">=")

    if has_pds and has_scale and has_wfe and has_ffm and has_vs:
        log_info(f"Semua material '{item_name}' lengkap! Membeli di /wartraining (Shop 2035)...")
        if cmd.is_not_in_map("wartraining"):
            await cmd.join_map("wartraining")
            await cmd.sleep(1000)
        await cmd.ensure_load_shop(2035)
        await cmd.buy_item(2035, item_name, 1)
        await cmd.sleep(1000)
        return cmd.is_in_inventory(item_name)
    else:
        log_warning(
            f"'{item_name}' belum dimiliki. Status bahan:\n"
            f" - Polished DragonSlayer: {'OK' if has_pds else 'Kurang'}\n"
            f" - Enchanted Scale: {cmd.get_quant_item('Enchanted Scale')}/125\n"
            f" - Warfury Emblem: {cmd.get_quant_item('Warfury Emblem')}/60\n"
            f" - Flame-Forged Metal: {cmd.get_quant_item('Flame-Forged Metal')}/10\n"
            f" - Void Scale: {cmd.get_quant_item('Void Scale')}/13"
        )
        return False


async def check_dragon_of_time(cmd: Command) -> bool:
    """Mengecek keberadaan class Dragon of Time."""
    item_name = "Dragon of Time"
    if cmd.is_in_bank(item_name):
        await cmd.bank_to_inv(item_name)
        return True
    if cmd.is_in_inventory(item_name):
        log_success(f"'{item_name}' siap di inventory.")
        return True

    log_warning(f"Class '{item_name}' tidak ditemukan di inventory atau bank! Selesaikan quest Dragon of Time terlebih dahulu.")
    return False


async def check_drakath_the_eternal(cmd: Command) -> bool:
    """
    Mengecek keberadaan armor Drakath the Eternal.
    Sesuai UnlockForgeEnhancements.cs:
    - Jika tidak ada Drakath the Eternal, cek Drakath Armor dan Dage's Scroll Fragment.
    - Jika Drakath Armor ada, quest 8457 (Drakath the Eternal) dapat diselesaikan.
    """
    item_name = "Drakath the Eternal"
    if cmd.is_in_bank(item_name):
        await cmd.bank_to_inv(item_name)
        return True
    if cmd.is_in_inventory(item_name):
        log_success(f"'{item_name}' siap di inventory.")
        return True

    log_info(f"Mengecek Drakath Armor untuk membuat '{item_name}'...")
    if cmd.is_in_bank("Drakath Armor"):
        await cmd.bank_to_inv("Drakath Armor")

    if not cmd.is_in_inventory("Drakath Armor"):
        dage_scrolls = cmd.get_quant_item("Dage's Scroll Fragment")
        log_warning(
            f"Tidak dapat menyelesaikan Hero's Valiance: 'Drakath Armor' belum ada.\n"
            f" - Dage's Scroll Fragment: {dage_scrolls}/13 (Daily Quest)\n"
            f" Silakan selesaikan daily Dage's Scroll Fragment terlebih dahulu."
        )
        return False

    # Jika Drakath Armor ada, cek quest 8457
    log_info("Drakath Armor ditemukan! Mencoba menyelesaikan Quest 8457 ('Drakath the Eternal')...")
    cmd.add_drop([item_name, "Drakath's Sword", "Reality Shard", "Death's Oversight", "Crystallized Chaos", "Star Fragment"])

    solo_class = cmd.get_solo_class()
    farm_class = cmd.get_farm_class()

    await cmd.ensure_accept_quest(8457)

    # Drakath's Sword
    if not cmd.is_in_inventory("Drakath's Sword"):
        if solo_class:
            await cmd.equip_item(solo_class)
        await hunt_item(
            cmd=cmd,
            item_name="Drakath's Sword",
            item_qty=1,
            map_name="ultradrakath",
            monster_name="Champion of Chaos",
            farming_logger=True
        )

    # Crystallized Chaos x800
    if not cmd.is_in_inventory("Crystallized Chaos", 800):
        if farm_class:
            await cmd.equip_item(farm_class)
        await hunt_item(
            cmd=cmd,
            item_name="Crystallized Chaos",
            item_qty=800,
            map_name="chaoslab",
            cell="r3",
            pad="Center",
            monster_name="Chaorrupted Moglin",
            farming_logger=True
        )

    # Death's Oversight x5
    if not cmd.is_in_inventory("Death's Oversight", 5):
        if solo_class:
            await cmd.equip_item(solo_class)
        await hunt_item(
            cmd=cmd,
            item_name="Death's Oversight",
            item_qty=5,
            map_name="shadowattack",
            cell="Boss",
            pad="Left",
            monster_name="Death",
            farming_logger=True
        )

    # Reality Shard x200 (Quest 8456)
    while cmd.is_still_connected() and not cmd.is_in_inventory("Reality Shard", 200, ">="):
        await cmd.ensure_accept_quest(8456)
        await hunt_item(
            cmd=cmd,
            item_name="Preserved Chaos Fairy Wing",
            item_qty=5,
            map_name="eternalchaos",
            monster_name="Chaos Time Fairy",
            is_temp=True,
            farming_logger=True
        )
        await cmd.ensure_turn_in_quest(8456)

    # Turn in quest 8457 jika syarat terpenuhi
    if cmd.can_turnin_quest(8457):
        await cmd.ensure_turn_in_quest(8457)
        await cmd.sleep(1000)

    return cmd.is_in_inventory(item_name)


async def check_lord_of_order(cmd: Command) -> bool:
    """Mengecek apakah quest akhir Lord of Order (Quest 7165) sudah selesai."""
    is_loo_done = await cmd.is_completed_before(7165) or cmd.is_in_inventory_or_bank("Lord of Order")
    if is_loo_done:
        log_success("Lord of Order (Quest 7165 / Class) terpenuhi.")
        return True
    else:
        log_warning("Quest 7165 ('The Final Challenge') untuk Lord of Order belum selesai. Selesaikan daily LoO terlebih dahulu.")
        return False


async def print_checklist(cmd: Command):
    """Menampilkan checklist status 6 item Valiance."""
    print(Fore.YELLOW + "\n============== STATUS ITEM VALIANCE ==============" + Fore.RESET)
    for it in REQUIRED_ITEMS:
        qty = cmd.get_quant_item(it)
        status = Fore.GREEN + "[ADA]" if qty > 0 else Fore.RED + "[TIDAK ADA]"
        print(f" {status} {Fore.WHITE}{it}{Fore.RESET}")
    print(Fore.YELLOW + "==================================================\n" + Fore.RESET)


async def main(cmd: Command):
    log_info("Memulai Scriptable Bot: Hero's Valiance Quest (Quest 8741)...")

    # 1. Cek apakah Hero's Valiance sudah pernah diselesaikan
    if await cmd.is_completed_before(VALIANCE_QUEST_ID):
        log_success("Quest 8741 (Hero's Valiance) SUDAH SELESAI sebelumnya! Enhancement sudah terbuka.")
        return

    # 2. Pindahkan semua item terkait dari Bank ke Inventory
    await check_and_transfer_bank(cmd, REQUIRED_ITEMS)
    cmd.add_drop(ALL_DROPS)

    # 3. Blacksmithing Reputation Rank 10
    await ensure_blacksmithing_rep(cmd, target_rank=10, use_gold=True)

    # 4. Eternity Blade
    await get_eternity_blade(cmd)

    # 5. Gravelyn's DoomFire Token
    await get_gravelyns_doomfire_token(cmd)

    # 6. ArchPaladin Armor
    await get_archpaladin_armor(cmd)

    # 7. Fire Champion's Armor
    await check_fire_champions_armor(cmd)

    # 8. Dragon of Time
    await check_dragon_of_time(cmd)

    # 9. Drakath the Eternal
    await check_drakath_the_eternal(cmd)

    # 10. Lord of Order Check
    await check_lord_of_order(cmd)

    # 11. Final Verification dan Turn-in Quest 8741
    await check_and_transfer_bank(cmd, REQUIRED_ITEMS)
    await print_checklist(cmd)

    all_ready = all(cmd.is_in_inventory(it) for it in REQUIRED_ITEMS)

    if all_ready:
        log_info("Semua persyaratan terpenuhi! Menerima dan menyelesaikan Quest 8741 (Hero's Valiance)...")
        if cmd.is_not_in_map("forge"):
            await cmd.join_map("forge")
            await cmd.sleep(1000)

        await cmd.ensure_accept_quest(VALIANCE_QUEST_ID)
        await cmd.sleep(500)
        await cmd.ensure_turn_in_quest(VALIANCE_QUEST_ID)
        await cmd.sleep(1000)

        if await cmd.is_completed_before(VALIANCE_QUEST_ID):
            print(Fore.GREEN + "\n========================================================")
            print("  CONGRATULATIONS! ENHANCEMENT UNLOCKED: HERO'S VALIANCE")
            print("========================================================\n" + Fore.RESET)
        else:
            log_warning("Quest 8741 telah dicoba di-turn in. Silakan periksa enhancement di /forge shop.")
    else:
        log_warning(
            "Belum dapat menyelesaikan Quest Hero's Valiance saat ini karena beberapa item prasyarat (seperti Dragon of Time atau Drakath the Eternal) belum lengkap.\n"
            "Item yang berhasil diperoleh tetap tersimpan di inventory Anda."
        )


if __name__ == "__main__":
    username = input("Username: ")
    password = input("Password: ")
    server = input("Server: ")

    b = Bot(
        roomNumber=1,
        itemsDropWhiteList=ALL_DROPS,
        showLog=True,
        showDebug=False,
        showChat=True,
        isScriptable=True,
        autoRelogin=True,
        muteSpamWarning=True
    )
    b.set_login_info(username, password, server)
    asyncio.run(b.start_bot(main))
