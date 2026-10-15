"""Enhancements -- weapon, helm and cape, both forge and basic.

Two captures at the repo root feed this registry.

``forge_enhancement.jsonl`` -- three forge ``loadShop`` packets::

    shop 2142  "Forge Weapon Enhancements"   sES = Weapon
    shop 2164  "Forge Helmet Enhancements"   sES = he
    shop 2143  "Forge Cape Enhancements"     sES = ba

``basic_enhancement.jsonl`` -- three basic (non-forge) ``loadShop`` packets::

    "Lucky Awe Enh"    PatternID 9   Weapon only
    "Lvl 50+ Lucky Enh" PatternID 9  Weapon / ar / ba / he
    "Lvl 50+ Wizard Enh" PatternID 6 Weapon / ar / ba / he

The same item identity rule holds for both: **the socketed ``EnhID`` is the
shop's ``ItemID``**, verified against captured inventory in
``tools/xcheck_basic_enh.py`` -- Awe Blast 52369, Wizard Armor 66435 and
Lucky Cape 66446 all come from the basic file, Valiance 70752 and Lament
71543 from the forge one.

A basic entry looks the same as a forge one::

    {"ItemID": 66435, "sName": "Wizard Armor Enhancement", "PatternID": 6,
     "sES": "ar", "iRty": 6, "iLvl": 100, "iCost": 7560, "EnhID": 0}

Note ``EnhID: 0`` -- the shop's own ``EnhID`` field is always zero; the
identity is the ``ItemID``.  Also note that one *name* spans many ids: the
Lvl 50+ shops sell the same name at every level from 51 to 100, so a name
alone does not identify a tier.  ``level`` disambiguates (see
:func:`by_name_level`), and forge names, which are one-per-id, do not need it.

Two id fields, and **they are not interchangeable**:

``ItemID`` -- what an inventory item reports as ``EnhID`` / ``iEnh``
    This is the enhancement's true identity: 78 distinct values in the shops,
    all unique, encoding both the enhancement *and* its rarity tier.  Two items
    socketed with the same enhancement at the same rarity share it.

``PatternID`` -- what an inventory item reports as ``EnhPatternID``
    A forge *pattern* family, NOT an enhancement.  It is ambiguous::

        pattern 10 = Arcana's Concerto, Forge, Lacerate, Praxis,
                     Ravenous, Smite, Valiance
        pattern 10 also spans all three slots (weapon/helm/cape "Forge")

    Every other pattern maps to exactly one name, but pattern 10 does not, so
    matching on ``EnhPatternID`` alone picks an arbitrary item.  In this
    account's inventory, "equip whatever has pattern 10" lands on
    *Battle Oracle Hood* (a helm) rather than any weapon.

A given enhancement only fits one slot, which the shop's ``sES`` states --
Valiance fits a weapon, Penitence a cape, Vim a helm.  That slot is a hard
constraint, so :func:`equip` infers it rather than leaving it to chance.

Registering beyond the captures
    :func:`register_custom` adds an id neither file covers.  10 distinct
    socketed ids in this account's inventory appear in neither file (0, 1856,
    1955, 1956, 8182, 52100, 52233, 66423, 66439, 66440) -- they come from
    shops that were never captured, so they stay unnamed.

Loading
    :func:`load` runs automatically on first use and reads **both** files in
    a single clear-then-register pass, so the two registries cannot clobber
    each other.  A missing file is not an error: that half is simply skipped
    and lookups return ``None`` rather than raising.
"""
from __future__ import annotations

import json
from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, Iterable, List, Optional, Sequence, Tuple, Union

# Equipment slots an enhancement can fit, as the server writes them.
SLOT_WEAPON = "Weapon"
SLOT_HELM = "he"
SLOT_CAPE = "ba"
SLOT_CLASS = "ar"
SLOT_ARMOR = "co"

#: Readable slot name -> server `sES` code.
SLOT_CODES = {
    "weapon": SLOT_WEAPON, "sword": SLOT_WEAPON, "gun": SLOT_WEAPON,
    "dagger": SLOT_WEAPON, "class": SLOT_CLASS, "classes": SLOT_CLASS,
    "armor": SLOT_ARMOR, "armour": SLOT_ARMOR, "cape": SLOT_CAPE,
    "helm": SLOT_HELM, "helmet": SLOT_HELM, "pet": "pe", "house": "ho",
    "floor": "hi",
    # raw codes, so passing sES verbatim also works (lookup is lowercased)
    "weapon_": SLOT_WEAPON, "ar": SLOT_CLASS, "co": SLOT_ARMOR,
    "ba": SLOT_CAPE, "he": SLOT_HELM, "pe": "pe", "ho": "ho", "hi": "hi",
}

#: `sES` code -> readable name, for messages.
SLOT_LABELS = {
    SLOT_WEAPON: "Weapon", SLOT_HELM: "Helm", SLOT_CAPE: "Cape",
    SLOT_CLASS: "Class", SLOT_ARMOR: "Armor", "pe": "Pet", "ho": "House",
}

#: Both shop captures, in the order they are registered.  ``source`` records
#: which file an entry came from so messages can say where a name lives.
FORGE_JSONL = Path(__file__).resolve().parent.parent / "forge_enhancement.jsonl"
BASIC_JSONL = Path(__file__).resolve().parent.parent / "basic_enhancement.jsonl"
DEFAULT_PATHS = (FORGE_JSONL, BASIC_JSONL)

# Kept for callers that still reference the old single-file name.
_DEFAULT_PATH = FORGE_JSONL


def slot_code(slot: Optional[str]) -> Optional[str]:
    """Normalise a slot to the server's ``sES`` code.

    Accepts readable names (``"Cape"``) and raw codes (``"ba"``).  Returns
    ``None`` for ``None``/empty, and raises ``ValueError`` for anything else so
    a typo does not silently match every slot.
    """
    if slot is None:
        return None
    key = str(slot).strip()
    if not key:
        return None
    if key in SLOT_CODES:
        return SLOT_CODES[key]
    low = key.lower()
    if low in SLOT_CODES:
        return SLOT_CODES[low]
    raise ValueError(f"unknown equipment slot {slot!r}; "
                     f"use one of {sorted(set(SLOT_CODES))}")


@dataclass(frozen=True)
class ForgeEnhancement:
    """One rarity tier of one enhancement, as sold by a forge shop."""

    item_id: int          # unique: shop ItemID == inventory EnhID/iEnh
    name: str
    pattern_id: int       # forge pattern family; NOT unique (see module docs)
    slot: str             # sES this enhancement fits
    rarity: int = 0
    level: int = 0
    cost: int = 0
    dps: int = 100
    shop_id: int = 0
    shop_name: str = ""
    #: Which capture this came from: ``"forge"``, ``"basic"`` or ``"custom"``
    #: (the last set by :func:`register_custom`, which is neither file).
    source: str = ""

    @property
    def slot_label(self) -> str:
        return SLOT_LABELS.get(self.slot, self.slot)

    @property
    def is_weapon(self) -> bool:
        return self.slot == SLOT_WEAPON

    @property
    def is_helm(self) -> bool:
        return self.slot == SLOT_HELM

    @property
    def is_cape(self) -> bool:
        return self.slot == SLOT_CAPE

    @property
    def is_class(self) -> bool:
        return self.slot == SLOT_CLASS

    def describe(self) -> str:
        return (f"{self.name} ({self.slot_label}, rarity {self.rarity}, "
                f"lvl {self.level}, pattern {self.pattern_id}, "
                f"item {self.item_id})")

    def __str__(self) -> str:  # pragma: no cover - display helper
        return f"{self.name} {self.slot_label} R{self.rarity}"


@dataclass(frozen=True)
class Enhancement:
    """The enhancement actually socketed into one inventory item.

    Built from the item's own ``EnhID``/``EnhPatternID``; ``name`` is ``None``
    when that id is not one of the forge shops we have captured (some
    enhancements come from elsewhere -- 15 distinct such ids are on this
    account).
    """

    item_id: int = 0          # EnhID / iEnh -- 0 when the item has none
    pattern_id: int = 0       # EnhPatternID
    level: int = 0            # EnhLvl
    rarity: int = 0           # EnhRty
    dps: int = 0              # EnhDPS
    range: int = 0            # EnhRng

    @property
    def record(self) -> Optional[ForgeEnhancement]:
        """The shop entry for this enhancement, when we have it."""
        return get(self.item_id)

    @property
    def name(self) -> Optional[str]:
        rec = self.record
        return rec.name if rec else None

    @property
    def slot(self) -> Optional[str]:
        """Which equipment slot this enhancement fits (``None`` if unknown)."""
        rec = self.record
        return rec.slot if rec else None

    @property
    def is_known(self) -> bool:
        return self.record is not None

    def describe(self) -> str:
        rec = self.record
        if rec:
            return rec.describe()
        return (f"enhancement item {self.item_id} (pattern {self.pattern_id}, "
                f"lvl {self.level}, rarity {self.rarity}) -- not in the "
                f"captured forge shops")

    def __str__(self) -> str:  # pragma: no cover - display helper
        return self.name or f"EnhID#{self.item_id}"


# ----------------------------------------------------------------------
# registry
# ----------------------------------------------------------------------
_BY_ITEM: Dict[int, ForgeEnhancement] = {}
_BY_PATTERN: Dict[int, List[ForgeEnhancement]] = {}
_BY_NAME: Dict[str, List[ForgeEnhancement]] = {}
_BY_SLOT: Dict[str, List[ForgeEnhancement]] = {}
#: Tuple of paths the registry was last built from (plural -- see load()).
_LOADED_FROM: Optional[Tuple[Path, ...]] = None
_LOAD_ATTEMPTED = False


def load(path: Optional[Path] = None, *, force: bool = False) -> int:
    """(Re)build the registry from the shop captures, returning entry count.

    With no ``path``, reads every file in :data:`DEFAULT_PATHS` -- the forge
    *and* the basic captures -- in a **single** clear-then-register pass.  That
    ordering matters: clearing per file would leave only the last file's
    entries, so the forge registry would silently vanish as soon as basic
    enhancements were added.

    A missing file is skipped rather than raising, so a checkout with only one
    capture still loads the other.  Returns the total number of entries
    registered.
    """
    global _LOADED_FROM, _LOAD_ATTEMPTED
    paths = (Path(path),) if path else DEFAULT_PATHS
    if not force and _LOADED_FROM == paths and _BY_ITEM:
        return len(_BY_ITEM)
    if not any(p.exists() for p in paths):
        _LOAD_ATTEMPTED = True
        return 0

    entries: List[ForgeEnhancement] = []
    for target in paths:
        if not target.exists():
            continue
        entries.extend(_read_shop_file(target))

    _BY_ITEM.clear()
    _BY_PATTERN.clear()
    _BY_NAME.clear()
    _BY_SLOT.clear()
    for entry in entries:
        register(entry)
    _LOADED_FROM = paths
    _LOAD_ATTEMPTED = True
    return len(entries)


def _read_shop_file(target: Path) -> List[ForgeEnhancement]:
    """Parse one shop-packet jsonl into registry entries.

    Source is derived from the file name so a caller can point ``load`` at a
    differently-named capture and still get a sensible tag.
    """
    source = "basic" if target.name == BASIC_JSONL.name else "forge"
    entries: List[ForgeEnhancement] = []
    for line_no, line in enumerate(
            target.read_text(encoding="utf-8").splitlines(), 1):
        if not line.strip():
            continue
        try:
            payload = json.loads(line)
        except ValueError as exc:
            raise ValueError(f"{target.name}:{line_no}: not valid JSON") from exc
        shop = (payload.get("b") or {}).get("o") or {}
        info = shop.get("shopinfo") or {}
        shop_id = int(info.get("ShopID", 0))
        shop_name = str(info.get("sName", ""))
        for item in info.get("items") or []:
            entries.append(ForgeEnhancement(
                item_id=int(item["ItemID"]),
                name=str(item.get("sName", "")),
                pattern_id=int(item.get("PatternID", 0) or 0),
                slot=str(item.get("sES", "")),
                rarity=int(item.get("iRty", 0) or 0),
                level=int(item.get("iLvl", 0) or 0),
                cost=int(item.get("iCost", 0) or 0),
                dps=int(item.get("iDPS", 0) or 0),
                shop_id=shop_id,
                shop_name=shop_name,
                source=source,
            ))
    return entries


def _ensure_loaded() -> None:
    if not _LOAD_ATTEMPTED:
        load()


def register(entry: ForgeEnhancement) -> ForgeEnhancement:
    """Add (or replace) one enhancement in the registry."""
    _BY_ITEM[entry.item_id] = entry
    _BY_PATTERN.setdefault(entry.pattern_id, []).append(entry)
    _BY_NAME.setdefault(entry.name.strip().lower(), []).append(entry)
    _BY_SLOT.setdefault(entry.slot, []).append(entry)
    return entry


def register_custom(item_id: int, name: str, pattern_id: int = 0,
                    slot: str = "", rarity: int = 0, level: int = 0) -> ForgeEnhancement:
    """Add an enhancement neither capture covers.

    Needed for enhancements bought outside the forge and basic shops -- this
    account owns 10 distinct ``EnhID`` values (1856, 1955, 8182, 66440, ...)
    with no shop entry in either file.  Tagged ``source="custom"`` so it is
    distinguishable from a captured record.
    """
    return register(ForgeEnhancement(
        item_id=int(item_id), name=str(name), pattern_id=int(pattern_id),
        slot=slot or "", rarity=int(rarity), level=int(level),
        source="custom",
    ))


# ----------------------------------------------------------------------
# lookup
# ----------------------------------------------------------------------
def get(item_id: Optional[int]) -> Optional[ForgeEnhancement]:
    """The enhancement with this exact ``EnhID``, or ``None``."""
    if not item_id:
        return None
    _ensure_loaded()
    return _BY_ITEM.get(int(item_id))


def all_enhancements() -> List[ForgeEnhancement]:
    _ensure_loaded()
    return list(_BY_ITEM.values())


def find(name: str, slot: Optional[str] = None) -> List[ForgeEnhancement]:
    """Every rarity tier of ``name``, optionally restricted to one slot.

    Sorted cheapest-first, so ``find(...)[0]`` is the entry-level version.
    """
    _ensure_loaded()
    rows = _BY_NAME.get(str(name).strip().lower(), [])
    code = slot_code(slot)
    if code:
        rows = [r for r in rows if r.slot == code]
    return sorted(rows, key=lambda r: (r.level, r.rarity, r.cost))


def best(name: str, slot: Optional[str] = None) -> Optional[ForgeEnhancement]:
    """Highest-level tier of ``name``, or ``None`` if unregistered."""
    rows = find(name, slot=slot)
    return rows[-1] if rows else None


def by_pattern(pattern_id: int) -> List[ForgeEnhancement]:
    """Everything sharing a forge pattern. **Not** a single enhancement."""
    _ensure_loaded()
    return list(_BY_PATTERN.get(int(pattern_id), []))


def by_name_level(name: str, level: int, slot: Optional[str] = None,
                  rarity: Optional[int] = None) -> List[ForgeEnhancement]:
    """The tiers of ``name`` sold at exactly ``level``, optionally by rarity.

    The basic shops sell one name at every level from 51 to 100, so a name
    alone identifies a *family* and ``level`` narrows it down.  Forge names are
    one-per-id, so for them this is the same set as :func:`find` whenever
    ``level`` matches, and empty when it does not -- which is the point:
    asking for level 30 of a level-100-only enhancement must not silently hand
    back a different tier.

    **Level is not unique at the cap.**  The Lvl 50+ shops carry 51 entries
    but only 50 distinct levels: level 100 exists twice, once at rarity 5 and
    once at rarity 6.  So ``level=100`` may return two records -- pass
    ``rarity`` to pin down which, or take the highest-rarity one (see
    :func:`best_tier`), which is the strictly stronger item at identical cost.

    Example::

        by_name_level("Wizard Armor Enhancement", 100)          # R5 + R6
        by_name_level("Wizard Armor Enhancement", 100, rarity=6)  # -> 52276
        by_name_level("Wizard Armor Enhancement", 51)           # -> 19638
        by_name_level("Valiance", 100)                          # -> 70752
    """
    _ensure_loaded()
    rows = find(name, slot=slot)
    rows = [r for r in rows if r.level == int(level)]
    if rarity is not None:
        rows = [r for r in rows if r.rarity == int(rarity)]
    return rows


def best_tier(name: str, level: int, slot: Optional[str] = None
              ) -> Optional[ForgeEnhancement]:
    """Highest-rarity tier of ``name`` at ``level``, or ``None``.

    The deterministic answer when :func:`by_name_level` returns several: at
    level 100 both candidates cost the same, so the higher rarity is simply
    the better item.
    """
    rows = by_name_level(name, level, slot=slot)
    if not rows:
        return None
    return max(rows, key=lambda r: (r.rarity, r.item_id))


def by_slot(slot: str) -> List[ForgeEnhancement]:
    """Every enhancement that fits equipment slot ``slot``."""
    _ensure_loaded()
    return list(_BY_SLOT.get(slot_code(slot) or "", []))


def names(slot: Optional[str] = None) -> List[str]:
    """Distinct enhancement names, optionally for one slot."""
    _ensure_loaded()
    rows = by_slot(slot) if slot else list(_BY_ITEM.values())
    return sorted({r.name for r in rows}, key=str.lower)


def slots_of(name: str) -> List[str]:
    """Which slots an enhancement fits -- more than one for pattern-10 names."""
    return sorted({SLOT_LABELS.get(r.slot, r.slot) for r in find(name)})


def is_pattern_unique(pattern_id: int) -> bool:
    """True when a pattern id maps to exactly one enhancement name.

    Useful as a guard: matching on ``EnhPatternID`` is only sound when this
    holds, and it does not hold for pattern 10.
    """
    rows = by_pattern(pattern_id)
    return bool(rows) and len({r.name for r in rows}) == 1


# ----------------------------------------------------------------------
# resolving a caller's target
# ----------------------------------------------------------------------
def resolve_ids(target: Union[int, str]) -> Tuple[set, set]:
    """Turn a caller's target into ``(item_ids, pattern_ids)``.

    Accepts an ``EnhID`` (70752), an enhancement name (``"Valiance"``), or a
    numeric string.  Both sets are returned because inventory items sometimes
    report ``EnhID: 0`` while still carrying ``EnhPatternID``; callers match on
    ``item_ids`` first and only fall back to ``pattern_ids`` when ``EnhID`` is
    absent (see :func:`item_matches`).
    """
    _ensure_loaded()
    if isinstance(target, bool):
        return set(), set()
    if isinstance(target, int):
        item_id = int(target)
        if item_id in _BY_ITEM:
            return {item_id}, {_BY_ITEM[item_id].pattern_id}
        # Not a known EnhID. Legacy call sites passed EnhPatternID (for
        # example equip_item_by_enhancement(29) for Penitence), so expand the
        # pattern into every rarity tier it covers -- otherwise an item that
        # *does* report an EnhID could never match a pattern-only target.
        rows = by_pattern(item_id)
        if rows:
            return {r.item_id for r in rows}, {item_id}
        # Neither a known EnhID nor a known pattern.  Ten socketed ids on this
        # account (1856, 1955, 8182, 66440, ...) came from shops we never
        # captured, so there is no name for them -- but the id still identifies
        # the enhancement uniquely and matching it against inventory is exactly
        # what the pre-registry equip_item_by_enhancement(enh_id) did.  Refusing
        # here would be a regression, so accept it as a raw id.  Pattern ids
        # are small (1..30) and EnhIDs are large (1856+), so the two do not
        # collide in practice.
        return {item_id}, {item_id}
    text = str(target).strip()
    if not text:
        return set(), set()
    if text.lstrip("-").isdigit():
        return resolve_ids(int(text))
    rows = find(text)
    return ({r.item_id for r in rows}, {r.pattern_id for r in rows})


def item_matches(item, target: Union[int, str],
                 slot: Optional[str] = None) -> bool:
    """Whether inventory ``item`` carries ``target``'s enhancement.

    Prefers the item's unique ``enh_id``.  Falls back to ``enh_pattern_id``
    only when the item reports no ``enh_id`` -- pattern matching on an item
    that *does* have an id would wrongly equate the seven pattern-10
    enhancements.
    """
    item_ids, pattern_ids = resolve_ids(target)
    if not item_ids and not pattern_ids:
        return False

    code = slot_code(slot)
    if code and getattr(item, "s_es", None) != code:
        return False

    enh_id = getattr(item, "enh_id", 0)
    if enh_id:
        return enh_id in item_ids
    return getattr(item, "enh_pattern_id", 0) in pattern_ids
