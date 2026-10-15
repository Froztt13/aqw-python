import os
from dotenv import load_dotenv
import importlib
import builtins
from core.bot import Bot
import asyncio
import sys

# Define a custom print function that includes flush=True
# IDK why but Docker logs doesnt work without this
def custom_print(*args, **kwargs):
    kwargs['flush'] = True
    # Use sys.stdout.write to avoid recursion
    sys.stdout.write(" ".join(map(str, args)) + "\n")
    sys.stdout.flush()

# Override the built-in print function
builtins.print = custom_print

# Load environment variables from .env file
load_dotenv()

# You can use this approach if you prefer to use direct input instead of .env file:
# Replace the following lines with direct assignments if you do not want to use .env
# Example:
# usernames = ["username1", "username2"]
# passwords = ["password1", "password2"]
# servers = ["server1", "server2"]
# bot_paths = ["path.to.bot1", "path.to.bot2"]

# Retrieve and parse environment variables
def parse_env_variable(variable):
    return variable.strip("[]").split(",") if variable else []

# Use environment variables (default approach)
usernames = parse_env_variable(os.getenv("USERNAME_AQW"))
passwords = parse_env_variable(os.getenv("PASSWORD_AQW"))
servers = parse_env_variable(os.getenv("SERVER"))
bot_paths = parse_env_variable(os.getenv("BOT_PATH"))

# Ensure lengths match
if len(usernames) != len(passwords) or len(usernames) != len(servers) or len(usernames) != len(bot_paths):
    print("Error: The number of usernames, passwords, servers, and bot paths must be equal!")
    exit(1)

# # Whitelist of items for the bot
# items_white_list = [
#     "Astral Ephemerite Essence",
#     "Belrot the Fiend Essence",
#     "Black Knight Essence",
#     "Tiger Leech Essence",
#     "Carnax Essence",
#     "Chaos Vordred Essence",
#     "Dai Tengu Essence",
#     "Unending Avatar Essence",
#     "Void Dragon Essence",
#     "Creature Creation Essence",
#     "Void Aura"
# ]

# Bot setup function
def create_bot(username, password, server, room_number):
    bot = Bot(
        roomNumber=room_number,
        # itemsDropWhiteList=items_white_list,
        showLog=True,
        showDebug=False,
        showChat=True,
        isScriptable=True,
        farmClass="Legion Revenant"
    )
    bot.set_login_info(username, password, server)
    return bot

# Run bot asynchronously
async def run_bot(bot_class_path, bot_instance):
    try:
        bot_class = importlib.import_module(bot_class_path)
        print(f"Starting bot: {bot_class_path.split('.')[-1]}")
        await bot_instance.start_bot(bot_class.main)
    except ModuleNotFoundError as e:
        print(f"Error: {e}")


async def main():
    tasks = [
        run_bot(bot_paths[i], create_bot(usernames[i], passwords[i], servers[i], room_number=9099 + i))
        for i in range(len(usernames))
    ]
    await asyncio.gather(*tasks)

if __name__ == "__main__":
    print(f"Total bots: {len(usernames)}")
    asyncio.run(main())
