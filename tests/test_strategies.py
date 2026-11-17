"""Unit tests for the change appliers and the three Gold designs, with in-memory fakes."""

from __future__ import annotations

from dataclasses import dataclass, field

import pandas as pd

from src.models import SPAN_COLUMNS as COLUMNS
from src.strategies import (
    AppendChangedRows,
    CarrySilverView,
    CutPointCopy,
    MirrorBySpanKey,
    UpsertBySpanKey,
    temporal_join,
)

from .conftest import spans


def change(kind: str, customer_id: int, city: str, start: str, stop: str | None, version: int = 1) -> dict:
    return {
        "customer_id": customer_id,
        "city": city,
        "valid_from": start,
        "valid_to": stop,
        "_change_type": kind,
        "_commit_version": version,
    }


@dataclass
class FakeSilver:
    """An in-memory `HistoryReader`: a list of versions and the change rows of each commit."""

    versions: list[pd.DataFrame]
    feed: list[dict] = field(default_factory=list)

    def version(self) -> int:
        return len(self.versions) - 1

    def read(self, version: int | None = None) -> pd.DataFrame:
        return self.versions[self.version() if version is None else version]

    def changes(self, start: int, end: int | None = None) -> pd.DataFrame:
        end = self.version() if end is None else end
        rows = [c for c in self.feed if start <= c["_commit_version"] <= end]
        return pd.DataFrame(rows, columns=[*COLUMNS, "_change_type", "_commit_version"])


GOLD = spans((1, "Pune", "2026-01-10", None))
MOVE = pd.DataFrame(
    [
        change("update_preimage", 1, "Pune", "2026-01-10", None),
        change("update_postimage", 1, "Pune", "2026-01-10", "2026-06-01"),
        change("insert", 1, "Mumbai", "2026-06-01", None),
    ]
)


def test_append_turns_an_update_into_a_second_row() -> None:
    assert len(AppendChangedRows().apply(GOLD, MOVE)) == 3


def test_mirror_applies_an_update_in_place() -> None:
    out = MirrorBySpanKey().apply(GOLD, MOVE)
    assert out[["city", "valid_to"]].values.tolist() == [["Pune", "2026-06-01"], ["Mumbai", None]]


def test_upsert_ignores_deletes_and_mirror_applies_them() -> None:
    delete = pd.DataFrame([change("delete", 1, "Pune", "2026-01-10", None)])
    assert len(UpsertBySpanKey().apply(GOLD, delete)) == 1
    assert len(MirrorBySpanKey().apply(GOLD, delete)) == 0


def test_option_1_view_always_reads_the_latest_silver() -> None:
    silver = FakeSilver([GOLD])
    view = CarrySilverView(silver, renames=(("valid_from", "start_date"),))
    silver.versions.append(spans((1, "Pune", "2026-01-10", "2026-06-01"), (1, "Mumbai", "2026-06-01", None)))
    assert list(view.read()["start_date"]) == ["2026-01-10", "2026-06-01"]


def test_option_2_catch_up_reads_only_changes_after_the_cut_point() -> None:
    after_move = spans((1, "Pune", "2026-01-10", "2026-06-01"), (1, "Mumbai", "2026-06-01", None))
    silver = FakeSilver([GOLD], feed=MOVE.to_dict("records"))
    option_2 = CutPointCopy(silver, MirrorBySpanKey())
    gold, cut_point = option_2.bootstrap()
    silver.versions.append(after_move)
    gold, latest = option_2.catch_up(gold, cut_point)
    assert (cut_point, latest, len(gold)) == (0, 1, 2)


def test_option_3_drops_customer_time_with_no_adviser() -> None:
    customers = spans((1, "A", "2026-01-01", None))
    advisers = pd.DataFrame([{"customer_id": 1, "adviser": "X", "valid_from": "2026-03-01", "valid_to": None}])
    assert [r.as_tuple() for r in temporal_join(customers, advisers)] == [("A", "X", "2026-03-01", None)]
