from core.bot import Bot
from core.command import Command
from abstracts.base_command import BaseCommand
from colorama import Fore

class StopBotCmd(BaseCommand):
    
    def __init__(self, msg: str = ""):
        self.msg = msg
    
    async def execute(self, bot: Bot, cmd: Command):
        print(Fore.RED + self.msg + Fore.RESET)
        bot.stop_bot()
        
    def to_string(self):
        return "Stop bot"