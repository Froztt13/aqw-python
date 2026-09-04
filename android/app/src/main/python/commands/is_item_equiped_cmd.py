from core.bot import Bot
from core.command import Command
from abstracts.base_command import BaseCommand

class IsItemEquipedCmd(BaseCommand):
    skip_delay = True
    
    def __init__(self, item_name: str):
        self.item_name = item_name
    
    async def execute(self, bot: Bot, cmd: Command):
        item = bot.player.get_item_inventory(self.item_name)
        if not item or not item.is_equipped:
            bot.index += 1
        
    def to_string(self):
        return f"Is item equiped : {self.item_name}"