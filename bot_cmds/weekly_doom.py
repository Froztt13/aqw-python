from core.bot import Bot
import commands as cmd
import asyncio

users = [
	{
		'user': 'username',
		'pass': 'password'
	},
	{
		'user': 'username',
		'pass': 'password'
	}
]

for user in users:
    b = Bot(roomNumber="9099", showLog = True, showDebug=True, cmdDelay = 500)
    b.set_login_info(user['user'], user['pass'], "Swordhaven (EU)")
    b.add_cmds([
        cmd.IsInInvCmd("Epic Item of Digital Awesomeness"),
        cmd.MessageCmd(msg="You have \"Epic Item of Digital Awesomeness\" in your inventory!!"),
        cmd.IsInBankCmd("Gear of Doom"),
        cmd.BankToInvCmd("Gear of Doom"),
        cmd.IsInInvCmd("Gear of Doom", 3, operator="<"),
        cmd.StopBotCmd(msg="Not enough Gear of Doom."),
        cmd.JoinMapCmd("doom"),
        cmd.AcceptQuestCmd(3076),
        cmd.TurnInQuestCmd(3076),
        cmd.SleepCmd(1000),
        cmd.StopBotCmd(msg="Bot Finished.")
    ])
    asyncio.run(b.start_bot())