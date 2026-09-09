from core.command import Command
import bot.va.void_aura as va_bot
from bot.general.models import TaskDefinition, SubModuleDefinition

# --- Task Runner implementations for Void Aura ---
async def _run_void_aura_main(cmd: Command, qty: int):
    await va_bot.farm_void_aura(cmd, target_qty=qty)

async def _run_essence_astral(cmd: Command, qty: int):
    await va_bot.farm_single_essence(cmd, "Astral Ephemerite Essence", qty=qty)

async def _run_essence_belrot(cmd: Command, qty: int):
    await va_bot.farm_single_essence(cmd, "Belrot the Fiend Essence", qty=qty)

async def _run_essence_blackknight(cmd: Command, qty: int):
    await va_bot.farm_single_essence(cmd, "Black Knight Essence", qty=qty)

async def _run_essence_tigerleech(cmd: Command, qty: int):
    await va_bot.farm_single_essence(cmd, "Tiger Leech Essence", qty=qty)

async def _run_essence_carnax(cmd: Command, qty: int):
    await va_bot.farm_single_essence(cmd, "Carnax Essence", qty=qty)

async def _run_essence_chaosvordred(cmd: Command, qty: int):
    await va_bot.farm_single_essence(cmd, "Chaos Vordred Essence", qty=qty)

async def _run_essence_daitengu(cmd: Command, qty: int):
    await va_bot.farm_single_essence(cmd, "Dai Tengu Essence", qty=qty)

async def _run_essence_unending(cmd: Command, qty: int):
    await va_bot.farm_single_essence(cmd, "Unending Avatar Essence", qty=qty)

async def _run_essence_voiddragon(cmd: Command, qty: int):
    await va_bot.farm_single_essence(cmd, "Void Dragon Essence", qty=qty)

async def _run_essence_creature(cmd: Command, qty: int):
    await va_bot.farm_single_essence(cmd, "Creature Creation Essence", qty=qty)

# --- Tasks Definition ---
va_tasks = [
    TaskDefinition(
        task_id="retrieve_va",
        name="Retrieve Void Auras (Quest 4432)",
        description="Farms 100 of all 10 essences across maps and turns in Quest 4432 (5x batch) for Void Auras until target is reached.",
        default_qty=100,
        tracked_item="Void Aura",
        quest_id=4432,
        runner_fn=_run_void_aura_main
    ),
    TaskDefinition(
        task_id="essence_astral",
        name="Astral Ephemerite Essence",
        description="Hunts Astral Ephemerite in /timespace.",
        default_qty=100,
        tracked_item="Astral Ephemerite Essence",
        quest_id=0,
        runner_fn=_run_essence_astral
    ),
    TaskDefinition(
        task_id="essence_belrot",
        name="Belrot the Fiend Essence",
        description="Hunts Belrot the Fiend in /citadel.",
        default_qty=100,
        tracked_item="Belrot the Fiend Essence",
        quest_id=0,
        runner_fn=_run_essence_belrot
    ),
    TaskDefinition(
        task_id="essence_blackknight",
        name="Black Knight Essence",
        description="Hunts Black Knight in /greenguardwest.",
        default_qty=100,
        tracked_item="Black Knight Essence",
        quest_id=0,
        runner_fn=_run_essence_blackknight
    ),
    TaskDefinition(
        task_id="essence_tigerleech",
        name="Tiger Leech Essence",
        description="Hunts Tiger Leech in /mudluk.",
        default_qty=100,
        tracked_item="Tiger Leech Essence",
        quest_id=0,
        runner_fn=_run_essence_tigerleech
    ),
    TaskDefinition(
        task_id="essence_carnax",
        name="Carnax Essence",
        description="Hunts Carnax in /aqlesson.",
        default_qty=100,
        tracked_item="Carnax Essence",
        quest_id=0,
        runner_fn=_run_essence_carnax
    ),
    TaskDefinition(
        task_id="essence_chaosvordred",
        name="Chaos Vordred Essence",
        description="Hunts Chaos Vordred in /necrocavern.",
        default_qty=100,
        tracked_item="Chaos Vordred Essence",
        quest_id=0,
        runner_fn=_run_essence_chaosvordred
    ),
    TaskDefinition(
        task_id="essence_daitengu",
        name="Dai Tengu Essence",
        description="Hunts Dai Tengu in /hachiko.",
        default_qty=100,
        tracked_item="Dai Tengu Essence",
        quest_id=0,
        runner_fn=_run_essence_daitengu
    ),
    TaskDefinition(
        task_id="essence_unending",
        name="Unending Avatar Essence",
        description="Hunts Unending Avatar in /timevoid.",
        default_qty=100,
        tracked_item="Unending Avatar Essence",
        quest_id=0,
        runner_fn=_run_essence_unending
    ),
    TaskDefinition(
        task_id="essence_voiddragon",
        name="Void Dragon Essence",
        description="Hunts Void Dragon in /dragonchallenge.",
        default_qty=100,
        tracked_item="Void Dragon Essence",
        quest_id=0,
        runner_fn=_run_essence_voiddragon
    ),
    TaskDefinition(
        task_id="essence_creature",
        name="Creature Creation Essence",
        description="Hunts Creature Creation in /maul.",
        default_qty=100,
        tracked_item="Creature Creation Essence",
        quest_id=0,
        runner_fn=_run_essence_creature
    ),
]

VA_MODULE = SubModuleDefinition(
    module_id="va",
    name="Void Aura (NSOD)",
    category="Necrotic Sword",
    description="Automated Void Aura farming via Quest 4432 (Retrieve Void Auras). Farms all 10 monster essences in optimal 5x batch turn-ins for Necrotic Sword of Doom.",
    tasks=va_tasks
)
