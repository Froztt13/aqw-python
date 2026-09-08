from typing import Optional
from core.command import Command
from core.task import FarmTask, do_farm_tasks
from colorama import Fore

NULGATH_LARVAE_DROPS = [
    "Unidentified 13",
    "Tainted Gem",
    "Dark Crystal Shard",
    "Diamond of Nulgath",
    "Voucher of Nulgath",
    "Voucher of Nulgath (non-mem)",
    "Totem of Nulgath",
    "Gem of Nulgath",
    "Blood Gem of the Archfiend"
]

async def farm_larvae(cmd: Command, target_item: Optional[str] = None, target_qty: int = 50):
    map_name = "elemental"
    item_to_farm: list[FarmTask] = [
        FarmTask(
            item_name="Mana Energy for Nulgath",
            qty=1,
            map_name=map_name,
            cell="r5",
            pad="Left",
            is_solo=True
        ),
        FarmTask(
            item_name="Charged Mana Energy for Nulgath",
            qty=5,
            map_name=map_name,
            cell="r3",
            pad="Left",
            is_solo=False
        )
    ]

    # Whitelist all nation materials from Larva
    cmd.add_drop(NULGATH_LARVAE_DROPS)

    # Bank-to-inv non-voucher rewards so they stack in inventory
    bankable_items = [d for d in NULGATH_LARVAE_DROPS if d != "Voucher of Nulgath"]
    await cmd.bank_to_inv(bankable_items)

    complete_count = 0
    await cmd.register_quest(2566)

    print(Fore.CYAN + f"=== [Nulgath Larva] Starting farm (Quest 2566) ===" + Fore.RESET)
    if target_item:
        print(Fore.CYAN + f"Target: {target_item} x{target_qty}" + Fore.RESET)
    elif target_qty > 0:
        print(Fore.CYAN + f"Target Turn-Ins: {target_qty}" + Fore.RESET)
    else:
        print(Fore.CYAN + f"Mode: Infinite Loop (Continuous farm)" + Fore.RESET)

    while cmd.is_still_connected():
        # Check target item quantity if specified
        if target_item:
            if cmd.is_in_inventory(target_item, target_qty, operator=">="):
                print(Fore.GREEN + f"=== Target {target_item} reached: {target_qty}! ===" + Fore.RESET)
                break
        elif target_qty > 0:
            if complete_count >= target_qty:
                print(Fore.GREEN + f"=== Target turn-ins completed: {complete_count}/{target_qty}! ===" + Fore.RESET)
                break

        await do_farm_tasks(cmd, item_to_farm)

        # Auto sell member voucher to prevent inventory lock and gain 250k gold
        if cmd.is_in_inventory("Voucher of Nulgath"):
            print(Fore.YELLOW + "Selling 'Voucher of Nulgath' for 250,000 gold..." + Fore.RESET)
            await cmd.sell_item("Voucher of Nulgath")
            await cmd.sleep(1000)

        complete_count += 1
        cmd.bot.general_turn_in_count = complete_count
        print(Fore.GREEN + f"=== [Nulgath Larva] Completed turn-in #{complete_count} ===" + Fore.RESET)

async def main(cmd: Command):
    await farm_larvae(cmd)
