from pathlib import Path

import pytest
from pydantic import ValidationError
from sakuramedia_javdb_ranking.sync_jobs import (
    SyncBoardParams,
    build_jobs,
)

from src.plugins import PluginContext


def _context() -> PluginContext:
    return PluginContext(
        plugin_id="sakuramedia_javdb_ranking",
        settings={},
        data_dir=Path("/tmp/javdb-ranking-test"),
    )


def test_build_jobs_declares_cron_and_manual_task():
    jobs = build_jobs(_context(), prepare_run=lambda: None)
    assert [job.task_key for job in jobs] == [
        "sakuramedia_javdb_ranking_sync",
        "sakuramedia_javdb_ranking_sync_board",
    ]
    assert jobs[0].default_cron == "45 1 * * *"
    assert jobs[0].handler is not None
    assert jobs[1].manual_only is True
    assert jobs[1].params_schema is SyncBoardParams


def test_sync_board_params_validation():
    assert SyncBoardParams(board_key="censored", period="daily").period == "daily"
    assert SyncBoardParams(board_key="top250").model_dump() == {
        "board_key": "top250",
        "period": None,
    }
    with pytest.raises(ValidationError):
        SyncBoardParams(board_key="Bad-Key")


def test_sync_all_handler_prepares_run_and_passes_progress():
    calls = []
    context = _context()
    object.__setattr__(
        context,
        "sync_ranking_sources",
        lambda **kwargs: calls.append(kwargs) or {"ok": 1},
    )
    prepared = []
    jobs = build_jobs(context, prepare_run=lambda: prepared.append(1))

    class Reporter:
        progress_callback = object()

    jobs[0].handler(Reporter(), {})

    assert prepared == [1]
    assert list(calls[0]) == ["progress_callback"]


def test_sync_board_handler_uses_plugin_source_key():
    calls = []
    context = _context()
    object.__setattr__(
        context,
        "sync_ranking_board",
        lambda **kwargs: calls.append(kwargs) or {"ok": 1},
    )
    prepared = []
    jobs = build_jobs(context, prepare_run=lambda: prepared.append(1))

    jobs[1].handler(None, {"board_key": "censored", "period": "daily"})

    assert prepared == [1]
    assert calls == [
        {"source_key": "javdb", "board_key": "censored", "period": "daily"}
    ]
