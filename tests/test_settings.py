import pytest
from pydantic import ValidationError
from sakuramedia_javdb_ranking.settings import JavdbRankingSettings


def test_defaults_do_not_include_login_fields():
    settings = JavdbRankingSettings()
    assert settings.host == "jdforrepam.com"
    assert settings.timeout_seconds == 30.0
    assert settings.max_retries == 2
    assert "javdb_username" not in settings.model_dump()
    assert "javdb_password" not in settings.model_dump()


def test_legacy_credentials_are_ignored_during_upgrade():
    settings = JavdbRankingSettings(
        javdb_username="legacy-user",
        javdb_password="legacy-pass",
        host=" Example.COM ",
    )
    assert settings.host == "example.com"
    assert settings.model_dump() == {
        "host": "example.com",
        "timeout_seconds": 30.0,
        "max_retries": 2,
    }


def test_host_rejects_protocol_and_path():
    with pytest.raises(ValidationError):
        JavdbRankingSettings(host="https://jdforrepam.com")
    with pytest.raises(ValidationError):
        JavdbRankingSettings(host="jdforrepam.com/path")


def test_settings_schema_has_i18n_without_credentials():
    schema = JavdbRankingSettings.model_json_schema()
    properties = schema["properties"]
    assert set(properties) == {"host", "timeout_seconds", "max_retries"}
    assert properties["host"]["title"] == "JavDB 主机"
    assert properties["host"]["title_i18n"]["en"] == "JavDB host"
    assert properties["timeout_seconds"]["title_i18n"]["en"] == (
        "Request timeout (seconds)"
    )
