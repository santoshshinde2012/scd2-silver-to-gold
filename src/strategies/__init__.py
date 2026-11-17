"""The three Gold designs from the article, plus the ways Gold can apply change rows."""

from __future__ import annotations

from .change_appliers import AppendChangedRows, MirrorBySpanKey, UpsertBySpanKey
from .option_1_carry_view import CarrySilverView
from .option_2_cut_point import CutPointCopy, copy_and_replay_everything
from .option_3_own_history import current_value_join, temporal_join

__all__ = [
    "AppendChangedRows",
    "CarrySilverView",
    "CutPointCopy",
    "MirrorBySpanKey",
    "UpsertBySpanKey",
    "copy_and_replay_everything",
    "current_value_join",
    "temporal_join",
]
