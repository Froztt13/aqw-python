from core.bot import Bot
from core.command import Command
from abstracts.base_command import BaseCommand
from colorama import Fore 

class StartAggroCmd(BaseCommand):
    
    def __init__(self, mon_ids: []):
        self.mon_ids = mon_ids
    
    async def execute(self, bot: Bot, cmd: Command):
        cmd.start_aggro(self.mon_ids)
        
    def to_string(self):
        return f"Start aggro : {self.mon_ids}"