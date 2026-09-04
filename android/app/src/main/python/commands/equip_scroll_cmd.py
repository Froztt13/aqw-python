from core.bot import Bot
from core.command import Command
from model.inventory import ScrollType
from abstracts.base_command import BaseCommand
import asyncio

class EquipScrollCmd(BaseCommand):
    
    #item_type: scroll, elixir, potion
    def __init__(self, item_name: str, item_type: ScrollType = ScrollType.SCROLL):
        self.item_name = item_name
        self.item_type = item_type
    
    async def execute(self, bot: Bot, cmd: Command):
        await cmd.equip_scroll(self.item_name, self.item_type)
        
    def to_string(self):
        return f"Equip scroll : {self.item_name}"