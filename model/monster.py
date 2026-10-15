from core.utils import normalize
from model.aura import Aura

class Monster:
    # Backing field for the mon_name property. It is only set once bot.py has
    # matched strMonName against mon_id (core/bot.py:370), which can happen
    # after this object is constructed and used for targeting.
    _mon_name: str | None = None

    @property
    def mon_name(self) -> str:
        # Never None: every targeting site does `mon.mon_name.lower()` to build
        # a candidate list, and a monster whose definition has not been matched
        # yet would raise AttributeError on None. Returning "" makes it simply
        # not match, and keeps `mon.mon_name or fallback` falsy as callers
        # (mobile_bridge, build_hub_app) already expect.
        return self._mon_name or ""

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
        # Was str(json_data.get('tes', None)), which stores the literal string
        # "None" whenever the field is absent.
        self.tes: str = json_data.get('tes') or ""
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