"""Run the four daily ultra bosses on one launcher slot.

Entry point for ``py -m bot.ultra.daily`` -- ``ultra_daily_pane.bat`` pipes
``1``, ``2``, ``3`` or ``4`` on stdin, and that number is the launcher slot
in ``bot.ultra.config.LOADOUTS`` this run wears.  The four panes are four
*slots of the same daily*, not four different bots.

The run is four steps in a fixed order -- Tyndarius, Engineer, Ezrajal,
Warden.  Each step builds its own class out of ``bot/ultra/ultra_<boss>.py``
and hands it the same slot, so every boss equips the loadout configured for
that slot.  A boss that cannot equip its loadout stops the bot
(``CoreUltra._abort``) and the flag travels back up here, which is why step
two never starts after step one fails.

Nothing runs on import: ``input()`` and ``Bot(...)`` live under
``if __name__ == "__main__"``, so tests can import :class:`DailyUltra` and
replace a step.
"""

from __future__ import annotations

import asyncio
import os

from bot.ultra.config import ACCOUNTS, SERVER
from bot.ultra.telemetry import install_from_env
from bot.ultra.ultra_ezrajal import UltraEzrajal
from bot.ultra.ultra_engineer import UltraEngineer
from bot.ultra.ultra_tyndarius import UltraTyndarius
from bot.ultra.ultra_warden import UltraWarden
from core.bot import Bot
from core.command import Command


async def main(cmd: Command) -> None:
    """Standalone entry for ``BOT_PATH=bot.ultra.daily`` (slot from ``AQW_SLOT``)."""
    await DailyUltra(cmd, int(os.environ.get("AQW_SLOT", "1"))).run()


class DailyUltra:
    """The four daily bosses, run in order, stopping at the first failure."""

    def __init__(self, cmd: Command, index_class: int) -> None:
        self.cmd = cmd
        #: Launcher slot 1-4, straight from ``input("Select bot [1-4]")``.
        self.index_class = index_class
        #: Set when a step's boss aborts; :meth:`run` stops the sequence there.
        self.aborted = False

    # ------------------------------------------------------------------
    # the four steps
    # ------------------------------------------------------------------
    # One method per boss rather than a loop over a class tuple, so a single
    # step can be replaced (tests do) or run on its own without re-running
    # the other three.

    async def step_tyndarius(self) -> None:
        """Step 1 -- see ``bot/ultra/ultra_tyndarius.py``."""
        await self._run_one(UltraTyndarius)

    async def step_engineer(self) -> None:
        """Step 2 -- see ``bot/ultra/ultra_engineer.py``."""
        await self._run_one(UltraEngineer)

    async def step_ezrajal(self) -> None:
        """Step 3 -- see ``bot/ultra/ultra_ezrajal.py``."""
        await self._run_one(UltraEzrajal)

    async def step_warden(self) -> None:
        """Step 4 -- see ``bot/ultra/ultra_warden.py``."""
        await self._run_one(UltraWarden)

    async def _run_one(self, boss_cls) -> None:
        """Run one boss on this slot, then adopt its abort flag.

        Each boss is a fresh object and so starts with ``aborted = False``;
        the flag has to be copied up to this runner for :meth:`run` to see it.
        """
        boss = boss_cls(self.cmd, self.index_class)
        await boss.run()
        if boss.aborted:
            self.aborted = True

    # ------------------------------------------------------------------
    # the run
    # ------------------------------------------------------------------

    async def run(self) -> None:
        """Run the four steps in order, or stop at the first failure.

        A boss that aborted has *already* stopped the bot -- ``_abort`` sets
        the flag **and** calls ``stop_bot`` -- so all that is left here is
        declining to start the next one.
        """
        for step in (self.step_tyndarius, self.step_engineer,
                     self.step_ezrajal, self.step_warden):
            await step()
            if self.aborted:
                return
        self.cmd.stop_bot("finished daily ultra")


if __name__ == "__main__":
    input_int = int(input("Select bot [1-4] : "))
    # Per-pane slot, read back by main(); set here so it can never be inherited
    # as the same value by all four panes.
    os.environ["AQW_SLOT"] = str(input_int)
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
    telemetry = install_from_env(b, input_int, selected_slave.username)

    async def run_bot(cmd: Command) -> None:
        await main(cmd)

    try:
        asyncio.run(b.start_bot(run_bot))
    finally:
        if telemetry is not None:
            telemetry.close()
