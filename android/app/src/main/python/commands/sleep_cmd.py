from core.bot import Bot
from core.command import Command
from abstracts.base_command import BaseCommand
import asyncio

class SleepCmd(BaseCommand):
    skip_delay = True
    
    def __init__(self, milliseconds: int):
        self.milliseconds = milliseconds
    
    async def execute(self, bot: Bot, cmd: Command):
        await asyncio.sleep(self.milliseconds/1000)
        
    def to_string(self):
        return f"Sleep {self.milliseconds}ms"