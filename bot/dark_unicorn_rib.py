import asyncio
from datetime import datetime
from core.bot import Bot
from core.command import Command
from core.task import FarmTask, do_farm_tasks
from colorama import Fore

b = Bot(
    roomNumber=9099,
    itemsDropWhiteList=[
        "Dark Unicorn Rib",
        "Legion Token",
        "Living BladeMaster",
        "BladeMaster's Dual Katanas",
        "Lesser Caladbolg"
    ],
    showLog=True,
    showDebug=False,
    showChat=True,
    isScriptable=True,
    farmClass="Legion Revenant",
    respawnCellPad=["Enter", "Spawn"],
    muteSpamWarning=True
)
b.set_login_info("username", "password", "alteon")


async def main(cmd: Command):
    # await cmd.register_quest(3393)
    await cmd.accept_quest(3393)
    
    skillList = [0,1,2,0,3,4]
    skillIndex = 0
    killTime = 0

    while cmd.is_still_connected():
        if (cmd.is_not_in_map("doomvault")):
            await cmd.join_map("doomvault", 9099)
            await cmd.sleep(2000)
        if (cmd.is_not_in_cell("r5")):
            await cmd.jump_cell("r5", "Left")
            await cmd.sleep(2000)
            
        while(cmd.is_monster_alive("Binky") == False):
            await cmd.sleep(200)
        
        while(cmd.is_monster_alive("Binky")):
            if (cmd.get_player().hasAura("Skill Locked")):
                await cmd.use_skill(skillList[skillIndex])
            else:
                await cmd.use_skill(0)
            await cmd.sleep(200)
            skillIndex = skillIndex + 1
            if (skillIndex >= len(skillList)):
                skillIndex = 0
        
        killTime = killTime + 1
        print(f"[{datetime.now().strftime('%H:%M:%S')}] Binky killed : {killTime}x")
        
asyncio.run(b.start_bot(main))