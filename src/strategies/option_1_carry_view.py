"""Option 1: carry Silver's spans as they are.

Gold is a view over Silver. It keeps no rows of its own, so there is nothing to bootstrap,
nothing to replay, and a refresh cannot write the past twice.
"""

from __future__ import annotations

from dataclasses import dataclass

import pandas as pd

from ..protocols import HistoryReader


@dataclass(frozen=True)
class CarrySilverView:
    """A view: every read returns what Silver holds now, with Gold's column names."""

    silver: HistoryReader
    #: Databricks AUTO CDC names the history columns `__START_AT` and `__END_AT`.
    #: The local Silver already uses Gold's names, so the default mapping is empty.
    renames: tuple[tuple[str, str], ...] = ()

    def read(self) -> pd.DataFrame:
        return self.silver.read().rename(columns=dict(self.renames))
