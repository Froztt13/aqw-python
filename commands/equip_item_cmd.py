from core.bot import Bot
from abstracts.command import Command
import time

class EquipItemCmd(Command):
    
    def __init__(self, item_name: str):
        self.item_name = item_name
    
    def execute(self, bot: Bot):
        bot.ensure_leave_from_combat()
        
        is_equipped = False
        s_type = None
        for item in bot.player.INVENTORY:
            if item.item_name == self.item_name.lower():
                packet = f"%xt%zm%equipItem%{bot.areaId}%{item.item_id}%"
                bot.write_message(packet)
                is_equipped = True
                s_type = item.s_type
                item.is_equipped = is_equipped
                time.sleep(0.5)
                break
        # Update unequip previous item
        if is_equipped and s_type:
            for item in bot.player.INVENTORY:
                if item.s_type == s_type and item.is_equipped and not item.item_name == self.item_name.lower():
                    item.is_equipped = False
                    break
        
    def to_string(self):
        return f"Equip item : {self.item_name}"