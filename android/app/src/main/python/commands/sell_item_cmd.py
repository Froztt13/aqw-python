from core.bot import Bot
from core.command import Command
from abstracts.base_command import BaseCommand
import asyncio

class SellItemCmd(BaseCommand):
    
    def __init__(self, item_name: str, qty: int = 1):
        self.item_name = item_name
        self.qty = qty = qty
    
    async def execute(self, bot: Bot, cmd: Command):
        await cmd.sell_item(self.item_name, self.qty)
        
    def to_string(self):
        return f"Sell : {self.item_name}"