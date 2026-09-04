from core.bot import Bot
from core.command import Command
from abstracts.base_command import BaseCommand

class IsNotInMapCmd(BaseCommand):
    skip_delay = True
    
    def __init__(self, mapName: str):
        self.mapName = mapName
    
    async def execute(self, bot: Bot, cmd: Command):
        if(self.mapName.lower() == bot.strMapName.lower()):
            bot.index += 1
        
    def to_string(self):
        return f"Is not in map : {self.mapName}"