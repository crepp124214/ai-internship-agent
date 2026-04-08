"""UserLlmConfig 业务逻辑层。"""

from typing import List, Optional

from src.data_access.entities.user_llm_config import UserLlmConfig
from sqlalchemy.orm import Session
from src.data_access.repositories.user_llm_config_repository import user_llm_config_repository
from src.presentation.schemas.user_llm_config import UserLlmConfigCreate
from src.utils.crypto import decrypt_api_key, encrypt_api_key

class UserLlmConfigService:
    def get_user_configs(self, db: Session, user_id: int) -> List[UserLlmConfig]:
        """获取用户所有启用的 Agent 配置。"""
        return user_llm_config_repository.get_active_by_user(db, user_id)

    def get_config_for_agent(self, db: Session, user_id: int, agent: str) -> Optional[dict]:
        """获取特定 Agent 的用户配置（解密后的完整配置含 api_key）。"""
        config = user_llm_config_repository.get_by_user_and_agent(db, user_id, agent)
        if not config or not config.is_active:
            return None
        return {
            "provider": config.provider,
            "model": config.model,
            "api_key": decrypt_api_key(config.api_key_encrypted),
            "base_url": config.base_url,
            "temperature": config.temperature or 0.7,
        }

    def save_config(self, db: Session, user_id: int, data: UserLlmConfigCreate):
        """创建或更新用户配置，API Key 加密存储。"""
        encrypted_key = encrypt_api_key(data.api_key)
        return user_llm_config_repository.upsert(
            db,
            user_id=user_id,
            agent=data.agent,
            provider=data.provider,
            model=data.model,
            api_key_encrypted=encrypted_key,
            base_url=data.base_url,
            temperature=data.temperature,
        )

    def delete_config(self, db: Session, user_id: int, agent: str) -> bool:
        """删除用户指定 Agent 的配置。"""
        return user_llm_config_repository.delete_by_user_and_agent(db, user_id, agent)

user_llm_config_service = UserLlmConfigService()