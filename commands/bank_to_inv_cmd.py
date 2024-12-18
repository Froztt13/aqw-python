from core.bot import Bot
from abstracts.command import Command
import asyncio

class BankToInvCmd(Command):
    
    def __init__(self, itemName: str):
        self.itemName = itemName
            
    async def execute(self, bot: Bot):
        item = bot.player.get_item_bank(self.itemName)        
        if item:
            packet = f"%xt%zm%bankToInv%{bot.areaId}%{item.item_id}%{item.char_item_id}%"
            bot.write_message(packet)
            is_exist = False
            for itemInv in bot.player.INVENTORY:
                if itemInv.item_name == item.item_name:
                    bot.player.INVENTORY.remove(itemInv)
                    bot.player.INVENTORY.append(item)
                    is_exist = True
                    break
            if not is_exist:
                bot.player.INVENTORY.append(item)
            for itemBank in bot.player.BANK:
                if itemBank.item_name == item.item_name:
                    bot.player.BANK.remove(itemBank)
                    break
            await asyncio.sleep(1)
        
    def to_string(self):
        return f"Bank to inv : {self.itemName}"