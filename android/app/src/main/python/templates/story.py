from core.bot import Bot
import commands as cmd
from .general import get_map_items
from abc import ABC, abstractmethod

skill = cmd.UseSkillCmd()

class QuestReq(ABC):
    @abstractmethod
    def to_cmds(self):
        return []

class QuestItemReq(QuestReq):
    def __init__(self, item_name, qty: int = 1, monster: str = "*", is_temp: bool = True):
        self.item_name = item_name
        self.qty = qty
        self.monster = monster
        self.is_temp = is_temp
        
    def to_cmds(self):
        return [
            cmd.IsInInvCmd(self.item_name, self.qty, operator=">=", isTemp=self.is_temp),
            cmd.DownIndexCmd(_attack_monster_len() + 3),
            cmd.HuntMonsterCmd(self.monster),
            *_attack_monster(self.monster),
            cmd.UpIndexCmd(_attack_monster_len() + 3),
            cmd.SleepCmd(500),
            cmd.JumpCmd('Enter', 'Spawn'),
        ]
        
class QuestMapItemReq(QuestReq):
    def __init__(self, map_item_id: int, map_item_name: str = None, qty: int = 1):
        self.map_item_name = map_item_name
        self.map_item_id = map_item_id
        self.qty = qty
        
    def get_items(self):
        return [*get_map_items(self.map_item_id, self.qty)]
    
    def to_cmds(self):
        map_item_cmds_list = self.get_items()
        return [
            *map_item_cmds_list,
            cmd.IsInInvCmd(self.map_item_name, self.qty, operator="<", isTemp=True),
            cmd.UpIndexCmd(len(map_item_cmds_list) + 1)
        ]

class QuestSingleReq(QuestReq):
    quest_id = None
    
    def __init__(self, monster: str = "*"):
        self.monster = monster
    
    def set_quest_id(self, quest_id: int):
        self.quest_id = quest_id    
    
    def to_cmds(self):
        return [
            cmd.HuntMonsterCmd(self.monster),
            *_attack_monster(self.monster),
            cmd.CannotTurnInQuestCmd(self.quest_id),
            cmd.UpIndexCmd(_attack_monster_len() + 2),
            cmd.SleepCmd(500)
        ]
    
# Do a story quest in one map
def do_story_quest(
    quest_id: int,
    quest_reqs
):
    quest_reqs_cmds = [] # List of QuestReq
    for req in quest_reqs:
        if req.__class__ == QuestSingleReq:
            req.set_quest_id(quest_id)
        quest_reqs_cmds.extend(req.to_cmds())
    label_cleared = f"Quest {quest_id} is cleared"
    return [
        cmd.AcceptQuestCmd(quest_id),
        cmd.SleepCmd(500),
        cmd.QuestNotInProgressCmd(quest_id),
        cmd.ToLabelCmd(label_cleared),
        *quest_reqs_cmds,
        cmd.TurnInQuestCmd(quest_id),
        cmd.LabelCmd(label_cleared),
    ]
    
def _attack_monster(monster_name: str = "*"):
    return [
        skill.createSkill(0, monster_name),
        skill.createSkill(1),
        skill.createSkill(2),
        skill.createSkill(0),
        skill.createSkill(3),
        skill.createSkill(4),
    ]
    
def _attack_monster_len():
    return len(_attack_monster())