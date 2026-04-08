import pytest
from unittest.mock import MagicMock

from src.data_access.entities.user_llm_config import UserLlmConfig
from src.data_access.repositories.user_llm_config_repository import (
    user_llm_config_repository,
)


def test_get_by_user_and_agent_returns_config():
    """测试根据用户ID和Agent获取配置成功的情况。"""
    mock_db = MagicMock()
    mock_config = MagicMock(spec=UserLlmConfig)
    mock_config.user_id = 10
    mock_config.agent = "resume_agent"
    mock_db.query.return_value.filter.return_value.first.return_value = mock_config

    result = user_llm_config_repository.get_by_user_and_agent(mock_db, 10, "resume_agent")

    assert result == mock_config
    assert result.user_id == 10
    assert result.agent == "resume_agent"


def test_get_by_user_and_agent_returns_none():
    """测试根据用户ID和Agent获取不存在的配置时返回None。"""
    mock_db = MagicMock()
    mock_db.query.return_value.filter.return_value.first.return_value = None

    result = user_llm_config_repository.get_by_user_and_agent(mock_db, 99, "nonexistent")

    assert result is None


def test_upsert_creates_new():
    """测试upsert创建新配置的情况。"""
    mock_db = MagicMock()
    mock_db.query.return_value.filter.return_value.first.return_value = None

    new_config = user_llm_config_repository.upsert(
        mock_db,
        user_id=10,
        agent="resume_agent",
        provider="deepseek",
        model="deepseek-chat",
        api_key_encrypted="enc_key",
        base_url="https://api.deepseek.com",
        temperature=0.5,
    )

    assert new_config.user_id == 10
    assert new_config.agent == "resume_agent"
    assert new_config.provider == "deepseek"
    mock_db.add.assert_called_once()
    mock_db.commit.assert_called_once()


def test_upsert_updates_existing():
    """测试upsert更新现有配置的情况。"""
    mock_db = MagicMock()
    existing = UserLlmConfig(
        id=1,
        user_id=10,
        agent="resume_agent",
        provider="openai",
        model="gpt-4o-mini",
        api_key_encrypted="old_key",
    )
    mock_db.query.return_value.filter.return_value.first.return_value = existing

    updated = user_llm_config_repository.upsert(
        mock_db,
        user_id=10,
        agent="resume_agent",
        provider="deepseek",
        model="deepseek-chat",
        api_key_encrypted="new_key",
        base_url=None,
        temperature=0.8,
    )

    assert updated.provider == "deepseek"
    assert updated.api_key_encrypted == "new_key"
    assert updated.temperature == 0.8
    mock_db.commit.assert_called_once()


def test_delete_by_user_and_agent_success():
    """测试删除现有配置成功的情况。"""
    mock_db = MagicMock()
    mock_config = MagicMock(spec=UserLlmConfig)
    mock_db.query.return_value.filter.return_value.first.return_value = mock_config

    result = user_llm_config_repository.delete_by_user_and_agent(mock_db, 10, "resume_agent")

    assert result is True
    mock_db.delete.assert_called_once_with(mock_config)
    mock_db.commit.assert_called_once()


def test_delete_by_user_and_agent_not_found():
    """测试删除不存在的配置时返回False。"""
    mock_db = MagicMock()
    mock_db.query.return_value.filter.return_value.first.return_value = None

    result = user_llm_config_repository.delete_by_user_and_agent(mock_db, 99, "nonexistent")

    assert result is False
    mock_db.delete.assert_not_called()


def test_get_active_by_user():
    """测试获取用户所有激活的配置。"""
    mock_db = MagicMock()
    mock_configs = [MagicMock(spec=UserLlmConfig), MagicMock(spec=UserLlmConfig)]
    mock_db.query.return_value.filter.return_value.all.return_value = mock_configs

    result = user_llm_config_repository.get_active_by_user(mock_db, 10)

    assert result == mock_configs
    assert len(result) == 2


def test_get_by_id():
    """测试根据ID获取配置。"""
    mock_db = MagicMock()
    mock_config = MagicMock(spec=UserLlmConfig)
    mock_db.query.return_value.filter.return_value.first.return_value = mock_config

    result = user_llm_config_repository.get_by_id(mock_db, 1)

    assert result == mock_config