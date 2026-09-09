from core.command import Command
import bot.nulgath.larvae as nulgath_larvae
from bot.general.models import TaskDefinition, SubModuleDefinition

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

# --- Tasks Definition ---
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

NULGATH_MODULE = SubModuleDefinition(
    module_id="nulgath",
    name="Nulgath Materials",
    category="Nation Farm",
    description="Automated Nulgath Nation resource farming: Nulgath Larva (Quest 2566) for Unidentified 13, Diamonds, Dark Crystal Shards, Tainted Gems, Totems, and Vouchers.",
    tasks=nulgath_tasks
)
