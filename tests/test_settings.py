import pytest
from pydantic import ValidationError

from sakuramedia_javdb_ranking.settings import JavdbRankingSettings


def test_account_configured_requires_both_non_blank():
    assert JavdbRankingSettings().account_configured is False
    assert JavdbRankingSettings(javdb_username="user").account_configured is False
    assert (
        JavdbRankingSettings(javdb_username=" user ", javdb_password=" pass ").account_configured
        is True
    )


def test_credentials_are_stripped():
    settings = JavdbRankingSettings(javdb_username="  user  ", javdb_password="  pass  ")
    assert settings.javdb_username == "user"
    assert settings.javdb_password == "pass"


def test_unknown_setting_keys_are_rejected():
    with pytest.raises(ValidationError):
        JavdbRankingSettings(javdb_user="user")
