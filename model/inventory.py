"""Item model covering every field the server actually sends.

Fields observed across ``loadInventoryBig`` / ``retrieveInventory`` /
``addItems`` / ``dropItem`` (see tools/dump_payloads.py, tools/survey_enh.py).
Keys absent from a given payload fall back to a safe default, so one parser
serves all four packet shapes.

Enhancement
    Each item carries the enhancement socketed into it::

        "EnhPatternID": 10,  # WHICH enhancement  -> Valiance (identity)
        "EnhID": 70750,      # this one copy of it (unique per item)
        "iEnh": 70750,       # older alias of EnhID
        "EnhLvl": 100, "EnhRty": 7, "EnhDPS": 100, "EnhRng": 10

    Names are not sent by the server; :mod:`model.enhancement` maps the id.
"""
from __future__ import annotations

from core.utils import normalize
from enum import Enum
from typing import Any, Dict, List, Optional

from . import enhancement as _enh


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


def _int(data: Dict[str, Any], key: str, default: int = 0) -> int:
    """``int`` of a payload value, tolerating ``''``/``None``/floats."""
    try:
        return int(float(data.get(key, default) or default))
    except (TypeError, ValueError):
        return default


def _flag(data: Dict[str, Any], key: str) -> bool:
    """Read a boolean the server sends as ``0``/``1`` (or ``True``/``False``)."""
    value = data.get(key, 0)
    if isinstance(value, bool):
        return value
    try:
        return int(float(value or 0)) == 1
    except (TypeError, ValueError):
        return False


class ItemInventory:
    def __init__(self, json_data):
        data = json_data or {}
        self.raw: Dict[str, Any] = data

        # --- identity -------------------------------------------------
        # `item_name` is normalised (lower-cased) for case-insensitive
        # lookups, which is what every existing caller compares against.
        # `s_name` keeps the server's original casing -- needed for anything
        # human-facing, such as enhancement names ("Valiance", "Arcana's
        # Concerto") that must not be reported as "valiance".
        self.s_name: str = str(data.get('sName', ''))
        self.item_name: str = normalize(str(data.get('sName', '')))
        self.item_id: str = str(data.get('ItemID', ''))
        self.desc: str = str(data.get('sDesc', ''))
        self.icon: str = str(data.get('sIcon', ''))
        self.file: str = str(data.get('sFile', ''))
        self.link: str = str(data.get('sLink', ''))
        self.element: str = str(data.get('sElmt', ''))

        # --- quantity / economy ---------------------------------------
        self.qty: int = _int(data, 'iQty')
        self.qty_now: int = _int(data, 'iQtyNow')
        self.cost: int = _int(data, 'iCost')
        self.is_acs: bool = _flag(data, 'bCoins')       # Adventure Coin price
        self.is_temp: bool = _flag(data, 'bTemp')       # temp (non-inventory) item
        self.is_upgrade: bool = _flag(data, 'bUpg')     # requires upgrade / legend
        self.is_house: bool = _flag(data, 'bHouse')
        self.is_staff: bool = _flag(data, 'bStaff')
        self.stackable: int = _int(data, 'iStk')        # max stack size

        # --- slot / type ----------------------------------------------
        # ar = "Class"
        # co = "Armor"
        # ba = "Cape"
        # he = "Helm"
        # Weapon = all weapon types
        # hi = "Floor Item"
        # pe = "Pet"
        # ho = "House"
        # None = all misc types
        self.s_es: str = str(data.get('sES', ''))
        self.s_type: str = str(data.get('sType', ''))
        self.s_meta: str = str(data.get('sMeta', 0))
        self.req_quests: str = str(data.get('sReqQuests', ''))

        # --- equipped state -------------------------------------------
        self.is_equipped: bool = _flag(data, 'bEquip')
        self.is_weared: bool = _flag(data, 'bWear')
        self.char_item_id: int = _int(data, 'CharItemID')
        self.shop_item_id: str = data.get('ShopItemID', '')

        # --- item power ------------------------------------------------
        self.level: int = _int(data, 'iLvl')
        self.dps: int = _int(data, 'iDPS')
        self.rarity: int = _int(data, 'iRty')
        self.range: int = _int(data, 'iRng')

        # --- enhancement socketed into this item ------------------------
        # Shop items send `PatternID`; inventory items send `EnhPatternID`.
        # Same field, two spellings, so accept either.
        self.enh_pattern_id: int = _int(data, 'EnhPatternID',
                                        _int(data, 'PatternID'))
        self.enh_id: int = _int(data, 'EnhID', _int(data, 'iEnh'))
        self.enh_level: int = _int(data, 'EnhLvl')
        self.enh_rarity: int = _int(data, 'EnhRty')
        self.enh_dps: int = _int(data, 'EnhDPS')
        self.enh_range: int = _int(data, 'EnhRng')

        # --- quests this item turns in ---------------------------------
        self.turn_in: List[ItemInventory] = []

    # ------------------------------------------------------------------
    # enhancement helpers
    # ------------------------------------------------------------------
    @property
    def enhancement(self) -> Optional[_enh.Enhancement]:
        """The enhancement socketed here, or ``None`` when there is none."""
        if not self.enh_pattern_id and not self.enh_id:
            return None
        return _enh.Enhancement(
            item_id=self.enh_id,
            pattern_id=self.enh_pattern_id,
            level=self.enh_level,
            rarity=self.enh_rarity,
            dps=self.enh_dps,
            range=self.enh_range,
        )

    @property
    def enhancement_name(self) -> Optional[str]:
        """Display name of the socketed enhancement (``None`` if unregistered).

        Resolved from ``EnhID`` -- the unique id -- not from ``EnhPatternID``,
        which several enhancements share.
        """
        enh = self.enhancement
        return enh.name if enh else None

    @property
    def has_enhancement(self) -> bool:
        return bool(self.enh_pattern_id or self.enh_id)

    @property
    def enhancement_slot(self) -> Optional[str]:
        """Which equipment slot the socketed enhancement fits, if known."""
        enh = self.enhancement
        return enh.slot if enh else None

    # ------------------------------------------------------------------
    # display
    # ------------------------------------------------------------------
    @property
    def slot(self) -> str:
        """Human slot name (``Weapon`` stays ``Weapon``; codes are expanded)."""
        return {
            'ar': 'Class', 'co': 'Armor', 'ba': 'Cape', 'he': 'Helm',
            'pe': 'Pet', 'ho': 'House', 'hi': 'Floor Item',
        }.get(self.s_es, self.s_es or 'None')

    @property
    def is_weapon(self) -> bool:
        return self.s_es == 'Weapon'

    @property
    def is_class(self) -> bool:
        return self.s_es == 'ar'

    def describe(self) -> str:
        """One-line summary used by inspection helpers."""
        bits = [f"[{self.slot}]", self.item_name or f"item {self.item_id}"]
        if self.level:
            bits.append(f"lvl {self.level}")
        if self.dps:
            bits.append(f"dps {self.dps}")
        if self.rarity:
            bits.append(f"r{self.rarity}")
        enh = self.enhancement
        if enh:
            bits.append(enh.describe())
        if self.is_equipped:
            bits.append("(equipped)")
        return " ".join(bits)

    def __str__(self) -> str:  # pragma: no cover - display helper
        return self.describe()
