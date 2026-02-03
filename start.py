import importlib

from colorama import Fore
from core.bot import Bot
import commands as cmd
import asyncio

username = input("Username: ")
password = input("Password: ")
server = input("Server: ")
bot_path = input(f"Bot path (e.g., {Fore.BLUE}bot.nulgath.larvae{Fore.RESET}): ")

# Initialize bot
b = Bot(
    roomNumber=1, 
    itemsDropWhiteList=[
        "Mana Energy for Nulgath",
        "Gem of Nulgath",
        "Diamond of Nulgath",
        "Voucher of Nulgath",
        "Voucher of Nulgath (non-mem)",
        "Dark Crystal Shard",
        "Totem of Nulgath",
        "Blood Gem of the Archfiend",
        "Unidentified 13",
        "Tainted Gem",
        "Unidentified 10"
        "Void Aura"
    ], 
    showLog=True, 
    showDebug=False,
    showChat=True,
    isScriptable=True,
    followPlayer="",
    slavesPlayer=[],
    # farmClass="Legion Revenant",
    # soloClass="Void HighLord",
    autoRelogin=True,
    muteSpamWarning=True
)
b.set_login_info(username, password, server)

bot_path = bot_path
try:
    bot_class = importlib.import_module(bot_path)
    print(f"starting bot: {bot_path.split('.')[-1]}")
    asyncio.run(b.start_bot(bot_class.main))
except ModuleNotFoundError as e:
    print(f"Error: {e}")
