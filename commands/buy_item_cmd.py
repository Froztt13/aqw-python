from core.bot import Bot
from core.command import Command
from abstracts.base_command import BaseCommand
import asyncio

class BuyItemCmd(BaseCommand):
    
    def __init__(self, item_name: str, shop_id: int, qty: int = 1):
        self.item_name = item_name
        self.shop_id = shop_id
        self.qty = qty
    
    async def execute(self, bot: Bot, cmd: Command):  
        await cmd.buy_item(item_name=self.item_name, shop_id=self.shop_id, qty=self.qty)
        
    def to_string(self):
        return f"Buy : {self.item_name}"