"""
this just example, not actually do malgor
"""


import json
from core.bot import Bot
from core.command import Command
from colorama import Fore

speaker_counter = 0

async def main(bot: Bot):
    cmd = Command(bot)
    private_room_number = 999999
    
    await cmd.equip_scroll("Scroll of Enrage")

    await cmd.ensure_accept_quest(8154)
    await cmd.join_map("ultraspeaker", private_room_number)

    while not cmd.wait_count_player(4):
        await cmd.sleep(100)
    await cmd.jump_cell("Boss", "Left")

    skill_list = [0,2,0,3,4,1]
    skill_index = 0

    bot.subscribe(message_handler)

    while cmd.is_monster_alive("The First Speaker") and cmd.is_still_connected():
        mons_hp = cmd.get_monster_hp("The First Speaker")
        print("my hp:", cmd.bot.player.CURRENT_HP,"/", cmd.bot.player.MAX_HP)
        if mons_hp > -1:
            print("The First Speaker:", mons_hp)
        
        if cmd.hp_below_percentage(60):
            equipped_class = cmd.get_equipped_class()
            if equipped_class:
                class_name = equipped_class.item_name.lower()
                if class_name == "archpaladin" or class_name == "lord of order":
                    await cmd.use_skill(2)
                elif class_name == "legion revenant":
                    await cmd.use_skill(3)

        await cmd.use_skill(5)
        await cmd.use_skill(skill_list[skill_index], "The First Speaker")
        skill_index += 1
        if skill_index >= len(skill_list):
            skill_index = 0
        await cmd.sleep(500)
    
    await cmd.join_map("battleon", private_room_number)

    print("finished ultra speaker")
    await cmd.sleep(100000)


def message_handler(message):
    global speaker_counter
    if message:
        if is_valid_json(message):
            data = json.loads(message)
        try:
            data = data["b"]["o"]
        except:
            return
        cmd = data["cmd"]
        if cmd == "ct":
            anims = data.get("anims")
            if anims:
                for anim in anims:
                    msg = anim.get("msg")
                    if msg:
                        print(msg)
                        if "truth" in msg or "listen" in msg:
                            whoTaunt, whoZone, whatZone, delay = malgorHandler()
                            print(speaker_counter)
        elif cmd == "event":
            print(Fore.GREEN + data["args"]["zoneSet"] + Fore.WHITE)

def malgorHandler():
    global speaker_counter
    if speaker_counter == 0:
        return ("Legion Revenant", None, None, 0)
    elif speaker_counter == 1:
        return ("Lord Of Order", "Verus DoomKnight", "IN", 0)
    elif speaker_counter == 2:
        return ("ArchPaladin", "Verus DoomKnight", "OUT", 0)
    elif speaker_counter == 3 or speaker_counter == 7:
        return ("Lord Of Order", None, None, 500)
    elif speaker_counter == 4:
        return (None, "Legion Revenant", "IN", 0)
    elif speaker_counter == 5:
        return ("Legion Revenant", "Legion Revenant", "OUT", 500)
    elif speaker_counter == 8:
        return (None, "ArchPaladin", "IN", 0)
    elif speaker_counter == 9:
        return ("ArchPaladin", "ArchPaladin", "OUT", 0)
    elif speaker_counter == 10:
        return ("Legion Revenant", None, None, 500)
    elif speaker_counter == 11:
        return (None, "Lord Of Order", "IN", 0)
    elif speaker_counter == 12:
        return ("Lord Of Order", "Lord Of Order", "OUT", 500)
    elif speaker_counter == 14:
        return ("Legion Revenant", None, None, 0)
    elif speaker_counter == 15:
        speaker_counter = 1  # Resetting speaker_counter to 1
        return ("Lord Of Order", "Verus DoomKnight", "IN", 500)
    
    return (None, None, None, 0)

def is_valid_json(s):
    try:
        json.loads(s)
        return True
    except json.JSONDecodeError:
        return False