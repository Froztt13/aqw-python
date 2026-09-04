from abc import ABC, abstractmethod
from core.bot import Bot
from core.command import Command

class BaseCommand(ABC):
    
    skip_delay = False
    
    @abstractmethod
    async def execute(self, bot: Bot, cmd: Command):
        pass
        
    @abstractmethod
    def to_string(self):
        return "Command"