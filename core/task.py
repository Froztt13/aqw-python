from core.command import Command
from model import monster
from templates.hunt import hunt_item
from dataclasses import dataclass
@dataclass(frozen=True)
class FarmTask:
    item_name: str
    qty: int
    map_name: str
    cell: str
    pad: str
    monster_name: str = "*"
    is_solo: bool = False
    room_number: int = None

async def do_farm_tasks(cmd: Command, tasks: list[FarmTask]):
    for task in tasks:
        if not cmd.is_still_connected():
            return

        if task.is_solo:
            class_to_equip = cmd.get_solo_class()
        else:
            class_to_equip = cmd.get_farm_class()

        if class_to_equip:
            await cmd.equip_item(class_to_equip)

        await hunt_item(
            cmd=cmd,
            item_name=task.item_name,
            item_qty=task.qty,
            cell=task.cell,
            pad=task.pad,
            map_name=task.map_name,
            room_number=task.room_number,
            monster_name=task.monster_name,
            farming_logger=True,
            is_temp=True
        )
