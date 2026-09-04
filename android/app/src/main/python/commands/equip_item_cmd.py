from core.bot import Bot
from core.command import Command
from abstracts.base_command import BaseCommand
import asyncio

class EquipItemCmd(BaseCommand):
    
    def __init__(self, item_name: str):
        self.item_name = item_name
    
    async def execute(self, bot: Bot, cmd: Command):
        await cmd.equip_item(self.item_name)
        
    def to_string(self):
        return f"Equip item : {self.item_name}"