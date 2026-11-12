"""JavDB 排行榜来源声明。"""

from __future__ import annotations

from typing import Any

from src.plugins import PluginRankingBoard, PluginRankingSource

from .top250 import top250_numbers, top250_periods
from .translations import text_map

STANDARD_PERIODS = ("daily", "weekly", "monthly")


def build_ranking_source(*, client_holder: Any) -> PluginRankingSource:
    """声明 5 个免费榜和内置 TOP250 数据。"""
    boards = (
        PluginRankingBoard(
            key="playback_all",
            name="热播",
            name_i18n=text_map("boards.playback_all"),
            supported_periods=STANDARD_PERIODS,
            default_period="daily",
            fetch_numbers=lambda period: client_holder.get().get_playback_rank_numbers(
                filter_by="all", period=period
            ),
        ),
        PluginRankingBoard(
            key="playback_high_score",
            name="高评分",
            name_i18n=text_map("boards.playback_high_score"),
            supported_periods=STANDARD_PERIODS,
            default_period="daily",
            fetch_numbers=lambda period: client_holder.get().get_playback_rank_numbers(
                filter_by="high_score", period=period
            ),
        ),
        PluginRankingBoard(
            key="censored",
            name="有码",
            name_i18n=text_map("boards.censored"),
            supported_periods=STANDARD_PERIODS,
            default_period="daily",
            fetch_numbers=lambda period: client_holder.get().get_rank_numbers(
                video_type="0", period=period
            ),
        ),
        PluginRankingBoard(
            key="uncensored",
            name="无码",
            name_i18n=text_map("boards.uncensored"),
            supported_periods=STANDARD_PERIODS,
            default_period="daily",
            fetch_numbers=lambda period: client_holder.get().get_rank_numbers(
                video_type="1", period=period
            ),
        ),
        PluginRankingBoard(
            key="fc2",
            name="FC2",
            name_i18n=text_map("boards.fc2"),
            supported_periods=STANDARD_PERIODS,
            default_period="daily",
            fetch_numbers=lambda period: client_holder.get().get_rank_numbers(
                video_type="3", period=period
            ),
        ),
        PluginRankingBoard(
            key="top250",
            name="TOP250",
            name_i18n=text_map("boards.top250"),
            supported_periods=top250_periods(),
            default_period="all",
            fetch_numbers=top250_numbers,
        ),
    )
    return PluginRankingSource(
        source_key="javdb",
        name="JavDB",
        name_i18n=text_map("source.javdb.name"),
        boards=boards,
    )
