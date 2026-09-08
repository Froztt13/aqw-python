from core.bot import Bot
from core.command import Command
from bot.LR.core_lr import revenant_spellscroll

async def main(cmd: Command):
    await revenant_spellscroll(cmd)