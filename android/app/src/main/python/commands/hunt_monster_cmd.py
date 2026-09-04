from core.bot import Bot
from core.command import Command
from abstracts.base_command import BaseCommand
from model import Monster

# Command for search monster and auto jump cell to the monster
# JUST JUMP
class HuntMonsterCmd(BaseCommand):
    
    def __init__(self, monsterName: str, byMostMonster: bool = False, byAliveMonster: bool = True):
        self.monsterName = monsterName
        self.byMostMonster = byMostMonster
        self.byAliveMonster = byAliveMonster
    
    async def execute(self, bot: Bot, cmd: Command):
        await cmd.jump_to_monster(self.monsterName, self.byMostMonster, self.byAliveMonster)
        
    def to_string(self):
        return f"Hunt for : {self.monsterName}"