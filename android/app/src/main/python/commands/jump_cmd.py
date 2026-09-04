from core.bot import Bot
from core.command import Command
from abstracts.base_command import BaseCommand

class JumpCmd(BaseCommand):
    
    def __init__(self, cell: str, pad: str):
        self.cell = cell
        self.pad = pad
    
    async def execute(self, bot: Bot, cmd: Command):
        await cmd.jump_cell(self.cell, self.pad)
        
    def to_string(self):
        return f"Jump : {self.cell} {self.pad}"