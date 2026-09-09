import typing
from typing import Dict, List, Any, Callable, Optional
from core.command import Command

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
