from core.bot import Bot
from core.command import Command
from abstracts.base_command import BaseCommand
from colorama import Fore 

class StopAggroCmd(BaseCommand):
    
    def __init__(self):
        pass
    
    async def execute(self, bot: Bot, cmd: Command):
        cmd.stop_aggro()
        
    def to_string(self):
        return f"Stop aggro"