"""Option 3: Gold changes the grain, so it builds history of its own with a temporal join."""

from __future__ import annotations

import pandas as pd

from ..models import OPEN_END, JoinedSpan
from ..spans import span_end


def temporal_join(customers: pd.DataFrame, advisers: pd.DataFrame) -> list[JoinedSpan]:
    """Pair each customer span with every adviser span that overlaps it, cut to the overlap.

    Time with no adviser span is dropped. Whether to show that gap instead is a business decision.
    """
    rows: list[JoinedSpan] = []
    for c in customers.to_dict("records"):
        for a in advisers[advisers["customer_id"] == c["customer_id"]].to_dict("records"):
            start = max(c["valid_from"], a["valid_from"])
            stop = min(span_end(c["valid_to"]) or OPEN_END, span_end(a["valid_to"]) or OPEN_END)
            if start < stop:
                rows.append(JoinedSpan(c["city"], a["adviser"], start, None if stop == OPEN_END else stop))
    return sorted(rows, key=lambda r: r.valid_from)


def current_value_join(customers: pd.DataFrame, advisers: pd.DataFrame) -> list[JoinedSpan]:
    """The tempting join: today's adviser beside every past customer span. Wrong for the past."""
    current = advisers[advisers["valid_to"].isna()].set_index("customer_id")["adviser"]
    rows = [
        JoinedSpan(c["city"], current[c["customer_id"]], c["valid_from"], span_end(c["valid_to"]))
        for c in customers.to_dict("records")
    ]
    return sorted(rows, key=lambda r: r.valid_from)
