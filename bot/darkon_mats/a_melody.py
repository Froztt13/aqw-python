from bot.darkon_mats.core_darkon_mats import a_melody
from core.bot import Bot
from core.commands import Command

async def main(bot: Bot):
    cmd = Command(bot)

    await a_melody(cmd, 300)