class SlaveConfig:
    def __init__(self, username, password, char_class, bot_class, role, **bot_kwargs):
        self.username = username
        self.password = password
        self.char_class = char_class
        self.bot_class = bot_class
        self.role = role
        self.bot_kwargs = bot_kwargs