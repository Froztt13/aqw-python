"""Shared machinery for every ultra boss -- and nothing boss-specific.

**Each boss lives in its own module** (``plan.md`` Phase 4):
``bot/ultra/ultra_tyndarius.py``, ``ultra_engineer.py``, ``ultra_ezrajal.py``,
``ultra_warden.py``, ``ultra_gramiel.py``, ``ultra_drakath.py``.  Each one
holds ``class Ultra< Boss>(CoreUltra)`` with a ``run()``, plus a
``main(cmd)`` shim so ``start.py`` / ``gui.py`` can run it standalone.
``bot/ultra/daily.py`` drives the four daily bosses in order, picking the
launcher slot from stdin.  If you need to change how a *specific* boss
fights, that file is the place -- not this one.

``CoreUltra`` holds what all of them do the same way:

=================================  ==========================================
``apply_loadout(boss)``            equip the class, gear and scroll named in
                                   ``bot.ultra.config.LOADOUTS``, or **stop
                                   the bot**
``join_and_wait(map)``             enter the map in the private room and wait
                                   for four players
``precast_buffs()``                skills 1-3 as buffs, 700 ms apart
``attack_loop(...)``               the skill rotation, including the support
                                   heal, the finisher hook and the
                                   counter-attack guard
``finish(quest)``                  turn in, back to Yulgar, rest, unsubscribe
``message_handler``                the counter-attack telegraph
=================================  ==========================================

Gear is selected by **enhancement name** -- never by item name, with the class
as the single exception (no enhancement identifies a class uniquely).  The
config field is the slot, so ``equip_enhancement`` is always told whether it
is picking a weapon, a helm or a cape.

Failure is loud by design: if the class is in neither inventory nor bank, or
an enhancement cannot be found, ``_abort()`` stops the bot instead of
continuing with whatever happened to be equipped.  See ``plan.md``.

``UltraSpeaker`` at the bottom is the whole of the old ``ultra_speaker.py``
with its module-level globals turned into instance state.  It is the one
fight still defined here because it is driven by ``Bot(soloClass=...)``
rather than by a launcher slot, and it owns its own telegraph handling.
"""

from __future__ import annotations

import json
import time
from datetime import datetime
from typing import Awaitable, Callable, Optional, Sequence

from colorama import Fore

from bot.ultra import config, party
from bot.ultra.config import Enhance, Loadout
from bot.ultra.ultralog import FightLog
from core.command import Command, SkillMode
from core.utils import is_valid_json

#: Called once per tick by :meth:`CoreUltra.attack_loop`, before the main skill.
_Tick = Callable[[], Awaitable[None]]


class CoreUltra:
    """Common equipment, navigation and fight machinery for the ultra bosses."""

    #: Set by ``message_handler`` while Ultra Ezrajal telegraphs a counter
    #: attack; class-level so an instance starts at the documented default.
    counter_attack = False

    def __init__(self, cmd: Command, index_class: int) -> None:
        self.cmd = cmd
        #: Launcher slot 1-4, straight from ``input("Select bot [1-4]")``.
        self.index_class = index_class
        self.private_room = 9909
        self.counter_attack = False
        #: Set once :meth:`_abort` fires; every entry point checks it so a
        #: failed equip stops the whole run, not just the current boss.
        self.aborted = False
        #: Boss name for telemetry; set by :meth:`_open_log`.
        self.boss = ""
        #: Per-account activity log.  Inert until :meth:`apply_loadout` opens
        #: it, and incapable of raising either way -- see ``ultralog.py``.
        self.log = FightLog()
        #: Change-detection state for :meth:`_log_state`, reset per fight.
        self._log_state = ""
        self._log_names: dict = {}
        self._log_at = 0.0
        self._log_fail_at = 0.0

    # ------------------------------------------------------------------
    # loadout
    # ------------------------------------------------------------------

    def _abort(self, message: str) -> None:
        """Stop the bot over a loadout that cannot be equipped.

        Sets :attr:`aborted` first so a caller that is part-way through a
        sequence of bosses can bail out even though ``stop_bot`` is
        asynchronous in effect.
        """
        print(Fore.RED + f"[ultra] {message}" + Fore.RESET)
        self.log.event("ABORT", message=message)
        self.aborted = True
        self.cmd.stop_bot(message)

    def _tele(self, kind: str, **fields) -> None:
        """Forward an event to the optional telemetry writer, if one is attached."""
        tel = getattr(self.cmd.bot, "telemetry", None)
        if tel is not None:
            tel.write(kind, **fields)

    def _open_log(self, boss: str, slot: str) -> None:
        """Start (or restart) this account's activity log for ``boss``.

        Called once the boss is known, because that is the earliest point a
        log line would say anything useful -- and because every failure from
        here on is the kind worth reading back.  The account name comes from
        the live connection, so a login that never happened still yields a
        file rather than an exception.
        """
        try:
            username = self.cmd.bot.username
        except Exception:
            username = ""
        self._log_state = ""
        self._log_names = {}
        self._log_at = 0.0
        self._log_fail_at = 0.0
        self.log.open(boss, slot, username)
        self.boss = boss
        self._tele("boss_start", boss=boss, slot=slot)

    async def apply_loadout(self, boss: str) -> Optional[Loadout]:
        """Equip everything ``bot.ultra.config.LOADOUTS[boss][index_class]`` names.

        Order matters and mirrors what the bosses did by hand:

        1. **class first** -- ``equip_item``, which looks in the inventory and
           then in the bank, withdrawing if it is banked;
        2. **gear by enhancement name**, each pinned to its slot;
        3. **scroll last**, and only when the loadout asks for one (so a boss
           without a scroll keeps whichever scroll the previous boss put on).

        Args:
            boss: Key into ``config.LOADOUTS`` -- ``"tyndarius"``, ``"grammiel"``…

        Returns:
            The :class:`Loadout` on success, or ``None`` after the bot has been
            stopped.  Callers return immediately on ``None``.

        Raises nothing: every failure path goes through :meth:`_abort`.
        """
        if self.aborted:
            return None

        try:
            loadout = config.get_loadout(boss, self.index_class)
        except KeyError as error:
            self._abort(f"{boss} slot {self.index_class}: {error.args[0]}")
            return None

        # Log the plan *before* equipping: a run that dies on the third piece
        # of gear still shows what it was trying to wear, and which of the
        # four it got through.
        self._open_log(boss, str(self.index_class))
        self.log.event("LOADOUT", cls=loadout.cls, weapon=loadout.weapon,
                       helm=loadout.helm, cape=loadout.cape,
                       scroll=loadout.scroll, prio=loadout.monster_prio,
                       order=loadout.kill_order)

        # 1. class -- the one piece of gear named by item.
        self.log.event("STEP", part="class", name=loadout.cls)
        if not await self.cmd.equip_item(loadout.cls):
            self._abort(
                f"{boss} slot {self.index_class}: class {loadout.cls!r} is in "
                f"neither inventory nor bank"
            )
            return None

        # 2. gear -- by enhancement name, slot pinned by the config field.
        for field_name in ("weapon", "helm", "cape"):
            spec = getattr(loadout, field_name)
            if spec is None:
                continue          # this loadout does not specify the slot
            if isinstance(spec, Enhance):
                name, kwargs = spec.name, {}
                if spec.level is not None:
                    kwargs["level"] = spec.level
                if spec.rarity is not None:
                    kwargs["rarity"] = spec.rarity
            else:
                name, kwargs = spec, {}

            self.log.event("STEP", part=field_name, name=name)
            if not await self.cmd.equip_enhancement(
                name, config.GEAR_SLOTS[field_name], **kwargs
            ):
                detail = ", ".join(f"{k}={v}" for k, v in kwargs.items())
                detail = f" ({detail})" if detail else ""
                self._abort(
                    f"{boss} slot {self.index_class}: no item in inventory "
                    f"carries the {field_name} enhancement {name!r}{detail}"
                )
                return None

        # 3. scroll last.
        if loadout.scroll:
            self.log.event("STEP", part="scroll", name=loadout.scroll)
        if loadout.scroll and not await self.cmd.equip_scroll(loadout.scroll):
            self._abort(
                f"{boss} slot {self.index_class}: scroll {loadout.scroll!r} "
                f"is not in inventory"
            )
            return None

        self.log.event("EQUIPPED", cls=loadout.cls, weapon=loadout.weapon,
                       helm=loadout.helm, cape=loadout.cape,
                       scroll=loadout.scroll)
        self._tele("equipped", boss=boss, cls=loadout.cls,
                   weapon=loadout.weapon, helm=loadout.helm, cape=loadout.cape,
                   scroll=loadout.scroll, worn=self._worn_gear())
        self._tele("stats", boss=boss, **self._stats_block())
        return loadout

    def _worn_gear(self) -> list:
        """The gear actually on the character now, with its resolved enhancement.

        ``enh_id`` is the true identity (the config names an enhancement, but
        several items can carry one name); ``enh`` is that id read back through
        the enhancement registry.  This is what a gear R&D pass compares across
        runs -- the FightLog ``EQUIPPED`` line only records the *intent*.
        """
        worn = []
        try:
            from model import enhancement
            for item in self.cmd.bot.player.INVENTORY:
                if not item.is_equipped:
                    continue
                record = enhancement.get(item.enh_id)
                worn.append({
                    "slot": item.s_es, "name": item.s_name, "id": item.item_id,
                    "enh_id": item.enh_id, "enh": record.name if record else None,
                    "pattern": item.enh_pattern_id, "level": item.level,
                })
        except Exception:
            pass
        return worn

    def _stats_block(self) -> dict:
        """The server's stat block for the gear just equipped.

        ``$ap``/``$sp``, the outgoing modifiers (``$tdo``/``$cpo``/``$cdo``/
        ``$cho``), crit/hit and the raw ``$tha`` -- taken straight from the
        parsed ``stu`` merge, so these are the game's own numbers.  The rules
        for reading them (caps, stacking, coefficients) are in
        ``bot/ultra/reference/AQW_STATS.md``.
        """
        try:
            stats = self.cmd.bot.player.STATS
            values = {k: v for k, v in stats.values.items() if k.startswith("$")}
            return {"values": values, "wdps": stats.weapon_dps}
        except Exception:
            return {"values": {}, "wdps": 0}

    def equipped_class_name(self) -> str:
        """Lower-cased name of the equipped class, or ``""`` when none is on.

        ``get_equipped_class()`` returns ``None`` when nothing is equipped, so
        the ``.item_name.lower()`` that used to be open-coded (twice, in the
        Gramiel fight and again in ``message_handler``) was an attribute
        waiting to happen.
        """
        item = self.cmd.get_equipped_class()
        return item.item_name.lower() if item else ""

    # ------------------------------------------------------------------
    # shared fight machinery
    # ------------------------------------------------------------------

    async def join_and_wait(self, map_name: str) -> None:
        """Join ``map_name`` in the private room, then wait for a full group."""
        while self.cmd.is_not_in_map(map_name):
            await self.cmd.join_map(map_name, self.private_room)
            await self.cmd.sleep(100)
        while not self.cmd.wait_count_player(4):
            await self.cmd.sleep(100)
        # Rendezvous before buffing/pulling: the panes reach this point a few
        # seconds apart, and whichever pulls first starts the boss phase count
        # for everyone.  Skipped with no AQW_RUN_ID (single bot).
        if party.enabled():
            party.barrier(f"{map_name}_start",
                          getattr(self.cmd.bot, "username", ""), 4, timeout=90)

    async def precast_buffs(self, *, skills: Sequence[int] = (1, 2, 3),
                            buff_only: bool = True, gap_ms: int = 1000) -> None:
        """Fire ``skills`` before pulling, ``gap_ms`` apart.

        Daily bosses cast them as buffs 1000 ms apart.  Ultra Speaker uses the
        same helper with ``buff_only=False`` because it wants the casts (not
        just their buffs).
        """
        for skill in skills:
            await self.cmd.use_skill(skill, buff_only=buff_only)
            await self.cmd.sleep(gap_ms)

    async def attack_loop(
        self,
        skill_list: Sequence[int],
        *,
        monster: str = "*",
        monster_prio: str = "",
        heal_below: Optional[float] = None,
        heal_skill: int = 2,
        support_slots: Sequence[int] = (3, 4),
        gap_ms: int = 250,
        respect_counter_attack: bool = False,
        on_tick: Optional[_Tick] = None,
    ) -> None:
        """Walk ``skill_list`` round and round until ``monster`` dies.

        Args:
            skill_list: Rotation to cycle; ``0`` means the auto-attack.
            monster: ``is_monster_alive`` argument -- ``"*"`` for "anything".
            monster_prio: Passed to every ``use_skill``; ``""`` for none.
            heal_below: When set, support slots top up any ally under this
                percentage by casting ``heal_skill`` first.
            heal_skill: Skill cast by the heal check.
            support_slots: ``index_class`` values treated as support.
            gap_ms: Pause after every rotation step.
            respect_counter_attack: While Ultra Ezrajal's counter-attack
                telegraph is active, stop attacking but keep casting the
                rotation's heal/buff slots (``tgt`` ``f``/``s``).  Off by
                default: Ezrajal is the only boss that sets ``counter_attack``.
            on_tick: Extra work between the heal check and the main skill --
                Ultra Warden uses it to spend its finisher under 600k HP.

        The rotation always advances even when a cast is skipped, so the loop
        cannot wedge on one skill that happens to be on cooldown.
        """
        index = 0
        while self.cmd.is_monster_alive(monster) and self.cmd.is_still_connected():
            self._log_state_now(monster_prio)

            if heal_below is not None and self.index_class in support_slots:
                for player in self.cmd.bot.player_in_area:
                    if player.is_hp_below(heal_below):
                        await self.cmd.use_skill(heal_skill)

            if respect_counter_attack and self.counter_attack:
                # Counter attack is up: a hostile skill would be punished, but
                # a heal/buff must still go out.  BUFF_ONLY makes use_skill fire
                # the slot only when its target is friendly/self and send
                # nothing for a hostile one.
                await self.cmd.use_skill(skill_list[index], monster_prio,
                                         skill_mode=SkillMode.BUFF_ONLY)
                index += 1
                if index >= len(skill_list):
                    index = 0
                await self.cmd.sleep(gap_ms)
                continue

            if on_tick is not None:
                await on_tick()

            slot = skill_list[index]
            sent = await self.cmd.use_skill(slot, monster_prio)
            if slot == 5:
                self._log_scroll(sent)
            elif not sent:
                self._log_failed_skill(slot)
            index += 1
            if index >= len(skill_list):
                index = 0
            await self.cmd.sleep(gap_ms)

    def _log_state_now(self, prio: str) -> None:
        """Record the fight's state when it changes, and at least every 5 s.

        Change detection is what keeps the file readable: a fight that looks
        identical for two minutes writes twelve lines, not a thousand.

        The ``tgt=`` half is the diagnostic that matters.  It reports whether
        each configured priority target resolves *right now*, so an id the
        game never matches shows up as ``no`` forever instead of as a silent
        no-op, and a respawn shows as ``no`` flipping back to ``yes``.
        """
        if self.log.path is None:
            return
        try:
            player = self.cmd.bot.player
            cell = player.CELL
            mobs, names = [], {}
            for mon in self.cmd.bot.monsters:
                if mon.frame != cell:
                    continue
                names[mon.mon_map_id] = mon.mon_name
                percent = (round(mon.current_hp / mon.max_hp * 100)
                           if mon.max_hp else 0)
                state = "up" if mon.is_alive else "dn"
                mobs.append(f"{mon.mon_map_id}:{state}:{percent}")
            hp = (round(player.CURRENT_HP / player.MAX_HP * 100)
                  if player.MAX_HP else 0)
            tokens = [t.strip() for t in prio.split(",") if t.strip()]
            targets = {t: ("yes" if self.cmd.is_monster_alive(t) else "no")
                       for t in tokens}
            connected = self.cmd.is_still_connected()

            snapshot = f"hp={hp} tgt={targets} mob={' '.join(sorted(mobs))}"
            now = time.time()
            if snapshot == self._log_state and now - self._log_at < 5.0:
                return
            self._log_state = snapshot
            self._log_at = now
            self.log.event("STATE", hp=f"{hp}%", conn=connected,
                           tgt=[f"{k}:{v}" for k, v in targets.items()],
                           mob=" ".join(sorted(mobs)))
            if names != self._log_names:
                self._log_names = names
                self.log.event(
                    "CELL",
                    monsters=[f"{k}={v}" for k, v in sorted(names.items())],
                )
        except Exception:
            # Logging must never be the reason a fight stops.
            return

    def _log_scroll(self, sent: bool) -> None:
        """Record **every** scroll attempt -- throttled or not.

        The one cast worth logging unconditionally.  ``equip_scroll`` returning
        true only says the item is on; slot 5 firing is what actually spends
        it, and the two can disagree.

        ``tgt`` is logged beside it because slot 5 ships from ``sAct`` pointing
        at ``"f"`` (friendly) and only the ``seia`` message re-points it at
        ``"h"``.  While it reads ``"f"`` the cast takes the *player* branch,
        returns True, and never reaches ``use_scroll`` at all -- so a plain
        success flag would cheerfully report a scroll that never left the belt.
        """
        if self.log.path is None:
            return
        try:
            skills = self.cmd.bot.player.SKILLS
            target = skills[5].target if len(skills) > 5 else "absent"
        except Exception:
            target = "?"
        self.log.event("SCROLL", ok="yes" if sent else "no", tgt=target)

    def _log_failed_skill(self, skill: int) -> None:
        """Note a cast that came back false, saying which gate refused it.

        ``use_skill`` fails for several quite different reasons and the bare
        boolean cannot tell them apart:

        ==========  ======================================================
        ``mana``    not enough mana for what that slot costs
        ``cd``      the slot's own cooldown -- normal, and what a
                    round-robin rotation is *expected* to hit
        ``unsafe``  ``check_is_skill_safe`` held it back for this class
        ``no-slot`` the class has no such skill slot at all
        ``no-tgt``  nothing alive matched, or ``skill_mode`` filtered it
        ==========  ======================================================

        Throttled to one line per two seconds, so a rotation that spends most
        of its cycle waiting on cooldown reads as a rate rather than a flood.
        """
        if self.log.path is None:
            return
        now = time.time()
        if now - self._log_fail_at < 2.0:
            return
        self._log_fail_at = now
        self.log.event("SKILL", skill=skill, ok="no",
                       why=self._why_skill_failed(skill))

    def _why_skill_failed(self, skill: int) -> str:
        """Which of ``use_skill``'s gates refused this cast.  Never raises."""
        try:
            player = self.cmd.bot.player
            if skill >= len(player.SKILLS):
                return "no-slot"
            entry = player.SKILLS[skill]
            cost = entry.mana * player.ManaCost
            if player.MANA < cost:
                return f"mana {player.MANA}<{cost}"
            deadline = entry.next_use
            if deadline is not None:
                wait_ms = int((deadline - datetime.now()).total_seconds() * 1000)
                if wait_ms > 0:
                    return f"cd {wait_ms}ms"
            if not self.cmd.check_is_skill_safe(skill):
                return "unsafe"
            return "no-tgt"
        except Exception:
            return "?"

    #: Slots that make up one ultra party.
    PARTY_SLOTS = party.PARTY_SLOTS

    async def fight_until_party_ready(self, quest: int, fight) -> bool:
        """Fight ``fight`` until every pane holds the quest's temp item.

        Each round: fight the boss, publish this slot's ``can_turnin`` verdict to
        the shared run directory, and wait for the other three.  When all four
        hold the item the quest is turned in **once** and the caller moves on.
        If anyone is missing it, every slot fights another round; if the whole
        party wiped, all four re-pull together instead.  Without ``AQW_RUN_ID``
        there is no party to coordinate, so one fight wins.
        """
        if not party.enabled():
            await fight()
            return self.cmd.can_turnin_quest(quest)
        for round_number in range(1, party.MAX_ROUNDS + 1):
            deaths_before = getattr(self.cmd.bot, "deaths", 0)
            await fight()
            if not self.cmd.is_still_connected():
                return False
            died = getattr(self.cmd.bot, "deaths", 0) > deaths_before
            ok = self.cmd.can_turnin_quest(quest)
            self._tele("attempt", boss=self.boss, round=round_number, ok=ok, died=died)
            party.report(self.boss, round_number, self.index_class, ok)
            party.report(f"{self.boss}_wipe", round_number, self.index_class, died)
            results = party.wait(self.boss, round_number, self.PARTY_SLOTS)
            if len(results) == len(self.PARTY_SLOTS) and all(results.values()):
                print(f"[ultra] {self.boss}: all slots have the item (round {round_number})")
                await self.cmd.turn_in_quest(quest)     # once, then move on
                return True
            wiped = party.wait(f"{self.boss}_wipe", round_number, self.PARTY_SLOTS)
            if len(wiped) == len(self.PARTY_SLOTS) and all(wiped.values()):
                print(f"[ultra] {self.boss}: party wipe -- re-pulling together")
                await self.restart_pull(quest)
                continue
            print(f"[ultra] {self.boss}: party incomplete in round {round_number}, refighting")
            await self.wait_for_boss()
        print(f"[ultra] {self.boss}: giving up after {party.MAX_ROUNDS} rounds")
        self._abort(f"{self.boss}: party never got the item after {party.MAX_ROUNDS} rounds")
        return False

    async def restart_pull(self, quest: int) -> None:
        """After a party wipe: re-accept the quest and re-enter together."""
        await self.cmd.accept_quest(quest)
        map_name = getattr(self, "MAP", "")
        if map_name:
            await self.join_and_wait(map_name)      # includes the barrier

    async def wait_for_boss(self) -> None:
        """Wait until a monster is alive in the cell again (boss respawned)."""
        while self.cmd.is_still_connected() and not self.cmd.is_monster_alive("*"):
            await self.cmd.sleep(1000)

    async def finish(self, quest: int, *, spawn: bool = True,
                     unsubscribe: bool = False) -> None:
        """Wrap a boss up: leave the cell, go rest in Yulgar.

        The quest turn-in happens once in ``fight_until_party_ready``, after the
        whole party holds the temp item.
        """
        self.log.event("FINISH", quest=quest)
        self._tele("boss_end", boss=self.boss, quest=quest)
        if unsubscribe:
            self.cmd.bot.unsubscribe(self.message_handler)
            self.counter_attack = False
        if spawn:
            await self.cmd.jump_cell("Enter", "Spawn")
        await self.cmd.join_map("yulgar")
        await self.cmd.rest()
        await self.cmd.sleep(4000)
        self.log.close()

    # ------------------------------------------------------------------
    # server message handling
    # ------------------------------------------------------------------

    def _parse_message(self, message):
        """Unwrap a server payload's ``b.o``, or return ``None``.

        Every handler starts with this, so the ``data["b"]["o"]`` unpack and
        its guard live in exactly one place instead of once per boss.
        """
        if not message or not is_valid_json(message):
            return None
        try:
            data = json.loads(message)["b"]["o"]
        except Exception:
            return None
        return data if isinstance(data, dict) else None

    def message_handler(self, message) -> None:
        """React to the counter-attack telegraph.

        Installed by Ultra Ezrajal (then removed in ``finish``).  Bosses with
        telegraphs of their own override this, call ``_on_counter_attack``
        first -- the old code had one shared handler covering both bosses, so
        Gramiel's fight always saw the counter-attack flags too, even though
        neither of its loops reads them -- and add their own branch.
        """
        data = self._parse_message(message)
        if not data or data.get("cmd") != "ct":
            return
        self._on_counter_attack(data)

    def _on_counter_attack(self, data: dict) -> None:
        """Set :attr:`counter_attack` on the telegraph, clear it on ``aura--``."""
        for anim in data.get("anims") or []:
            msg = anim.get("msg")
            if msg and isinstance(msg, str) and "prepares a counter attack" in msg:
                self.counter_attack = True
                print("Counter Attack", self.counter_attack)

        for action in data.get("a") or []:
            if action.get("cmd") == "aura--":
                removed_aura = action.get("aura", {}).get("nam", "")
                if "Counter Attack" in removed_aura:
                    self.counter_attack = False
                    print("Counter Attack", self.counter_attack)


class UltraSpeaker(CoreUltra):
    """The Ultra Speaker fight, moved out of ``bot/ultra/ultra_speaker.py``.

    Speaker has no launcher slots.  It equips whatever ``Bot(soloClass=...)``
    was configured with, then looks that class up in ``config.SOLO_LOADOUTS``
    to decide its gear.  Everything that used to be a module global --
    ``speaker_counter``, ``taunter_class``, ``zone_class``, ``what_zone``,
    ``force_taunt``, ``force_skill``, ``in_zone``, ``force_heal``,
    ``skill_to_heal`` -- is now an instance attribute, so two speakers in one
    process would no longer fight over each other's state.

    The fight is a reaction machine: ``message_handler`` reads the boss's
    telegraphs, :meth:`malgor_handler` turns a step counter into *who taunts*
    and *who is inside the zone*, and the main loop acts on those flags rather
    than on a fixed rotation.
    """

    #: Legion Revenant has no auto-attack in the rotation the original picked.
    SOLO_SKILLS = {"legion revenant": [0, 2, 0, 3, 4]}
    #: Used for every other class -- the original left ``skill_list`` unbound
    #: when ``soloClass`` was something else, which was a NameError waiting to
    #: happen.
    DEFAULT_SKILLS = [0, 1, 2, 0, 3, 4]

    #: X the character stands at when inside / outside the damage zone.
    IN_ZONE_X = 203
    OUT_ZONE_X = 100

    def __init__(self, cmd: Command, index_class: int = 1) -> None:
        super().__init__(cmd, index_class)
        # Formerly module-level globals in ultra_speaker.py.
        self.speaker_counter = 0
        self.taunter_class: Optional[str] = None
        self.zone_class = ""
        self.what_zone = ""
        self.force_taunt = False
        self.force_skill = False
        self.skill_to_force = 1
        self.in_zone = False
        self.force_heal = False
        self.skill_to_heal = -1

    async def run(self) -> None:
        """Equip the solo class's loadout, then fight The First Speaker."""
        solo = self.cmd.get_solo_class()
        if not solo:
            self._abort("speaker: Bot(soloClass=...) is unset, so there is no "
                        "class to equip")
            return
        if await self.apply_solo_loadout(solo) is None:
            return

        await self.cmd.accept_quest(9173)
        await self.cmd.join_map("ultraspeaker", self.private_room)
        while not self.cmd.wait_count_player(4):
            await self.cmd.sleep(100)

        # Rendezvous before buffing/pulling: the four panes reach this point a
        # few seconds apart, and whichever pulls first starts the boss phase
        # count for everyone, so the rest begin mid-sequence.  Waiting for all
        # four here lines them up.  Skipped with no AQW_RUN_ID (single bot).
        if party.enabled():
            party.barrier("speaker_start",
                          getattr(self.cmd.bot, "username", ""), 4, timeout=90)

        await self.precast_buffs(buff_only=True, gap_ms=1000)
        await self.cmd.jump_cell("Boss", "Left")

        skill_list = list(self.SOLO_SKILLS.get(solo.lower(), self.DEFAULT_SKILLS))
        skill_index = 0
        self.cmd.bot.subscribe(self.message_handler)

        counter = 0
        start_time = time.time()

        seen_alive = False
        while self.cmd.is_still_connected():
            mons_hp = self.cmd.get_monster_hp("The First Speaker")
            if mons_hp == 0 or (mons_hp < 0 and seen_alive):
                # The fight is over at exactly 0 HP, or when the boss vanishes
                # after having been seen alive.  A -1 before the first sighting
                # only means it is not in the cell yet, not that it is dead.
                break
            if mons_hp < 0:
                await self.cmd.sleep(500)
                continue
            seen_alive = True
            counter += 1
            if mons_hp > 9_990_000:
                # Above this the boss is in its opening state: restart the
                # telegraph sequence so a fresh pull re-reads it.
                self.speaker_counter = 0
            if counter >= 50:
                print("The First Speaker:", mons_hp)
                counter = 0

            equipped_class = self.equipped_class_name()

            if self.taunter_class:
                if not self.force_taunt and equipped_class == self.taunter_class.lower():
                    self.force_taunt = True
                    continue

            if self.force_taunt:
                if not self.cmd.bot.player.canUseSkill(5):
                    await self.cmd.sleep(100)
                    continue
                print(equipped_class, "taunt")
                self.force_taunt = False
                self.taunter_class = None
                await self.cmd.use_skill(5, target_monsters="The First Speaker")

            if self.force_heal:
                self.force_heal = False
                await self.cmd.sleep(500)
                if self.skill_to_heal != -1:
                    await self.cmd.use_skill(self.skill_to_heal)
                    self.skill_to_heal = -1

            if self.force_skill and equipped_class == "legion revenant":
                await self.cmd.use_skill(1, "The First Speaker")
                self.force_skill = False

            if self.zone_class:
                if self.zone_class.lower() == equipped_class:
                    if self.what_zone == "IN":
                        self.in_zone = True
                    elif self.what_zone == "OUT":
                        self.in_zone = False
                    self._tele("zone_apply", cls=equipped_class,
                               in_zone=self.in_zone, what=self.what_zone,
                               x=self.cmd.bot.player.X)
                    self.zone_class = ""

            x = self.cmd.bot.player.getPlayerPositionXY()[0]
            if self.in_zone:
                if x != self.IN_ZONE_X:
                    print(Fore.BLUE + "I SOHULD IN ZONE" + Fore.WHITE)
                    await self.cmd.walk_to(self.IN_ZONE_X, 301)
            elif x != self.OUT_ZONE_X:
                print(Fore.BLUE + "I SOHULD OUT ZONE" + Fore.WHITE)
                await self.cmd.walk_to(self.OUT_ZONE_X, 321)

            if self.cmd.hp_below_percentage(60):
                if equipped_class in ("archpaladin", "lord of order"):
                    await self.cmd.use_skill(2)
                elif equipped_class == "legion revenant":
                    await self.cmd.use_skill(3)

            await self.cmd.use_skill(skill_list[skill_index], "The First Speaker")
            skill_index += 1
            if skill_index >= len(skill_list):
                skill_index = 0
            await self.cmd.sleep(100)

        elapsed_time = time.time() - start_time
        minutes = int(elapsed_time // 60)
        seconds = int(elapsed_time % 60)
        print(f"Elapsed time: {minutes} minutes, {seconds} seconds")

        self.cmd.bot.unsubscribe(self.message_handler)
        await self.cmd.join_map("battleon", self.private_room)
        self.log.event("FINISH", quest=9173)
        self._tele("boss_end", boss="speaker", quest=9173)
        self.log.close()
        print("finished ultra speaker")
        await self.cmd.sleep(100000)

    async def apply_solo_loadout(self, class_name: str) -> Optional[Loadout]:
        """Equip the class plus the gear ``config.SOLO_LOADOUTS`` pairs with it.

        Same rules as :meth:`apply_loadout` -- bank withdrawal for the class,
        enhancement name for the gear, stop on anything missing -- except that
        the loadout is looked up by class rather than by launcher slot.
        """
        if self.aborted:
            return None
        try:
            loadout = config.get_solo_loadout(class_name)
        except KeyError as error:
            self._abort(f"speaker: {error.args[0]}")
            return None

        self._open_log("speaker", loadout.cls)
        self.log.event("LOADOUT", cls=loadout.cls, weapon=loadout.weapon,
                       helm=loadout.helm, cape=loadout.cape,
                       scroll=loadout.scroll, prio=loadout.monster_prio)

        if not await self.cmd.equip_item(loadout.cls):
            self._abort(f"speaker: class {loadout.cls!r} is in neither "
                        f"inventory nor bank")
            return None

        for field_name in ("weapon", "helm", "cape"):
            spec = getattr(loadout, field_name)
            if spec is None:
                continue
            name = spec.name if isinstance(spec, Enhance) else spec
            kwargs = {}
            if isinstance(spec, Enhance):
                if spec.level is not None:
                    kwargs["level"] = spec.level
                if spec.rarity is not None:
                    kwargs["rarity"] = spec.rarity
            if not await self.cmd.equip_enhancement(
                name, config.GEAR_SLOTS[field_name], **kwargs
            ):
                self._abort(f"speaker: {field_name} enhancement {name!r} "
                            f"is not in inventory")
                return None

        if loadout.scroll and not await self.cmd.equip_scroll(loadout.scroll):
            self._abort(f"speaker: scroll {loadout.scroll!r} is not in inventory")
            return None

        self.log.event("EQUIPPED", cls=loadout.cls, weapon=loadout.weapon,
                       helm=loadout.helm, cape=loadout.cape,
                       scroll=loadout.scroll)
        self._tele("equipped", boss="speaker", cls=loadout.cls,
                   weapon=loadout.weapon, helm=loadout.helm, cape=loadout.cape,
                   scroll=loadout.scroll, worn=self._worn_gear())
        self._tele("stats", boss="speaker", **self._stats_block())
        return loadout

    # ------------------------------------------------------------------
    # telegraph handling
    # ------------------------------------------------------------------

    def message_handler(self, message) -> None:
        """Read the boss's telegraphs into :attr:`taunter_class` / :attr:`zone_class`.

        Overrides :meth:`CoreUltra.message_handler`: Speaker reports player HP
        and a ``zoneSet`` event as well as anims, and none of the counter-attack
        or Gramiel-taunt handling applies here.
        """
        if not message or not is_valid_json(message):
            return
        data = json.loads(message)
        try:
            data = data["b"]["o"]
        except Exception:
            return

        cmd = data.get("cmd")
        if cmd == "ct":
            self._speaker_ct(data)
        elif cmd == "event":
            zone = data.get("args", {}).get("zoneSet")
            if zone:
                print(Fore.GREEN + zone + Fore.WHITE)
                if zone == "A":
                    self.force_skill = True
                    self.skill_to_force = 1

    def _speaker_ct(self, data) -> None:
        """Handle a ``ct`` packet: low-HP heal, then the truth/listen telegraph."""
        players = data.get("p")
        if players:
            for ply in players.values():
                if not ply:
                    continue
                hp = ply.get("intHP")
                if hp and hp <= 2000:
                    class_name = self.equipped_class_name()
                    if not class_name:
                        continue
                    if class_name in ("archpaladin", "lord of order"):
                        self.skill_to_heal = 2
                        self.force_heal = True
                    elif class_name == "legion revenant":
                        self.skill_to_heal = 3
                        self.force_heal = True

        for anim in data.get("anims") or []:
            msg = anim.get("msg")
            if not msg:
                continue
            if "truth" in msg or "listen" in msg:
                # A pending assignment that never got consumed is lost when this
                # overwrites it -- the single-slot taunt/zone state.  Log it so a
                # run can show whether that is what drifts.
                if self.zone_class or self.taunter_class:
                    self._tele("zone_lost", cls=self.equipped_class_name(),
                               x=self.cmd.bot.player.X,
                               prev_zone=self.zone_class, prev_what=self.what_zone,
                               prev_taunt=self.taunter_class)
                step = self.speaker_counter
                who_taunt, who_zone, what_zone, _delay = self.malgor_handler()
                self.taunter_class = who_taunt
                self.zone_class = who_zone or ""
                self.what_zone = what_zone or ""
                self._tele("zone", step=step, msg=msg, taunt=who_taunt,
                           zone=who_zone, what=what_zone, in_zone=self.in_zone,
                           x=self.cmd.bot.player.X)

    def malgor_handler(self):
        """Map the telegraph counter onto (taunter, zone class, zone, delay).

        Order matches the original exactly: read the counter, work out the
        step's answer, apply step 15's reset, *then* increment.  Skipping or
        reordering those last two is what decides whether the sequence
        resumes at step 2 (correct) or replays step 1.
        """
        step = self.speaker_counter
        answer = self._malgor_step(step)
        if step == 15:
            self.speaker_counter = 1
        self.speaker_counter += 1
        return answer

    @staticmethod
    def _malgor_step(step: int):
        if step == 0:
            return ("Legion Revenant", None, None, 0)
        if step == 1:
            return ("Lord Of Order", "Verus DoomKnight", "IN", 0)
        if step == 2:
            return ("ArchPaladin", "Verus DoomKnight", "OUT", 0)
        if step in (3, 7):
            return ("Lord Of Order", None, None, 500)
        if step == 4:
            return (None, "Legion Revenant", "IN", 0)
        if step == 5:
            return ("Legion Revenant", "Legion Revenant", "OUT", 500)
        if step == 8:
            return (None, "ArchPaladin", "IN", 0)
        if step == 9:
            return ("ArchPaladin", "ArchPaladin", "OUT", 0)
        if step == 10:
            return ("Legion Revenant", None, None, 500)
        if step == 11:
            return (None, "Lord Of Order", "IN", 0)
        if step == 12:
            return ("Lord Of Order", "Lord Of Order", "OUT", 500)
        if step == 14:
            return ("Legion Revenant", None, None, 0)
        if step == 15:
            return ("Lord Of Order", "Verus DoomKnight", "IN", 500)
        return (None, None, None, 0)
