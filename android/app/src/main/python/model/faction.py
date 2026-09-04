# {
#     'FactionID': '46',
#     'CharFactionID': '45578506',
#     'sName': 'Aegis',
#     'iRep': '302500'
#   }
from core.utils import normalize

class Faction:
    def __init__(self, faction: dict):
        self.faction_id: int = int(faction.get('FactionID', 0))
        self.char_faction_id: str = str(faction.get('CharFactionID', ''))
        self.faction_name: str = normalize(faction.get('sName', ''))
        self.rep: int = int(faction.get('iRep', 0))
    
    def get_rep(self) -> int:
        return self.rep
    
    def add_rep(self, irep: int) -> None:
        self.rep += irep
    
    def is_max(self) -> bool:
        return self.get_rank() == 10
    
    def get_rank(self) -> int:
        if self.rep >= 302500:
            return 10
        elif self.rep >= 202500:
            return 9
        elif self.rep >= 129600:
            return 8
        elif self.rep >= 78400:
            return 7
        elif self.rep >= 44100:
            return 6
        elif self.rep >= 22500:
            return 5
        elif self.rep >= 10000:
            return 4
        elif self.rep >= 3600:
            return 3
        elif self.rep >= 900:
            return 2
        else:
            return 1