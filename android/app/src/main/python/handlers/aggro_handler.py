import asyncio
from typing import TYPE_CHECKING
from colorama import Fore

if TYPE_CHECKING:
    from core.bot import Bot
    
async def aggro_handler_task(bot: 'Bot'):
    print("Running aggro handler...")
    #  %xt%zm%aggroMon%0%id%
    while bot.is_client_connected:
        if not bot.is_aggro_handler_task_running:
            break
        if len(bot.aggro_mons_id) > 0:
            aggroMon = f"%xt%zm%aggroMon%{bot.areaId}%{'%'.join(map(str, bot.aggro_mons_id))}%"
            bot.write_message(aggroMon)
        await asyncio.sleep(bot.aggro_delay_ms/1000)
    print("Stopping aggro handler...")