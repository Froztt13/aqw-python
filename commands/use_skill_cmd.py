from core.bot import Bot
from abstracts.command import Command
from model.monster import Monster
import asyncio

class UseSkillCmd(Command):
    
    skip_delay = True
    
    def __init__(self, index: int = 0, target_monsters: str = "*", hunt: bool = False, scroll_id: int = 0):
        self.index = index
        self.target_monsters = target_monsters
    
    def createSkill(self, index: int, target_monsters: str = "*"):
        self.index = index
        if target_monsters != "*":
            self.target_monsters = target_monsters
        return UseSkillCmd(index, self.target_monsters)
    
    async def execute(self, bot: Bot):
        if not bot.player.canUseSkill(int(self.index)) and not bot.canuseskill:
            bot.debug(f"Skill {self.index} not ready yet")
            return

        skill = bot.player.SKILLS[int(self.index)]
        bot.skillAnim = skill["anim"]
        bot.skillNumber = self.index
        max_target = int(skill.get("tgtMax", 1))

        if skill["tgt"] == "h": 
            priority_monsters_id = []
            cell_monsters_id = [mon.mon_map_id for mon in bot.monsters if mon.frame == bot.player.CELL and mon.is_alive]
            final_ids = []
            if self.target_monsters != "*":
                # Mapping priority_monsters_id
                for target_monster in self.target_monsters.split(','):
                    for monster in bot.monsters:
                        if target_monster.startswith('id.'):
                            target_monster_id = target_monster.split('.')[1]
                            if monster.mon_map_id == target_monster_id \
                                    and monster.frame == bot.player.CELL \
                                    and monster.is_alive:
                                priority_monsters_id.append(monster.mon_map_id)
                                break
                        else:
                            if monster.mon_name.lower() == target_monster.lower() \
                                    and monster.frame == bot.player.CELL \
                                    and monster.is_alive:
                                priority_monsters_id.append(monster.mon_map_id)
                                break
                # Check if the first index is one of the priority targets
                if len(priority_monsters_id) > 0:
                    if not cell_monsters_id[0] in priority_monsters_id:
                        cell_monsters_id.pop(0)
                        cell_monsters_id.insert(0, priority_monsters_id[0])
                # Remove duplicate monster id and keep the order
                seen = set()
                for monster_id in cell_monsters_id:
                    if monster_id not in seen:
                        final_ids.append(monster_id)
                        seen.add(monster_id)
            else:
                final_ids = cell_monsters_id
            # print(f"tgt: {final_ids}")
            bot.use_skill_to_monster("a" if bot.skillNumber == 0 else bot.skillNumber, final_ids, max_target)
        elif skill["tgt"] == "f":
            bot.use_skill_to_player(bot.skillNumber, max_target)
        bot.canuseskill = False
        await asyncio.sleep(1)
        # bot.player.delayAllSkills(except_skill = self.index) # delay from cdreduction
        
    def to_string(self):
        # return f"UseSkill : {self.index}"
        return None
