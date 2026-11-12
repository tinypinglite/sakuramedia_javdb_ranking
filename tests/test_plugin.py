import json
from pathlib import Path

from sakuramedia_javdb_ranking.plugin import PLUGIN_ID, register

from src.plugins import HOST_API_VERSION, PluginContext


def _context(settings=None) -> PluginContext:
    return PluginContext(
        plugin_id=PLUGIN_ID,
        settings=settings or {},
        data_dir=Path("/tmp/javdb-ranking-test"),
        plugin_root=Path(__file__).resolve().parents[1],
    )


def test_manifest_matches_registration_and_host_api():
    root = Path(__file__).resolve().parents[1]
    manifest = json.loads((root / "manifest.json").read_text(encoding="utf-8"))
    registration = register(_context())
    assert manifest["plugin_id"] == PLUGIN_ID
    assert manifest["host_api_version"] == HOST_API_VERSION
    assert registration.plugin_id == PLUGIN_ID
    assert registration.version == manifest["version"]
    assert registration.host_api_version == HOST_API_VERSION


def test_registration_ignores_legacy_credentials_without_network():
    registration = register(
        _context(
            {
                "javdb_username": "legacy-user",
                "javdb_password": "legacy-password",
            }
        )
    )
    source = registration.extensions[0].data
    assert source.source_key == "javdb"
    assert [board.key for board in source.boards][-1] == "top250"
    assert [job.task_key for job in registration.jobs] == [
        "sakuramedia_javdb_ranking_sync",
        "sakuramedia_javdb_ranking_sync_board",
    ]
