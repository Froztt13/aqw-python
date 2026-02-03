from core.command import Command
from core.task import FarmTask, do_farm_tasks
from colorama import Fore

async def main(cmd: Command):
    map_name = "elemental"    
    item_to_farm: list[FarmTask] = [
        FarmTask(
            item_name="Mana Energy for Nulgath", 
            qty=1, 
            map_name=map_name,
            cell="r5", 
            pad="Left"
        ),
        FarmTask(
            item_name="Charged Mana Energy for Nulgath", 
            qty=5, 
            map_name=map_name, 
            cell="r3", 
            pad="Left"
        )
    ]
    complete_count = 0

    await cmd.register_quest(2566)

    while cmd.is_still_connected():
        await do_farm_tasks(cmd, item_to_farm)
        if (cmd.is_in_inventory("Voucher of Nulgath")):
            await cmd.sell_item("Voucher of Nulgath")
            await cmd.sleep(1000)
        complete_count = complete_count + 1
        print(Fore.GREEN + f"Complete count : {complete_count}" + Fore.RESET)