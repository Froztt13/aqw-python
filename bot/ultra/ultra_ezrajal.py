from core.bot import Bot
from core.command import Command
import json

counter_attack = False
async def main(cmd: Command):
    global counter_attack
    private_room_number = 1231

    if cmd.bot.soloClass:
        await cmd.equip_item(cmd.bot.soloClass)
        await cmd.equip_item_by_enhancement(enh_pattern_id=29) # 29 for penitence
        await cmd.equip_item_by_enhancement(enh_pattern_id=10) # 10 for valiance
    
    await cmd.ensure_accept_quest(8152)
    await cmd.join_map("ultraezrajal", private_room_number)

    while not cmd.wait_count_player(4):
        await cmd.sleep(100)

    await cmd.jump_cell("r2", "Left")
    skill_list = [0,1,2,0,3,4]
    skill_index = 0

    cmd.bot.subscribe(message_handler)

    while cmd.is_monster_alive("Ultra Ezrajal") and cmd.is_still_connected():
        mons_hp = cmd.get_monster_hp("Ultra Ezrajal")
        # print("my hp:", cmd.bot.player.CURRENT_HP,"/", cmd.bot.player.MAX_HP)
        if mons_hp > -1:
            print(f"Ultra Ezrajal: {mons_hp} : {cmd.get_monster_hp_percentage('Ultra Ezrajal')}%")
        if cmd.hp_below_percentage(60):
            equipped_class = cmd.get_equipped_class()
            if equipped_class:
                class_name = equipped_class.item_name.lower()
                if class_name == "archpaladin" or class_name == "lord of order":
                    await cmd.use_skill(2)
                elif class_name == "legion revenant":
                    await cmd.use_skill(3)
        if counter_attack:
            await cmd.sleep(100)
            continue
        await cmd.use_skill(skill_list[skill_index], "Ultra Ezrajal")
        skill_index += 1
        if skill_index >= len(skill_list):
            skill_index = 0
        await cmd.sleep(100)
    
    await cmd.join_map("battleon", private_room_number)
    await cmd.turn_in_quest(8152)

    print("finished ultra ezrajal")
    await cmd.sleep(100000)

def message_handler(message):
    global counter_attack
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
            a = data.get("a")
            if anims:
                for anim in anims:
                    msg = anim.get("msg")
                    if msg:
                        if "prepares a counter attack" in msg:
                            counter_attack = True
                            print("Counter Attack", counter_attack)
            if a:
                for action in a:
                    if action.get('cmd') == 'aura-':
                        removed_aura = action.get('aura', {}).get('nam')
                        if "Counter Attack" in removed_aura:
                            counter_attack = False
                            print("Counter Attack", counter_attack)

def is_valid_json(s):
    try:
        json.loads(s)
        return True
    except json.JSONDecodeError:
        return False