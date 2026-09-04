from core.bot import Bot
from core.command import Command
from abstracts.base_command import BaseCommand

class WaitPlayerCountCmd(BaseCommand):
    
    def __init__(self, playerCount: int):
        self.playerCount = playerCount
    
    async def execute(self, bot: Bot, cmd: Command):
        if len(bot.user_ids) < self.playerCount:
            bot.index -= 1
        
    def to_string(self):
        return f"Waiting for : [{self.playerCount}] player(s)"