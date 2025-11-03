import json
import sys
from core.bot import Bot
from core.command import Command, SkillMode
from core.utils import is_valid_json

class Slave:
    def __init__(self, username, password, char_class):
        self.username = username
        self.password = password
        self.char_class = char_class

server = "Alteon"
default_room_number = 9099  # For checking Master account is in locked zone map
targets_priority = "Defense Drone,Staff of Inversion"
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
                
        if is_valid_json(message):
            try:
                data = json.loads(message)["b"]["o"]
                cmdData = data["cmd"]

                if cmdData == "pi":
                    # handle party invitation here
                    pass

                if cmdData == "ct":
                    pass

            except Exception:
                return
        
    cmd.subscribe(handle_message)
    
    async def goto_master():
        global checking_locked_zone
        print(f"goto master...")
        await cmd.goto_player(follow_player)
        await cmd.sleep(200)
        if cmd.get_player_in_map(follow_player):
            checking_locked_zone = False
    
    async def checking_map():
        global checking_locked_zone
        map_to_check = [
            "ultraengineer",
            "doomvaultb",
            "championdrakath",
            "tercessuinotlim",
            "icestormunder"
        ]
        for map_name in map_to_check:
            print(f"checking {map_name}...")
            await cmd.join_map(map_name, roomNumber=default_room_number)
            while cmd.is_not_in_map(map_name):
                await cmd.sleep(100)
            if cmd.get_player_in_map(follow_player):
                print(f"stopped at {map_name}...")
                checking_locked_zone = False
                await cmd.sleep(1000)
                break
        await goto_master()
                
    while(cmd.is_still_connected()):
        await cmd.sleep(200)
        if not cmd.is_player_alive():
            await cmd.sleep(200)
            continue
        
        if checking_locked_zone:
            print(f"checking locked zone...")
            await checking_map()
        
        master = cmd.get_player_in_map(follow_player)
        check_master_in_cell = master and master.str_frame == cmd.get_player().CELL
        
        if not check_master_in_cell and not checking_locked_zone:
            await goto_master()
            continue
        
        targeted_monster = cmd.get_player().getLastTarget()
        skill_mode = SkillMode.ALL
        if targeted_monster and targeted_monster.getAura('Counter Attack'):
            skill_mode = SkillMode.BUFF_ONLY
            print('buff only mode...')
        
        await cmd.use_skill(
            index=skills[skill_index],
            target_monsters=targets_priority,
            skill_mode=skill_mode
            )
        
        skill_index = skill_index + 1
        if skill_index >= len(skills):
            skill_index = 0


if __name__ == "__main__":
    import asyncio

    # Handle input that contains slave number and follow player
    input_str = input(f"Select your slaves [1-{len(slaves)}] : ")

    # Extract both slave number and follow player from input
    input_parts = input_str.strip().split(maxsplit=1)

    # Check if we have both slave number and follow player
    if len(input_parts) < 2:
        print("Error: Input format should be: <slave_number> <player_name>")
        print("Example: 2 cysero")
        sys.exit(1)

    # The first part should be the slave number
    try:
        input_int = int(input_parts[0])
        selected_slave = slaves[input_int - 1]
    except (ValueError, IndexError) as e:
        print(f"Error: Invalid slave selection '{input_parts[0]}'")
        print(f"Please enter a number between 1 and {len(slaves)}")
        sys.exit(1)

    # The second part is the follow player name
    follow_player = input_parts[1]

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