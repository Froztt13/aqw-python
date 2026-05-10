from core.bot import Bot
from core.command import Command
from core.task import FarmTask, do_farm_tasks
from colorama import Fore
import asyncio

async def main(cmd: Command):
    # Set this to True if you are a Member (Legend)
    is_member = False
    # Set the target quantity for each flame
    target_qty = 100

    # Setup targets for each flame
    targets = [
        {
            "name": "Black Flame of Maleno",
            "quest_id": 10369,
            "quest_id_member": 10370,
            "tasks": [
                FarmTask(
                    item_name="Powder of Algaroth", 
                    qty=1, 
                    map_name="mountmaleno", 
                    cell="r10", 
                    pad="Bottom", 
                    monster_name="*", 
                    is_solo=True, 
                    room_number=9099
                ),
                FarmTask(
                    item_name="Plumbago", 
                    qty=3, 
                    map_name="mountmaleno", 
                    cell="r6", 
                    pad="Right", 
                    monster_name="*", 
                    is_solo=False, 
                    room_number=9099
                ),
                FarmTask(
                    item_name="Lapis Infernalis", 
                    qty=9, 
                    map_name="mountmaleno", 
                    cell="r9", 
                    pad="Right", 
                    monster_name="*", 
                    is_solo=False, 
                    room_number=9099
                ),
            ]
        },
        {
            "name": "White Flame of Albedo",
            "quest_id": 10423,
            "quest_id_member": 10424,
            "tasks": [
                FarmTask(
                    item_name="Albedo Flicker", 
                    qty=1, 
                    map_name="forgealbedo", 
                    cell="r10", 
                    pad="Bottom", 
                    monster_name="*", 
                    is_solo=True, 
                    room_number=9099
                ),
                FarmTask(
                    item_name="Calx", 
                    qty=6, 
                    map_name="forgealbedo", 
                    cell="r7", 
                    pad="Left", 
                    monster_name="*", 
                    is_solo=False, 
                    room_number=9099
                ),
                FarmTask(
                    item_name="Corrosive Sublimate", 
                    qty=9, 
                    map_name="forgealbedo", 
                    cell="r3", 
                    pad="Left", 
                    monster_name="*", 
                    is_solo=False, 
                    room_number=9099
                ),
            ]
        },
        {
            "name": "Red Flame of Rubedo",
            "quest_id": 10688,
            "quest_id_member": 10689,
            "tasks": [
                FarmTask(
                    item_name="Rubedo Flicker", 
                    qty=1, 
                    map_name="warwickforest", 
                    cell="r10", 
                    pad="Top", 
                    monster_name="*", 
                    is_solo=True, 
                    room_number=9099
                ),
                FarmTask(
                    item_name="Kolr's Needle", 
                    qty=1, 
                    map_name="warwickforest", 
                    cell="r9", 
                    pad="Right", 
                    monster_name="*", 
                    is_solo=True, 
                    room_number=9099
                ),
                FarmTask(
                    item_name="Alkahest", 
                    qty=100, 
                    map_name="warwickforest", 
                    cell="r4", 
                    pad="Right", 
                    monster_name="*", 
                    is_solo=False, 
                    room_number=9099
                ),
            ]
        },
        {
            "name": "Yellow Flame of Citrinitas",
            "quest_id": 10619,
            "quest_id_member": 10620,
            "tasks": [
                FarmTask(
                    item_name="Citrinitas Flicker", 
                    qty=1, 
                    map_name="fortluma", 
                    cell="r11", 
                    pad="Right", 
                    monster_name="*", 
                    is_solo=True, 
                    room_number=9099
                ),
                FarmTask(
                    item_name="Draconic Contrasoul", 
                    qty=1, 
                    map_name="fortluma", 
                    cell="r9", 
                    pad="Left", 
                    monster_name="*", 
                    is_solo=True, 
                    room_number=9099
                ),
                FarmTask(
                    item_name="King's Yellow", 
                    qty=1, 
                    map_name="fortluma", 
                    cell="r5", 
                    pad="Left", 
                    monster_name="*", 
                    is_solo=True, 
                    room_number=9099
                ),
            ]
        }
    ]

    # Whitelist all target flames
    all_flames = [t["name"] for t in targets]
    cmd.add_drop(all_flames)

    for target in targets:
        item_name = target["name"]
        quest_id = target["quest_id_member"] if is_member else target["quest_id"]
        tasks = target["tasks"]

        print(Fore.CYAN + f"Starting farm for {item_name} (Quest: {quest_id})..." + Fore.RESET)
        await cmd.register_quest(quest_id)
        
        while cmd.is_still_connected() and cmd.get_quant_item(item_name) < target_qty:
            cmd.farming_logger(item_name, target_qty)
            await do_farm_tasks(cmd, tasks)
            await asyncio.sleep(1)
        
        print(Fore.GREEN + f"Target reached: {target_qty}x {item_name}" + Fore.RESET)

    print(Fore.GREEN + "All farming tasks completed!" + Fore.RESET)

if __name__ == "__main__":
    import asyncio
    
    item_to_farm: list[str] = [
        "Black Flame of Maleno",
        "White Flame of Albedo",
        "Red Flame of Rubedo",
        "Yellow Flame of Citrinitas"
    ]
    
    bot = Bot(itemsDropWhiteList=item_to_farm,
              cmdDelay=600,
              showDebug=False,
              autoRelogin=True,
              isScriptable=True)  
    
    # Set default login info or uncomment to use input
    login = input("Login (username,pass): ").split(",")
    bot.set_login_info(login[0], login[1], "Gravelyn")

    asyncio.run(bot.start_bot(main))
