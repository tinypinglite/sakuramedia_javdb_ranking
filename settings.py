from pydantic import BaseModel, ConfigDict, Field, field_validator


class JavdbRankingSettings(BaseModel):
    """排行榜插件私有配置（plugins.settings.sakuramedia_javdb_ranking）。"""

    model_config = ConfigDict(extra="forbid")

    javdb_username: str | None = Field(default=None, title="JavDB 用户名")
    javdb_password: str | None = Field(default=None, title="JavDB 密码", json_schema_extra={"format": "password"})

    @field_validator("javdb_username", "javdb_password")
    @classmethod
    def _strip_whitespace(cls, value: str | None) -> str | None:
        return value.strip() if value is not None else None

    @property
    def account_configured(self) -> bool:
        # 账号与密码都非空白才视为已配置，决定 TOP250 是否可抓。
        return bool(self.javdb_username and self.javdb_password)
