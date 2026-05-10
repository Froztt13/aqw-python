from core.bot import Bot
from core.command import Command
from core.task import FarmTask, do_farm_tasks
from colorama import Fore

async def main(cmd: Command):
    map_name = "forgealbedo"    
    room_number = 9099
    item_to_farm: list[FarmTask] = [
        FarmTask(
            item_name="Albedo Flicker", 
            qty=1, 
            map_name=map_name,
            room_number=room_number,
            cell="r10", 
            pad="Bottom",
            is_solo=True
        ),
        FarmTask(
            item_name="Calx", 
            qty=6, 
            map_name=map_name, 
            room_number=room_number,
            cell="r7", 
            pad="Left"
        ),
        FarmTask(
            item_name="Corrosive Sublimate", 
            qty=9, 
            map_name=map_name, 
            room_number=room_number,
            cell="r3", 
            pad="Left"
        ),
    ]
    complete_count = 0

    await cmd.register_quest(10423)
    # await cmd.register_quest(10424) # Member

    while (cmd.is_still_connected() and complete_count < 1000):
        await do_farm_tasks(cmd, item_to_farm)
        complete_count = complete_count + 1
        print(Fore.GREEN + f"Complete count : {complete_count}" + Fore.RESET)


item_to_farm: list[str] = [
    "White Flame of Albedo"
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
    bot.set_login_info(login[0], login[1], "Gravelyn")  # Set login info


    asyncio.run(bot.start_bot(main))  # Run the main coroutine

