from pydantic import BaseModel, ConfigDict, Field, field_validator

from .translations import text_map


class JavdbRankingSettings(BaseModel):
    """排行榜插件私有配置（plugins.settings.sakuramedia_javdb_ranking）。"""

    model_config = ConfigDict(extra="forbid")

    javdb_username: str | None = Field(
        default=None,
        title="JavDB 用户名",
        json_schema_extra={
            "title_i18n": text_map("settings.javdb_username.title"),
        },
    )
    javdb_password: str | None = Field(
        default=None,
        title="JavDB 密码",
        json_schema_extra={
            "format": "password",
            "title_i18n": text_map("settings.javdb_password.title"),
        },
    )

    @field_validator("javdb_username", "javdb_password")
    @classmethod
    def _strip_whitespace(cls, value: str | None) -> str | None:
        return value.strip() if value is not None else None

    @property
    def account_configured(self) -> bool:
        # 账号与密码都非空白才视为已配置，决定 TOP250 是否可抓。
        return bool(self.javdb_username and self.javdb_password)
