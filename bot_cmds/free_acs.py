from core.bot import Bot
import commands as cmd
import asyncio
import os
from templates import attack
from templates.hunt import hunt_item_cmds

# Credentials are NOT stored in this tracked file. Set
#   AQW_FREE_ACS_ACCOUNTS=user1:pass1,user2:pass2
# in your environment (or .env) before running.
users = [
	{"user": entry.split(":", 1)[0], "pass": entry.split(":", 1)[1]}
	for entry in os.environ.get("AQW_FREE_ACS_ACCOUNTS", "").split(",")
	if ":" in entry
]

atk = attack.generalAttack
itemName = "Free ACs..."
itemQty = 1

for user in users:
		b = Bot(roomNumber="9099", showLog = True, showDebug=False, cmdDelay = 500)
		b.set_login_info(user['user'], user['pass'], "alteon")
	# 	b.add_cmds([
	# 			cmd.AcceptQuestCmd(10455),
	# 			cmd.JoinMapCmd("eventhub", 9909),
	# 			cmd.JumpCmd("Bottom", "Upstairs"),
	# 			cmd.EquipItemCmd("Legion Revenant"),
    # cmd.LabelCmd("ATK")
	# 	] + atk + [
	# 		cmd.IsInInvCmd(itemName, itemQty, isTemp=True),
	# 			cmd.TurnInQuestCmd(10455),
	# 		cmd.StopBotCmd(),
	# 		cmd.ToLabelCmd("ATK")
	# 	])
		b.add_cmds([cmd.EquipItemCmd("Legion Revenant"),
			cmd.AcceptQuestCmd(10455),
			*hunt_item_cmds(
				item_name= itemName,
				item_qty = 1,
				map_name = "eventhub",
				room_number = 9909,
				cell = "Upstairs",
				pad = "Bottom",
				monster_name = "*"
			),
			cmd.TurnInQuestCmd(10455),
			cmd.SleepCmd(1000),
			cmd.StopBotCmd()
		])
		asyncio.run(b.start_bot())
