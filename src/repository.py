"""Silver as a local Delta table with a change data feed, using the open-source `deltalake` library."""

from __future__ import annotations

from pathlib import Path

import pandas as pd
import pyarrow as pa
from deltalake import DeltaTable, write_deltalake

from .models import CHANGE_ORDER, SPAN_COLUMNS, Move
from .spans import normalise

SPAN_SCHEMA = pa.schema(
    [
        ("customer_id", pa.int64()),
        ("city", pa.string()),
        ("valid_from", pa.string()),
        ("valid_to", pa.string()),
    ]
)


class DeltaHistoryRepository:
    """Customer spans in Silver. Implements both `HistoryReader` and `HistoryWriter`."""

    def __init__(self, root: Path, table_name: str = "silver_customer_history") -> None:
        self.path = str(root / table_name)

    # ---- write side: what an SCD type 2 process would do -----------------------------------
    def first_load(self, rows: list[dict]) -> int:
        write_deltalake(
            self.path,
            pa.Table.from_pylist(rows, schema=SPAN_SCHEMA),
            configuration={"delta.enableChangeDataFeed": "true"},
        )
        return self.version()

    def move(self, move: Move) -> int:
        """Close the open span (one commit), then add the new span (a second commit)."""
        DeltaTable(self.path).update(
            predicate=f"customer_id = {move.customer_id} AND valid_to IS NULL",
            updates={"valid_to": f"'{move.on}'"},
        )
        write_deltalake(self.path, pa.Table.from_pylist([self._open_span(move)], schema=SPAN_SCHEMA), mode="append")
        return self.version()

    def correct_move_date(self, move: Move) -> int:
        """Rewrite one customer's spans in one commit, with the corrected move date."""
        spans = self.read()
        mine = spans[spans["customer_id"] == move.customer_id].sort_values("valid_from").to_dict("records")
        first = dict(mine[0], valid_to=move.on)
        write_deltalake(
            self.path,
            pa.Table.from_pylist([first, self._open_span(move)], schema=SPAN_SCHEMA),
            mode="overwrite",
            predicate=f"customer_id = {move.customer_id}",
        )
        return self.version()

    # ---- read side -------------------------------------------------------------------------
    def version(self) -> int:
        return DeltaTable(self.path).version()

    def read(self, version: int | None = None) -> pd.DataFrame:
        return normalise(DeltaTable(self.path, version=version).to_pandas())

    def changes(self, start: int, end: int | None = None) -> pd.DataFrame:
        """Change rows with commit version from `start` to `end`, in the order they should be applied."""
        end = self.version() if end is None else end
        if start > end:
            return pd.DataFrame(columns=SPAN_COLUMNS + ["_change_type", "_commit_version"])
        reader = DeltaTable(self.path).load_cdf(starting_version=start, ending_version=end)
        feed = pa.table(reader.read_all()).to_pandas()
        feed["_order"] = feed["_change_type"].map(CHANGE_ORDER)
        return feed.sort_values(["_commit_version", "_order"]).drop(columns="_order").reset_index(drop=True)

    @staticmethod
    def _open_span(move: Move) -> dict:
        return {"customer_id": move.customer_id, "city": move.city, "valid_from": move.on, "valid_to": None}
