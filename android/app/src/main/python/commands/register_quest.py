from core.bot import Bot
from core.command import Command
from abstracts.base_command import BaseCommand

class RegisterQuestCmd(BaseCommand):
    
    def __init__(self, questId: int):
        self.questId = questId
    
    async def execute(self, bot: Bot, cmd: Command):
        if self.questId not in bot.registered_auto_quest_ids:
            bot.registered_auto_quest_ids.append(self.questId)
            bot.accept_quest(self.questId)
        
    def to_string(self):
        return f"Register quest : {self.questId}"