from core.bot import Bot
from core.command import Command
from abstracts.base_command import BaseCommand

class JoinHouseCmd(BaseCommand):
    
    def __init__(self, houseName: str, safeLeave: bool = True):
        self.houseName = houseName
        self.safeLeave = safeLeave
    
    async def execute(self, bot: Bot, cmd: Command):
        await cmd.join_house(self.houseName, self.safeLeave)
        
    def to_string(self):
        return f"Goto house : {self.houseName}"