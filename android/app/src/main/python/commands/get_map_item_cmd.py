from core.bot import Bot
from core.command import Command
from abstracts.base_command import BaseCommand

class GetMapItemCmd(BaseCommand):
    
    def __init__(self, map_item_id: int, qty: int = 1):
        self.map_item_id = map_item_id
        self.qty = qty

    async def execute(self, bot: Bot, cmd: Command):
        await cmd.get_map_item(self.map_item_id, self.qty)
        
    def to_string(self):
        return f"Get map item: {self.map_item_id}"