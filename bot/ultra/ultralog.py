"""Per-account activity log for the ultra fights.

Every account appends to its own file under ``logs/ultra/<account>.log``, so
after a wipe you can read back what each of the four panes actually did:

* ``RUN`` / ``LOADOUT`` -- which boss, slot, class, gear, scroll and target
  priority were used, and therefore which were missing when the fight opened;
* ``CELL`` -- the ``id.N`` -> monster-name map of the fight cell, logged once
  whenever it changes, so an id in the config can be read back as a name;
* ``STATE`` -- HP, connection, and whether each configured target currently
  resolves, whenever any of them changes and at least every five seconds;
* ``SKILL`` -- a cast that came back false, which is what a rotation that is
  silently doing nothing looks like from the outside;
* ``ABORT`` / ``FINISH`` -- why the bot stopped, and when.

Nothing in here can fail the fight.  :class:`FightLog` swallows every
exception and a failed open simply leaves the log inert: a logger that raises
is worse than no logger at all, because it would take down the very bot it
was asked to record.
"""

from __future__ import annotations

import os
from datetime import datetime
from typing import Any, Optional

#: ``<repo>/logs/ultra`` -- three directories up from ``bot/ultra/``.
LOG_DIR = os.path.normpath(
    os.path.join(
        os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))),
        "logs",
        "ultra",
    )
)


def _stamp() -> str:
    """Local time to the millisecond, so two ticks never sort alike."""
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S.%f")[:-3]


def _fmt(value: Any) -> str:
    """Render one field on one line: ``None`` becomes ``-``, spaces get quotes."""
    if value is None:
        return "-"
    if isinstance(value, str):
        return '"{}"'.format(value) if (" " in value or value == "") else value
    if isinstance(value, (list, tuple, set)):
        return ",".join(str(item) for item in value) or "-"
    return str(value)


class FightLog:
    """Append-only event log.  Every method is best-effort and never raises."""

    def __init__(self) -> None:
        self.path: Optional[str] = None
        self._fh = None

    # -- lifecycle -----------------------------------------------------

    def open(self, boss: str, slot: str, username: str) -> None:
        """Attach to ``logs/ultra/<account>.log``, appending across runs.

        One file per account rather than per boss: a daily pane fights four
        bosses in a row, and reading that back in order is the whole point.
        """
        self.close()
        try:
            os.makedirs(LOG_DIR, exist_ok=True)
            account = "".join(
                c for c in (username or "unknown") if c.isalnum() or c in "-_"
            ) or "unknown"
            handle = open(os.path.join(LOG_DIR, f"{account}.log"), "a",
                          encoding="utf-8")
        except Exception:
            return
        self._fh = handle
        self.path = os.path.join(LOG_DIR, f"{account}.log")
        self.event("RUN", boss=boss, slot=slot, account=username or "unknown")

    def close(self) -> None:
        """Flush and detach.  Safe to call twice, or on a log never opened."""
        handle, self._fh = self._fh, None
        self.path = None
        if handle is None:
            return
        try:
            handle.close()
        except Exception:
            pass

    # -- recording -----------------------------------------------------

    def event(self, kind: str, **fields: Any) -> None:
        """Append ``<time>  <KIND>  key=value ...``.  Never raises."""
        handle = self._fh
        if handle is None:
            return
        try:
            line = _stamp() + "  " + kind.ljust(10)
            if fields:
                line += " " + " ".join(
                    f"{key}={_fmt(value)}" for key, value in fields.items()
                )
            handle.write(line + "\n")
            handle.flush()
        except Exception:
            pass
