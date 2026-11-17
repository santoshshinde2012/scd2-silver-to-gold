"""Three ways Gold can apply Silver's change rows. Only the last one keeps Gold equal to Silver."""

from __future__ import annotations

from dataclasses import dataclass

import pandas as pd

from ..models import SPAN_KEY
from ..spans import normalise

NEW_VALUES = ("insert", "update_postimage")


@dataclass(frozen=True)
class AppendChangedRows:
    """Treat every new or updated row as a new history row. This is what doubles history."""

    name: str = "append every changed row"

    def apply(self, gold: pd.DataFrame, changes: pd.DataFrame) -> pd.DataFrame:
        new_rows = changes[changes["_change_type"].isin(NEW_VALUES)]
        return normalise(pd.concat([gold, new_rows], ignore_index=True))


@dataclass(frozen=True)
class UpsertBySpanKey:
    """Replace a span by its key, but ignore deletes. A corrected date leaves the old span behind."""

    name: str = "upsert by span key, ignore deletes"

    def apply(self, gold: pd.DataFrame, changes: pd.DataFrame) -> pd.DataFrame:
        out = gold.set_index(SPAN_KEY)
        for row in changes.to_dict("records"):
            if row["_change_type"] in NEW_VALUES:
                out.loc[(row["customer_id"], row["valid_from"]), ["city", "valid_to"]] = [row["city"], row["valid_to"]]
        return normalise(out.reset_index())


@dataclass(frozen=True)
class MirrorBySpanKey:
    """Replace a span by its key and remove deleted spans. Pre-images only say what was there."""

    name: str = "mirror by span key, with deletes"

    def apply(self, gold: pd.DataFrame, changes: pd.DataFrame) -> pd.DataFrame:
        out = gold.set_index(SPAN_KEY)
        for row in changes.to_dict("records"):
            key = (row["customer_id"], row["valid_from"])
            if row["_change_type"] == "delete":
                out = out.drop(index=key, errors="ignore")
            elif row["_change_type"] in NEW_VALUES:
                out.loc[key, ["city", "valid_to"]] = [row["city"], row["valid_to"]]
        return normalise(out.reset_index())
