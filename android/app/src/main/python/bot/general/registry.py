import typing
from typing import Dict, List, Any, Callable, Optional
from core.command import Command
import bot.LR.core_lr as core_lr
import bot.nulgath.larvae as nulgath_larvae

class TaskDefinition:
    def __init__(
        self,
        task_id: str,
        name: str,
        description: str,
        default_qty: int,
        tracked_item: str,
        quest_id: int = 0,
        runner_fn: Optional[Callable[[Command, int], typing.Awaitable[None]]] = None
    ):
        self.task_id = task_id
        self.name = name
        self.description = description
        self.default_qty = default_qty
        self.tracked_item = tracked_item
        self.quest_id = quest_id
        self.runner_fn = runner_fn

    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.task_id,
            "name": self.name,
            "description": self.description,
            "default_qty": self.default_qty,
            "tracked_item": self.tracked_item,
            "quest_id": self.quest_id
        }

class SubModuleDefinition:
    def __init__(
        self,
        module_id: str,
        name: str,
        category: str,
        description: str,
        tasks: List[TaskDefinition]
    ):
        self.module_id = module_id
        self.name = name
        self.category = category
        self.description = description
        self.tasks = tasks
        self._tasks_map = {t.task_id: t for t in tasks}

    def get_task(self, task_id: str) -> Optional[TaskDefinition]:
        return self._tasks_map.get(task_id)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.module_id,
            "name": self.name,
            "category": self.category,
            "description": self.description,
            "tasks": [t.to_dict() for t in self.tasks]
        }


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

# --- Task Runner implementations for Nulgath Materials ---
async def _run_nulgath_larvae(cmd: Command, qty: int):
    # Infinite loop - continuous turn-in farming without target item
    await nulgath_larvae.farm_larvae(cmd, target_item=None, target_qty=0)

async def _run_nulgath_uni13(cmd: Command, qty: int):
    await nulgath_larvae.farm_larvae(cmd, target_item="Unidentified 13", target_qty=qty)

async def _run_nulgath_diamond(cmd: Command, qty: int):
    await nulgath_larvae.farm_larvae(cmd, target_item="Diamond of Nulgath", target_qty=qty)

async def _run_nulgath_dcs(cmd: Command, qty: int):
    await nulgath_larvae.farm_larvae(cmd, target_item="Dark Crystal Shard", target_qty=qty)

async def _run_nulgath_tainted(cmd: Command, qty: int):
    await nulgath_larvae.farm_larvae(cmd, target_item="Tainted Gem", target_qty=qty)

async def _run_nulgath_voucher_nonmem(cmd: Command, qty: int):
    await nulgath_larvae.farm_larvae(cmd, target_item="Voucher of Nulgath (non-mem)", target_qty=qty)

async def _run_nulgath_totem(cmd: Command, qty: int):
    await nulgath_larvae.farm_larvae(cmd, target_item="Totem of Nulgath", target_qty=qty)

async def _run_nulgath_gem(cmd: Command, qty: int):
    await nulgath_larvae.farm_larvae(cmd, target_item="Gem of Nulgath", target_qty=qty)

async def _run_nulgath_blood_gem(cmd: Command, qty: int):
    await nulgath_larvae.farm_larvae(cmd, target_item="Blood Gem of the Archfiend", target_qty=qty)


# --- Registry of Sub-Modules ---
REGISTRY: Dict[str, SubModuleDefinition] = {}

def register_submodule(submodule: SubModuleDefinition):
    REGISTRY[submodule.module_id] = submodule

# Register Legion Revenant Farm Submodule
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

register_submodule(SubModuleDefinition(
    module_id="lr",
    name="Legion Revenant Farm",
    category="Endgame Class",
    description="Automated Legion Revenant farming: Fealty 1 (Spellscroll), Fealty 2 (Conquest Wreath), Fealty 3 (Exalted Crown), and Legion Tokens.",
    tasks=lr_tasks
))

# Register Nulgath Materials Submodule
nulgath_tasks = [
    TaskDefinition(
        task_id="larvae",
        name="Nulgath Larva (Turn-ins)",
        description="Farms Mana Energy & Charged Mana Energy in /elemental in an infinite loop. Auto-sells member Voucher for 250,000 gold.",
        default_qty=0,
        tracked_item="",
        quest_id=2566,
        runner_fn=_run_nulgath_larvae
    ),
    TaskDefinition(
        task_id="larvae_uni13",
        name="Unidentified 13 (Uni 13)",
        description="Farms Nulgath Larva quest 2566 until target Unidentified 13 is reached.",
        default_qty=3,
        tracked_item="Unidentified 13",
        quest_id=2566,
        runner_fn=_run_nulgath_uni13
    ),
    TaskDefinition(
        task_id="larvae_diamond",
        name="Diamond of Nulgath",
        description="Farms Nulgath Larva quest 2566 until target Diamond of Nulgath is reached.",
        default_qty=100,
        tracked_item="Diamond of Nulgath",
        quest_id=2566,
        runner_fn=_run_nulgath_diamond
    ),
    TaskDefinition(
        task_id="larvae_dcs",
        name="Dark Crystal Shard",
        description="Farms Nulgath Larva quest 2566 until target Dark Crystal Shard is reached.",
        default_qty=50,
        tracked_item="Dark Crystal Shard",
        quest_id=2566,
        runner_fn=_run_nulgath_dcs
    ),
    TaskDefinition(
        task_id="larvae_tainted",
        name="Tainted Gem",
        description="Farms Nulgath Larva quest 2566 until target Tainted Gem is reached.",
        default_qty=100,
        tracked_item="Tainted Gem",
        quest_id=2566,
        runner_fn=_run_nulgath_tainted
    ),
    TaskDefinition(
        task_id="larvae_voucher_nonmem",
        name="Voucher of Nulgath (non-mem)",
        description="Farms Nulgath Larva quest 2566 until non-member Voucher of Nulgath drops.",
        default_qty=1,
        tracked_item="Voucher of Nulgath (non-mem)",
        quest_id=2566,
        runner_fn=_run_nulgath_voucher_nonmem
    ),
    TaskDefinition(
        task_id="larvae_totem",
        name="Totem of Nulgath",
        description="Farms Nulgath Larva quest 2566 until target Totem of Nulgath is reached.",
        default_qty=10,
        tracked_item="Totem of Nulgath",
        quest_id=2566,
        runner_fn=_run_nulgath_totem
    ),
    TaskDefinition(
        task_id="larvae_gem",
        name="Gem of Nulgath",
        description="Farms Nulgath Larva quest 2566 until target Gem of Nulgath is reached.",
        default_qty=50,
        tracked_item="Gem of Nulgath",
        quest_id=2566,
        runner_fn=_run_nulgath_gem
    ),
    TaskDefinition(
        task_id="larvae_blood_gem",
        name="Blood Gem of the Archfiend",
        description="Farms Nulgath Larva quest 2566 until target Blood Gem of the Archfiend is reached.",
        default_qty=10,
        tracked_item="Blood Gem of the Archfiend",
        quest_id=2566,
        runner_fn=_run_nulgath_blood_gem
    )
]

register_submodule(SubModuleDefinition(
    module_id="nulgath",
    name="Nulgath Materials",
    category="Nation Farm",
    description="Automated Nulgath Nation resource farming: Nulgath Larva (Quest 2566) for Unidentified 13, Diamonds, Dark Crystal Shards, Tainted Gems, Totems, and Vouchers.",
    tasks=nulgath_tasks
))

def get_submodules_list() -> List[Dict[str, Any]]:
    return [sub.to_dict() for sub in REGISTRY.values()]
