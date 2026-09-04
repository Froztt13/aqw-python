from core.bot import Bot
from core.command import Command
from abstracts.base_command import BaseCommand
from colorama import Fore 

class AcceptQuestCmd(BaseCommand):
    
    def __init__(self, quest_id: int):
        self.quest_id = quest_id
    
    async def execute(self, bot: Bot, cmd: Command):
        bot.accept_quest(self.quest_id)
        
    def to_string(self):
        return f"Accept quest : {self.quest_id}"