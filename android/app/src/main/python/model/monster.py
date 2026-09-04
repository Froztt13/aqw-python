from core.utils import normalize
from model.aura import Aura

class Monster:
    _mon_name: str = None

    @property
    def mon_name(self) -> str:
        return self._mon_name

    @mon_name.setter
    def mon_name(self, value: str):
        self._mon_name = normalize(value) if value else None
    
    # Init with monBranch json data
    def __init__(self, json_data):
        self.mon_map_id: str = str(json_data['MonMapID'])
        self.mon_id: str = str(json_data['MonID'])
        self.is_alive: bool = int(json_data['intState']) > 0
        self.current_hp: int = json_data['intHP']
        self.max_hp: int = json_data['intHPMax']
        self.tes: str = str(json_data.get('tes', None))
        self.frame: str = None
        self.AURAS: list[Aura] = []

    def addAura(self, auras:list):
        for aura in auras:
            is_new = aura.get('isNew', False)
            name = normalize(aura.get('nam'))
            if is_new:
                self.AURAS.append(Aura(aura))
            else:
                for existing_aura in self.AURAS:
                    if existing_aura.name == name:
                        existing_aura.refresh(aura.get('dur', 0))
    
    def removeAura(self, auraName: str):
        normalized_name = normalize(auraName)
        for aura in self.AURAS[:]:
            if aura.name == normalized_name:
                self.AURAS.remove(aura)
                break

    def getAura(self, auraName: str) -> Aura:
        normalized_name = normalize(auraName)
        for aura in self.AURAS:
            if aura.name == normalized_name and not aura.is_expired():
                return aura
        return None

    def hasAura(self, auraName: str) -> bool:
        normalized_name = normalize(auraName)
        for aura in self.AURAS:
            if aura.name == normalized_name and not aura.is_expired():
                return True
        return False