"""SakuraMedia JavDB 排行榜插件入口。"""

from __future__ import annotations

from src.plugins import (
    HOST_API_VERSION,
    RANKING_SOURCE_EXTENSION_KEY,
    PluginContext,
    PluginExtension,
    PluginRegistration,
)

from .boards import build_ranking_source
from .providers import PerRunProviderHolder
from .settings import JavdbRankingSettings
from .sync_jobs import build_jobs

__version__ = "0.1.1"
PLUGIN_ID = "sakuramedia_javdb_ranking"
DISPLAY_NAME = "SakuraMedia JavDB 排行榜"


def register(context: PluginContext) -> PluginRegistration:
    """声明排行榜来源与同步任务；只做轻量装配，不发起网络请求。"""
    settings = JavdbRankingSettings.model_validate(context.settings)
    # 每个任务运行开始时新建 provider（运行内复用）：JavdbProvider 登录失败后
    # 同实例不再重试，跨运行复用会把一次失败变成永久停抓。
    provider_holder = PerRunProviderHolder(
        factory=lambda: context.build_javdb_provider(
            username=settings.javdb_username,
            password=settings.javdb_password,
        )
    )
    source = build_ranking_source(
        provider_holder=provider_holder,
        account_configured=settings.account_configured,
    )
    return PluginRegistration(
        plugin_id=PLUGIN_ID,
        display_name=DISPLAY_NAME,
        version=__version__,
        host_api_version=HOST_API_VERSION,
        extensions=(
            PluginExtension(key=RANKING_SOURCE_EXTENSION_KEY, data=source),
        ),
        jobs=build_jobs(
            context,
            prepare_run=provider_holder.fresh_for_current_thread,
        ),
    )
