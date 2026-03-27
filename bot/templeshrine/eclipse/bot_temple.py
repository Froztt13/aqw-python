import asyncio
from bot.templeshrine.eclipse.core.config import SlaveConfig
from bot.templeshrine.eclipse.core.core_eclipse import EclipseMasterBot, EclipseSlaveBot
from core.bot import Bot
from colorama import Fore

from core.command import Command

# Requirement:
# a lot of "Scroll of Enrage", minimal 50
# 1 taunt_parity="odd" for each converge_type "sun" and "moon"
# 1 taunt_parity="even" for each converge_type "sun" and "moon"
# 2 light_gather_taunter    (tanky class)
# 1 moon_haze_taunter       
# 1 sunset_knight_taunter

server = "safiria"
slaves = [
    # LR, Arcana Concerto, Penitance
    SlaveConfig("username",
                "password",
                "Legion Revenant",
                EclipseMasterBot,
                default_target="Ascended Solstice,Blessless Deer",
                taunt_parity="odd",
                converge_type="sun",
                light_gather_taunter=False,
                ),

    # SC, Praxis, Absolution
    SlaveConfig("username",
                "password",
                "StoneCrusher",
                EclipseSlaveBot,
                default_target="Ascended Solstice",
                taunt_parity="even",
                converge_type="sun",
                light_gather_taunter=False,
                debug_mon=True
                ),

    # AP, Valiance, Penitence
    SlaveConfig("username",
                "password",
                "ArchPaladin",
                EclipseSlaveBot,
                default_target="Ascended Midnight",
                taunt_parity="odd",
                converge_type="moon",
                light_gather_taunter=True,
                moon_haze_taunter=True,
                ),

    # LOO, Arcana Concerto, Absolution
    SlaveConfig("username",
                "password",
                "Lord of Order",
                EclipseSlaveBot,
                default_target="Ascended Midnight",
                taunt_parity="even",
                converge_type="moon",
                light_gather_taunter=True,
                sunset_knight_taunter=True,
                ),
]

input_str = input("Select bot [1-4] : ")
input_int = int(input_str)
selected_slave = slaves[input_int - 1]

print(f"Bot selected : {Fore.YELLOW}{selected_slave.bot_class.__name__}{Fore.RESET}")
print(f"Account config : {Fore.YELLOW}{selected_slave.username.upper()} - {selected_slave.char_class}{Fore.RESET}")

b = Bot(
    roomNumber=9099,
    itemsDropWhiteList=[
        "Sliver of Sunlight",
        "Sliver of Moonlight",
        "Ecliptic Offering",
    ],
    showLog=True,
    showDebug=False,
    showChat=True,
    isScriptable=True,
    followPlayer=slaves[0].username.lower(),
    slavesPlayer=[slave.username for i, slave in enumerate(slaves) if i != 0],
    farmClass=selected_slave.char_class,
    respawnCellPad=["Enter", "Spawn"],
    muteSpamWarning=True
)
b.set_login_info(selected_slave.username, selected_slave.password, server)

async def run_bot(cmd: Command):
    bot_instance = selected_slave.bot_class(cmd, **selected_slave.bot_kwargs)

    await bot_instance.prepare_items()    
    if isinstance(bot_instance, EclipseMasterBot):
        await bot_instance.setup_party()
    else:
        await bot_instance.wait_party_invite()
    await bot_instance.attack_loop()

print(f"Bot: {selected_slave.bot_class.__name__}")
for param in selected_slave.bot_kwargs:
    print(f"{param}: {Fore.YELLOW}{selected_slave.bot_kwargs[param]}{Fore.RESET}")

asyncio.run(b.start_bot(run_bot))
