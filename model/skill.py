"""One skill-bar slot, as sent by ``sAct``.

Wire format (``{"t":"xt","b":{"r":-1,"o":{"cmd":"sAct","actions":{"active":[...]}}}}``)
observed for Legion Revenant -- 21 fields, and not every skill carries all of
them::

    nam    nam              typ   ref    tgt  tgtMax  mp    cd
    0      Malevolent Burst aa    aa     h    3       -15   1500
    1      Atramentous Shade m     a1     h    3        10   6000
    2      ...               m     a2     h    3        15   6000
    3      ...               m     a3     f    7        15   6000
    4      ...               m     a4     h    3        20  12000
    5      (scroll slot)     i     i1     f    -         0  60000

``typ``
    ``aa`` auto-attack, ``m`` a class skill, ``i`` an item/scroll slot.

``tgt``
    ``h`` hostile (needs a monster to aim at), ``f`` friendly (aims at a
    player), ``s`` self. This is what ``use_skill`` branches on, and the
    reason a cast can be refused with everything else healthy: a ``tgt="h"``
    skill with no live monster in the cell has nothing to send.

``mp``
    Signed. Slot 0 reports ``-15`` because the auto-attack *returns* mana, so
    ``MANA < mp * cost`` is never true for it.

Not always present: ``id``, ``tgtMax``, ``tgtMin`` (5 of 6 skills),
``damage``, ``dsrc``, ``auras`` (4 of 6), ``hasPassives`` (3), ``auto``,
``forceResult`` (1 each). Every accessor below therefore uses ``.get`` with a
sensible default rather than indexing.

**Why this is a dict:** ``SKILLS[n]`` is read as a mapping in ~40 places
across ``core/``, the GUIs and every bot script -- ``skill["cd"]``,
``skill.get("anim")``, ``player.SKILLS[5]["nextUse"] = now``. Subclassing
``dict`` gives typed accessors for new code while leaving every one of those
call sites untouched.
"""
from __future__ import annotations

from datetime import datetime
from typing import Any, Dict, List, Optional


class Skill(dict):
    """A skill slot: dict-compatible, with named accessors over it."""

    # --- identity -----------------------------------------------------
    @property
    def id(self) -> int:
        """Server skill id, or 0 when the payload omits it."""
        return int(self.get("id") or 0)

    @property
    def name(self) -> str:
        """Display name (``nam``); empty string when absent."""
        return str(self.get("nam") or "")

    @property
    def ref(self) -> str:
        """Short action ref used in packets, e.g. ``aa`` / ``a1`` / ``i1``."""
        return str(self.get("ref") or "")

    @property
    def description(self) -> str:
        return str(self.get("desc") or "")

    @property
    def icon(self) -> str:
        return str(self.get("icon") or "")

    @property
    def animation(self) -> str:
        """``anim`` -- what the bot assigns to ``bot.skillAnim``."""
        return str(self.get("anim") or "")

    @property
    def string_label(self) -> str:
        """``strl`` -- the animation string id keyed into ``skills_ref``."""
        return str(self.get("strl") or "")

    # --- classification ------------------------------------------------
    @property
    def type(self) -> str:
        """``typ``: ``aa`` auto-attack, ``m`` class skill, ``i`` item."""
        return str(self.get("typ") or "")

    @property
    def target(self) -> str:
        """``tgt``: ``h`` hostile, ``f`` friendly, ``s`` self."""
        return str(self.get("tgt") or "")

    @property
    def is_auto_attack(self) -> bool:
        return self.type == "aa"

    @property
    def is_item(self) -> bool:
        return self.type == "i"

    @property
    def needs_monster(self) -> bool:
        """True when casting requires a live monster in the cell.

        This is the branch behind a large share of cast refusals: a hostile
        skill with an empty cell has no target to send, so ``use_skill``
        returns False even though the slot is off cooldown.
        """
        return self.target == "h"

    @property
    def is_attack(self) -> bool:
        """Hostile skill -- the ones ``SkillMode.ATTACK_ONLY`` allows."""
        return self.target == "h"

    @property
    def is_buff(self) -> bool:
        """Friendly/self skill -- the ones ``SkillMode.BUFF_ONLY`` allows."""
        return self.target in ("f", "s")

    # --- costs and timing ---------------------------------------------
    @property
    def mana(self) -> int:
        """Signed mana delta. Negative means the skill *grants* mana."""
        try:
            return int(self.get("mp") or 0)
        except (TypeError, ValueError):
            return 0

    @property
    def cooldown_ms(self) -> int:
        """Server cooldown in ms, before any cooldown reduction."""
        try:
            return int(self.get("cd") or 0)
        except (TypeError, ValueError):
            return 0

    @property
    def max_targets(self) -> int:
        """``tgtMax`` -- how many monsters the packet hits; 1 when absent."""
        try:
            return int(self.get("tgtMax") or 1)
        except (TypeError, ValueError):
            return 1

    @property
    def min_targets(self) -> int:
        try:
            return int(self.get("tgtMin") or 1)
        except (TypeError, ValueError):
            return 1

    @property
    def range(self) -> int:
        try:
            return int(self.get("range") or 0)
        except (TypeError, ValueError):
            return 0

    @property
    def damage(self) -> float:
        """Damage coefficient (0.85 = 85% of the damage source)."""
        try:
            return float(self.get("damage") or 0.0)
        except (TypeError, ValueError):
            return 0.0

    @property
    def damage_source(self) -> str:
        """``dsrc`` -- e.g. ``SP1`` (spell power) or a physical source."""
        return str(self.get("dsrc") or "")

    @property
    def force_result(self) -> str:
        """``forceResult`` -- e.g. ``crit``; empty when the roll is free."""
        return str(self.get("forceResult") or "")

    @property
    def is_auto(self) -> bool:
        """``auto`` -- server fires it automatically (true for slot 0)."""
        return bool(self.get("auto"))

    @property
    def has_passives(self) -> bool:
        return bool(self.get("hasPassives"))

    @property
    def auras(self) -> List[Dict[str, Any]]:
        """Auras this skill applies, as sent (may contain empty objects)."""
        value = self.get("auras")
        return value if isinstance(value, list) else []

    def effective_cooldown_ms(self, cooldown_reduction: float = 0.0) -> float:
        """Cooldown after applying ``cooldown_reduction`` (already capped).

        Callers must pass ``PlayerStats.cooldown_reduction``, which clamps to
        0.5 -- see ``model.stats`` for why the raw ``$tha`` is unusable.
        """
        return self.cooldown_ms * (1.0 - max(0.0, min(cooldown_reduction, 0.5)))

    def mana_cost(self, cost_multiplier: float = 1.0) -> float:
        """Mana this skill costs right now (negative when it grants mana)."""
        return self.mana * (cost_multiplier or 1.0)

    # --- local cast state (written by bot.py / player.py) --------------
    @property
    def next_use(self) -> Optional[datetime]:
        """Local cooldown deadline; ``None`` before the slot is first used."""
        value = self.get("nextUse")
        return value if isinstance(value, datetime) else None

    @next_use.setter
    def next_use(self, when: datetime) -> None:
        self["nextUse"] = when

    @property
    def cast_count(self) -> int:
        return int(self.get("_casts") or 0)

    @cast_count.setter
    def cast_count(self, value: int) -> None:
        self["_casts"] = int(value)

    def is_ready(self, now: Optional[datetime] = None) -> bool:
        deadline = self.next_use
        if deadline is None:
            return True
        return deadline <= (now or datetime.now())

    def ready_in_ms(self, now: Optional[datetime] = None) -> float:
        """Milliseconds until this slot can fire; 0 when already ready."""
        deadline = self.next_use
        if deadline is None:
            return 0.0
        delta = (deadline - (now or datetime.now())).total_seconds() * 1000.0
        return max(0.0, delta)

    # --- construction / display ----------------------------------------
    @classmethod
    def from_payload(cls, data: Dict[str, Any]) -> "Skill":
        """Copy an ``sAct`` entry into a Skill, dropping nothing."""
        return cls(data or {})

    def describe(self) -> str:
        slot = f"{self.ref or '?'}"
        bits = [f"{slot}", f"({self.type or 'm'}/{self.target or '?'})",
                f"cd {self.cooldown_ms}", f"mp {self.mana:+d}"]
        if self.max_targets > 1:
            bits.append(f"x{self.max_targets}")
        if self.name:
            bits.append(f"-- {self.name}")
        return " ".join(bits)

    def __str__(self) -> str:  # pragma: no cover - display helper
        return f"<Skill {self.describe()}>"
