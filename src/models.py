"""Value objects and column names shared by every module."""

from __future__ import annotations

from dataclasses import dataclass

#: One span is one customer plus the day it starts. Gold applies changes by this key.
SPAN_KEY: list[str] = ["customer_id", "valid_from"]
#: The columns of a customer span, in Silver and in Gold.
SPAN_COLUMNS: list[str] = ["customer_id", "city", "valid_from", "valid_to"]
#: A date later than any real one, used as the end of an open span when comparing.
OPEN_END = "9999-12-31"

#: Change data feed row types, in the order they should be applied within one commit.
CHANGE_ORDER: dict[str, int] = {"update_preimage": 0, "update_postimage": 1, "delete": 2, "insert": 3}


@dataclass(frozen=True)
class Move:
    """A business event: a customer lives in a new city from a date."""

    customer_id: int
    city: str
    on: str


@dataclass(frozen=True)
class SpanStats:
    """What we count in a history table for one customer."""

    spans: int
    overlapping_pairs: int
    open_spans: int


@dataclass(frozen=True)
class JoinedSpan:
    """One Gold row at the new grain: a city and an adviser over one period."""

    city: str
    adviser: str
    valid_from: str
    valid_to: str | None

    def as_tuple(self) -> tuple[str, str, str, str | None]:
        return (self.city, self.adviser, self.valid_from, self.valid_to)
