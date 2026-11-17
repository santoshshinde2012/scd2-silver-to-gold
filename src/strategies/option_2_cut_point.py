"""Option 2: Gold is its own table, copied once at one cut point V, then kept current by span key."""

from __future__ import annotations

from dataclasses import dataclass

import pandas as pd

from ..protocols import ChangeApplier, HistoryReader


def copy_and_replay_everything(silver: HistoryReader, applier: ChangeApplier) -> pd.DataFrame:
    """The failure: copy today's Silver, then replay every retained change on top of it.

    This is what a full refresh can do when a one-time copy and a change-feed reader both start again.
    """
    return applier.apply(silver.read(), silver.changes(0))


@dataclass(frozen=True)
class CutPointCopy:
    """Copy Silver at one recorded version V; the change reader starts after V."""

    silver: HistoryReader
    applier: ChangeApplier

    def bootstrap(self) -> tuple[pd.DataFrame, int]:
        """Return Gold's first copy and the version V it was taken at. Record V with Gold."""
        cut_point = self.silver.version()
        return self.silver.read(cut_point), cut_point

    def catch_up(self, gold: pd.DataFrame, after: int) -> tuple[pd.DataFrame, int]:
        """Apply only changes committed after `after`. Returns Gold and the new version to record."""
        latest = self.silver.version()
        return self.applier.apply(gold, self.silver.changes(after + 1, latest)), latest
