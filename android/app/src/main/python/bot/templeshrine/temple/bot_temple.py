import asyncio

from bot.templeshrine.temple.core.core_temple import MidnightSunBot, SolsticeMoonBot
from bot.templeshrine.temple.core.config import SlaveConfig
from core.command import Command
from core.bot import Bot
from colorama import Fore

# Choose one
temple_bot = SolsticeMoonBot
# temple_bot = MidnightSunBot

server = "yokai (sea)"
slaves = [
    SlaveConfig("username", "password", # party leader
                "Legion Revenant", 
                temple_bot,
                role="master", 
                is_taunter=False),
    
    SlaveConfig("username", "password", 
                "StoneCrusher", 
                temple_bot,
                role="slave",
                is_taunter=False),
    
    SlaveConfig("username", "password", 
                "ArchPaladin", 
                temple_bot,
                role="slave",
                is_taunter=True), # just need 1 taunter
    
    SlaveConfig("username", "password", 
                "Lord of Order", 
                temple_bot,
                role="slave",
                is_taunter=False),
]

def main():
    input_str = input("Select bot [1-4] : ")
    input_int = int(input_str)
    selected_slave = slaves[input_int - 1]

    print(f"Bot selected : {Fore.YELLOW}{selected_slave.bot_class.__name__}{Fore.RESET}")
    print(f"Account config : {Fore.YELLOW}{selected_slave.username.upper()} - {selected_slave.char_class}{Fore.RESET}")

    # Inisialisasi bot
    b = Bot(
        roomNumber=9099,
        itemsDropWhiteList=[
            "Fragment of Midnight",
            "Fragment of Sunlight",
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
    )
    b.set_login_info(selected_slave.username, selected_slave.password, server)

    async def run_bot(cmd: Command):
        bot_instance = selected_slave.bot_class(
            cmd, 
            role=selected_slave.role, 
            **selected_slave.bot_kwargs)
        await bot_instance.start()

    print(f"Bot: {selected_slave.bot_class.__name__}")
    for param in selected_slave.bot_kwargs:
        print(f"{param}: {selected_slave.bot_kwargs[param]}")

    asyncio.run(b.start_bot(run_bot))


if __name__ == "__main__":
    main()
