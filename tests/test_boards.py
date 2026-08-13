import pytest
from src.metadata._providers.exceptions import JavdbAuthError
from src.plugins import PluginRankingSource

from sakuramedia_javdb_ranking.boards import (
    TOP250_FIXED_PERIODS,
    TOP250_START_YEAR,
    build_ranking_source,
    build_top250_should_fetch,
    top250_periods,
    top250_type_for_period,
)
from sakuramedia_javdb_ranking.providers import PerRunProviderHolder


class FakeProvider:
    """记录调用的假 provider，验证各 board 抓取参数。"""

    def __init__(self):
        self.calls = []

    def get_playback_rank_numbers(self, *, filter_by, period):
        self.calls.append(("playback", filter_by, period))
        return ["ABP-001"]

    def get_rank_numbers(self, *, video_type, period):
        self.calls.append(("rank", video_type, period))
        return ["ABP-002"]

    def get_top_numbers(self, top_type, type_value, max_pages=None):
        self.calls.append(("top", top_type, type_value))
        return ["ABP-003"]


class FlakyProvider(FakeProvider):
    """首次 TOP250 抓取抛登录失败，之后正常；模拟一次失败只影响当次运行。"""

    def __init__(self):
        super().__init__()
        self._fail_once = True

    def get_top_numbers(self, top_type, type_value, max_pages=None):
        if self._fail_once:
            self._fail_once = False
            raise JavdbAuthError("login already failed for this provider instance")
        return super().get_top_numbers(top_type, type_value, max_pages)


def _source_with(provider):
    holder = PerRunProviderHolder(factory=lambda: provider)
    return build_ranking_source(
        provider_holder=holder,
        account_configured=True,
    )


def test_ranking_source_declares_six_boards():
    source = _source_with(FakeProvider())
    assert isinstance(source, PluginRankingSource)
    assert source.source_key == "javdb"
    assert [board.key for board in source.boards] == [
        "playback_all",
        "playback_high_score",
        "censored",
        "uncensored",
        "fc2",
        "top250",
    ]


def test_top250_periods_include_fixed_and_historical_years():
    periods = top250_periods()
    assert periods[:4] == TOP250_FIXED_PERIODS
    assert str(TOP250_START_YEAR) in periods
    assert periods[-1] == str(TOP250_START_YEAR)


def test_top250_type_for_period_maps_fixed_and_year():
    assert top250_type_for_period("all") == ("all", "")
    assert top250_type_for_period("censored") == ("video_type", "0")
    assert top250_type_for_period("uncensored") == ("video_type", "1")
    assert top250_type_for_period("fc2") == ("video_type", "3")
    assert top250_type_for_period("2018") == ("year", "2018")


def test_top250_should_fetch_rules():
    with_account = build_top250_should_fetch(account_configured=True)
    without_account = build_top250_should_fetch(account_configured=False)

    assert without_account("all", False) is False
    assert without_account("2020", True) is False
    assert with_account("all", False) is True
    assert with_account("2020", False) is True
    assert with_account("2020", True) is False


def test_free_boards_call_provider_with_mapped_args():
    provider = FakeProvider()
    source = _source_with(provider)

    source.boards[0].fetch_numbers("daily")
    source.boards[1].fetch_numbers("weekly")
    source.boards[2].fetch_numbers("monthly")
    source.boards[3].fetch_numbers("daily")
    source.boards[4].fetch_numbers("daily")

    assert provider.calls == [
        ("playback", "all", "daily"),
        ("playback", "high_score", "weekly"),
        ("rank", "0", "monthly"),
        ("rank", "1", "daily"),
        ("rank", "3", "daily"),
    ]


def test_top250_fetch_numbers_maps_period_to_top_api():
    provider = FakeProvider()
    source = _source_with(provider)

    source.boards[5].fetch_numbers("2018")
    source.boards[5].fetch_numbers("censored")

    assert provider.calls == [
        ("top", "year", "2018"),
        ("top", "video_type", "0"),
    ]


def test_provider_failure_does_not_poison_next_run():
    providers = [FlakyProvider(), FakeProvider()]
    holder = PerRunProviderHolder(factory=lambda: providers.pop(0))
    source = build_ranking_source(
        provider_holder=holder,
        account_configured=True,
    )

    holder.fresh_for_current_thread()
    with pytest.raises(JavdbAuthError):
        source.boards[5].fetch_numbers("all")

    holder.fresh_for_current_thread()
    assert source.boards[5].fetch_numbers("all") == ["ABP-003"]


def test_provider_holder_reuses_instance_within_run():
    provider = FakeProvider()
    holder = PerRunProviderHolder(factory=lambda: provider)
    source = build_ranking_source(
        provider_holder=holder,
        account_configured=True,
    )

    holder.fresh_for_current_thread()
    assert holder.get() is provider
    source.boards[0].fetch_numbers("daily")
    source.boards[5].fetch_numbers("all")
    assert len(provider.calls) == 2
