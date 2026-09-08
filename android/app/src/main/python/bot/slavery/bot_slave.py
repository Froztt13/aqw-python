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

    
class SkillConfig:
    def __init__(self, index: int, threshold_type: str = "NONE", operator: str = "<", threshold_value: int = 0):
        self.index = int(index)
        self.threshold_type = str(threshold_type or "NONE").upper()
        self.operator = str(operator or "<")
        self.threshold_value = int(threshold_value or 0)

    def check_threshold(self, player_obj) -> bool:
        if self.threshold_type == "HP" and self.threshold_value > 0:
            if not player_obj or player_obj.MAX_HP <= 0:
                return True
            hp_pct = (player_obj.CURRENT_HP / player_obj.MAX_HP) * 100
            return hp_pct < self.threshold_value if self.operator == "<" else hp_pct > self.threshold_value
            
        elif self.threshold_type == "MP" and self.threshold_value > 0:
            if not player_obj or player_obj.MAX_MP <= 0:
                return True
            mp_pct = (player_obj.MANA / player_obj.MAX_MP) * 100
            return mp_pct < self.threshold_value if self.operator == "<" else mp_pct > self.threshold_value
            
        return True

    def __repr__(self):
        if self.threshold_type != "NONE" and self.threshold_value > 0:
            return f"Skill({self.index}, {self.threshold_type} {self.operator} {self.threshold_value}%)"
        return f"Skill({self.index})"


def parse_skills_list(raw) -> list:
    result = []
    if isinstance(raw, list):
        for item in raw:
            if isinstance(item, dict):
                idx = item.get("index", 1)
                t_type = item.get("threshold_type", "NONE")
                op = item.get("operator", "<")
                val = item.get("threshold_value", 0)
                result.append(SkillConfig(idx, t_type, op, val))
            elif isinstance(item, (int, str)) and str(item).strip().isdigit():
                result.append(SkillConfig(int(item)))
            elif hasattr(item, "index"):
                result.append(SkillConfig(
                    getattr(item, "index", 1),
                    getattr(item, "threshold_type", "NONE"),
                    getattr(item, "operator", "<"),
                    getattr(item, "threshold_value", 0)
                ))
    elif isinstance(raw, str):
        try:
            parsed = json.loads(raw)
            if isinstance(parsed, list):
                return parse_skills_list(parsed)
        except Exception:
            pass
        for s in raw.split(","):
            s_clean = s.strip()
            if s_clean.isdigit() and int(s_clean) != 0:
                result.append(SkillConfig(int(s_clean)))
    
    if not result:
        result = [SkillConfig(1), SkillConfig(2), SkillConfig(3), SkillConfig(4)]
    return result


checking_locked_zone = False
async def main(cmd: Command):
    cmd.bot.checking_locked_zone = False
    cmd.bot.last_skills = []
    raw_skills = getattr(cmd.bot, "skills", None)
    skills = parse_skills_list(raw_skills)
        
    skill_index = 0
    other_skills_used = 0
    
    # Resolve dynamic properties if injected via GUI, otherwise fallback to script globals
    f_player = getattr(cmd.bot, "follow_player", None) or (follow_player if 'follow_player' in globals() else "")
    room_num = getattr(cmd.bot, "default_room_number", None) or default_room_number
    targets = getattr(cmd.bot, "targets_priority", None) or targets_priority
    
    copy_walk = getattr(cmd.bot, "copy_walk", True)
    auto_zone = getattr(cmd.bot, "auto_zone", "none")
    
    await cmd.equip_item(cmd.get_farm_class())
    await cmd.sleep(1000)

    cmd.bot.taunt_error = False
    
    def handle_message(message):
        # %xt%warning%-1%Cannot goto to player in a Locked zone.%
        if message.startswith("%") and message.endswith("%"):
            # print(f"message: {message}")
            if "locked zone" in message.lower():
                cmd.bot.checking_locked_zone = True
                
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
        print(f"[{cmd.bot.username}] goto master...")
        await cmd.goto_player(f_player)
        await cmd.sleep(200)
        if cmd.get_player_in_map(f_player):
            cmd.bot.checking_locked_zone = False
    
    async def checking_map():
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
            print(f"[{cmd.bot.username}] checking {map_name}...")
            await cmd.join_map(map_name, roomNumber=room_num)
            while cmd.is_not_in_map(map_name):
                await cmd.sleep(100)
            if cmd.get_player_in_map(f_player):
                print(f"[{cmd.bot.username}] stopped at {map_name}...")
                cmd.bot.checking_locked_zone = False
                await cmd.sleep(1000)
                break
        await goto_master()
    is_currently_taunter = False
    while(cmd.is_still_connected()):
        await cmd.sleep(200)
        if not cmd.is_player_alive():
            await cmd.sleep(200)
            continue

        # Sync dynamic settings from GUI/Bot instance
        f_player = getattr(cmd.bot, "follow_player", None) or ""
        room_num = getattr(cmd.bot, "default_room_number", None) or 9099
        targets = getattr(cmd.bot, "targets_priority", None) or ""
        copy_walk = getattr(cmd.bot, "copy_walk", True)
        auto_zone = getattr(cmd.bot, "auto_zone", "none")

        # Bounds check skill index in case skills list is modified
        if skill_index >= len(skills):
            skill_index = 0

        # Check dynamic changes in taunter flag or scroll availability
        dynamic_taunter = getattr(cmd.bot, "taunter", False)
        
        # Verify scroll availability if taunter is enabled
        has_scrolls = False
        if dynamic_taunter:
            item_enrage = cmd.get_player().get_item_inventory("Scroll of Enrage")
            if item_enrage and item_enrage.qty > 0:
                has_scrolls = True
                cmd.bot.taunt_error = False
            else:
                cmd.bot.taunt_error = True
        else:
            cmd.bot.taunt_error = False

        # Determine if the bot should be active in the taunt rotation
        should_be_active_taunter = dynamic_taunter and has_scrolls

        if should_be_active_taunter != is_currently_taunter:
            is_currently_taunter = should_be_active_taunter
            coordinator = getattr(cmd.bot, "taunt_coordinator", None)
            if is_currently_taunter:
                print(f"[{cmd.bot.username}] Enrolling in Taunt Rotation. Equipping Scroll of Enrage...")
                await cmd.equip_scroll("Scroll of Enrage")
                if coordinator:
                    coordinator.register_taunter(cmd.bot.username)
                has_5 = any(s.index == 5 for s in skills)
                if not has_5:
                    skills.append(SkillConfig(5))
            else:
                print(f"[{cmd.bot.username}] Withdrawing from Taunt Rotation.")
                if coordinator:
                    coordinator.unregister_taunter(cmd.bot.username)
                skills = [s for s in skills if s.index != 5]
            
        is_paused = getattr(cmd.bot, "is_paused", False)
        if is_paused:
            if not getattr(cmd.bot, "was_paused", False):
                cmd.bot.was_paused = True
                print(f"[{cmd.bot.username}] Pausing bot: leaving combat, waiting 1s, and jumping to current cell.")
                await cmd.leave_combat(safeLeave=False)
                await cmd.sleep(1000)
                player = cmd.get_player()
                if player:
                    await cmd.jump_cell(player.CELL, player.PAD)
            await cmd.sleep(500)
            continue
        else:
            cmd.bot.was_paused = False
        
        if getattr(cmd.bot, "checking_locked_zone", False):
            print(f"[{cmd.bot.username}] checking locked zone...")
            await checking_map()
        
        master = cmd.get_player_in_map(f_player)
        check_master_in_cell = master and master.str_frame == cmd.get_player().CELL
        
        if not check_master_in_cell and not getattr(cmd.bot, "checking_locked_zone", False):
            await goto_master()
            continue
        
        targeted_monster = cmd.get_player().getLastTarget()
        skill_mode = SkillMode.ALL
        if targeted_monster and targeted_monster.getAura('Counter Attack'):
            skill_mode = SkillMode.BUFF_ONLY
            print('buff only mode...')
        
        # Check health and MP thresholds
        player_obj = cmd.get_player()
        if skill_index >= len(skills):
            skill_index = 0

        current_skill_cfg = skills[skill_index]
        current_skill = current_skill_cfg.index
        
        # If casting taunt (skill 5), only proceed if it's our turn in the rotation
        if current_skill == 5:
            coordinator = getattr(cmd.bot, "taunt_coordinator", None)
            
            # Skip taunt if player has forbidden boss auras (Elegy of Madness or Seed Planted)
            if player_obj and (player_obj.hasAura("Elegy of Madness") or player_obj.hasAura("Seed Planted")):
                if coordinator:
                    coordinator.skip_taunt(cmd.bot.username)
                skill_index = (skill_index + 1) % len(skills)
                continue

            if coordinator:
                active_taunter = coordinator.get_active_taunter()
                if active_taunter != cmd.bot.username:
                    # Skip skill 5 this cycle
                    skill_index = (skill_index + 1) % len(skills)
                    continue
        
        # Directly check this skill's threshold condition!
        if not current_skill_cfg.check_threshold(player_obj):
            # Condition NOT met -> skip to next skill in rotation
            skill_index = (skill_index + 1) % len(skills)
            continue
        
        # Check and use auto-attack (skill 0) if available
        if cmd.bot.player.canUseSkill(0) and cmd.check_is_skill_safe(0):
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

        success = await cmd.use_skill(
            index=current_skill,
            target_monsters=targets,
            skill_mode=skill_mode
        )
        
        if success:
            last_skills = getattr(cmd.bot, "last_skills", [])
            last_skills.append(current_skill)
            if len(last_skills) > 3:
                last_skills.pop(0)
            cmd.bot.last_skills = last_skills
        
        skill_index = (skill_index + 1) % len(skills)


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