from core.bot import Bot
from core.command import Command
from abstracts.base_command import BaseCommand
from colorama import Fore 

class TurnInQuestCmd(BaseCommand):
    
    def __init__(self, quest_id: int, item_id: int = -1, turn_in_count: int = 1):
        self.quest_id = quest_id
        self.item_id = item_id
        self.turn_in_count = turn_in_count
    
    async def execute(self, bot: Bot, cmd: Command):
        bot.turn_in_quest(self.quest_id, self.item_id, self.turn_in_count)
        
    def to_string(self):
        return f"Turn in quest : {self.quest_id}^{self.item_id}"