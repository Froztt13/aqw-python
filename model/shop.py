from typing import List

from .inventory import ItemInventory
from . import enhancement as _enh


class Shop:
    def __init__(self, json_data):
        items = [ItemInventory(shop_item)
                 for shop_item in json_data.get('items') or []]
        self.shop_id: str = str(json_data['ShopID'])
        self.shop_name: str = json_data['sName']
        self.items: List[ItemInventory] = items
        self.is_member: bool = json_data.get('bUpgrd') in (True, "1", 1)
        self.location: str = str(json_data.get('Location', ''))

    @property
    def is_forge(self) -> bool:
        """True for the weapon / helmet / cape enhancement shops.

        Identified by ``Location == "forge"`` (what the real forge shops send)
        or, defensively, by selling items of type ``Enhancement``.
        """
        if self.location == "forge":
            return True
        return any(i.s_type == "Enhancement" for i in self.items)

    def register_enhancements(self) -> int:
        """Add this shop's enhancements to the shared registry.

        Lets the map build itself at runtime: opening a forge shop teaches the
        bot every enhancement it sells, so :func:`model.enhancement.find`
        works even without ``forge_enhancement.jsonl`` on disk.

        Returns:
            int: Number of enhancements registered.
        """
        if not self.is_forge:
            return 0
        count = 0
        for item in self.items:
            if not item.item_id or not item.s_name:
                continue
            _enh.register(_enh.ForgeEnhancement(
                item_id=int(item.item_id),
                name=item.s_name,
                pattern_id=item.enh_pattern_id,
                slot=item.s_es,
                rarity=item.rarity,
                level=item.level,
                cost=item.cost,
                dps=item.dps,
                shop_id=int(self.shop_id or 0),
                shop_name=self.shop_name,
            ))
            count += 1
        return count

    def get_item(self, item_name: str):
        for item in self.items:
            if item.item_name == item_name:
                return item
        return None
