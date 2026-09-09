from core.command import Command
import bot.LR.core_lr as core_lr
from bot.general.models import TaskDefinition, SubModuleDefinition

# --- Task Runner implementations for Legion Revenant ---
async def _run_spellscroll(cmd: Command, qty: int):
    await core_lr.revenant_spellscroll(cmd, qty)

async def _run_conquest_wreath(cmd: Command, qty: int):
    await core_lr.conquest_wreath(cmd, qty)

async def _run_exalted_crown(cmd: Command, qty: int):
    await core_lr.exalted_crown(cmd, qty)

async def _run_legion_token(cmd: Command, qty: int):
    await core_lr.get_leto_ssp(cmd, qty)

async def _run_dages_favor(cmd: Command, qty: int):
    await core_lr.get_dages_favor(cmd, qty)

async def _run_emblem_of_dage(cmd: Command, qty: int):
    await core_lr.get_emblem_of_dage(cmd, qty)

async def _run_diamond_token(cmd: Command, qty: int):
    await core_lr.get_diamond_token_of_dage(cmd, qty)

async def _run_dark_token(cmd: Command, qty: int):
    await core_lr.get_dark_token(cmd, qty)

async def _run_full_lr(cmd: Command, qty: int):
    print("=== [General Bot] Starting Full Legion Revenant Sequence ===")
    print(">>> Phase 1: Revenant's Spellscroll (20x)")
    await core_lr.revenant_spellscroll(cmd, 20)
    if not cmd.is_still_connected():
        return
    print(">>> Phase 2: Conquest Wreath (6x)")
    await core_lr.conquest_wreath(cmd, 6)
    if not cmd.is_still_connected():
        return
    print(">>> Phase 3: Exalted Crown (10x)")
    await core_lr.exalted_crown(cmd, 10)
    print("=== [General Bot] Full Legion Revenant Sequence Finished! ===")

# --- Tasks Definition ---
lr_tasks = [
    TaskDefinition(
        task_id="spellscroll",
        name="Revenant's Spellscroll (Fealty 1)",
        description="Farms 50 Aeacus Empowered, 300 Tethered Soul, 500 Darkened Essence, 1000 Dracolich Contract.",
        default_qty=20,
        tracked_item="Revenant's Spellscroll",
        quest_id=6897,
        runner_fn=_run_spellscroll
    ),
    TaskDefinition(
        task_id="conquest_wreath",
        name="Conquest Wreath (Fealty 2)",
        description="Farms 400 of each Cohort conquered across 10 maps.",
        default_qty=6,
        tracked_item="Conquest Wreath",
        quest_id=6898,
        runner_fn=_run_conquest_wreath
    ),
    TaskDefinition(
        task_id="exalted_crown",
        name="Exalted Crown (Fealty 3)",
        description="Farms Hooded Legion Cowl, Legion Tokens, Dage's Favor, Emblems, and Dark Tokens.",
        default_qty=10,
        tracked_item="Exalted Crown",
        quest_id=6899,
        runner_fn=_run_exalted_crown
    ),
    TaskDefinition(
        task_id="legion_token",
        name="Legion Token (Shogun Paragon Pet)",
        description="Farms Fotia souls for quick Legion Tokens via Quest 5755.",
        default_qty=4000,
        tracked_item="Legion Token",
        quest_id=5755,
        runner_fn=_run_legion_token
    ),
    TaskDefinition(
        task_id="full_lr",
        name="Full LR Farm (Fealty 1 -> 2 -> 3)",
        description="Executes Fealty 1, Fealty 2, and Fealty 3 sequentially until complete.",
        default_qty=1,
        tracked_item="Exalted Crown",
        quest_id=0,
        runner_fn=_run_full_lr
    ),
    TaskDefinition(
        task_id="dages_favor",
        name="Dage's Favor",
        description="Hunts in /evilwarnul for Dage's Favor.",
        default_qty=300,
        tracked_item="Dage's Favor",
        quest_id=0,
        runner_fn=_run_dages_favor
    ),
    TaskDefinition(
        task_id="emblem_of_dage",
        name="Emblem of Dage",
        description="Farms Fiend Seal and Shadow Seal in /shadowblast via Quest 4742.",
        default_qty=20,
        tracked_item="Emblem of Dage",
        quest_id=4742,
        runner_fn=_run_emblem_of_dage
    ),
    TaskDefinition(
        task_id="diamond_token",
        name="Diamond Token of Dage",
        description="Farms Defeated Makai, Carnax Eye, Fluffy Bones, and Blood Titan Blade via Quest 4743.",
        default_qty=30,
        tracked_item="Diamond Token of Dage",
        quest_id=4743,
        runner_fn=_run_diamond_token
    ),
    TaskDefinition(
        task_id="dark_token",
        name="Dark Token",
        description="Farms Seraphic Medals in /seraphicwardage via Quests 6248 & 6249.",
        default_qty=100,
        tracked_item="Dark Token",
        quest_id=6248,
        runner_fn=_run_dark_token
    )
]

LR_MODULE = SubModuleDefinition(
    module_id="lr",
    name="Legion Revenant Farm",
    category="Endgame Class",
    description="Automated Legion Revenant farming: Fealty 1 (Spellscroll), Fealty 2 (Conquest Wreath), Fealty 3 (Exalted Crown), and Legion Tokens.",
    tasks=lr_tasks
)
