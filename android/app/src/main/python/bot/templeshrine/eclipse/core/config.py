from .core_eclipse import EclipseMasterBot, EclipseSlaveBot

class SlaveConfig:
    def __init__(self, username, password, char_class, bot_class, **bot_kwargs):
        self.username = username
        self.password = password
        self.char_class = char_class
        self.bot_class = bot_class
        self.bot_kwargs = bot_kwargs
