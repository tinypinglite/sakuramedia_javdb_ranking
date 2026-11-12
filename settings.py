from __future__ import annotations

import re

from pydantic import BaseModel, ConfigDict, Field, field_validator

from .translations import text_map


class JavdbRankingSettings(BaseModel):
    """排行榜插件配置；不再保存或使用 JavDB 登录信息。"""

    # 兼容旧版本留在 plugins.settings 里的 javdb_username / javdb_password：
    # 忽略未知字段，避免升级时因历史配置无法通过校验。
    model_config = ConfigDict(extra="ignore")

    host: str = Field(
        default="jdforrepam.com",
        title="JavDB 主机",
        description="只填写域名，例如 jdforrepam.com",
        json_schema_extra={
            "title_i18n": text_map("settings.host.title"),
            "description_i18n": text_map("settings.host.description"),
        },
    )
    timeout_seconds: float = Field(
        default=30.0,
        ge=1.0,
        le=120.0,
        title="请求超时（秒）",
        json_schema_extra={
            "title_i18n": text_map("settings.timeout_seconds.title"),
        },
    )
    max_retries: int = Field(
        default=2,
        ge=0,
        le=5,
        title="最大重试次数",
        json_schema_extra={
            "title_i18n": text_map("settings.max_retries.title"),
        },
    )

    @field_validator("host")
    @classmethod
    def validate_host(cls, value: str) -> str:
        host = value.strip().lower()
        if not re.fullmatch(r"[a-z0-9](?:[a-z0-9.-]*[a-z0-9])?", host):
            raise ValueError("host 必须是域名，不能包含协议、端口或路径")
        return host
