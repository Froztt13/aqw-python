"""Manual configuration for the ultra bots: accounts and per-boss loadouts.

**This is the file you fill in by hand.**  ``bot/ultra/README.md`` walks through
it step by step; the short version:

* gear is named by **enhancement**, never by item -- except the class, which has
  no enhancement that identifies it uniquely;
* if an enhancement you name cannot be resolved, the bot **stops** rather than
  fighting with whatever happened to be equipped.

Two registries back the enhancement names:

===============================  =========================================
``forge_enhancement.jsonl``      forge shops -- one name per id, e.g.
                                 ``Valiance``, ``Forge``, ``Penitence``
``basic_enhancement.jsonl``      basic shops -- one name across many levels,
                                 e.g. ``Awe Blast``, ``Lucky Helm
                                 Enhancement``
===============================  =========================================

Both are read by :func:`model.enhancement.load`, so a name works the same way
whichever file it came from.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, Optional, Tuple, Union

__all__ = [
    "AccConfig",
    "Enhance",
    "EnhSpec",
    "Loadout",
    "ACCOUNTS",
    "SERVER",
    "LOADOUTS",
    "SOLO_LOADOUTS",
    "SOLO_ROLES",
    "get_solo_loadout",
    "get_solo_role",
    "get_loadout",
    "loadout_bosses",
    "GEAR_SLOTS",
    "SLOT1",
    "SLOT2",
    "SLOT3",
    "SLOT4",
]


# ---------------------------------------------------------------------------
# accounts
# ---------------------------------------------------------------------------

#: Server every account logs into.  One value so the two launchers cannot drift.
SERVER = "alteon"


class AccConfig:
    """One account's login details.

    Args:
        username: AQW account name.
        password: AQW password.
        server: Overrides :data:`SERVER` for this account only.
    """

    def __init__(self, username: str, password: str,
                 server: str = SERVER) -> None:
        self.username = username
        self.password = password
        self.server = server

    def __repr__(self) -> str:  # pragma: no cover - display helper
        return f"AccConfig({self.username!r}, server={self.server!r})"


#: The four accounts, in launcher order.  ``py -m bot.ultra.daily`` pipes ``1``
#: through ``4`` on stdin, and ``slaves[n]`` is what that input selects -- so
#: the order here *is* the 2x2 pane layout of the ``.bat`` launchers.
#: Slot 1 is also the account the others follow.
#:
#: Credentials are placeholders: fill in the real logins locally and do NOT
#: commit them.  ``ACCOUNT_1..4`` match the launcher pane order.
ACCOUNTS: list[AccConfig] = [
    AccConfig("ACCOUNT_1_USERNAME", "ACCOUNT_1_PASSWORD"),
    AccConfig("ACCOUNT_2_USERNAME", "ACCOUNT_2_PASSWORD"),
    AccConfig("ACCOUNT_3_USERNAME", "ACCOUNT_3_PASSWORD"),
    AccConfig("ACCOUNT_4_USERNAME", "ACCOUNT_4_PASSWORD"),
]


# ---------------------------------------------------------------------------
# gear specs
# ---------------------------------------------------------------------------

@dataclass(frozen=True)
class Enhance:
    """An enhancement to socket, optionally pinned to one tier.

    Basic shops sell a single name at every level from 51 to 100, so a bare
    name addresses the whole family and matches whatever tier you own.  Pin it
    only when you own several tiers of the same enhancement and need a
    specific one::

        "Awe Blast"                       # any tier you own
        Enhance("Awe Blast", level=100)   # only the level-100 tier
        Enhance("Awe Blast", level=100, rarity=7)   # level 100 exists at two
                                                    # rarities; this picks R7

    Forge names are one-per-id, so ``level`` is unnecessary for them -- and if
    it does not match, the lookup returns nothing and the bot stops.

    Args:
        name: Enhancement name exactly as it appears in the shop capture.
        level: Optional tier pin, 51..100 for basic enhancements.
        rarity: Optional rarity pin, needed only at the level-100 cap.
    """

    name: str
    level: Optional[int] = None
    rarity: Optional[int] = None


#: What a loadout slot accepts: a bare name, an :class:`Enhance` to pin a tier,
#: or ``None`` to leave that equipment slot alone.
EnhSpec = Union[str, Enhance, None]


@dataclass(frozen=True)
class Loadout:
    """Everything one slot equips before a boss fight.

    Gear is expressed as **enhancement names** -- ``equip_enhancement`` finds
    whichever inventory item carries it.  The class is the one item name here:
    many classes share a socketed enhancement, so no enhancement identifies a
    class uniquely.  Scroll names stay as names too, because a scroll is its
    own equipment type and carries no enhancement.

    **The field is the slot.**  ``apply_loadout`` passes it explicitly, so a
    name that exists in more than one slot stays unambiguous -- ``Forge``
    alone has 24 tiers across Weapon, cape and helm in the captures, and
    ``helm="Forge"`` still equips the helm.

    Args:
        cls: Class item name, e.g. ``"Legion Revenant"``.
        weapon: Weapon enhancement.  ``None`` leaves the slot untouched --
            used where the old code named no gear at all.
        cape: Cape enhancement.
        helm: Helm enhancement.
        scroll: Scroll item name, or ``None`` for none.
        monster_prio: Comma-separated target for ``use_skill`` /
            ``is_monster_alive``.  Empty string means "whatever is alive" --
            the fight targets no monster specifically.
        kill_order: Bosses to clear one after another before the main target
            (only Ultra Grammiel uses this; it walks the list in order).
    """

    cls: str
    weapon: EnhSpec = None
    cape: EnhSpec = None
    helm: EnhSpec = None
    scroll: Optional[str] = None
    monster_prio: str = ""
    kill_order: Tuple[str, ...] = ()


# ---------------------------------------------------------------------------
# the four launcher slots
# ---------------------------------------------------------------------------
#
# The ints below are what ``.bat`` pipes on stdin, not job titles: slot 1 plays
# Quantum Chronomancer in Ultra Tyndarius but Legendary Hero in Ultra Warden.
# Each boss's table says what its own slots wear.

SLOT1 = 1
SLOT2 = 2
SLOT3 = 3
SLOT4 = 4


#: Equipment slot each gear field is pinned to when equipping.  ``apply_loadout``
#: reads this, so a name that exists in several slots (``Forge``) is always
#: searched in the right one.
GEAR_SLOTS: Dict[str, str] = {
    "weapon": "Weapon",
    "helm": "he",
    "cape": "ba",
}


# ---------------------------------------------------------------------------
# reusable bundles
# ---------------------------------------------------------------------------
#
# Most bosses reuse the same four slot builds, so they are named once here and
# referenced by each boss.  A boss that differs writes its slots out in full --
# see Ultra Warden's SLOT1.  Edit a bundle to change every boss that uses it;
# edit a boss's own table to change just that boss.

#: Slot 2 across Tyndarius / Engineer / Warden / Ezrajal / Drakath: tanky DPS.
STANDARD_SLOT2 = dict(
    cls="Legion Revenant",
    weapon="Arcana's Concerto",
    cape="Vainglory",
    helm="Forge",
)

#: Slot 3 across Tyndarius / Engineer / Warden / Ezrajal / Drakath: support.
#:
#: ``weapon="Awe Blast"`` is the **Lucky Awe Blast** -- the basic-shop family
#: sold in the Lucky Awe Enh shop, not a forge enhancement.  It has 11 tiers
#: (levels 1..100) all in the Weapon slot, and this account owns exactly one
#: of them (52369, level 100, rarity 7), so no ``level=`` is needed.  Pin it
#: with ``Enhance("Awe Blast", level=100)`` only if you own more than one tier
#: and need a specific one.
STANDARD_SLOT3 = dict(
    cls="Lord Of Order",
    weapon="Awe Blast",                 # Lucky Awe Blast (basic, Weapon)
    cape="Penitence",
    helm="Lucky Helm Enhancement",
)

#: Slot 4 across Tyndarius / Engineer / Warden / Ezrajal / Drakath: support.
STANDARD_SLOT4 = dict(
    cls="ArchPaladin",
    weapon="Ravenous",
    cape="Penitence",
    helm="Lucky Helm Enhancement",
)


# ---------------------------------------------------------------------------
# loadouts: boss -> launcher slot -> what that slot equips
# ---------------------------------------------------------------------------
#
# `monster_prio` / `kill_order` live here because they vary by slot inside one
# boss (Ultra Tyndarius sends slot 1 at id.1 and slot 2 at id.3).
#
# **Every loadout in this table brings ``scroll="Scroll of Enrage"``** -- the
# four bosses and all four slots of each.  ``monster_prio`` is re-read on every
# rotation step, so a target listed first is hit for as long as it is alive and
# picked up again the moment it respawns; when the whole list is dead the skill
# falls through to whatever else is alive in the cell, which is how the boss
# itself gets hit once the adds are down.
LOADOUTS: Dict[str, Dict[int, Loadout]] = {
    "tyndarius": {
        SLOT1: Loadout(
            cls="Quantum Chronomancer",
            weapon="Valiance",
            cape="Lament",
            helm="Forge",
            scroll="Scroll of Enrage",
            monster_prio="id.1,id.3,id.2",
        ),
        SLOT2: Loadout(**STANDARD_SLOT2,
                       scroll="Scroll of Enrage",
                       monster_prio="id.3,id.1,id.2"),
        SLOT3: Loadout(**STANDARD_SLOT3,
                       scroll="Scroll of Enrage",
                       monster_prio="id.2"),
        SLOT4: Loadout(**STANDARD_SLOT4,
                       scroll="Scroll of Enrage",
                       monster_prio="id.2"),
    },
    "engineer": {
        SLOT1: Loadout(
            cls="Quantum Chronomancer",
            weapon="Valiance",
            cape="Lament",
            helm="Forge",
            scroll="Scroll of Enrage",
            monster_prio="Attack Drone,Defense Drone",
        ),
        SLOT2: Loadout(**STANDARD_SLOT2,
                       scroll="Scroll of Enrage",
                       monster_prio="Attack Drone,Defense Drone"),
        SLOT3: Loadout(**STANDARD_SLOT3,
                       scroll="Scroll of Enrage",
                       monster_prio="Attack Drone,Defense Drone"),
        SLOT4: Loadout(**STANDARD_SLOT4,
                       scroll="Scroll of Enrage",
                       monster_prio="Attack Drone,Defense Drone"),
    },
    # Warden deviates on gear: slot 1 is Legendary Hero on Forge, not QCM on
    # Lament.  Its scroll is the same as everywhere else -- Enrage.
    "warden": {
        SLOT1: Loadout(
            cls="Legendary Hero",
            weapon="Ravenous",
            cape="Penitence",
            helm="Forge",
            scroll="Scroll of Enrage",
        ),
        SLOT2: Loadout(**STANDARD_SLOT2,
                       scroll="Scroll of Enrage"),
        SLOT3: Loadout(**STANDARD_SLOT3,
                       scroll="Scroll of Enrage"),
        SLOT4: Loadout(**STANDARD_SLOT4,
                       scroll="Scroll of Enrage"),
    },
    "ezrajal": {
        SLOT1: Loadout(
            cls="Quantum Chronomancer",
            weapon="Valiance",
            cape="Lament",
            helm="Forge",
            scroll="Scroll of Enrage",
        ),
        SLOT2: Loadout(**STANDARD_SLOT2,
                       scroll="Scroll of Enrage"),
        SLOT3: Loadout(**STANDARD_SLOT3,
                       scroll="Scroll of Enrage"),
        SLOT4: Loadout(**STANDARD_SLOT4,
                       scroll="Scroll of Enrage"),
    },
    # Grammiel has its own four builds and one shared scroll; `kill_order`
    # clears the two side crystals before Gramiel himself.
    "grammiel": {
        SLOT1: Loadout(
            cls="LightCaster",
            weapon="Valiance",
            cape="Penitence",
            helm="Wizard Helm Enhancement",
            scroll="Scroll of Enrage",
            kill_order=("id.3", "id.2"),
        ),
        SLOT2: Loadout(
            cls="Obsidian Paladin Chronomancer",
            weapon="Mana Vamp",
            cape="Penitence",
            helm="Lucky Helm Enhancement",
            scroll="Scroll of Enrage",
            kill_order=("id.2", "id.3"),
        ),
        SLOT3: Loadout(
            cls="Lord Of Order",
            weapon="Arcana's Concerto",
            cape="Penitence",
            helm="Forge",
            scroll="Scroll of Enrage",
            kill_order=("id.3", "id.2"),
        ),
        SLOT4: Loadout(
            cls="StoneCrusher",
            weapon="Valiance",
            cape="Penitence",
            helm="Wizard Helm Enhancement",
            scroll="Scroll of Enrage",
            kill_order=("id.2", "id.3"),
        ),
    },
    # Champion Drakath equips and stops -- it has no fight loop yet, so the
    # slots are here ready for when it does.
    "drakath": {
        SLOT1: Loadout(
            cls="StoneCrusher",
            weapon="Valiance",
            cape="Lament",
            helm="Forge",
            scroll="Scroll of Enrage",
        ),
        SLOT2: Loadout(
            cls="Legion Revenant",
            weapon="Arcana's Concerto",
            cape="Vainglory",
            helm="Wizard Helm Enhancement",
            scroll="Scroll of Enrage",
        ),
        SLOT3: Loadout(**STANDARD_SLOT3,
                       scroll="Scroll of Enrage"),
        SLOT4: Loadout(**STANDARD_SLOT4,
                       scroll="Scroll of Enrage"),
    },
}


# ---------------------------------------------------------------------------
# speaker loadouts: keyed by class, not by launcher slot
# ---------------------------------------------------------------------------
#
# Ultra Speaker has no slots -- it fights whatever ``Bot(soloClass=...)`` was
# given, and equips the gear that matches *that* class.
#
# The three gear fields used to be empty strings in `ultra_speaker.py` with a
# comment beside each.  The comments are the intent, so they are filled in
# here, and the original comment is quoted above each line.  The mapping
# resolves the comment offset: the note on the `"class"` line is the *weapon*
# (Arcana / Lace / Valiance / Dauntless are all weapon enhancements), the note
# on the `"helm"` line is the helm, the note on the `"cape"` line is the cape.
# The note on the `"weapon"` line repeated the helm in three of the four
# entries and is not used.
#
# If the inference is wrong for your account, this is the one place to fix it.

SOLO_LOADOUTS: Dict[str, Loadout] = {
    "legion revenant": Loadout(
        cls="Legion Revenant",
        weapon="Arcana's Concerto",      # was: # Arcana
        helm="Wizard Helm Enhancement",  # was: # Wizard
        cape="Penitence",                # was: # Penitence
        scroll="Scroll of Enrage",
    ),
    "archpaladin": Loadout(
        cls="ArchPaladin",
        weapon="Lacerate",               # kept: owned, dodge-heavy boss utility
        helm="Forge",                    # party pick (was Lucky)
        cape="Penitence",                # was: # Penitence
        scroll="Scroll of Enrage",
    ),
    "lord of order": Loadout(
        cls="Lord Of Order",
        weapon="Valiance",               # was: # Valiance
        helm="Lucky Helm Enhancement",   # was: # Luck
        cape="Penitence",                # was: # Penitence
        scroll="Scroll of Enrage",
    ),
    "verus doomknight": Loadout(
        cls="Verus DoomKnight",
        weapon="Ravenous",               # party pick (was Dauntless: self Cannot-Heal)
        helm="Anima",                    # kept: Forge ownership on this account unproven
        cape="Penitence",                # was: # Penitence
        scroll="Scroll of Enrage",
    ),
}


#: Which class each launcher pane wears, in pane order.  ``echo 1 | py -m
#: bot.ultra.ultra_speaker`` takes entry 1, ``echo 2`` entry 2, and so on --
#: the same index as :data:`ACCOUNTS`, so pane *n* logs in as account *n*
#: wearing role *n*.  The four panes therefore cover the four roles
#: ``malgor_handler`` rotates through in one Speaker run.
#:
#: These are **class item names**, because that is what ``Bot(soloClass=...)``
#: holds and what ``equip_item`` matches; the matching
#: :data:`SOLO_LOADOUTS` key is the lower-case form.  Reorder a name here and
#: the pane follows -- the gear is looked up from it, not stored beside it.
SOLO_ROLES: Tuple[str, ...] = (
    "Legion Revenant",
    "ArchPaladin",
    "Lord Of Order",
    "Verus DoomKnight",
)


def get_solo_role(pane: int) -> str:
    """The class :data:`SOLO_ROLES` gives launcher ``pane`` (1-based).

    Raises:
        KeyError: listing the roles that *are* configured.  Piping ``5``, or
            a ``SOLO_ROLES`` shorter than ``ACCOUNTS``, fails loudly instead
            of silently wrapping around to the first role.
    """
    try:
        n = int(pane)
    except (TypeError, ValueError):
        raise KeyError(f"speaker pane must be a number, got {pane!r}") from None
    if not 1 <= n <= len(SOLO_ROLES):
        known = ", ".join(f"{i + 1}={role}" for i, role in enumerate(SOLO_ROLES))
        raise KeyError(f"no speaker role for pane {pane!r}; has: {known}")
    return SOLO_ROLES[n - 1]


def loadout_bosses() -> Tuple[str, ...]:
    """Boss keys that have a table in :data:`LOADOUTS`, in definition order."""
    return tuple(LOADOUTS)


def get_loadout(boss: str, slot: int) -> Loadout:
    """The :class:`Loadout` for ``boss``'s launcher ``slot``.

    Raises:
        KeyError: naming the boss and the slots that *are* configured, so a
            typo or a slot the boss does not define fails immediately instead
            of equipping nothing.
    """
    table = LOADOUTS.get(boss)
    if table is None:
        known = ", ".join(loadout_bosses())
        raise KeyError(f"no loadout table for boss {boss!r}; known: {known}")
    loadout = table.get(int(slot))
    if loadout is None:
        have = ", ".join(str(s) for s in sorted(table))
        raise KeyError(f"boss {boss!r} defines no slot {slot}; has: {have}")
    return loadout


def get_solo_loadout(class_name: str) -> Loadout:
    """The speaker's :class:`Loadout` for ``class_name``.

    Matched case-insensitively on the lower-cased class item name, because
    ``Bot(soloClass=...)`` carries whatever casing the config file used.

    Raises:
        KeyError: listing the classes that *are* configured, so a typo fails
            immediately instead of equipping nothing.
    """
    loadout = SOLO_LOADOUTS.get(class_name.lower())
    if loadout is None:
        known = ", ".join(sorted(SOLO_LOADOUTS))
        raise KeyError(f"no speaker loadout for class {class_name!r}; known: {known}")
    return loadout
