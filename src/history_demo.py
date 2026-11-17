"""Composition root: wire the local Delta table to the scenario and print what happened.

Run from the `code/` folder:  python -m src.history_demo
"""

from __future__ import annotations

import shutil
from dataclasses import asdict
from pathlib import Path

import deltalake

from .repository import DeltaHistoryRepository
from .scenario import ScenarioResult, SeedData, run_scenario

CODE_ROOT = Path(__file__).resolve().parent.parent
SEED_FILE = CODE_ROOT / "data" / "history.json"


def run(lake: Path, seed_file: Path = SEED_FILE) -> ScenarioResult:
    """Start from an empty folder, build Silver, and run every step of the example."""
    if lake.exists():
        shutil.rmtree(lake)
    return run_scenario(DeltaHistoryRepository(lake), SeedData.from_file(seed_file))


def report(r: ScenarioResult) -> list[str]:
    """The lines the article quotes, in order."""
    return [
        f"deltalake {deltalake.__version__} on local disk; not a Databricks runtime",
        f"1. One move wrote these change rows: {r.change_rows_for_one_move}. "
        f"Silver for customer 42: {asdict(r.silver_42)}",
        f"2. Copy Silver and replay retained changes as rows: customer 42 {asdict(r.replay_without_cut_point_42)}",
        f"3. Option 2, one cut point (V={r.cut_point_version}), then later changes by key: "
        f"Gold matches Silver: {r.cut_point_matches_silver}",
        f"4. Correction change types: {r.correction_change_types}",
        f"   Ignore deletes: customer 42 {asdict(r.ignore_deletes_42)}",
        f"   Apply deletes:  customer 42 {asdict(r.with_deletes_42)}; matches Silver: {r.with_deletes_matches_silver}",
        f"   Silver after the correction: {r.silver_42_after_correction}",
        f"5. Option 1, a view over Silver after the move and the correction: customer 42 {asdict(r.carry_view_42)}; "
        f"matches Silver: {r.carry_view_matches_silver}",
        f"6. Option 3, Gold changes the grain. Temporal join: {r.temporal_join}",
        f"   Current-adviser join: {r.current_adviser_join}",
    ]


def main() -> None:
    for line in report(run(CODE_ROOT / "lake")):
        print(line)


if __name__ == "__main__":
    main()
