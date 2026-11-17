"""Shared fixtures: one full run of the article's example on a temporary Delta lake."""

from __future__ import annotations

import pandas as pd
import pytest

from src.history_demo import run
from src.scenario import ScenarioResult


@pytest.fixture(scope="session")
def result(tmp_path_factory: pytest.TempPathFactory) -> ScenarioResult:
    return run(tmp_path_factory.mktemp("lake"))


def spans(*rows: tuple[int, str, str, str | None]) -> pd.DataFrame:
    """Build a small span table: (customer_id, city, valid_from, valid_to)."""
    return pd.DataFrame([dict(zip(["customer_id", "city", "valid_from", "valid_to"], r, strict=True)) for r in rows])
