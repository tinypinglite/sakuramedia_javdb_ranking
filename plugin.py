"""SakuraMedia JavDB 排行榜插件入口。"""

from __future__ import annotations

import json
from pathlib import Path

from src.plugins import (
    HOST_API_VERSION,
    RANKING_SOURCE_EXTENSION_KEY,
    PluginContext,
    PluginExtension,
    PluginRegistration,
)

from .boards import build_ranking_source
from .client import JavdbClient
from .providers import PerRunClientHolder
from .settings import JavdbRankingSettings
from .sync_jobs import build_jobs
from .translations import text_map

__version__ = json.loads(
    Path(__file__).with_name("manifest.json").read_text(encoding="utf-8")
)["version"]
PLUGIN_ID = "sakuramedia_javdb_ranking"
DISPLAY_NAME = "SakuraMedia JavDB 排行榜"
DISPLAY_NAME_I18N = text_map("manifest.display_name")


def register(context: PluginContext) -> PluginRegistration:
    """声明排行榜来源与同步任务；只做轻量装配，不发起网络请求。"""
    settings = JavdbRankingSettings.model_validate(context.settings)
    client_holder = PerRunClientHolder(
        factory=lambda: JavdbClient(
            host=settings.host,
            timeout_seconds=settings.timeout_seconds,
            max_retries=settings.max_retries,
            i18n=context.i18n,
        )
    )
    source = build_ranking_source(client_holder=client_holder)
    return PluginRegistration(
        plugin_id=PLUGIN_ID,
        display_name=DISPLAY_NAME,
        display_name_i18n=DISPLAY_NAME_I18N,
        version=__version__,
        host_api_version=HOST_API_VERSION,
        extensions=(
            PluginExtension(key=RANKING_SOURCE_EXTENSION_KEY, data=source),
        ),
        jobs=build_jobs(
            context,
            prepare_run=client_holder.fresh_for_current_thread,
            finish_run=client_holder.close_current_thread,
        ),
    )
