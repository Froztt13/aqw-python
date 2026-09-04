from core.bot import Bot
from core.command import Command
from abstracts.base_command import BaseCommand

class CanTurnInQuestCmd(BaseCommand):
    skip_delay = True
    
    def __init__(self, questId: int):
        self.questId = questId

    async def execute(self, bot: Bot, cmd: Command):
        if(bot.can_turn_in_quest(self.questId) == False):
            bot.index += 1
        
    def to_string(self):
        return f"Can turn in quest: {self.questId}"