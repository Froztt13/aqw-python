from core.bot import Bot
from core.command import Command
from templates.hunt import kill_quest

async def main(bot: Bot):
    cmd = Command(bot)
    item_name = "Generosity Coin"
    await cmd.bank_to_inv(item_name)
    cmd.add_drop(item_name)


    await kill_quest(
        cmd,
        quest_id=10510,
        map_name="battleontown",
        monster_name="Frogzard",
        room_number=99999999
    )

    await cmd.join_map("battleon")
    cmd.stop_bot()