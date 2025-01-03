from core.bot import Bot
from abstracts.command import Command
from model.monster import Monster

# Command for search monster and auto jump cell to the monster
class HuntMonsterCmd(Command):
    
    def __init__(self, monsterName: str, mostMonsters: bool = False):
        self.monsterName = monsterName
        self.mostMonsters = mostMonsters
    
    async def execute(self, bot: Bot):
        # Check if monster in current cell is exist and alive
        for monster in bot.monsters:
            if monster.mon_name.lower() == self.monsterName.lower() \
                    and monster.is_alive \
                    and bot.player.CELL == monster.frame:
                return

        # Hunt monster in other cell
        if self.mostMonsters:
            cell = bot.find_best_cell(self.monsterName)
            if cell:
                bot.jump_cell(cell, "Left")
                return
        for monster in bot.monsters:
            if monster.mon_name.lower() == self.monsterName.lower() \
                    and monster.is_alive \
                    and bot.player.CELL != monster.frame:
                # TODO need to handle the rigth pad
                bot.jump_cell(monster.frame, "Left")
                return
        
    def to_string(self):
        return f"Hunt for : {self.monsterName}"
