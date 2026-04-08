"""
UserLlmConfig Repository - 提供用户LLM配置的数据访问方法。
"""

from typing import List, Optional

from sqlalchemy.orm import Session

from src.data_access.entities.user_llm_config import UserLlmConfig


class UserLlmConfigRepository:
    """UserLlmConfig 的数据访问方法。"""

    def get_by_id(self, db: Session, id: int) -> Optional[UserLlmConfig]:
        """根据ID获取配置。"""
        return db.query(UserLlmConfig).filter(UserLlmConfig.id == id).first()

    def get_by_user_and_agent(
        self, db: Session, user_id: int, agent: str
    ) -> Optional[UserLlmConfig]:
        """根据用户ID和Agent获取配置。"""
        return (
            db.query(UserLlmConfig)
            .filter(UserLlmConfig.user_id == user_id, UserLlmConfig.agent == agent)
            .first()
        )

    def get_active_by_user(self, db: Session, user_id: int) -> List[UserLlmConfig]:
        """获取用户所有激活的配置。"""
        return (
            db.query(UserLlmConfig)
            .filter(UserLlmConfig.user_id == user_id, UserLlmConfig.is_active == True)
            .all()
        )

    def upsert(
        self,
        db: Session,
        user_id: int,
        agent: str,
        provider: str,
        model: str,
        api_key_encrypted: str,
        base_url: Optional[str] = None,
        temperature: Optional[float] = None,
    ) -> UserLlmConfig:
        """
        插入或更新用户LLM配置。

        如果存在则更新，否则创建。
        """
        existing = self.get_by_user_and_agent(db, user_id, agent)

        if existing is not None:
            # 更新现有配置
            existing.provider = provider
            existing.model = model
            existing.api_key_encrypted = api_key_encrypted
            existing.base_url = base_url
            existing.temperature = temperature
            db.commit()
            db.refresh(existing)
            return existing
        else:
            # 创建新配置
            new_config = UserLlmConfig(
                user_id=user_id,
                agent=agent,
                provider=provider,
                model=model,
                api_key_encrypted=api_key_encrypted,
                base_url=base_url,
                temperature=temperature,
                is_active=True,
            )
            db.add(new_config)
            db.commit()
            db.refresh(new_config)
            return new_config

    def delete_by_user_and_agent(self, db: Session, user_id: int, agent: str) -> bool:
        """
        根据用户ID和Agent删除配置。

        返回是否成功删除。
        """
        config = self.get_by_user_and_agent(db, user_id, agent)
        if config is None:
            return False

        db.delete(config)
        db.commit()
        return True


# 单例实例
user_llm_config_repository = UserLlmConfigRepository()