from core.bot import Bot
from templates.hunt import hunt_item_cmds
import commands as cmd
import asyncio

username = input("Username: ")
password = input("Password: ")
server = input("Server: ")

# Initialize bot
b = Bot(
    roomNumber=None, 
    itemsDropWhiteList=[
        "Astral Ephemerite Essence",
        "Belrot the Fiend Essence",
        "Black Knight Essence",
        "Tiger Leech Essence",
        "Carnax Essence",
        "Chaos Vordred Essence",
        "Dai Tengu Essence",
        "Unending Avatar Essence",
        "Void Dragon Essence",
        "Creature Creation Essence",
        "Void Aura"
      ], 
    cmdDelay=1000,
    showLog=True, 
    showDebug=False,
    showChat=True)
b.set_login_info(username, password, server)

# Initialize variables
private_room_number = 999999

# Arrange commands
b.add_cmds([
        cmd.AcceptQuestCmd(4432),
        cmd.SleepCmd(1000),
        *hunt_item_cmds(
            item_name = "Astral Ephemerite Essence",
            item_qty = 100,
            map_name = "timespace",
            room_number = private_room_number,
            cell = "Frame1",
            pad = "Spawn",
            monster_name = "*"
        ),
        *hunt_item_cmds(
            item_name = "Belrot the Fiend Essence",
            item_qty = 100,
            map_name = "citadel",
            room_number = private_room_number,
            cell = "m13",
            pad = "Left",
            monster_name = "*"
        ),
        *hunt_item_cmds(
            item_name = "Black Knight Essence",
            item_qty = 100,
            map_name = "greenguardwest",
            room_number = None,
            cell = "BKWest15",
            pad = "Left",
            monster_name = "*"
        ),
        *hunt_item_cmds(
            item_name = "Tiger Leech Essence",
            item_qty = 100,
            map_name = "mudluk",
            room_number = private_room_number,
            cell = "Boss",
            pad = "Down",
            monster_name = "*"
        ),
        *hunt_item_cmds(
            item_name = "Carnax Essence",
            item_qty = 100,
            map_name = "aqlesson",
            room_number = None,
            cell = "Frame9",
            pad = "Right",
            monster_name = "*"
        ),
        *hunt_item_cmds(
            item_name = "Chaos Vordred Essence",
            item_qty = 100,
            map_name = "necrocavern",
            room_number = None,
            cell = "r16",
            pad = "Down",
            monster_name = "*"
        ),
        *hunt_item_cmds(
            item_name = "Dai Tengu Essence",
            item_qty = 100,
            map_name = "hachiko",
            room_number = private_room_number,
            cell = "Roof",
            pad = "Left",
            monster_name = "*"
        ),
        *hunt_item_cmds(
            item_name = "Unending Avatar Essence",
            item_qty = 100,
            map_name = "timevoid",
            room_number = None,
            cell = "Frame8",
            pad = "Left",
            monster_name = "*"
        ),
        *hunt_item_cmds(
            item_name = "Void Dragon Essence",
            item_qty = 100,
            map_name = "dragonchallenge",
            room_number = None,
            cell = "r4",
            pad = "Left",
            monster_name = "*"
        ),
        *hunt_item_cmds(
            item_name = "Creature Creation Essence",
            item_qty = 100,
            map_name = "maul",
            room_number = private_room_number,
            cell = "r3",
            pad = "Down",
            monster_name = "*"
        ),
        cmd.TurnInQuestCmd(4432, turn_in_count=5),
        cmd.SleepCmd(1000)
    ])

# Start bot
asyncio.run(b.start_bot())