"""JavDB 排行榜来源声明：6 个 board、动态年份与抓取前判断。"""

from __future__ import annotations

from collections.abc import Callable
from typing import Any

from src.common.runtime_time import runtime_now
from src.plugins import PluginRankingBoard, PluginRankingSource

# TOP250 固定子榜；年份维度由 supported_periods_provider 动态补齐。
TOP250_FIXED_PERIODS = ("all", "uncensored", "censored", "fc2")
TOP250_START_YEAR = 2008


def _current_year() -> int:
    # 与宿主运行时区保持一致（原内置实现同为 runtime_now），避免元旦前后年份错位。
    return runtime_now().year


def top250_periods() -> tuple[str, ...]:
    """TOP250 最终周期集合：固定子榜在前，年份从当前年回溯到起始年。"""
    return TOP250_FIXED_PERIODS + tuple(
        str(year) for year in range(_current_year(), TOP250_START_YEAR - 1, -1)
    )


def top250_type_for_period(period: str) -> tuple[str, str]:
    """把 top250 的 period 映射成 /api/v1/movies/top 的 (type, type_value)。"""
    if period == "all":
        return ("all", "")
    video_types = {"censored": "0", "uncensored": "1", "fc2": "3"}
    if period in video_types:
        return ("video_type", video_types[period])
    return ("year", period)


def build_top250_should_fetch(
    *,
    account_configured: bool,
) -> Callable[[str, bool], bool]:
    """TOP250 抓取前判断：未配账号不抓；历史年份已有数据不重抓。"""

    def should_fetch(period: str, has_items: bool) -> bool:
        if not account_configured:
            return False
        if period.isdigit() and int(period) < _current_year() and has_items:
            return False
        return True

    return should_fetch


def build_ranking_source(
    *,
    provider_holder: Any,
    account_configured: bool,
) -> PluginRankingSource:
    """按最终契约组装 JavDB 排行榜来源；provider 由 holder 按运行提供。"""
    boards = (
        PluginRankingBoard(
            key="playback_all",
            name="热播",
            supported_periods=("daily", "weekly", "monthly"),
            default_period="daily",
            fetch_numbers=lambda period: provider_holder.get().get_playback_rank_numbers(
                filter_by="all", period=period
            ),
        ),
        PluginRankingBoard(
            key="playback_high_score",
            name="高评分",
            supported_periods=("daily", "weekly", "monthly"),
            default_period="daily",
            fetch_numbers=lambda period: provider_holder.get().get_playback_rank_numbers(
                filter_by="high_score", period=period
            ),
        ),
        PluginRankingBoard(
            key="censored",
            name="有码",
            supported_periods=("daily", "weekly", "monthly"),
            default_period="daily",
            fetch_numbers=lambda period: provider_holder.get().get_rank_numbers(
                video_type="0", period=period
            ),
        ),
        PluginRankingBoard(
            key="uncensored",
            name="无码",
            supported_periods=("daily", "weekly", "monthly"),
            default_period="daily",
            fetch_numbers=lambda period: provider_holder.get().get_rank_numbers(
                video_type="1", period=period
            ),
        ),
        PluginRankingBoard(
            key="fc2",
            name="FC2",
            supported_periods=("daily", "weekly", "monthly"),
            default_period="daily",
            fetch_numbers=lambda period: provider_holder.get().get_rank_numbers(
                video_type="3", period=period
            ),
        ),
        PluginRankingBoard(
            key="top250",
            name="TOP250",
            supported_periods=(),
            default_period="all",
            supported_periods_provider=top250_periods,
            should_fetch=build_top250_should_fetch(
                account_configured=account_configured
            ),
            fetch_numbers=lambda period: provider_holder.get().get_top_numbers(
                *top250_type_for_period(period)
            ),
        ),
    )
    return PluginRankingSource(source_key="javdb", name="JavDB", boards=boards)
