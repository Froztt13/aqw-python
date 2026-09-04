from core.bot import Bot
from core.command import Command
from abstracts.base_command import BaseCommand

class MessageCmd(BaseCommand):
    skip_delay = True
    
    def __init__(self, msg: str):
        self.msg = msg
    
    async def execute(self, bot: Bot, cmd: Command):
        pass
        
    def to_string(self):
        return f"{self.msg}"