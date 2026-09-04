from core.bot import Bot
from core.command import Command
from abstracts.base_command import BaseCommand

class WalkCmd(BaseCommand):
    
    def __init__(self, x: str, y: str, speed: int = 8):
        self.x = x
        self.y = y
        self.speed = speed
    
    async def execute(self, bot: Bot, cmd: Command):
        await bot.walk_to(self.x, self.y, self.speed)
        
    def to_string(self):
        return f"Walk : {self.x} {self.y}"