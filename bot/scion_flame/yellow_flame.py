from core.bot import Bot
from core.command import Command
from core.task import FarmTask, do_farm_tasks
from colorama import Fore

async def main(cmd: Command):
    map_name = "fortluma"    
    room_number = 9099
    item_to_farm: list[FarmTask] = [
        FarmTask(
            item_name="Citrinitas Flicker", 
            qty=1, 
            map_name=map_name,
            room_number=room_number,
            cell="r11", 
            pad="Right",
            is_solo=True
        ),
        FarmTask(
            item_name="Draconic Contrasoul", 
            qty=1, 
            map_name=map_name, 
            room_number=room_number,
            cell="r9", 
            pad="Left",
            is_solo=True
        ),
        FarmTask(
            item_name="King's Yellow", 
            qty=1, 
            map_name=map_name, 
            room_number=room_number,
            cell="r5", 
            pad="Left", 
            is_solo=True
        ),
    ]
    complete_count = 0

    await cmd.register_quest(10619)
    # await cmd.register_quest(10620) # Member

    while (cmd.is_still_connected() and complete_count < 1000):
        await do_farm_tasks(cmd, item_to_farm)
        complete_count = complete_count + 1
        print(Fore.GREEN + f"Complete count : {complete_count}" + Fore.RESET)


item_to_farm: list[str] = [
    "Yellow Flame of Citrinitas"
]

if __name__ == "__main__":
    import asyncio
    bot = Bot(itemsDropWhiteList=item_to_farm,
              cmdDelay=600,
              showDebug=False,
              autoRelogin=True,
              isScriptable=True)  
    run = Command(bot) 
    
    login = input("Login (username,pass): ").split(",")
    bot.set_login_info(login[0], login[1], "Gravelyn")

    asyncio.run(bot.start_bot(main))  # Run the main coroutine

