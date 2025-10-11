import json
from core.bot import Bot
from core.command import Command
from core.utils import is_valid_json

class Slave:
    def __init__(self, username, password, char_class):
        self.username = username
        self.password = password
        self.char_class = char_class
        
server = "Alteon"
default_room_number = 9099  # For checking Master account is in locked zone map
follow_player = "user to follow"
slaves = [
    Slave("user", "pass", "Lord of Order"),
    Slave("user", "pass", "Legion Revenant"),
]

whitelist = [
        "Treasure Chest",
        "Void Aura",
    ]

    
checking_locked_zone = False
async def main(cmd: Command):
    global checking_locked_zone
    skills = [0,1,2,0,3,4]
    skill_index = 0
    
    await cmd.equip_item(cmd.get_farm_class())
    await cmd.sleep(500)
    
    def handle_message(message):
        # %xt%warning%-1%Cannot goto to player in a Locked zone.%
        global checking_locked_zone
        if message.startswith("%") and message.endswith("%"):
            # print(f"message: {message}")
            if "locked zone" in message.lower():
                checking_locked_zone = True
    cmd.subscribe(handle_message)
    
    async def goto_master():
        print(f"goto master...")
        await cmd.goto_player(follow_player)
        await cmd.sleep(200)
    
    async def checking_map():
        global checking_locked_zone
        map_to_check = [
            "doomvaultb",
            "tercessuinotlim"
        ]
        for map_name in map_to_check:
            print(f"checking {map_name}...")
            await cmd.join_map(map_name, roomNumber=default_room_number)
            await cmd.sleep(500)
            if cmd.get_player_in_map(follow_player):
                checking_locked_zone = False
                break
                
    while(cmd.is_still_connected()):
        if not cmd.is_player_alive():
            continue
        
        if checking_locked_zone:
            print(f"checking locked zone...")
            await checking_map()
        
        master = cmd.get_player_in_map(follow_player)
        check_master_in_cell = master and master.str_frame == cmd.get_player().CELL
        
        if not check_master_in_cell and not checking_locked_zone:
            await goto_master()
            continue
        
        await cmd.use_skill(skills[skill_index])
        await cmd.sleep(200)
        
        skill_index = skill_index + 1
        if skill_index >= len(skills):
            skill_index = 0


if __name__ == "__main__":
    import asyncio
    
    input_str = input(f"Select your slaves [1-{len(slaves)}] : ")
    input_int = int(input_str)
    selected_slave = slaves[input_int - 1]

    bot = Bot(itemsDropWhiteList=whitelist,
              cmdDelay=500,
              showDebug=True,
              autoRelogin=True,
              isScriptable=True,
              followPlayer=follow_player,
              farmClass=selected_slave.char_class)
    run = Command(bot)     
    bot.set_login_info(selected_slave.username, selected_slave.password, server)  # Set login info

    asyncio.run(bot.start_bot(main))  # Run the main coroutine