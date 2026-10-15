"""Cross-process party coordination for the four-pane ultra run.

The four panes are separate processes, so "did every player get the boss's temp
item?" has to travel through a file.  State lives in
``capture_logs/ultra/<run_id>/party/<boss>.r<round>.slot<N>.json``: the round
is in the name, so a new round never overwrites the verdict a slower pane is
still reading.

Disabled unless ``AQW_RUN_ID`` is set -- which ``ultra_daily_pane.bat`` does --
so a single bot launched by hand just fights once and does not wait for a party
that is not there.
"""

from __future__ import annotations

import json
import os
import time
from pathlib import Path

#: Launcher slots that make up one ultra party.
PARTY_SLOTS = (1, 2, 3, 4)
#: Give up (and move on) after this many rounds rather than looping forever.
MAX_ROUNDS = 6
#: How long one round waits for the other panes before treating them as absent.
WAIT_TIMEOUT_S = 180


def enabled() -> bool:
    return bool(os.environ.get("AQW_RUN_ID", "").strip())


def _dir() -> Path:
    base = Path(__file__).resolve().parents[2] / "capture_logs" / "ultra"
    run = os.environ.get("AQW_RUN_ID", "").strip() or "manual"
    path = base / run / "party"
    path.mkdir(parents=True, exist_ok=True)
    return path


def report(boss: str, round_number: int, slot: int, ok: bool) -> None:
    """Publish this slot's verdict for ``boss`` in ``round_number``."""
    try:
        (_dir() / f"{boss}.r{round_number}.slot{slot}.json").write_text(
            json.dumps({"ok": bool(ok), "t": time.time()}), encoding="utf-8"
        )
    except Exception:
        pass


def wait(boss: str, round_number: int, slots=PARTY_SLOTS,
         timeout: int = WAIT_TIMEOUT_S) -> dict:
    """Block until every slot reports this round, or the timeout expires.

    Returns ``{slot: ok}`` with only the slots that reported.
    """
    deadline = time.time() + timeout
    found: dict[int, bool] = {}
    while time.time() < deadline and len(found) < len(slots):
        for slot in slots:
            if slot in found:
                continue
            path = _dir() / f"{boss}.r{round_number}.slot{slot}.json"
            if path.exists():
                try:
                    found[slot] = bool(json.loads(path.read_text(encoding="utf-8")).get("ok"))
                except Exception:
                    pass
        if len(found) < len(slots):
            time.sleep(1)
    return found


def barrier(name: str, key: str, size: int = 4, timeout: int = 60) -> bool:
    """Rendezvous: every caller leaves its own marker and waits for ``size``.

    Unlike :func:`wait`, the key is arbitrary (a username here), so it works for
    a one-off sync point rather than a numbered round.  Returns True if the
    barrier filled before the timeout, False otherwise (the caller proceeds
    anyway -- a missing pane must not wedge the run).
    """
    directory = _dir()
    safe_key = "".join(c for c in (key or "x") if c.isalnum() or c in "-_") or "x"
    try:
        (directory / f"{name}.{safe_key}.ready").write_text(str(time.time()),
                                                            encoding="utf-8")
    except Exception:
        pass
    deadline = time.time() + timeout
    while time.time() < deadline:
        try:
            if len(list(directory.glob(f"{name}.*.ready"))) >= size:
                return True
        except Exception:
            pass
        time.sleep(0.2)
    return False


# A wipe kills every pane within seconds.  Deaths further apart than this are
# separate solo deaths, not one wipe.
WIPE_SPAN_S = 20.0


def _safe_key(key) -> str:
    return "".join(c for c in str(key) if c.isalnum() or c in "-_") or "x"


def report_death(name: str, key) -> float:
    """Record that ``key`` just died; returns the death timestamp.

    ``key`` is any per-pane id -- a slot number, or the account name where the
    launcher does not pass one (Ultra Speaker).  Stored per key so the panes can
    tell a full-party wipe (all die together) from one pane going down alone.
    """
    now = time.time()
    try:
        (_dir() / f"{name}.{_safe_key(key)}.dead").write_text(str(now), encoding="utf-8")
    except Exception:
        pass
    return now


def clear_death(name: str, key) -> None:
    """Drop one pane's death marker once its fate is settled."""
    try:
        (_dir() / f"{name}.{_safe_key(key)}.dead").unlink()
    except Exception:
        pass


def death_times(name: str, keys=PARTY_SLOTS) -> dict:
    """``{key: death_epoch}`` for every pane key that currently has a marker."""
    found: dict = {}
    for key in keys:
        try:
            found[key] = float(
                (_dir() / f"{name}.{_safe_key(key)}.dead").read_text(encoding="utf-8")
            )
        except Exception:
            continue
    return found


# --- finished / "all quests done" markers -------------------------------
# A pane writes one of these when it has turned in all its quests.  The party
# stops only once all four exist; if one is missing the run keeps going.

def mark_done(name: str, key) -> None:
    try:
        (_dir() / f"{name}.{_safe_key(key)}.done").write_text(str(time.time()),
                                                              encoding="utf-8")
    except Exception:
        pass


def clear_done(name: str, keys=PARTY_SLOTS) -> None:
    for key in keys:
        try:
            (_dir() / f"{name}.{_safe_key(key)}.done").unlink()
        except Exception:
            pass


def all_done(name: str, keys=PARTY_SLOTS) -> bool:
    """True only when every pane has a done marker."""
    for key in keys:
        if not (_dir() / f"{name}.{_safe_key(key)}.done").exists():
            return False
    return True


def mark_abort(name: str, key, reason: str) -> None:
    """Record a preflight failure (e.g. too few Scrolls) so the app does not
    relogin into the same failure."""
    try:
        (_dir() / f"{name}.{_safe_key(key)}.abort").write_text(str(reason),
                                                               encoding="utf-8")
    except Exception:
        pass


def clear_abort(name: str, keys=PARTY_SLOTS) -> None:
    for key in keys:
        try:
            (_dir() / f"{name}.{_safe_key(key)}.abort").unlink()
        except Exception:
            pass


def any_abort(name: str, keys=PARTY_SLOTS):
    """Return the first abort reason found, or ``None``."""
    for key in keys:
        try:
            path = _dir() / f"{name}.{_safe_key(key)}.abort"
            if path.exists():
                return path.read_text(encoding="utf-8")
        except Exception:
            continue
    return None
