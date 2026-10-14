"""Structured per-account telemetry for the ultra fights.

One JSONL file per account under ``capture_logs/ultra/<run_id>/``, written by a
subscriber that wraps ``Bot.handle_server_response``.  It records the four
things the fights are analysed on -- inventory, player state, monster state,
and who hit whom -- from the packets the bot already receives, so it adds no
game traffic.

Off unless ``AQW_TELEMETRY=1``.  Every method is best-effort: a logger that
raises would take down the fight it was asked to record, so failures are
swallowed exactly like ``ultralog.FightLog``.

Enabled by ``install_from_env(bot, slot, account)`` from ``daily.py``; the run
id comes from ``AQW_RUN_ID`` (set once by ``ultra_daily_pane.bat`` so the four
panes land in one directory).

* ``meta`` / ``map`` / ``inventory`` / ``boss_start`` / ``boss_end`` / ``death``
  -- one-off markers;
* ``monsters`` -- the cell's monsters when a map loads;
* ``monster`` -- one monster's HP when it changes;
* ``player`` -- our own HP/MP/state when it changes;
* ``damage`` -- one hit we dealt (from ``ct.sarsa``);
* ``hurt`` / ``heal`` -- one hit/heal on us (from ``ct.sara``).
"""

from __future__ import annotations

import json
import os
import time
from datetime import datetime
from typing import Any, Optional

#: ``<repo>/capture_logs/ultra`` -- three directories up from ``bot/ultra/``.
LOG_DIR = os.path.normpath(
    os.path.join(
        os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))),
        "capture_logs",
        "ultra",
    )
)

#: A monster not seen for this long is treated as gone -- boss deaths and cell
#: changes stop updating a monster, and its last HP must not be read as current.
MONSTER_TTL_S = 15.0


def install_from_env(bot, slot: int, account: str) -> Optional["UltraTelemetry"]:
    """Attach telemetry to ``bot`` when ``AQW_TELEMETRY`` is on, else return None."""
    if os.environ.get("AQW_TELEMETRY", "").strip().lower() not in ("1", "true", "yes"):
        return None
    run_id = os.environ.get("AQW_RUN_ID", "").strip() or datetime.now().strftime("%Y%m%d_%H%M%S")
    tel = UltraTelemetry(bot, run_id, slot, account)
    bot.telemetry = tel
    return tel


def _safe(name: str) -> str:
    return "".join(c for c in (name or "unknown") if c.isalnum() or c in "-_") or "unknown"


class UltraTelemetry:
    """Append-only JSONL writer + packet interpreter.  Never raises."""

    def __init__(self, bot, run_id: str, slot: int, account: str) -> None:
        self.bot = bot
        self.run_id = run_id
        self.slot = slot
        self.account = account
        self.count = 0
        self._fh = None
        self._last_player = None
        self._last_monster: dict[str, tuple] = {}
        self._monster_seen: dict[str, float] = {}
        self._last_auras: tuple = ()
        self._last_anims: Optional[list] = None
        self._last_pos: Optional[tuple] = None
        self.boss = ""
        self._open()
        self._install()

    # -- lifecycle -----------------------------------------------------

    def _open(self) -> None:
        try:
            directory = os.path.join(LOG_DIR, _safe(self.run_id))
            os.makedirs(directory, exist_ok=True)
            path = os.path.join(directory, f"slot{self.slot}_{_safe(self.account)}.jsonl")
            self._fh = open(path, "w", encoding="utf-8")
        except Exception:
            self._fh = None
            return
        self.write("meta", run_id=self.run_id, slot=self.slot, account=self.account,
                   started=datetime.now().strftime("%Y-%m-%d %H:%M:%S"))

    def close(self) -> None:
        handle, self._fh = self._fh, None
        if handle is None:
            return
        try:
            self.write("end", records=self.count)
            handle.flush()
            handle.close()
        except Exception:
            pass

    # -- writing -------------------------------------------------------

    def write(self, kind: str, **fields: Any) -> None:
        handle = self._fh
        if handle is None:
            return
        try:
            record = {"t": round(time.time(), 3), "kind": kind}
            record.update(fields)
            handle.write(json.dumps(record, ensure_ascii=False) + "\n")
            self.count += 1
            if self.count % 200 == 0:
                handle.flush()
        except Exception:
            pass

    # -- hook ----------------------------------------------------------

    def _install(self) -> None:
        original = self.bot.handle_server_response

        async def wrapped(msg):
            result = await original(msg)
            try:
                self._capture(msg)
            except Exception:
                pass
            return result

        self.bot.handle_server_response = wrapped

    def _capture(self, msg: str) -> None:
        if not msg or '"cmd"' not in msg:
            return
        try:
            data = json.loads(msg.strip())["b"]["o"]
        except Exception:
            return
        cmd = data.get("cmd")
        if cmd == "moveToArea":
            self.write("map", map=data.get("strMapName"), area=data.get("areaId"))
            self._snapshot_monsters()
        elif cmd == "loadInventoryBig":
            self._snapshot_inventory()
        elif cmd == "addItems":
            self._add_items(data)
        elif cmd == "sAct":
            self._skill_loadout()
        elif cmd == "mtls":
            self._decay()
            self._monster_hp(str(data.get("id")))
        elif cmd == "ct":
            self._decay()
            self._ct(data)
            self._log_monster_auras(data)
            self._log_anims(data)
            self._log_position()
            if data.get("a"):
                # ct.a carries the auras; the bot has already applied our own,
                # so read them back rather than re-parsing the packet.
                self._log_auras()
        elif cmd == "stu":
            self._log_stat_change(data)
        elif cmd == "uotls":
            self._player(data)
        elif cmd == "event":
            self.write("event", zone=(data.get("args") or {}).get("zoneSet"))
        elif cmd == "playerDeath":
            self.write("death")

    # -- snapshots -----------------------------------------------------

    def _snapshot_monsters(self) -> None:
        now = time.time()
        monsters = []
        present = set()
        for mon in getattr(self.bot, "monsters", []):
            present.add(mon.mon_map_id)
            monsters.append({
                "id": mon.mon_map_id, "name": mon.mon_name, "frame": mon.frame,
                "hp": mon.current_hp, "max": mon.max_hp, "alive": mon.is_alive,
            })
        # A map load is a full rebuild: anything tracked but no longer listed is
        # gone, so its last HP can never be read as current again.
        for mon_map_id in list(self._monster_seen):
            if mon_map_id not in present:
                self._emit_gone(mon_map_id, "map")
        self._monster_seen = {mon_map_id: now for mon_map_id in present}
        self.write("monsters", cell=self.bot.player.CELL, monsters=monsters)

    def _emit_gone(self, mon_map_id: str, reason: str) -> None:
        self.write("monster_gone", id=mon_map_id, reason=reason)
        self._monster_seen.pop(mon_map_id, None)
        self._last_monster.pop(mon_map_id, None)

    def _decay(self) -> None:
        """Expire monsters whose HP has stopped updating (death, cell change)."""
        now = time.time()
        for mon_map_id, seen in list(self._monster_seen.items()):
            if now - seen > MONSTER_TTL_S:
                self._emit_gone(mon_map_id, "ttl")

    def _snapshot_inventory(self) -> None:
        inventory = getattr(self.bot.player, "INVENTORY", [])
        equipped = [
            {"slot": item.s_es, "name": item.s_name, "id": item.item_id,
             "enh_id": item.enh_id, "enh_pattern": item.enh_pattern_id, "level": item.level}
            for item in inventory if item.is_equipped
        ]
        items = sorted({item.s_name: item.qty for item in inventory}.items())
        self.write("inventory", equipped=equipped, items=items)

    def _add_items(self, data: dict) -> None:
        """Log every item the server adds -- the boss temp items land here."""
        for item_id, item in (data.get("items") or {}).items():
            self.write("add_item", id=str(item_id), name=item.get("sName"),
                       qty=item.get("iQty"), temp=not item.get("CharItemID"))

    def _skill_loadout(self) -> None:
        """Log each skill slot's target -- which of them are heal/buff."""
        try:
            slots = [{"i": i, "name": skill.name, "ref": skill.ref, "tgt": skill.target,
                      "cd": skill.cooldown_ms}
                     for i, skill in enumerate(self.bot.player.SKILLS)]
        except Exception:
            return
        self.write("skills", slots=slots)

    # -- per-packet ----------------------------------------------------

    def _monster_hp(self, mon_map_id: str) -> None:
        for mon in getattr(self.bot, "monsters", []):
            if mon.mon_map_id != mon_map_id:
                continue
            self._monster_seen[mon_map_id] = time.time()
            key = (mon.current_hp, mon.is_alive)
            if self._last_monster.get(mon_map_id) == key:
                return
            self._last_monster[mon_map_id] = key
            self.write("monster", id=mon.mon_map_id, name=mon.mon_name,
                       hp=mon.current_hp, max=mon.max_hp, alive=mon.is_alive)
            return

    def _player(self, data: dict) -> None:
        if str(data.get("unm")) != str(self.bot.player.USER):
            return
        o = data.get("o") or {}
        self._emit_player(o.get("intHP"), o.get("intMP"), o.get("intState"))

    def _emit_player(self, hp, mp, state) -> None:
        player = self.bot.player
        hp = player.CURRENT_HP if hp is None else int(hp)
        mp = player.MANA if mp is None else int(mp)
        state = 0 if state is None else int(state)
        key = (hp, mp, state)
        if key == self._last_player:
            return
        self._last_player = key
        self.write("player", hp=hp, max=player.MAX_HP, mp=mp, state=state)

    def _log_auras(self) -> None:
        """Log our own auras whenever the set changes.

        This is where The First Speaker's dangerous statuses live -- *Sanctity*,
        *Magia Burn*, *Stasis* -- so a wipe can be tied to the aura held at the
        time.  Names are normalised and the stack count comes from ``get_val``.
        """
        auras = []
        try:
            for aura in self.bot.player.AURAS:
                if aura.is_expired():
                    continue
                auras.append({"name": aura.name, "type": aura.aura_type,
                              "dur": aura.duration, "stacks": aura.get_val()})
        except Exception:
            return
        key = tuple(sorted((a["name"], a["stacks"]) for a in auras))
        if key == self._last_auras:
            return
        self._last_auras = key
        self.write("auras", auras=auras)

    def _log_monster_auras(self, data: dict) -> None:
        """Log monster aura add/remove from ``ct.a`` (e.g. a boss self-buff)."""
        for action in data.get("a") or []:
            tinf = str(action.get("tInf", ""))
            if not tinf.startswith("m:"):
                continue
            cmd = action.get("cmd") or ""
            if "aura+" in cmd:
                for aura in action.get("auras") or []:
                    self.write("monster_aura", id=tinf[2:], op="+",
                               name=aura.get("nam"), dur=aura.get("dur"))
            elif "aura-" in cmd:
                self.write("monster_aura", id=tinf[2:], op="-",
                           name=(action.get("aura") or {}).get("nam"))

    def _log_anims(self, data: dict) -> None:
        """Log the fight's telegraph text lines -- what the boss is asking for."""
        messages = []
        for anim in data.get("anims") or []:
            message = anim.get("msg") or anim.get("animStr")
            if message:
                messages.append(str(message))
        if not messages or messages == self._last_anims:
            return
        self._last_anims = messages
        self.write("anims", msgs=messages)

    def _log_position(self) -> None:
        """Log our X/Y, so the zone mechanics (do not stand in the glow) can be read."""
        try:
            x, y = self.bot.player.getPlayerPositionXY()
        except Exception:
            return
        key = (int(x), int(y))
        if key == self._last_pos:
            return
        self._last_pos = key
        self.write("pos", x=key[0], y=key[1], cell=self.bot.player.CELL)

    def _log_stat_change(self, data: dict) -> None:
        """Log a ``stu`` delta: buffs/debuffs move AP, SP and the modifiers."""
        sta = data.get("sta") or {}
        if not sta:
            return
        self.write("stat_change", values=dict(sta))

    def _ct(self, data: dict) -> None:
        own = f"p:{self.bot.username_id}"
        for mon_map_id in (data.get("m") or {}):
            self._monster_hp(str(mon_map_id))
        for name, condition in (data.get("p") or {}).items():
            if str(name) == str(self.bot.player.USER):
                self._emit_player(condition.get("intHP"), condition.get("intMP"),
                                  condition.get("intState"))
        for element in data.get("sarsa") or []:
            if element.get("cInf") != own:
                continue
            for action in element.get("a") or []:
                target = str(action.get("tInf", ""))
                amount = action.get("hp")
                if target.startswith("m:"):
                    self.write("damage", target=target[2:], amount=amount,
                               ty=action.get("type"), act=action.get("actRef"))
                elif target.startswith("p:"):
                    # hp present -> heal; none -> a buff/utility cast (e.g. slot 3).
                    if amount:
                        self.write("heal", target=target[2:], amount=amount,
                                   ty=action.get("type"), act=action.get("actRef"))
                    else:
                        self.write("cast", act=action.get("actRef"),
                                   target=target[2:], ty=action.get("type"))
        for element in data.get("sara") or []:
            self._sara(element.get("actionResult") or {}, own)

    def _sara(self, result: dict, own: str) -> None:
        caster = str(result.get("cInf", ""))
        target = str(result.get("tInf", ""))
        amount = result.get("hp")
        kind = result.get("typ") or result.get("type")
        if target == own:
            if caster.startswith("m"):
                self.write("hurt", amount=amount, caster=caster, ty=kind)
            elif caster == own:
                self.write("heal", target="self", amount=amount, ty=kind)
        elif caster == own and target.startswith("p:"):
            self.write("heal", target=target[2:], amount=amount, ty=kind)
