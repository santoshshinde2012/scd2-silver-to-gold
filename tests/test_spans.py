"""Unit tests for the span helpers."""

from __future__ import annotations

from src.spans import overlaps, same_history, span_stats

from .conftest import spans


def test_touching_spans_do_not_overlap() -> None:
    assert overlaps("2026-01-01", "2026-02-01", "2026-02-01", None) is False


def test_two_open_spans_overlap() -> None:
    assert overlaps("2026-01-01", None, "2026-03-01", None) is True


def test_span_stats_counts_spans_overlaps_and_open_ends() -> None:
    table = spans((1, "A", "2026-01-01", "2026-02-01"), (1, "B", "2026-02-01", None), (1, "B", "2026-03-01", None))
    stats = span_stats(table, 1)
    assert (stats.spans, stats.overlapping_pairs, stats.open_spans) == (3, 1, 2)


def test_same_history_ignores_row_order() -> None:
    a = spans((1, "A", "2026-01-01", "2026-02-01"), (1, "B", "2026-02-01", None))
    b = spans((1, "B", "2026-02-01", None), (1, "A", "2026-01-01", "2026-02-01"))
    assert same_history(a, b) is True
