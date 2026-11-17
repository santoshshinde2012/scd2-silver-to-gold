"""Small interfaces. The three designs depend on these, never on the `deltalake` library."""

from __future__ import annotations

from typing import Protocol

import pandas as pd

from .models import Move


class HistoryReader(Protocol):
    """Read side of a span table with a change data feed."""

    def version(self) -> int: ...

    def read(self, version: int | None = None) -> pd.DataFrame: ...

    def changes(self, start: int, end: int | None = None) -> pd.DataFrame: ...


class HistoryWriter(Protocol):
    """Write side of Silver, standing in for what an SCD type 2 process does to the table."""

    def first_load(self, rows: list[dict]) -> int: ...

    def move(self, move: Move) -> int: ...

    def correct_move_date(self, move: Move) -> int: ...


class ChangeApplier(Protocol):
    """How Gold applies a batch of change rows. Each way is one class."""

    @property
    def name(self) -> str: ...

    def apply(self, gold: pd.DataFrame, changes: pd.DataFrame) -> pd.DataFrame: ...
