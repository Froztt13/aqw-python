from core.bot import Bot
import commands as cmd
import asyncio

# Initialize bot
b = Bot(
    roomNumber=9099, 
    itemsDropWhiteList=[], 
    cmdDelay=1000,
    showLog=False, 
    showDebug=False,
    showChat=True,
    restartOnAFK=False,
    antiMod=False)
b.set_login_info("username", "pass", "yorumi")

# Arrange commands
b.add_cmds([
    cmd.JoinHouseCmd("idhq"),
    cmd.JumpCmd('r1a', 'Left'),
    cmd.WalkCmd('780', '500'),
    cmd.SleepCmd(60000),
    cmd.UpIndexCmd(1)
])

# Start bot
try:
    asyncio.run(b.start_bot())
except KeyboardInterrupt:
    print("\nBot stopped by user.")
except ModuleNotFoundError as e:
    print(f"\nError: {e}")