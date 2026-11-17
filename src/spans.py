"""Span helpers: normalise a frame, compare two histories, and count what can go wrong."""

from __future__ import annotations

from typing import Any

import pandas as pd

from .models import OPEN_END, SPAN_COLUMNS, SPAN_KEY, SpanStats


def span_end(value: Any) -> str | None:
    """An open span has no end. Pandas may hand us None or NaN for it."""
    if value is None or (isinstance(value, float) and pd.isna(value)):
        return None
    return value


def normalise(frame: pd.DataFrame) -> pd.DataFrame:
    """Keep the span columns, use None for open ends, and sort by the span key."""
    out = frame[SPAN_COLUMNS].copy()
    out["valid_to"] = pd.Series([span_end(v) for v in out["valid_to"]], index=out.index, dtype=object)
    return out.sort_values(SPAN_KEY).reset_index(drop=True)


def same_history(a: pd.DataFrame, b: pd.DataFrame) -> bool:
    """True when two tables hold exactly the same spans."""
    return normalise(a).astype(str).equals(normalise(b).astype(str))


def overlaps(a_from: str, a_to: str | None, b_from: str, b_to: str | None) -> bool:
    """Half-open periods overlap when each starts before the other ends. Touching is not overlapping."""
    return a_from < (b_to or OPEN_END) and b_from < (a_to or OPEN_END)


def span_stats(frame: pd.DataFrame, customer_id: int) -> SpanStats:
    """Count spans, overlapping pairs and open spans for one customer."""
    rows = frame[frame["customer_id"] == customer_id].to_dict("records")
    pairs = sum(
        overlaps(a["valid_from"], span_end(a["valid_to"]), b["valid_from"], span_end(b["valid_to"]))
        for i, a in enumerate(rows)
        for b in rows[i + 1 :]
    )
    open_spans = sum(1 for r in rows if span_end(r["valid_to"]) is None)
    return SpanStats(spans=len(rows), overlapping_pairs=pairs, open_spans=open_spans)
