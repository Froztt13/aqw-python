import json
import sys
import asyncio
from core.bot import Bot
from core.command import Command, SkillMode
from core.utils import is_valid_json

class Slave:
    def __init__(self, username, password, char_class):
        self.username = username
        self.password = password
        self.char_class = char_class

server = "Gravelyn"
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
    cmd.bot.last_skills = []
    skills_str = getattr(cmd.bot, "skills", "1,2,3,4")
    try:
        skills = [int(x.strip()) for x in skills_str.split(",") if x.strip().isdigit() and int(x.strip()) != 0]
        if not skills:
            skills = [1, 2, 3, 4]
    except Exception:
        skills = [1, 2, 3, 4]
        
    skill_index = 0
    other_skills_used = 0
    
    # Resolve dynamic properties if injected via GUI, otherwise fallback to script globals
    f_player = getattr(cmd.bot, "follow_player", None) or (follow_player if 'follow_player' in globals() else "")
    room_num = getattr(cmd.bot, "default_room_number", None) or default_room_number
    targets = getattr(cmd.bot, "targets_priority", None) or targets_priority
    
    copy_walk = getattr(cmd.bot, "copy_walk", True)
    auto_zone = getattr(cmd.bot, "auto_zone", "none")
    
    hp_operator = getattr(cmd.bot, "hp_operator", "<")
    hp_threshold = getattr(cmd.bot, "hp_threshold", 0)
    hp_skills_str = getattr(cmd.bot, "hp_skills", "")
    try:
        hp_skills = [int(x.strip()) for x in hp_skills_str.split(",") if x.strip().isdigit()]
    except Exception:
        hp_skills = []
        
    mp_operator = getattr(cmd.bot, "mp_operator", "<")
    mp_threshold = getattr(cmd.bot, "mp_threshold", 0)
    mp_skills_str = getattr(cmd.bot, "mp_skills", "")
    try:
        mp_skills = [int(x.strip()) for x in mp_skills_str.split(",") if x.strip().isdigit()]
    except Exception:
        mp_skills = []
    
    await cmd.equip_item(cmd.get_farm_class())
    await cmd.sleep(500)
    
    def handle_message(message):
        # %xt%warning%-1%Cannot goto to player in a Locked zone.%
        global checking_locked_zone
        if message.startswith("%") and message.endswith("%"):
            # print(f"message: {message}")
            if "locked zone" in message.lower():
                checking_locked_zone = True
                
            parts = message.split("%")
            if len(parts) > 5 and parts[2] == "uotls":
                try:
                    curr_username = parts[4].lower()
                    # print(f"[{cmd.bot.username}] uotls packet from '{curr_username}'. target='{f_player.lower() if f_player else ''}', copy_walk={copy_walk}, loading={cmd.bot.is_joining_map}")
                    if f_player and curr_username == f_player.lower() and not cmd.bot.is_joining_map and copy_walk:
                        movement = parts[5]
                        cell = None
                        pad = None
                        x = None
                        y = None
                        for m in movement.split(','):
                            m_parts = m.split(':')
                            if len(m_parts) == 2:
                                if m_parts[0] == "strFrame":
                                    cell = m_parts[1]
                                elif m_parts[0] == "strPad":
                                    pad = m_parts[1]
                                elif m_parts[0] == "tx":
                                    x = float(m_parts[1])
                                elif m_parts[0] == "ty":
                                    y = float(m_parts[1])
                        
                        if cell is not None and cell.lower() != cmd.bot.player.CELL.lower():
                            target_pad = pad if pad is not None else "Left"
                            asyncio.create_task(cmd.jump_cell(cell, target_pad))
                        elif x is not None and y is not None and (x != 0 or y != 0):
                            asyncio.create_task(cmd.walk_to(int(x), int(y)))
                except Exception as e:
                    print(f"Error handling uotls: {e}")
                
        if is_valid_json(message):
            try:
                data = json.loads(message)["b"]["o"]
                cmdData = data["cmd"]

                if cmdData == "pi":
                    pid = data.get("pid") or data.get("owner")
                    if pid:
                        cmd.bot.write_message(f"%xt%zm%gp%1%pa%{pid}%")

                if cmdData == "event":
                    args = data.get("args")
                    print(f"[{cmd.bot.username}] Event packet. auto_zone='{auto_zone}', args={args}")
                    if args and "zoneSet" in args:
                        zone = args["zoneSet"]
                        if auto_zone == "Astral Empyrean":
                            if zone == "A":
                                asyncio.create_task(cmd.walk_to(708, 447))
                            elif zone == "B":
                                asyncio.create_task(cmd.walk_to(287, 191))
                            else:
                                asyncio.create_task(cmd.walk_to(461, 329))
                        elif auto_zone == "Dark Carnax":
                            if zone == "A":
                                asyncio.create_task(cmd.walk_to(860, 400))
                            elif zone == "B":
                                asyncio.create_task(cmd.walk_to(49, 400))
                            else:
                                asyncio.create_task(cmd.walk_to(426, 372))
                        elif auto_zone == "Ultra Dage":
                            if zone == "A":
                                asyncio.create_task(cmd.walk_to(107, 400))
                            elif zone == "B":
                                asyncio.create_task(cmd.walk_to(843, 400))
                            else:
                                asyncio.create_task(cmd.walk_to(503, 276))
                        elif auto_zone == "Queen Iona":
                            async def handle_iona(zone_val):
                                await asyncio.sleep(0.5)
                                player = cmd.get_player()
                                pos_charge = player.hasAura("Positive Charge")
                                pos_charge_rev = player.hasAura("Positive Charge?")
                                neg_charge = player.hasAura("Negative Charge")
                                neg_charge_rev = player.hasAura("Negative Charge?")
                                
                                if zone_val == "A":
                                    if pos_charge or neg_charge_rev:
                                        await cmd.walk_to(679, 339)
                                    elif neg_charge or pos_charge_rev:
                                        await cmd.walk_to(272, 379)
                                elif zone_val == "B":
                                    if pos_charge or neg_charge_rev:
                                        await cmd.walk_to(272, 379)
                                    elif neg_charge or pos_charge_rev:
                                        await cmd.walk_to(679, 339)
                                else:
                                    await cmd.walk_to(490, 320)
                            asyncio.create_task(handle_iona(zone))
                        elif auto_zone == "Vordred":
                            if zone == "A":
                                asyncio.create_task(cmd.walk_to(731, 461))
                            elif zone == "B":
                                asyncio.create_task(cmd.walk_to(700, 321))
                            else:
                                asyncio.create_task(cmd.walk_to(748, 372))

                if cmdData == "ct":
                    pass

            except Exception:
                return
        
    cmd.subscribe(handle_message)
    
    async def goto_master():
        global checking_locked_zone
        print(f"goto master...")
        await cmd.goto_player(f_player)
        await cmd.sleep(200)
        if cmd.get_player_in_map(f_player):
            checking_locked_zone = False
    
    async def checking_map():
        global checking_locked_zone
        map_to_check = getattr(cmd.bot, "locked_zones", None)
        if not map_to_check:
            map_to_check = [
                "ultraezrajal",
                "ultrawarden",
                "ultraengineer",
                "doomvault",
                "doomvaultb",
                "championdrakath",
                "tercessuinotlim",
                "icestormunder",
            ]
        for map_name in map_to_check:
            print(f"checking {map_name}...")
            await cmd.join_map(map_name, roomNumber=room_num)
            while cmd.is_not_in_map(map_name):
                await cmd.sleep(100)
            if cmd.get_player_in_map(f_player):
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
        
        master = cmd.get_player_in_map(f_player)
        check_master_in_cell = master and master.str_frame == cmd.get_player().CELL
        
        if not check_master_in_cell and not checking_locked_zone:
            await goto_master()
            continue
        
        targeted_monster = cmd.get_player().getLastTarget()
        skill_mode = SkillMode.ALL
        if targeted_monster and targeted_monster.getAura('Counter Attack'):
            skill_mode = SkillMode.BUFF_ONLY
            print('buff only mode...')
        
        # Check health and MP thresholds
        player_obj = cmd.get_player()
        current_skill = skills[skill_index]
        
        # Check HP threshold
        if hp_threshold > 0 and hp_skills:
            if current_skill in hp_skills:
                hp_pct = (player_obj.CURRENT_HP / player_obj.MAX_HP * 100) if player_obj.MAX_HP > 0 else 100
                is_triggered = hp_pct < hp_threshold if hp_operator == "<" else hp_pct > hp_threshold
                if not is_triggered:
                    # Skip since the condition to USE this skill is NOT met!
                    skill_index = (skill_index + 1) % len(skills)
                    continue
                
        # Check MP threshold
        if mp_threshold > 0 and mp_skills:
            if current_skill in mp_skills:
                mp_pct = (player_obj.MANA / player_obj.MAX_MP * 100) if player_obj.MAX_MP > 0 else 100
                is_triggered = mp_pct < mp_threshold if mp_operator == "<" else mp_pct > mp_threshold
                if not is_triggered:
                    # Skip since the condition to USE this skill is NOT met!
                    skill_index = (skill_index + 1) % len(skills)
                    continue
        
        success = await cmd.use_skill(
            index=skills[skill_index],
            target_monsters=targets,
            skill_mode=skill_mode
            )
        
        if success:
            last_skills = getattr(cmd.bot, "last_skills", [])
            last_skills.append(skills[skill_index])
            if len(last_skills) > 3:
                last_skills.pop(0)
            cmd.bot.last_skills = last_skills
            
            other_skills_used += 1
            if other_skills_used >= 2:
                success_0 = await cmd.use_skill(
                    index=0,
                    target_monsters=targets,
                    skill_mode=skill_mode
                )
                if success_0:
                    last_skills = getattr(cmd.bot, "last_skills", [])
                    last_skills.append(0)
                    if len(last_skills) > 3:
                        last_skills.pop(0)
                    cmd.bot.last_skills = last_skills
                other_skills_used = 0
        
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