"""Player stat block from the server's ``stu`` packet.

Wire format (``{"t":"xt","b":{"r":-1,"o":{"cmd":"stu","sta":{...}}}}``)::

    sta = {
      "_STR": 46,  "$STR": 126,      # _X = base, $X = current (buffed)
      "_END": 152, "$END": 182,
      "_DEX": 84,  "$DEX": 84,
      "_INT": 251, "$INT": 481,
      "_WIS": 114, "$WIS": 209,
      "_LCK": 114, "$LCK": 335,
      "$dsh": 50, "$ap": 252, "$sp": 1196,
      "$tdo": .1942, "$tcr": .3209, "$thi": .0956, "$tha": .2258,
      "$cao": 1.15, "$cai": 1, "$cmo": 2.0108, "$cmi": .3892,
      "$cpo": 1, "$cpi": 1, "$cdo": 1, "$cdi": 1,
      "$cho": 1, "$chi": .5, "$cmc": 1, "$scm": 3.627,
      "$shb": 0, "$smb": 0,
    }
    wDPS: 110

    Secondary stats: ``$thi`` hit (+90% base), ``$tdo`` evasion, ``$tcr`` crit,
    ``$tha`` haste (cap 0.5).  Combat multipliers are ``$c*o`` out / ``$c*i`` in,
    keyed a=all, p=physical, m=magical, d=DoT, h=healing (e.g. Penitence shows
    ``$cai``/``$cdo`` at 0.75).
    tempSta: {he: {...}, ar: {...}, ba: {...}, Weapon: {...}}   # per-slot bonus

**The server sends deltas.**  A full snapshot arrives on login/area change;
every later ``stu`` carries only the keys that *changed* (observed packets with
as few as 2 keys).  So :meth:`PlayerStats.update` merges, never replaces.

Cooldown reduction
------------------
``$tha`` is reported as high as **0.8444**, but skills never recast anywhere
near that fast.  ``tools/verify_cdr_cap.py`` checks this against the validated
capture and the answer is unambiguous -- observed minimum same-slot gaps versus
``base * (1 - cdr) + CD_START_DELAY_MS``::

      slot   base     obs min    cap .5   no cap
        0    1500      956ms     950ms     433ms
        1    6000     3202ms    3200ms    1134ms
        2    6000     3203ms    3200ms    1134ms
        3    6000     3202ms    3200ms    1134ms
        4   12000     6234ms    6200ms    2067ms

Every slot matches the capped figure to within 4-34 ms, and 84% of the ``$tha``
packets in that run were above 0.5 -- so the cap is load-bearing, not a
theoretical corner.  **The usable value is ``min($tha, 0.5)``**, exposed as
:attr:`PlayerStats.cooldown_reduction`.  Using the raw value would recast ~2.8x
too early and get the casts rejected.
"""
from __future__ import annotations

from typing import Any, Dict, Optional

#: The server reports `$tha` up to 0.8444 but only honours 0.5 for cooldowns.
#: See module docstring -- verified against capture_20261004_210744.jsonl.
MAX_COOLDOWN_REDUCTION = 0.5

#: Attributes with a `_X` (base) and `$X` (current) pair.
ATTRIBUTES = ("STR", "INT", "DEX", "WIS", "END", "LCK")

#: Equipment slots the server uses in `tempSta`.
SLOT_LABELS = {
    "he": "Helm",
    "ar": "Class",
    "co": "Armor",
    "ba": "Cape",
    "Weapon": "Weapon",
    "pe": "Pet",
}


def _num(value: Any) -> float:
    """Coerce a payload value to float, or 0.0 when it is absent/malformed."""
    if isinstance(value, bool):
        return float(value)
    try:
        return float(value)
    except (TypeError, ValueError):
        return 0.0


class PlayerStats:
    """Merged view of every ``stu`` packet seen so far."""

    def __init__(self) -> None:
        #: every raw key ever received, keyed exactly as the server sent it
        self.values: Dict[str, float] = {}
        #: per-equipment-slot stat contributions (from `tempSta`)
        self.slot_stats: Dict[str, Dict[str, float]] = {}
        #: weapon DPS reported alongside `sta`
        self.weapon_dps: float = 0.0
        #: number of `stu` packets merged in
        self.updates: int = 0
        #: set when a packet carried the full snapshot (base `_X` keys present)
        self.is_complete: bool = False

    # ------------------------------------------------------------------
    # ingest
    # ------------------------------------------------------------------
    def update(self, sta: Optional[Dict[str, Any]],
               temp_sta: Optional[Dict[str, Any]] = None,
                wdps: Any = None) -> None:
        """Merge one ``stu`` payload.

        Only the keys present are applied, because the server sends deltas.
        """
        if isinstance(sta, dict):
            for key, value in sta.items():
                if isinstance(value, (int, float)) and not isinstance(value, bool):
                    self.values[key] = float(value)
            self.updates += 1
            # a base-attribute key only ever appears in the full snapshot
            if any(k.startswith("_") for k in sta):
                self.is_complete = True

        if isinstance(temp_sta, dict):
            for slot, stats in temp_sta.items():
                if isinstance(stats, dict):
                    target = self.slot_stats.setdefault(str(slot), {})
                    for key, value in stats.items():
                        target[key] = _num(value)

        if wdps is not None:
            self.weapon_dps = _num(wdps)

    # ------------------------------------------------------------------
    # raw access
    # ------------------------------------------------------------------
    def get(self, key: str, default: float = 0.0) -> float:
        return self.values.get(key, default)

    def has(self, key: str) -> bool:
        return key in self.values

    @property
    def keys(self):
        return self.values.keys()

    # ------------------------------------------------------------------
    # attributes
    # ------------------------------------------------------------------
    def attribute(self, name: str) -> float:
        """Current (buffed) value of an attribute, e.g. ``attribute("INT")``."""
        return self.values.get(f"${name}", 0.0)

    def base_attribute(self, name: str) -> float:
        """Unbuffed base value of an attribute."""
        return self.values.get(f"_{name}", 0.0)

    @property
    def attributes(self) -> Dict[str, float]:
        return {a: self.attribute(a) for a in ATTRIBUTES}

    @property
    def base_attributes(self) -> Dict[str, float]:
        return {a: self.base_attribute(a) for a in ATTRIBUTES}

    # ------------------------------------------------------------------
    # the two that drive behaviour
    # ------------------------------------------------------------------
    @property
    def haste(self) -> float:
        """Raw ``$tha`` as reported -- can exceed the usable cap."""
        return self.get("$tha")

    @property
    def cooldown_reduction(self) -> float:
        """Cooldown reduction actually usable: ``min($tha, 0.5)``.

        This is what skill timers must use; see the module docstring.
        """
        return min(self.haste, MAX_COOLDOWN_REDUCTION)

    @property
    def mana_cost_multiplier(self) -> float:
        """``$cmc`` -- multiplier on a skill's mana cost (1.0 when unknown)."""
        return self.get("$cmc", 1.0) or 1.0

    @property
    def haste_incoming(self) -> float:
        return self.get("$thi")

    @property
    def skill_cost_modifier(self) -> float:
        """``$scm`` -- reported alongside ``$tha``; not yet used by the bot."""
        return self.get("$scm")

    def mana_cost(self, base_cost: int) -> float:
        """Mana a skill of ``base_cost`` actually costs right now."""
        return base_cost * self.mana_cost_multiplier

    # ------------------------------------------------------------------
    # damage / mitigation
    # ------------------------------------------------------------------
    @property
    def attack_power(self) -> float:
        return self.get("$ap")

    @property
    def spell_power(self) -> float:
        return self.get("$sp")

    @property
    def outgoing_damage(self) -> float:
        return self.get("$tdo")

    @property
    def incoming_damage(self) -> float:
        """``$tcr`` -- damage the player takes. Higher = squishier."""
        return self.get("$tcr")

    @property
    def is_squishy(self) -> bool:
        """Heuristic: taking an unusually large share of incoming damage."""
        value = self.incoming_damage
        return bool(value) and value > 0.7

    # ------------------------------------------------------------------
    # per-slot contributions
    # ------------------------------------------------------------------
    def slot_contribution(self, slot: str) -> Dict[str, float]:
        """Stats one gear slot contributes, e.g. ``slot_contribution("ba")``."""
        return dict(self.slot_stats.get(slot, {}))

    @property
    def contributions(self) -> Dict[str, Dict[str, float]]:
        """``tempSta`` with slot codes replaced by readable names."""
        return {SLOT_LABELS.get(slot, slot): dict(stats)
                for slot, stats in self.slot_stats.items()}

    # ------------------------------------------------------------------
    # display
    # ------------------------------------------------------------------
    def summary(self) -> str:
        parts = [f"{a}={self.attribute(a):.0f}" for a in ATTRIBUTES]
        parts.append(f"haste={self.haste:.4f}(usable {self.cooldown_reduction:.4f})")
        parts.append(f"cmc={self.mana_cost_multiplier:g}")
        parts.append(f"wDPS={self.weapon_dps:g}")
        return " ".join(parts)

    def __str__(self) -> str:  # pragma: no cover - display helper
        return f"<PlayerStats {self.summary()} n={self.updates}>"
