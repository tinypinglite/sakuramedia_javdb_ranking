"""同步任务声明：定时全量同步 + 手动单榜同步。"""

from __future__ import annotations

from collections.abc import Callable
from typing import Any

from pydantic import BaseModel, Field

from src.plugins import PluginContext
from src.scheduler.contracts import JobDefinition

from .boards import top250_periods
from .translations import text, text_map

# 手动任务参数在任务中心渲染为下拉：oneOf 的 const/title 提供提交值与中文标签，
# x-options-by 声明周期选项随 board_key 联动，选项用 x-when 标注适用榜单。
_STANDARD_BOARD_KEYS = (
    "playback_all",
    "playback_high_score",
    "censored",
    "uncensored",
    "fc2",
)


def _schema_option(
    value: str,
    title: str,
    when: tuple[str, ...] = (),
    *,
    title_i18n: dict[str, str] | None = None,
) -> dict[str, Any]:
    option: dict[str, Any] = {"const": value, "title": title}
    if when:
        option["x-when"] = list(when)
    if title_i18n is not None:
        option["title_i18n"] = title_i18n
    return option


def _board_key_options() -> list[dict[str, Any]]:
    return [
        _schema_option(
            key,
            text(f"boards.{key}"),
            title_i18n=text_map(f"boards.{key}"),
        )
        for key in (*_STANDARD_BOARD_KEYS, "top250")
    ]


def _period_options() -> list[dict[str, Any]]:
    options = [
        _schema_option(
            period,
            text(f"periods.{period}"),
            _STANDARD_BOARD_KEYS,
            title_i18n=text_map(f"periods.{period}"),
        )
        for period in ("daily", "weekly", "monthly")
    ]
    year_templates = text_map("periods.year")
    for period in top250_periods():
        if period.isdigit():
            title = text("periods.year").format(year=period)
            title_i18n = {
                locale: template.format(year=period)
                for locale, template in year_templates.items()
            }
        else:
            title = text(f"periods.{period}")
            title_i18n = text_map(f"periods.{period}")
        options.append(
            _schema_option(
                period,
                title,
                ("top250",),
                title_i18n=title_i18n,
            )
        )
    return options


class SyncBoardParams(BaseModel):
    """手动单榜同步参数；source_key 固定为本插件的 javdb。"""

    board_key: str = Field(
        min_length=1,
        max_length=64,
        pattern=r"^[a-z][a-z0-9_]*$",
        title=text("jobs.sync_board.params.board_key.title"),
        description=text("jobs.sync_board.params.board_key.description"),
        json_schema_extra={
            "oneOf": _board_key_options(),
            "title_i18n": text_map("jobs.sync_board.params.board_key.title"),
            "description_i18n": text_map(
                "jobs.sync_board.params.board_key.description"
            ),
        },
    )
    period: str = Field(
        min_length=1,
        max_length=32,
        title=text("jobs.sync_board.params.period.title"),
        description=text("jobs.sync_board.params.period.description"),
        json_schema_extra={
            "oneOf": _period_options(),
            "x-options-by": "board_key",
            "title_i18n": text_map("jobs.sync_board.params.period.title"),
            "description_i18n": text_map(
                "jobs.sync_board.params.period.description"
            ),
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
        reporter.emit(
            text=context.i18n.t(
                "sync.start_all",
                default=text("sync.start_all"),
            )
        )
        return context.sync_ranking_sources(
            progress_callback=reporter.progress_callback,
        )

    def run_sync_board(reporter, params):
        prepare_run()
        board_label = context.i18n.t(
            f"boards.{params['board_key']}",
            default=params["board_key"],
        )
        reporter.emit(
            text=context.i18n.t(
                "sync.start_board",
                default=text("sync.start_board").format(board=board_label),
                board=board_label,
            )
        )
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
            cli_help=text("jobs.sync.cli_help"),
            cli_help_i18n=text_map("jobs.sync.cli_help"),
            default_cron="45 1 * * *",
            handler=run_sync_all,
        ),
        JobDefinition(
            task_key="sakuramedia_javdb_ranking_sync_board",
            log_name="javdb-ranking-sync-board",
            cli_name="sync-javdb-ranking-board",
            cli_help=text("jobs.sync_board.cli_help"),
            cli_help_i18n=text_map("jobs.sync_board.cli_help"),
            manual_only=True,
            params_schema=SyncBoardParams,
            handler=run_sync_board,
        ),
    )
