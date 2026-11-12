from sakuramedia_javdb_ranking.boards import STANDARD_PERIODS, build_ranking_source
from sakuramedia_javdb_ranking.providers import PerRunClientHolder
from sakuramedia_javdb_ranking.top250 import top250_periods

from src.plugins import PluginRankingSource


class FakeClient:
    def __init__(self):
        self.calls = []
        self.closed = False

    def get_playback_rank_numbers(self, *, filter_by, period):
        self.calls.append(("playback", filter_by, period))
        return ["ABP-001"]

    def get_rank_numbers(self, *, video_type, period):
        self.calls.append(("rank", video_type, period))
        return ["ABP-002"]

    def close(self):
        self.closed = True


def _source_with(client):
    holder = PerRunClientHolder(factory=lambda: client)
    return build_ranking_source(client_holder=holder)


def test_ranking_source_declares_free_boards_and_static_top250():
    source = _source_with(FakeClient())
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
    assert all(
        board.supported_periods == STANDARD_PERIODS
        for board in source.boards[:5]
    )
    assert source.boards[5].supported_periods == top250_periods()


def test_ranking_source_declares_english_names():
    source = _source_with(FakeClient())
    assert source.name_i18n["en"] == "JavDB"
    assert [board.name_i18n["en"] for board in source.boards] == [
        "Popular",
        "Top Rated",
        "Censored",
        "Uncensored",
        "FC2",
        "TOP250",
    ]


def test_free_boards_call_client_with_mapped_args():
    client = FakeClient()
    source = _source_with(client)

    source.boards[0].fetch_numbers("daily")
    source.boards[1].fetch_numbers("weekly")
    source.boards[2].fetch_numbers("monthly")
    source.boards[3].fetch_numbers("daily")
    source.boards[4].fetch_numbers("daily")

    assert client.calls == [
        ("playback", "all", "daily"),
        ("playback", "high_score", "weekly"),
        ("rank", "0", "monthly"),
        ("rank", "1", "daily"),
        ("rank", "3", "daily"),
    ]


def test_top250_reads_bundled_numbers_without_client():
    client = FakeClient()
    source = _source_with(client)
    numbers = source.boards[5].fetch_numbers("all")
    assert numbers
    assert numbers == source.boards[5].fetch_numbers("all")
    assert client.calls == []


def test_client_holder_reuses_and_closes_per_run():
    clients = [FakeClient(), FakeClient()]
    holder = PerRunClientHolder(factory=lambda: clients.pop(0))

    first = holder.get()
    assert holder.get() is first
    holder.close_current_thread()
    assert first.closed is True

    second = holder.get()
    assert second is not first
    holder.close_current_thread()
    assert second.closed is True
