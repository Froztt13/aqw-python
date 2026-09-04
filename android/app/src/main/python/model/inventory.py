from core.utils import normalize
from enum import Enum

class ItemType(Enum):
    CLASS = "ar"
    ARMOR = "co"
    CAPE = "ba"
    HELM = "he"
    WEAPON = "Weapon"
    FLOOR_ITEM = "hi"
    PET = "pe"
    HOUSE = "ho"
    
class ScrollType(Enum):  
    SCROLL = "scroll"  
    ELIXIR = "elixir"  
    POTION = "potion" 
        
class ItemInventory:
    def __init__(self, json_data):
        self.item_name: str = normalize(str(json_data.get('sName', '')))
        self.item_id: str = str(json_data.get('ItemID', ''))
        self.qty: int = int(json_data.get('iQty', 0))
        self.is_acs: bool = str(json_data.get('bCoins', '0')) == "1"
        self.is_temp: bool = str(json_data.get('bTemp', '0')) == "1"
        # ar = "Class"
        # co = "Armor"
        # ba = "Cape"
        # he = "Helm"
        # Weapon = all weapon types
        # hi = "Floor Item"
        # pe = "Pet"
        # ho = "House"
        # None = all misc types
        self.s_es: str = str(json_data.get('sES', ''))
        self.s_type: str = str(json_data.get('sType', '')) # "Pet", "Cape", "Class", "Misc", "Armor", "Helm"
        self.s_meta: str = str(json_data.get('sMeta', 0))
        self.cost: int = int(json_data.get('iCost', 0))
        
        self.is_equipped: bool = int(json_data.get('bEquip', 0)) == 1
        self.is_weared: bool = int(json_data.get('bWear', 0)) == 1
        self.char_item_id: int = int(json_data.get('CharItemID', 0))
        self.shop_item_id: str = json_data.get('ShopItemID', '')
        self.qty_now: int = int(json_data.get('iQtyNow', 0))

        self.enh_pattern_id: int = int(json_data.get('EnhPatternID', 0))

        self.turn_in: list[ItemInventory] = ItemInventory
        