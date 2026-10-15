import asyncio
from datetime import datetime
from colorama import Fore
from core.bot import Bot
from core.command import Command
from templates.hunt import hunt_item, kill_quest
from core.task import FarmTask, do_farm_tasks

QUEST_DRAKATH_ARMOR = 3882  # Build Drakath's Armor
QUEST_DAILY_DAGES_SCROLL = 3596  # Daily: Dage's Scroll Fragment
QUEST_CHAOS_REP = 3594  # Embrace Your Chaos

REQUIRED_MATERIALS = [
    "Blade of Awe",
    "Unidentified 13",
    "Dage's Scroll Fragment",
    "Le Chocolat",
    "Treasure Chest",
    "Face of Chaos",
    "Blinding Light of Destiny"
]

ALL_DROPS = [
    "Drakath Armor",
    "Original Drakath Armor",
    "Get Your Original Drakath's Armor",
    "Blade of Awe",
    "Unidentified 13",
    "Dage's Scroll Fragment",
    "Le Chocolat",
    "Treasure Chest",
    "Face of Chaos",
    "Blinding Light of Destiny",
    # Sub-drops / mats
    "Mana Energy for Nulgath",
    "Charged Mana Energy for Nulgath",
    "Diamond of Nulgath",
    "Dark Crystal Shard",
    "Gem of Nulgath",
    "Tainted Gem",
    "Voucher of Nulgath",
    "Voucher of Nulgath (non-mem)"
]


def log_info(msg: str):
    print(Fore.CYAN + f"[{datetime.now().strftime('%H:%M:%S')}][DrakathArmor] " + Fore.WHITE + msg + Fore.RESET)


def log_success(msg: str):
    print(Fore.GREEN + f"[{datetime.now().strftime('%H:%M:%S')}][DrakathArmor] " + msg + Fore.RESET)


def log_warning(msg: str):
    print(Fore.YELLOW + f"[{datetime.now().strftime('%H:%M:%S')}][DrakathArmor] " + msg + Fore.RESET)


def log_error(msg: str):
    print(Fore.RED + f"[{datetime.now().strftime('%H:%M:%S')}][DrakathArmor] " + msg + Fore.RESET)


async def check_and_transfer_bank(cmd: Command, items: list[str]):
    """Mengecek item di bank dan memindahkannya ke inventory."""
    for item in items:
        if cmd.is_in_bank(item):
            log_info(f"Mengambil '{item}' dari Bank ke Inventory...")
            await cmd.bank_to_inv(item)
            await cmd.sleep(300)


async def ensure_chaos_rep(cmd: Command, target_rank: int = 10):
    """
    Farms Chaos Reputation hingga target_rank (default Rank 10).
    Menggunakan Quest 3594 ('Embrace Your Chaos') di /mountdoomskull cell b1.
    """
    current_rank = cmd.get_player().getFactionRank("Chaos")
    log_info(f"Status Chaos Reputation: Rank {current_rank}/{target_rank}")

    if current_rank >= target_rank:
        log_success("Chaos Reputation sudah Rank 10.")
        return

    farm_class = cmd.get_farm_class()
    if farm_class:
        await cmd.equip_item(farm_class)

    log_info("Farming Chaos Reputation di /mountdoomskull (Quest 3594)...")
    if cmd.is_not_in_map("mountdoomskull"):
        await cmd.join_map("mountdoomskull")
        await cmd.sleep(1000)

    while cmd.is_still_connected() and cmd.get_player().getFactionRank("Chaos") < target_rank:
        await cmd.ensure_accept_quest(QUEST_CHAOS_REP)
        await hunt_item(
            cmd=cmd,
            item_name="Chaos Power Increased",
            item_qty=6,
            map_name="mountdoomskull",
            cell="b1",
            pad="Left",
            monster_name="*",
            is_temp=True,
            farming_logger=True
        )
        await cmd.ensure_turn_in_quest(QUEST_CHAOS_REP)
        await cmd.sleep(400)

    log_success("Chaos Reputation berhasil mencapai Rank 10!")


async def do_daily_dages_scroll(cmd: Command):
    """
    Mengerjakan daily quest 3596 di /mountdoomskull untuk mendapatkan Dage's Scroll Fragment.
    """
    scroll_name = "Dage's Scroll Fragment"
    if cmd.is_in_bank(scroll_name):
        await cmd.bank_to_inv(scroll_name)

    current_qty = cmd.get_quant_item(scroll_name)
    log_info(f"Jumlah Dage's Scroll Fragment saat ini: {current_qty}/13")

    if current_qty >= 13:
        log_success("Dage's Scroll Fragment sudah lengkap (13/13).")
        return

    cmd.add_drop(scroll_name)
    farm_class = cmd.get_farm_class()
    if farm_class:
        await cmd.equip_item(farm_class)

    log_info("Mengecek Daily Quest 3596 ('Dage's Scroll Fragment') di /mountdoomskull...")
    if cmd.is_not_in_map("mountdoomskull"):
        await cmd.join_map("mountdoomskull")
        await cmd.sleep(1000)

    await cmd.ensure_accept_quest(QUEST_DAILY_DAGES_SCROLL)
    if cmd.quest_in_progress(QUEST_DAILY_DAGES_SCROLL):
        await hunt_item(
            cmd=cmd,
            item_name="Chaos Power Increased",
            item_qty=6,
            map_name="mountdoomskull",
            cell="b1",
            pad="Left",
            monster_name="*",
            is_temp=True,
            farming_logger=True
        )
        await cmd.ensure_turn_in_quest(QUEST_DAILY_DAGES_SCROLL)
        await cmd.sleep(1000)
        new_qty = cmd.get_quant_item(scroll_name)
        log_success(f"Daily Dage's Scroll Fragment selesai! Total sekarang: {new_qty}/13")
    else:
        log_info("Daily Dage's Scroll Fragment sudah pernah diselesaikan hari ini.")


async def get_le_chocolat(cmd: Command):
    """
    Membeli Le Chocolat seharga 1,250,000 gold dari /hyperspace (Shop 194).
    """
    item_name = "Le Chocolat"
    if cmd.is_in_bank(item_name):
        await cmd.bank_to_inv(item_name)
        return

    if cmd.is_in_inventory(item_name):
        log_success(f"'{item_name}' sudah ada di inventory.")
        return

    gold = cmd.get_player().GOLD
    log_info(f"Mengecek pembelian '{item_name}' (Harga: 1,250,000 gold | Gold Anda: {gold:,})...")

    if gold < 1250000:
        log_warning(f"Gold tidak mencukupi untuk membeli '{item_name}' (butuh 1.25M gold).")
        return

    if cmd.is_not_in_map("hyperspace"):
        await cmd.join_map("hyperspace")
        await cmd.sleep(1000)

    await cmd.ensure_load_shop(194)
    await cmd.buy_item(194, item_name, 1)
    await cmd.sleep(1000)

    if cmd.is_in_inventory(item_name):
        log_success(f"Berhasil membeli '{item_name}'!")


async def farm_treasure_chests(cmd: Command, target_qty: int = 100):
    """
    Farms Treasure Chest x100 dari /swordhavenundead.
    """
    item_name = "Treasure Chest"
    if cmd.is_in_bank(item_name):
        await cmd.bank_to_inv(item_name)

    current_qty = cmd.get_quant_item(item_name)
    if current_qty >= target_qty:
        log_success(f"'{item_name}' sudah lengkap ({current_qty}/{target_qty}).")
        return

    log_info(f"Farming '{item_name}' ({current_qty}/{target_qty}) di /swordhavenundead...")
    cmd.add_drop(item_name)

    farm_class = cmd.get_farm_class()
    if farm_class:
        await cmd.equip_item(farm_class)

    await hunt_item(
        cmd=cmd,
        item_name=item_name,
        item_qty=target_qty,
        map_name="swordhavenundead",
        cell="Left",
        pad="Right",
        monster_name="*",
        farming_logger=True
    )

    log_success(f"'{item_name}' x{target_qty} selesai!")


async def farm_face_of_chaos(cmd: Command):
    """
    Farms Face of Chaos dari Champion of Chaos di /ultradrakath.
    """
    item_name = "Face of Chaos"
    if cmd.is_in_bank(item_name):
        await cmd.bank_to_inv(item_name)
        return

    if cmd.is_in_inventory(item_name):
        log_success(f"'{item_name}' sudah ada di inventory.")
        return

    log_info(f"Farming '{item_name}' dari Champion of Chaos di /ultradrakath...")
    cmd.add_drop(item_name)

    solo_class = cmd.get_solo_class()
    if solo_class:
        await cmd.equip_item(solo_class)

    await hunt_item(
        cmd=cmd,
        item_name=item_name,
        item_qty=1,
        map_name="ultradrakath",
        cell="r1",
        pad="Left",
        monster_name="Champion of Chaos",
        farming_logger=True
    )

    log_success(f"'{item_name}' berhasil didapatkan!")


async def farm_unidentified_13(cmd: Command, target_qty: int = 3):
    """
    Mengecek dan mem-farm Unidentified 13 hingga target_qty (default 3x)
    menggunakan quest Nulgath Larvae (Quest 2566).
    """
    item_name = "Unidentified 13"
    if cmd.is_in_bank(item_name):
        await cmd.bank_to_inv(item_name)

    current_qty = cmd.get_quant_item(item_name)
    if current_qty >= target_qty:
        log_success(f"'{item_name}' sudah lengkap ({current_qty}/{target_qty}).")
        return

    log_info(f"'{item_name}' saat ini: {current_qty}/{target_qty}. Farming via Nulgath Larvae (Quest 2566)...")
    cmd.add_drop([
        item_name,
        "Mana Energy for Nulgath",
        "Charged Mana Energy for Nulgath"
    ])

    farm_class = cmd.get_farm_class()
    if farm_class:
        await cmd.equip_item(farm_class)

    larvae_tasks = [
        FarmTask(
            item_name="Mana Energy for Nulgath",
            qty=1,
            map_name="elemental",
            cell="r5",
            pad="Left"
        ),
        FarmTask(
            item_name="Charged Mana Energy for Nulgath",
            qty=5,
            map_name="elemental",
            cell="r3",
            pad="Left"
        )
    ]

    while cmd.is_still_connected() and cmd.get_quant_item(item_name) < target_qty:
        await cmd.ensure_accept_quest(2566)
        await do_farm_tasks(cmd, larvae_tasks)
        if cmd.can_turnin_quest(2566):
            await cmd.ensure_turn_in_quest(2566)
            await cmd.sleep(500)

    log_success(f"'{item_name}' x{target_qty} selesai!")


async def buy_drakath_armors(cmd: Command):
    """
    Membeli 'Drakath Armor' dan 'Original Drakath Armor' dari Shop 994.
    """
    log_info("Membuka Shop 994 untuk mengklaim Drakath Armor...")
    await cmd.ensure_load_shop(994)

    if not cmd.is_in_inventory("Original Drakath Armor"):
        log_info("Membeli Original Drakath Armor (0 AC)...")
        await cmd.buy_item(994, "Original Drakath Armor", 1)
        await cmd.sleep(1000)

    if not cmd.is_in_inventory("Drakath Armor"):
        log_info("Membeli Drakath Armor (0 AC)...")
        await cmd.buy_item(994, "Drakath Armor", 1)
        await cmd.sleep(1000)

    if cmd.is_in_inventory("Drakath Armor"):
        log_success("Drakath Armor berhasil masuk ke Inventory!")
    if cmd.is_in_inventory("Original Drakath Armor"):
        log_success("Original Drakath Armor berhasil masuk ke Inventory!")


async def print_status(cmd: Command):
    """Menampilkan ringkasan status material Drakath Armor."""
    print(Fore.YELLOW + "\n============== STATUS BAHAN DRAKATH ARMOR ==============" + Fore.RESET)
    c_rank = cmd.get_player().getFactionRank("Chaos")
    print(f" {'[OK]' if c_rank >= 10 else '[KURANG]'} Chaos Reputation: Rank {c_rank}/10")

    has_blod = cmd.is_in_inventory("Blinding Light of Destiny")
    print(f" {'[OK]' if has_blod else '[KURANG]'} Blinding Light of Destiny: {'Ada' if has_blod else 'Belum ada'}")

    has_boa = cmd.is_in_inventory("Blade of Awe")
    print(f" {'[OK]' if has_boa else '[KURANG]'} Blade of Awe: {'Ada' if has_boa else 'Belum ada'}")

    u13 = cmd.get_quant_item("Unidentified 13")
    print(f" {'[OK]' if u13 >= 3 else '[KURANG]'} Unidentified 13: {u13}/3")

    dage_scroll = cmd.get_quant_item("Dage's Scroll Fragment")
    print(f" {'[OK]' if dage_scroll >= 13 else '[KURANG]'} Dage's Scroll Fragment: {dage_scroll}/13 (Daily)")

    has_choco = cmd.is_in_inventory("Le Chocolat")
    print(f" {'[OK]' if has_choco else '[KURANG]'} Le Chocolat: {'Ada' if has_choco else 'Belum ada'}")

    chests = cmd.get_quant_item("Treasure Chest")
    print(f" {'[OK]' if chests >= 100 else '[KURANG]'} Treasure Chest: {chests}/100")

    has_foc = cmd.is_in_inventory("Face of Chaos")
    print(f" {'[OK]' if has_foc else '[KURANG]'} Face of Chaos: {'Ada' if has_foc else 'Belum ada'}")
    print(Fore.YELLOW + "========================================================\n" + Fore.RESET)


async def main(cmd: Command):
    log_info("Memulai Scriptable Bot: Drakath Armor (Quest 3882)...")

    # 1. Cek apakah sudah memiliki armor di inventory atau bank
    if cmd.is_in_inventory_or_bank("Drakath Armor") and cmd.is_in_inventory_or_bank("Original Drakath Armor"):
        await check_and_transfer_bank(cmd, ["Drakath Armor", "Original Drakath Armor"])
        log_success("Anda sudah memiliki Drakath Armor dan Original Drakath Armor!")
        return

    # 2. Pindahkan item terkait dari bank ke inventory & daftarkan drops
    await check_and_transfer_bank(cmd, REQUIRED_MATERIALS + ["Drakath Armor", "Original Drakath Armor", "Get Your Original Drakath's Armor"])
    cmd.add_drop(ALL_DROPS)

    # 3. Jika sudah memiliki quest item reward 'Get Your Original Drakath's Armor', langsung klaim dari shop 994
    if cmd.is_in_inventory("Get Your Original Drakath's Armor"):
        log_success("Item 'Get Your Original Drakath's Armor' ditemukan! Membuka Shop 994...")
        await buy_drakath_armors(cmd)
        return

    # 4. Pastikan Chaos Reputation Rank 10
    await ensure_chaos_rep(cmd, target_rank=10)

    # 5. Cek Blinding Light of Destiny (wajib untuk accept quest 3882)
    if not cmd.is_in_inventory("Blinding Light of Destiny"):
        log_warning("Blinding Light of Destiny (BLoD) belum ada di inventory. Diperlukan untuk memulai Quest 3882.")

    # 6. Cek Blade of Awe
    if not cmd.is_in_inventory("Blade of Awe"):
        log_warning("Blade of Awe belum ada di inventory. Diperlukan untuk menyelesaikan Quest 3882.")

    # 7. Selesaikan Daily Dage's Scroll Fragment (jika hari ini belum)
    await do_daily_dages_scroll(cmd)

    # 8. Farm Unidentified 13 (target: 3)
    await farm_unidentified_13(cmd, target_qty=3)

    # 9. Beli Le Chocolat (1.25M gold)
    await get_le_chocolat(cmd)

    # 10. Farm Treasure Chest x100
    await farm_treasure_chests(cmd, target_qty=100)

    # 11. Farm Face of Chaos
    await farm_face_of_chaos(cmd)

    # 12. Cetak status semua bahan
    await print_status(cmd)

    # 13. Verifikasi turn-in Quest 3882
    can_complete = (
        cmd.is_in_inventory("Blinding Light of Destiny") and
        cmd.is_in_inventory("Blade of Awe") and
        cmd.is_in_inventory("Unidentified 13", 3, ">=") and
        cmd.is_in_inventory("Dage's Scroll Fragment", 13, ">=") and
        cmd.is_in_inventory("Le Chocolat") and
        cmd.is_in_inventory("Treasure Chest", 100, ">=") and
        cmd.is_in_inventory("Face of Chaos") and
        cmd.get_player().getFactionRank("Chaos") >= 10
    )

    if can_complete:
        log_info("Semua persyaratan terpenuhi! Menerima dan menyelesaikan Quest 3882 (Build Drakath's Armor)...")
        if cmd.is_not_in_map("confrontation"):
            await cmd.join_map("confrontation")
            await cmd.sleep(1000)

        await cmd.ensure_accept_quest(QUEST_DRAKATH_ARMOR)
        await cmd.sleep(500)
        await cmd.ensure_turn_in_quest(QUEST_DRAKATH_ARMOR)
        await cmd.sleep(1000)

        if cmd.is_in_inventory("Get Your Original Drakath's Armor"):
            log_success("Quest 3882 berhasil diselesaikan! Mengklaim armor dari Shop 994...")
            await buy_drakath_armors(cmd)
            print(Fore.GREEN + "\n========================================================")
            print("  CONGRATULATIONS! UNLOCKED: DRAKATH ARMOR!")
            print("========================================================\n" + Fore.RESET)
    else:
        log_warning(
            "Bahan yang dapat di-farm otomatis telah selesai dikumpulkan.\n"
            "Jika Dage's Scroll Fragment belum mencapai 13, silakan jalankan kembali bot ini besok setelah daily reset."
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
