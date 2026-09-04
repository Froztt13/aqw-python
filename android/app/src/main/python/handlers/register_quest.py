import asyncio
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from core.bot import Bot

async def register_quest_task(bot: 'Bot'):
    print("Running registered quests...")
    while bot.is_client_connected:
        for registered_quest_id in bot.registered_auto_quest_ids:
            if bot.quest_not_in_progress(registered_quest_id):
                bot.accept_quest(registered_quest_id)
            if bot.can_turn_in_quest(registered_quest_id):
                bot.turn_in_quest(registered_quest_id)
                await asyncio.sleep(1)
                bot.accept_quest(registered_quest_id)
            await asyncio.sleep(1)
        await asyncio.sleep(2)
    print("Stopping registered quests...")