"""同步任务声明：定时全量同步 + 手动单榜同步。"""

from __future__ import annotations

from collections.abc import Callable
from typing import Any

from pydantic import BaseModel, Field

from src.plugins import PluginContext
from src.scheduler.contracts import JobDefinition


class SyncBoardParams(BaseModel):
    """手动单榜同步参数；source_key 固定为本插件的 javdb。"""

    board_key: str = Field(
        min_length=1,
        max_length=64,
        pattern=r"^[a-z][a-z0-9_]*$",
    )
    period: str | None = Field(default=None, max_length=32)


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
            period=params.get("period"),
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
