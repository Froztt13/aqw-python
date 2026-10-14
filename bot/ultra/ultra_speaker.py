"""Entry point for Ultra Speaker -- ``bot.ultra.ultra_speaker``.

The fight itself lives in :mod:`bot.ultra.core_ultra` as
``class UltraSpeaker(CoreUltra)``; ``plan.md`` Phase 3 folded the old
``ultra_speaker.py`` in there because it shared every line of machinery with
the other bosses.  This module is only the seam, and it exists for two
reasons:

* ``start.py`` / ``gui.py`` load ``BOT_PATH`` by name and call its
  ``main(cmd)`` -- deleting the file took that away, since "no importers"
  missed a module reached by a *string*, not an ``import``;
* the pane launcher needs ``py -m bot.ultra.ultra_speaker`` to run.

Speaker has **no loadout slots**.  Pane *n* picks ``ACCOUNTS[n-1]`` to log in
as and ``SOLO_ROLES[n-1]`` as ``Bot(soloClass=...)``, so the 2x2 grid covers
all four roles the boss's ``malgor_handler`` rotates through.  The gear for
each role is ``SOLO_LOADOUTS[class]``, looked up by name rather than stored
next to it.
"""

from __future__ import annotations

import asyncio

from bot.ultra.config import ACCOUNTS, SERVER, get_solo_role
from bot.ultra.core_ultra import UltraSpeaker
from bot.ultra.telemetry import install_from_env
from core.bot import Bot
from core.command import Command


async def main(cmd: Command) -> None:
    """Standalone entry for ``start.py`` / ``gui.py`` (``bot.ultra.ultra_speaker``).

    The class comes from ``Bot(soloClass=...)`` -- ``start.py`` has it as a
    commented-out argument and ``gui.py`` reads the ``solo_class`` config
    field.  If neither is set the fight stops with an explanation rather than
    guessing which of the four to wear.
    """
    await UltraSpeaker(cmd).run()


if __name__ == "__main__":
    input_str = input("Select bot [1-4] : ")
    input_int = int(input_str)
    selected_slave = ACCOUNTS[input_int - 1]
    # The one thing Speaker's constructor needs that the other two do not:
    # which of the four roles this pane plays.
    role = get_solo_role(input_int)

    b = Bot(
        roomNumber=9099,
        showLog=True,
        showDebug=False,
        showChat=True,
        isScriptable=True,
        followPlayer=ACCOUNTS[0].username.lower(),
        slavesPlayer=[slave.username for i, slave in enumerate(ACCOUNTS) if i != 0],
        muteSpamWarning=True,
        soloClass=role,
    )

    b.set_login_info(selected_slave.username, selected_slave.password, SERVER)
    telemetry = install_from_env(b, input_int, selected_slave.username)

    async def run_bot(cmd: Command) -> None:
        await UltraSpeaker(cmd).run()

    try:
        asyncio.run(b.start_bot(run_bot))
    finally:
        if telemetry is not None:
            telemetry.close()
