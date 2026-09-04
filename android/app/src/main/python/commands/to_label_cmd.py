from core.bot import Bot
from core.command import Command
from abstracts.base_command import BaseCommand

class ToLabelCmd(BaseCommand):
    skip_delay = True
    
    def __init__(self, label: str):
        self.label = label.upper()
    
    async def execute(self, bot: Bot, cmd: Command):
        for i, cmd in enumerate(bot.cmds):
            try:
                if cmd.to_string() == f"[{self.label}]":
                    bot.index = i
            except:
                print(f'err: {cmd.__class__.__name__} dont hv to_string() method')
                pass
        
    def to_string(self):
        return f"To label : [{self.label}]"