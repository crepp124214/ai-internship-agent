"""测试 UserLlmConfig ORM 实体模型。"""

from src.data_access.entities import UserLlmConfig


class TestUserLlmConfigEntity:
    """测试用户 LLM 配置实体"""

    def test_user_llm_config_table_name(self):
        """测试用户 LLM 配置表名称"""
        assert UserLlmConfig.__tablename__ == "user_llm_configs"

    def test_user_llm_config_has_required_columns(self):
        """测试用户 LLM 配置是否有必需的列"""
        assert hasattr(UserLlmConfig, "id")
        assert hasattr(UserLlmConfig, "user_id")
        assert hasattr(UserLlmConfig, "agent")
        assert hasattr(UserLlmConfig, "provider")
        assert hasattr(UserLlmConfig, "model")
        assert hasattr(UserLlmConfig, "api_key_encrypted")
        assert hasattr(UserLlmConfig, "base_url")
        assert hasattr(UserLlmConfig, "temperature")
        assert hasattr(UserLlmConfig, "is_active")
        assert hasattr(UserLlmConfig, "created_at")
        assert hasattr(UserLlmConfig, "updated_at")

    def test_user_llm_config_relationships(self):
        """测试用户 LLM 配置关系映射"""
        assert hasattr(UserLlmConfig, "user")

    def test_user_llm_config_repr(self):
        """测试用户 LLM 配置的 __repr__ 方法"""
        config = UserLlmConfig(
            user_id=1,
            agent="resume_agent",
            provider="openai",
            model="gpt-4",
            api_key_encrypted="encrypted_key",
        )
        repr_str = repr(config)
        assert "user_id=1" in repr_str
        assert "agent='resume_agent'" in repr_str
        assert "provider='openai'" in repr_str
        assert "model='gpt-4'" in repr_str

    def test_user_llm_config_unique_index(self):
        """测试用户 LLM 配置的唯一索引定义"""
        table_args = UserLlmConfig.__table_args__
        index_names = [idx.name for idx in table_args]
        assert "idx_user_llm_config_user_agent" in index_names