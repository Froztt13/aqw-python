from core.bot import Bot
import commands as cmd
from core.command import Command

async def hunt_item(
        cmd: Command,
        item_name: str, 
        item_qty: int, 
        map_name: str, 
        cell: str = None, 
        pad: str = "Left", 
        room_number: int = None, 
        monster_name: str = "*",
        most_monster: bool = False,
        farming_logger: bool = False,
        hunt: bool = False,
        skill_list: list[int] = [0,1,2,0,3,4],
        is_temp: bool = False,
    ):
    if cmd.is_in_bank(item_name):
        await cmd.bank_to_inv(item_name)

    if (cmd.is_in_inventory(item_name, item_qty, operator=">=") or cmd.is_in_inventory(item_name, item_qty, operator=">=", isTemp=True)):
        return

    cmd.add_drop(item_name)
    
    while cmd.is_not_in_map(map_name):
        await cmd.join_map(map_name, room_number)
        await cmd.sleep(1000)

    if cell:
        hunt = False
        while cmd.is_not_in_cell(cell):
            await cmd.jump_cell(cell, pad)
            await cmd.sleep(1000)
    else:
        await cmd.jump_to_monster(monster_name, most_monster)

    if farming_logger:
        cmd.farming_logger(item_name, item_qty, is_temp)

    skill_list = skill_list
    skill_index = 0

    while cmd.is_still_connected():
        if cmd.is_in_inventory(item_name, item_qty, operator=">=") or cmd.is_in_inventory(item_name, item_qty, operator=">=", isTemp=True):
            await cmd.leave_combat()
            break
        playerclass = cmd.get_equipped_class()
        playerclass = playerclass.item_name if playerclass else ""
        if "chrono shadow" in playerclass.lower():
            await cmd.wait_use_skill(skill_list[skill_index])
        else:
            await cmd.use_skill(skill_list[skill_index], monster_name, hunt)
        skill_index += 1
        if skill_index >= len(skill_list):
            skill_index = 0
        await cmd.sleep(100)
    return

async def kill_quest(
        cmd: Command,
        quest_id: int,
        map_name: str, 
        monster_name: str = "*",
        room_number: int = None, 
        hunt: bool = False
    ):
    await cmd.ensure_accept_quest(quest_id)
    
    if cmd.can_turnin_quest(quest_id):
        await cmd.ensure_turn_in_quest(quest_id)
        return
    
    if cmd.is_not_in_map(map_name):
        await cmd.join_map(map_name, room_number)
    
    await cmd.jump_to_monster(monster_name)

    while cmd.is_still_connected():
        if cmd.can_turnin_quest(quest_id):
            await cmd.leave_combat()
            await cmd.ensure_turn_in_quest(quest_id)
            return
        
        await attack_script(cmd, monster_name, hunt)

async def quest_item_req(cmd: Command, map_name: str, item_name: str, qty: int = 1, monster: str = "*", is_temp: bool = True):    
    if cmd.is_not_in_map(map_name):
        await cmd.join_map(map_name)

    while cmd.is_still_connected():
        if cmd.is_in_inventory(item_name, qty, operator=">=", isTemp=is_temp):
            cmd.leave_combat()
            return
        await attack_script(cmd, monster)

        
async def attack_script(cmd: Command, monster_name: str = "*", hunt: bool = False):
    await cmd.use_skill(0, monster_name, hunt=hunt)
    await cmd.use_skill(1, monster_name, hunt=hunt)
    await cmd.use_skill(2, monster_name, hunt=hunt)
    await cmd.use_skill(0, monster_name, hunt=hunt)
    await cmd.use_skill(3, monster_name, hunt=hunt)
    await cmd.use_skill(4, monster_name, hunt=hunt)


def hunt_item_cmds(
        item_name: str, 
        item_qty: int, 
        map_name: str, 
        cell: str = None, 
        pad: str = "Left", 
        room_number: int = None, 
        monster_name: str = "*",
        most_monster: bool = False,
    ):
    label_done = f"Hunt for {item_name} [{item_qty}x] is done"
    lebel_farming = f"Farming for {item_name} [{item_qty}x]"
    if cell:
        jumpcmd = cmd.JumpCmd(cell, pad)
    else:
        jumpcmd = cmd.HuntMonsterCmd(monster_name, most_monster)
    return [
        # Check is item in bank
        cmd.IsInBankCmd(item_name),
        cmd.BankToInvCmd(item_name),
        
        # Check is item qty already fullfiled
        cmd.IsInInvCmd(item_name, item_qty, operator=">="),
        cmd.ToLabelCmd(label_done),
        cmd.IsInInvCmd(item_name, item_qty, operator=">=", isTemp=True),
        cmd.ToLabelCmd(label_done),
        
        # Farming items
        cmd.IsNotInMapCmd(map_name),
        cmd.JoinMapCmd(map_name, room_number),
        jumpcmd,
        cmd.LabelCmd(lebel_farming),
        cmd.IsInInvCmd(item_name, item_qty, operator=">="),
        cmd.ToLabelCmd(label_done),
        cmd.IsInInvCmd(item_name, item_qty, operator=">=", isTemp=True),
        cmd.ToLabelCmd(label_done),
        *attack(monster_name),
        cmd.ToLabelCmd(lebel_farming),
        
        cmd.LabelCmd(label_done),
        cmd.SleepCmd(1000)
    ]

def hunt_monster_quest_temp_item(
        quest_id: int,
        map_name: str, 
        room_number: int = None, 
        monster_name: str = "*",
        most_monster: bool = False,
    ):
    """this function is used to do a quest required only one kind of temp item"""
    label_done = f"Hunt for quest [{quest_id}] is done"
    lebel_farming = f"Hunt for quest [{quest_id}]"
    label_stop = f"stopping quest {quest_id}"
    return [
        cmd.AcceptQuestCmd(quest_id),
        cmd.SleepCmd(1000),
        cmd.QuestNotInProgressCmd(quest_id),
        cmd.ToLabelCmd(label_stop),
        
        # Check is item qty already fullfiled
        cmd.CanTurnInQuestCmd(quest_id),
        cmd.ToLabelCmd(label_done),
        
        # Farming items
        cmd.IsNotInMapCmd(map_name),
        cmd.JoinMapCmd(map_name, room_number),
        cmd.HuntMonsterCmd(monster_name, most_monster),
        cmd.LabelCmd(lebel_farming),
        cmd.CanTurnInQuestCmd(quest_id),
        cmd.ToLabelCmd(label_done),
        *attack(monster_name),
        cmd.ToLabelCmd(lebel_farming),
        
        cmd.LabelCmd(label_done),
        cmd.TurnInQuestCmd(quest_id),
        cmd.LabelCmd(label_stop),
        cmd.SleepCmd(1000)
    ]
    
def attack(monster_name = "*"):
    return [
        cmd.UseSkillCmd(0, monster_name),
        cmd.UseSkillCmd(1, monster_name),
        cmd.UseSkillCmd(2, monster_name),
        cmd.UseSkillCmd(0, monster_name),
        cmd.UseSkillCmd(3, monster_name),
        cmd.UseSkillCmd(4, monster_name),
    ]

def attack_len():
    return len(attack())