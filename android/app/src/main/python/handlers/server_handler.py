import asyncio
from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from core.bot import Bot

async def server_handler_task(bot: 'Bot'):
    print("Running server handler...")
    while bot.is_client_connected:
        messages = bot.read_batch(bot.client_socket)
        if messages:
            for msg in messages:
                await bot.handle_server_response(msg)
    print("Stopping server handler...")