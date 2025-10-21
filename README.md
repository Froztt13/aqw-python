# AQW Python Bot

A comprehensive automation toolkit for AdventureQuest Worlds (AQW) that enables automated farming, questing, and combat operations.

> **Notice**: This software is designed for educational purposes and to assist with repetitive in-game tasks. Users are responsible for ensuring compliance with AQW's terms of service.

## Features

- **Dual Automation Modes**: Simple command queue system and advanced Python scripting capabilities
- **Quest Management**: Automated quest acceptance and completion
- **Combat System**: Intelligent monster targeting and skill execution
- **Inventory Control**: Automated item purchasing, selling, equipping, and management
- **Bank Integration**: Seamless item transfers between inventory and bank storage
- **Navigation System**: Automated map and location movement
- **Safety Mechanisms**: Built-in error handling and connection management

## System Requirements

- **Python 3.9 or higher** - [Download Python](https://www.python.org/downloads/)

## Installation Guide

### Step 1: Repository Acquisition

1. Open your terminal or command prompt interface
2. Clone the repository using Git:
   ```bash
   git clone https://github.com/Froztt13/aqw-python.git
   ```
3. Navigate to the project directory:
   ```bash
   cd aqw-python
   ```

### Step 2: Dependency Installation

Install the required Python packages:
```bash
pip install -r requirements.txt
```

Installation is now complete. You may proceed to the usage section.

## Usage Instructions

### Mode 1: Sequential Command Execution

This mode is suitable for users requiring simple automation tasks.

**Functionality**: Executes predefined commands in sequential order

**Example execution**:
```bash
python -m bot_cmds.bot_tes
```

**Process**:
1. Locate script files in the `bot_cmds/` directory
2. Each script contains ordered command sequences
3. The bot processes commands systematically
4. Scripts are easily modified and comprehensible

**Creating Custom Sequential Command Bots**:

To create your own sequential command execution bot:

1. **Available Commands**: Navigate to `D:\Python\aqw-python\commands` directory to access all available commands
2. **Command Structure**: Each command file contains predefined automation functions
3. **Create Custom Script**: Create a new Python file in the `bot_cmds/` directory
4. **Import Commands**: Import the required commands from the commands directory
5. **Sequence Execution**: Arrange commands in the desired execution order
6. **Configuration**: Modify parameters and settings as needed

**Example Custom Bot Structure**:

Refer to `D:\Python\aqw-python\bot_cmds\bot_tes.py` for a complete working example:

```python
from core.bot import Bot
import commands as cmd
from templates.attack import attack_monster
from templates.general import un_bank_items
import asyncio

# Initialize variables
drop_whitelist = [
    "Unidentified 19",
    "Unidentified 13",
    "Tainted Gem",
    "Dark Crystal Shard",
    "Diamond of Nulgath",
    "Voucher of Nulgath",
    "Voucher of Nulgath (non-mem)",
    "Random Weapon of Nulgath",
    "Gem of Nulgath",
    "Relic of Chaos"
]

# Initialize bot
b = Bot(
    roomNumber=9099,
    itemsDropWhiteList=drop_whitelist,
    cmdDelay=1000,
    showLog=True,
    showDebug=False,
    showChat=True
)
b.set_login_info("username", "password", "server")

# Arrange commands
b.add_cmds([
    *un_bank_items(items=drop_whitelist),
    cmd.RegisterQuestCmd(2857),
    cmd.JoinMapCmd("escherion"),
    cmd.JumpCmd("Boss", "Left"),
    cmd.LabelCmd("ATK"),
    *attack_monster(monster_name="Staff of Inversion,Escherion"),
    cmd.ToLabelCmd("ATK"),
    cmd.StopBotCmd()
])

# Start bot
asyncio.run(b.start_bot())
```

**Bot Structure Explanation**:
- **Import Required Modules**: Bot class, commands, templates
- **Initialize Variables**: Define drop whitelist and bot settings
- **Create Bot Instance**: Configure room, delay, logging preferences
- **Set Login Credentials**: Provide username, password, and server
- **Add Command Sequence**: Arrange commands in execution order
- **Start Bot Execution**: Run the bot asynchronously

### Mode 2: Advanced Python Scripting

This mode provides comprehensive control over bot behavior for experienced users.

**Functionality**: Custom Python code implementation for complex automation scenarios

**Example execution**:
```bash
python start.py
```

**Process**:
1. Utilize the `bot/` package to access bot functionalities
2. Develop custom Python scripts
3. Implement sophisticated farming and questing routines
4. Complete customization and flexibility

**Advanced Command Integration**:

For advanced Python scripting, you can access the comprehensive command class located at `D:\Python\aqw-python\core\command.py`:

1. **Command Class**: The `Command` class in `core/command.py` provides access to all bot functionalities
2. **Complete API**: Access to quest management, item operations, combat system, and navigation
3. **Method Integration**: Direct method calls for precise control over bot behavior
4. **Error Handling**: Built-in error handling and safety mechanisms
5. **Asynchronous Support**: Full async/await support for complex operations

**Example Advanced Script Structure**:
```python
from core.command import Command
from core.bot import Bot

# Initialize bot and command instances
bot = Bot()
cmd = Command(bot)

# Advanced automation with full control
async def advanced_farming_routine():
    await cmd.join_map("escherion")
    await cmd.jump_cell("Boss", "Left")

    # Complex logic and conditions
    skills = [0,1,2,0,3,4]
    skill_index = 0
    while cmd.is_player_alive():
        await cmd.use_skill(skills[skill_index], "Staff of Inversion,Escherion")
        skill_index = skill_index + 1
        if skill_index >= len(skills):
            skill_index = 0
        await cmd.sleep(100)
```

**Key Command Class Features**:
- **Quest Operations**: `accept_quest()`, `turn_in_quest()`, `ensure_accept_quest()`
- **Item Management**: `buy_item()`, `sell_item()`, `equip_item()`, `bank_to_inv()`
- **Combat Control**: `use_skill()`, `start_aggro()`, `leave_combat()`
- **Navigation**: `join_map()`, `jump_cell()`, `goto_player()`
- **Player Information**: `get_player()`, `is_player_alive()`, `get_monster_hp()`

## Command Documentation

For detailed function documentation and method references, please refer to the official documentation:

**Documentation Website**: [https://froztt13.github.io/aqw-python/](https://froztt13.github.io/aqw-python/)

**Currently Available**:
- Complete function documentation for the Command class
- Method parameters and return values
- Usage examples for individual functions
- API reference documentation

**For Complete Examples and Templates**:
- Sequential command examples: `D:\Python\aqw-python\bot_cmds\bot_tes.py`
- Command templates: `D:\Python\aqw-python\templates\`
- Available commands: `D:\Python\aqw-python\commands\`

## Docker Deployment (Optional)

For users familiar with containerized applications:

1. **Build and initialize**:
   ```bash
   docker-compose up --build -d
   ```

2. **Terminate containers**:
   ```bash
   docker-compose down
   ```

3. **Access container logs**:
   ```bash
   docker-compose logs
   ```

---

For detailed documentation and advanced usage instructions, visit: [https://froztt13.github.io/aqw-python/](https://froztt13.github.io/aqw-python/)
