"""The article's example, step by step. Orchestration only: it depends on protocols and strategies."""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Protocol

import pandas as pd

from .models import Move, SpanStats
from .protocols import HistoryReader, HistoryWriter
from .spans import same_history, span_end, span_stats
from .strategies import (
    AppendChangedRows,
    CarrySilverView,
    CutPointCopy,
    MirrorBySpanKey,
    UpsertBySpanKey,
    copy_and_replay_everything,
    current_value_join,
    temporal_join,
)

Row = tuple[str, str, str, str | None]


@dataclass(frozen=True)
class ScenarioResult:
    """Every number the article quotes from the local run."""

    change_rows_for_one_move: list[str]
    silver_42: SpanStats
    replay_without_cut_point_42: SpanStats
    carry_view_42: SpanStats
    carry_view_matches_silver: bool
    cut_point_version: int
    cut_point_matches_silver: bool
    correction_change_types: list[str]
    ignore_deletes_42: SpanStats
    with_deletes_42: SpanStats
    with_deletes_matches_silver: bool
    silver_42_after_correction: list[tuple[str, str, str | None]]
    temporal_join: list[Row]
    current_adviser_join: list[Row]


@dataclass(frozen=True)
class SeedData:
    """Synthetic customers, moves and advisers from `data/history.json`."""

    first_load: list[dict]
    move_42: Move
    move_7: Move
    correction_42: Move
    advisers_42: pd.DataFrame

    @classmethod
    def from_file(cls, path: Path) -> SeedData:
        raw = json.loads(path.read_text(encoding="utf-8"))
        return cls(
            first_load=raw["silver_first_load"],
            move_42=Move(**raw["move_42"]),
            move_7=Move(**raw["move_7"]),
            correction_42=Move(**raw["correction_42"]),
            advisers_42=pd.DataFrame(raw["advisers_42"]),
        )


class SilverTable(HistoryReader, HistoryWriter, Protocol):
    """Both sides of Silver. Only the scenario needs to write; the Gold designs only read."""


def run_scenario(silver: SilverTable, seed: SeedData) -> ScenarioResult:
    # 1. Silver keeps history: first load, then customer 42 moves.
    silver.first_load(seed.first_load)
    before_move = silver.version()
    silver.move(seed.move_42)
    change_rows = silver.changes(before_move + 1)["_change_type"].tolist()
    silver_42 = span_stats(silver.read(), 42)

    # The failure: copy today's Silver, then replay retained changes as new rows.
    doubled = copy_and_replay_everything(silver, AppendChangedRows())

    # Option 1: Gold is a view over Silver. It is read at the end, after every later change.
    option_1 = CarrySilverView(silver)

    # Option 2: copy at one cut point V, then only changes after V, by span key.
    option_2 = CutPointCopy(silver, MirrorBySpanKey())
    gold, cut_point = option_2.bootstrap()
    silver.move(seed.move_7)
    gold, after = option_2.catch_up(gold, cut_point)
    cut_point_matches = same_history(gold, silver.read())

    # A correction moves the date back: Silver rewrites the spans, so the feed has deletes and inserts.
    correction_version = silver.correct_move_date(seed.correction_42)
    correction_types = sorted(set(silver.changes(correction_version)["_change_type"]))
    ignore_deletes, _ = CutPointCopy(silver, UpsertBySpanKey()).catch_up(gold, after)
    with_deletes, _ = option_2.catch_up(gold, after)
    after_correction = [
        (r["city"], r["valid_from"], span_end(r["valid_to"]))
        for r in silver.read().query("customer_id == 42").to_dict("records")
    ]

    # Option 1, read now: the view shows Silver as it is after the move and the correction.
    view = option_1.read()

    # Option 3: Gold changes the grain (city with adviser), for customer 42 before the correction.
    spans_42 = silver.read(correction_version - 1).query("customer_id == 42")

    return ScenarioResult(
        change_rows_for_one_move=change_rows,
        silver_42=silver_42,
        replay_without_cut_point_42=span_stats(doubled, 42),
        carry_view_42=span_stats(view, 42),
        carry_view_matches_silver=same_history(view, silver.read()),
        cut_point_version=cut_point,
        cut_point_matches_silver=cut_point_matches,
        correction_change_types=correction_types,
        ignore_deletes_42=span_stats(ignore_deletes, 42),
        with_deletes_42=span_stats(with_deletes, 42),
        with_deletes_matches_silver=same_history(with_deletes, silver.read()),
        silver_42_after_correction=after_correction,
        temporal_join=[r.as_tuple() for r in temporal_join(spans_42, seed.advisers_42)],
        current_adviser_join=[r.as_tuple() for r in current_value_join(spans_42, seed.advisers_42)],
    )
