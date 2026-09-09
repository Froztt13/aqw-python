from typing import Dict, List, Any
from bot.general.models import TaskDefinition, SubModuleDefinition
from bot.general.modules import ALL_MODULES, LR_MODULE, NULGATH_MODULE, VA_MODULE

# Central Registry mapping module_id -> SubModuleDefinition
REGISTRY: Dict[str, SubModuleDefinition] = {
    module.module_id: module for module in ALL_MODULES
}

def register_submodule(submodule: SubModuleDefinition):
    """Registers or updates a submodule in the general bot registry."""
    REGISTRY[submodule.module_id] = submodule

def get_submodules_list() -> List[Dict[str, Any]]:
    """Returns serialized list of all available submodules and their tasks."""
    return [sub.to_dict() for sub in REGISTRY.values()]

__all__ = [
    "TaskDefinition",
    "SubModuleDefinition",
    "REGISTRY",
    "register_submodule",
    "get_submodules_list",
    "LR_MODULE",
    "NULGATH_MODULE",
    "VA_MODULE",
    "ALL_MODULES"
]
