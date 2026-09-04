from core.bot import Bot
from core.command import Command
from abstracts.base_command import BaseCommand

class DownIndexCmd(BaseCommand):
    skip_delay = True
    
    def __init__(self, value: int):
        self.value = value
    
    async def execute(self, bot: Bot, cmd: Command):
        bot.index += self.value-1
        
    def to_string(self):
        # return f"Down Index : {self.value}"
        return None