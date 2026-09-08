from core.bot import Bot
from core.command import Command
from bot.LR.core_lr import get_leto_ssp

async def main(cmd: Command):
    await get_leto_ssp(cmd, 50000)
    
whitelist = [
        "Legion Token"
    ]

if __name__ == "__main__":
    import asyncio
    bot = Bot(itemsDropWhiteList=whitelist,
              cmdDelay=600,
              showDebug=True,
              autoRelogin=True,
              isScriptable=True)  
    run = Command(bot) 
    login = input("Login (username,pass): ").split(",")
    
    bot.set_login_info(login[0], login[1],"Yokai (SEA)")  # Set login info

    asyncio.run(bot.start_bot(main))  # Run the main coroutine