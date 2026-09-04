from core.bot import Bot
from core.command import Command
from abstracts.base_command import BaseCommand

class IsInBankCmd(BaseCommand):
    skip_delay = True
    
    def __init__(self, itemName: str, itemQty: int = 1, operator: str = ">="):
        self.itemName = itemName
        self.itemQty = itemQty
        self.operator = operator
        self.inBank = [False, 0]
    
    async def execute(self, bot: Bot, cmd: Command):
        self.inBank = bot.player.isInBank(self.itemName, self.itemQty, self.operator)
        if(self.inBank[0] == False):
            bot.index += 1
        
    def to_string(self):
        return f"Is in bank : {self.itemName} {self.inBank[1]} {self.operator} {self.itemQty} "