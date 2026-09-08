from core.bot import Bot
from core.command import Command
from bot.LR.core_lr import conquest_wreath

async def main(cmd: Command):
    await conquest_wreath(cmd)