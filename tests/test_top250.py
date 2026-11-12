import pytest
from sakuramedia_javdb_ranking.top250 import (
    TOP250_FETCHED_AT,
    TOP250_PERIODS,
    top250_numbers,
)

FIXED_PERIODS = ("all", "censored", "uncensored", "fc2")


def test_top250_periods_cover_fixed_boards_and_history():
    assert TOP250_PERIODS[:4] == FIXED_PERIODS
    years = [int(period) for period in TOP250_PERIODS if period.isdigit()]
    assert years[0] == 2026
    assert years[-1] == 2008
    assert years == list(range(years[0], years[-1] - 1, -1))
    assert TOP250_FETCHED_AT


def test_top250_lists_are_non_empty_and_bounded():
    for period in TOP250_PERIODS:
        numbers = top250_numbers(period)
        assert numbers, period
        assert len(numbers) <= 250, period
        assert len(numbers) == len(set(numbers)), period
        assert all(isinstance(number, str) and number for number in numbers)


def test_top250_numbers_returns_a_copy():
    first = top250_numbers("all")
    first.clear()
    assert len(top250_numbers("all")) == 250


def test_top250_rejects_unknown_period():
    with pytest.raises(ValueError, match="unsupported top250 period"):
        top250_numbers("1999")
