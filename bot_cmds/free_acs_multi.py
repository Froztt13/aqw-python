from core.bot import Bot
import commands as cmd
import asyncio
from templates.hunt import hunt_item_cmds

# Multi-account list seperti pada weekly_doom.py
users = [
    {'user': 'username', 'pass': 'password'},
    {'user': 'username2', 'pass': 'password2'}
]

quest_id = 10894
item_name = "Free ACs..."
item_qty = 1
monster_name = "Agitated Orb"
map_name = "eventhub"
room_number = 99999
server_name = "Swordhaven (EU)"

for user in users:
    print(f"\n==========================================")
    print(f"[*] Starting bot for user: {user['user']}")
    print(f"==========================================")

    b = Bot(roomNumber=str(room_number), showLog=True, showDebug=False, cmdDelay=500)
    b.set_login_info(user['user'], user['pass'], server_name)

    b.add_cmds([
        cmd.JoinMapCmd(map_name, room_number),
        cmd.JumpCmd("Enter", "Spawn"),

        cmd.AcceptQuestCmd(quest_id),

        *hunt_item_cmds(
            item_name=item_name,
            item_qty=item_qty,
            map_name=map_name,
            room_number=room_number,
            monster_name=monster_name
        ),

        cmd.TurnInQuestCmd(quest_id, -1),
        cmd.SleepCmd(1000),

        cmd.StopBotCmd(msg="Bot completed! cihuyy...")
    ])

    asyncio.run(b.start_bot())
