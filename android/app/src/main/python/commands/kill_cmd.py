from core.bot import Bot
from core.command import Command
from abstracts.base_command import BaseCommand
from commands import UseSkillCmd

class KillCmd(BaseCommand):
    
    def __init__(self, monsterName: []):
        self.monsterName = monsterName
    
    async def execute(self, bot: Bot, cmd: Command):
        pass
        
    def to_string(self):
        return f"Kill : {self.monsterName}"