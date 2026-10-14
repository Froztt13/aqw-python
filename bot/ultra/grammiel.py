"""Run Ultra Gramiel on one launcher slot.

Entry point for ``py -m bot.ultra.grammiel`` -- ``ultra_grammiel.bat`` pipes
``1``, ``2``, ``3`` or ``4`` on stdin, and that number is the launcher slot
in ``bot.ultra.config.LOADOUTS["grammiel"]`` this run wears.  Unlike
``daily.py`` this is a *single* boss, so there is no sequence to stop
between -- a loadout that cannot be equipped stops the bot outright.

Nothing runs on import: ``input()`` and ``Bot(...)`` live under
``if __name__ == "__main__"``.
"""

from __future__ import annotations

import asyncio

from bot.ultra.config import ACCOUNTS, SERVER
from bot.ultra.ultra_gramiel import UltraGrammiel
from core.bot import Bot
from core.command import Command


async def fight_gramiel(cmd: Command, index_class: int) -> None:
    """Fight Gramiel once on ``index_class``'s loadout.

    Split out so the login plumbing below stays a straight copy of
    ``daily.py``; call it directly if you ever want Gramiel without a
    terminal attached.
    """
    await UltraGrammiel(cmd, index_class).run()


if __name__ == "__main__":
    input_str = input("Select bot [1-4] : ")
    input_int = int(input_str)
    selected_slave = ACCOUNTS[input_int - 1]

    b = Bot(
        roomNumber=9099,
        showLog=True,
        showDebug=False,
        showChat=True,
        isScriptable=True,
        followPlayer=ACCOUNTS[0].username.lower(),
        slavesPlayer=[slave.username for i, slave in enumerate(ACCOUNTS) if i != 0],
        muteSpamWarning=True
    )

    b.set_login_info(selected_slave.username, selected_slave.password, SERVER)

    async def run_bot(cmd: Command) -> None:
        await fight_gramiel(cmd, input_int)

    asyncio.run(b.start_bot(run_bot))
