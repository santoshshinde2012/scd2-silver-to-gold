"""Lock every number the article quotes from the local run."""

from __future__ import annotations

from dataclasses import asdict

from src.scenario import ScenarioResult


def test_one_move_is_three_change_rows(result: ScenarioResult) -> None:
    assert result.change_rows_for_one_move == ["update_preimage", "update_postimage", "insert"]
    assert asdict(result.silver_42) == {"spans": 2, "overlapping_pairs": 0, "open_spans": 1}


def test_copy_plus_replay_doubles_history(result: ScenarioResult) -> None:
    assert asdict(result.replay_without_cut_point_42) == {"spans": 5, "overlapping_pairs": 6, "open_spans": 3}


def test_option_1_view_carries_silver_as_it_is(result: ScenarioResult) -> None:
    assert asdict(result.carry_view_42) == {"spans": 2, "overlapping_pairs": 0, "open_spans": 1}
    assert result.carry_view_matches_silver is True


def test_option_2_one_cut_point_keeps_gold_equal_to_silver(result: ScenarioResult) -> None:
    assert result.cut_point_version == 2
    assert result.cut_point_matches_silver is True


def test_a_correction_arrives_as_deletes_and_inserts(result: ScenarioResult) -> None:
    assert result.correction_change_types == ["delete", "insert"]


def test_ignoring_deletes_leaves_an_old_open_span(result: ScenarioResult) -> None:
    assert asdict(result.ignore_deletes_42) == {"spans": 3, "overlapping_pairs": 1, "open_spans": 2}


def test_applying_deletes_matches_silver(result: ScenarioResult) -> None:
    assert asdict(result.with_deletes_42) == {"spans": 2, "overlapping_pairs": 0, "open_spans": 1}
    assert result.with_deletes_matches_silver is True
    assert result.silver_42_after_correction == [("Pune", "2026-01-10", "2026-05-20"), ("Mumbai", "2026-05-20", None)]


def test_option_3_temporal_join_splits_pune_at_the_adviser_change(result: ScenarioResult) -> None:
    assert result.temporal_join == [
        ("Pune", "Santosh", "2026-01-10", "2026-03-15"),
        ("Pune", "Ravi", "2026-03-15", "2026-06-01"),
        ("Mumbai", "Ravi", "2026-06-01", None),
    ]


def test_current_adviser_join_is_wrong_for_january(result: ScenarioResult) -> None:
    assert result.current_adviser_join[0] == ("Pune", "Ravi", "2026-01-10", "2026-06-01")
