"""同步任务声明：定时全量同步 + 手动单榜同步。"""

from __future__ import annotations

from collections.abc import Callable
from typing import Any

from pydantic import BaseModel, Field

from src.plugins import PluginContext
from src.scheduler.contracts import JobDefinition

from .boards import top250_periods

# 手动任务参数在任务中心渲染为下拉：oneOf 的 const/title 提供提交值与中文标签，
# x-options-by 声明周期选项随 board_key 联动，选项用 x-when 标注适用榜单。
_STANDARD_BOARD_KEYS = (
    "playback_all",
    "playback_high_score",
    "censored",
    "uncensored",
    "fc2",
)
_BOARD_TITLES = {
    "playback_all": "热播",
    "playback_high_score": "高评分",
    "censored": "有码",
    "uncensored": "无码",
    "fc2": "FC2",
    "top250": "TOP250",
}
_PERIOD_TITLES = {
    "daily": "日榜",
    "weekly": "周榜",
    "monthly": "月榜",
    "all": "全部",
    "uncensored": "无码",
    "censored": "有码",
    "fc2": "FC2",
}


def _schema_option(
    value: str,
    title: str,
    when: tuple[str, ...] = (),
) -> dict[str, Any]:
    option: dict[str, Any] = {"const": value, "title": title}
    if when:
        option["x-when"] = list(when)
    return option


def _board_key_options() -> list[dict[str, Any]]:
    return [
        _schema_option(key, _BOARD_TITLES[key])
        for key in (*_STANDARD_BOARD_KEYS, "top250")
    ]


def _period_options() -> list[dict[str, Any]]:
    options = [
        _schema_option(period, _PERIOD_TITLES[period], _STANDARD_BOARD_KEYS)
        for period in ("daily", "weekly", "monthly")
    ]
    options.extend(
        _schema_option(
            period,
            _PERIOD_TITLES.get(period, f"{period}年"),
            ("top250",),
        )
        for period in top250_periods()
    )
    return options


class SyncBoardParams(BaseModel):
    """手动单榜同步参数；source_key 固定为本插件的 javdb。"""

    board_key: str = Field(
        min_length=1,
        max_length=64,
        pattern=r"^[a-z][a-z0-9_]*$",
        title="榜单",
        description="选择要同步的榜单",
        json_schema_extra={"oneOf": _board_key_options()},
    )
    period: str = Field(
        min_length=1,
        max_length=32,
        title="周期",
        description="可选项随所选榜单变化",
        json_schema_extra={
            "oneOf": _period_options(),
            "x-options-by": "board_key",
        },
    )


def build_jobs(
    context: PluginContext,
    *,
    prepare_run: Callable[[], Any],
) -> tuple[JobDefinition, ...]:
    """返回本插件的任务声明；执行体只调宿主同步入口。"""

    def run_sync_all(reporter, _params):
        prepare_run()
        return context.sync_ranking_sources(
            progress_callback=reporter.progress_callback,
        )

    def run_sync_board(reporter, params):
        prepare_run()
        return context.sync_ranking_board(
            source_key="javdb",
            board_key=params["board_key"],
            period=params["period"],
        )

    return (
        JobDefinition(
            task_key="sakuramedia_javdb_ranking_sync",
            log_name="javdb-ranking-sync",
            cli_name="sync-javdb-ranking",
            cli_help="同步 JavDB 排行榜（热播/高评分/有码/无码/FC2/TOP250）",
            default_cron="45 1 * * *",
            handler=run_sync_all,
        ),
        JobDefinition(
            task_key="sakuramedia_javdb_ranking_sync_board",
            log_name="javdb-ranking-sync-board",
            cli_name="sync-javdb-ranking-board",
            cli_help="手动同步单个 JavDB 榜单",
            manual_only=True,
            params_schema=SyncBoardParams,
            handler=run_sync_board,
        ),
    )
