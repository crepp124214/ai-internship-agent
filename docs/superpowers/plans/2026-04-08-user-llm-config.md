# 用户 LLM 配置功能实现计划

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 允许用户为自己的 Resume/Job/Interview Agent 配置自定义 LLM API Key，支持任意 OpenAI/Anthropic 兼容 Provider

**Architecture:** 用户配置存储在 `user_llm_configs` 表，API Key 用 Fernet 加密。Agent 执行时通过 `user_id` + `agent_name` 查询用户配置，优先使用；不存在则回退到系统默认环境变量/YAML配置。

**Tech Stack:** SQLAlchemy 2.0, Pydantic, FastAPI, Fernet (cryptography), React, React Hook Form + Zod

---

## 文件结构

### 新建文件（按创建顺序）

| 文件 | 职责 |
|------|------|
| `src/utils/crypto.py` | Fernet 加密/解密 API Key |
| `src/data_access/entities/user_llm_config.py` | `UserLlmConfig` SQLAlchemy 模型 |
| `src/data_access/repositories/user_llm_config_repository.py` | Repository |
| `src/presentation/schemas/user_llm_config.py` | Pydantic Request/Response Schema |
| `src/business_logic/user_llm_config_service.py` | 业务逻辑（加密/解密、配置查询） |
| `src/presentation/api/v1/user_llm_configs.py` | CRUD API 端点 |
| `alembic/versions/008_user_llm_configs.py` | 数据库迁移 |
| `frontend/src/pages/settings/agent-config-page.tsx` | 前端配置页面 |

### 修改文件

| 文件 | 修改内容 |
|------|----------|
| `src/data_access/entities/__init__.py` | 导出 `UserLlmConfig` |
| `src/data_access/database.py` | `_import_all_entities()` 加入 `user_llm_config` |
| `src/data_access/repositories/__init__.py` | 导出 `user_llm_config_repository` |
| `src/main.py` | 注册 `user_llm_configs` router |
| `src/business_logic/agents/resume_agent/resume_agent.py` | `__init__` 接受 `user_id`，运行时查用户配置 |
| `src/business_logic/agents/job_agent/job_agent.py` | 同上 |
| `src/business_logic/agents/interview_agent/interview_agent.py` | 同上 |
| `src/business_logic/agent/agent_chat_service.py` | 调用 Agent 时传入 `user_id` |
| `frontend/src/layout/authenticated-app-shell.tsx` | 添加"Agent 配置"导航入口 |
| `frontend/src/app/router.tsx` | 添加 `/settings/agent-config` 路由 |
| `frontend/src/lib/api.ts` | 添加 `getUserLlmConfigs`, `saveUserLlmConfig`, `deleteUserLlmConfig` |

---

## Task 1: 加密工具

**Files:**
- Create: `src/utils/crypto.py`
- Test: `tests/unit/utils/test_crypto.py`

- [ ] **Step 1: 写测试**

```python
# tests/unit/utils/test_crypto.py
import pytest
from src.utils.crypto import encrypt_api_key, decrypt_api_key

def test_encrypt_decrypt_round_trip():
    original = "sk-test-123456"
    encrypted = encrypt_api_key(original)
    assert encrypted != original
    assert encrypt_api_key(original) != encrypted  # different each time (IV)
    decrypted = decrypt_api_key(encrypted)
    assert decrypted == original

def test_encrypt_none_returns_none():
    assert encrypt_api_key(None) is None

def test_decrypt_none_returns_none():
    assert decrypt_api_key(None) is None
```

- [ ] **Step 2: 运行测试验证失败**

Run: `pytest tests/unit/utils/test_crypto.py -v`
Expected: FAIL - module not found

- [ ] **Step 3: 实现加密工具**

```python
# src/utils/crypto.py
"""API Key 加密工具，使用 Fernet 对称加密。"""
from __future__ import annotations

import base64
import os
from typing import Optional

from cryptography.fernet import Fernet
from src.utils.config_loader import get_settings

_fernet: Optional[Fernet] = None


def _get_fernet() -> Fernet:
    global _fernet
    if _fernet is None:
        settings = get_settings()
        key = settings.SECRET_KEY.encode() if settings.SECRET_KEY else os.urandom(32)
        fernet_key = base64.urlsafe_b64encode(key[:32])
        _fernet = Fernet(fernet_key)
    return _fernet


def encrypt_api_key(api_key: Optional[str]) -> Optional[str]:
    """加密 API Key，返回 base64 字符串。"""
    if api_key is None:
        return None
    fernet = _get_fernet()
    return fernet.encrypt(api_key.encode()).decode()


def decrypt_api_key(encrypted: Optional[str]) -> Optional[str]:
    """解密 API Key。"""
    if encrypted is None:
        return None
    fernet = _get_fernet()
    return fernet.decrypt(encrypted.encode()).decode()
```

- [ ] **Step 4: 运行测试验证通过**

Run: `pytest tests/unit/utils/test_crypto.py -v`
Expected: PASS

- [ ] **Step 5: 提交**

```bash
git add src/utils/crypto.py tests/unit/utils/test_crypto.py
git commit -m "feat: add Fernet crypto utility for API key encryption"
```

---

## Task 2: 数据库模型

**Files:**
- Create: `src/data_access/entities/user_llm_config.py`
- Modify: `src/data_access/entities/__init__.py:1-10`
- Test: `tests/unit/data_access/test_user_llm_config_entity.py`

- [ ] **Step 1: 写测试**

```python
# tests/unit/data_access/test_user_llm_config_entity.py
import pytest
from datetime import datetime
from src.data_access.entities.user_llm_config import UserLlmConfig

def test_user_llm_config_fields():
    config = UserLlmConfig(
        id=1,
        user_id=10,
        agent="resume_agent",
        provider="openai",
        model="gpt-4o-mini",
        api_key_encrypted="encrypted_key",
        base_url=None,
        temperature=0.7,
        is_active=True,
    )
    assert config.id == 1
    assert config.user_id == 10
    assert config.agent == "resume_agent"
    assert config.provider == "openai"
    assert config.model == "gpt-4o-mini"
    assert config.api_key_encrypted == "encrypted_key"
    assert config.base_url is None
    assert config.temperature == 0.7
    assert config.is_active is True

def test_repr():
    config = UserLlmConfig(user_id=10, agent="resume_agent", provider="openai", model="gpt-4o-mini", api_key_encrypted="x")
    assert "resume_agent" in repr(config)
```

- [ ] **Step 2: 运行测试验证失败**

Run: `pytest tests/unit/data_access/test_user_llm_config_entity.py -v`
Expected: FAIL - module not found

- [ ] **Step 3: 实现实体**

```python
# src/data_access/entities/user_llm_config.py
"""用户 LLM 配置实体。"""

from datetime import datetime

from sqlalchemy import Boolean, Column, DateTime, Float, ForeignKey, Index, Integer, String
from sqlalchemy.orm import relationship

from src.data_access.database import Base


class UserLlmConfig(Base):
    """用户为特定 Agent 自定义的 LLM 配置。

    每个用户每个 Agent 只有一条记录，以 (user_id, agent) 为唯一约束。
    API Key 存储的是加密后的密文。
    """

    __tablename__ = "user_llm_configs"

    id = Column(Integer, primary_key=True, index=True, comment="主键")
    user_id = Column(
        Integer,
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
        comment="用户 ID",
    )
    agent = Column(String(50), nullable=False, comment="Agent 标识：resume_agent / job_agent / interview_agent")
    provider = Column(String(100), nullable=False, comment="Provider 标识")
    model = Column(String(100), nullable=False, comment="模型名称")
    api_key_encrypted = Column(String(500), nullable=False, comment="加密后的 API Key")
    base_url = Column(String(255), nullable=True, comment="自定义 API endpoint")
    temperature = Column(Float, nullable=True, default=0.7, comment="生成温度")
    is_active = Column(Boolean, nullable=False, default=True, comment="是否启用")
    created_at = Column(DateTime, nullable=False, default=datetime.now, comment="创建时间")
    updated_at = Column(DateTime, nullable=False, default=datetime.now, onupdate=datetime.now, comment="更新时间")

    user = relationship("User", lazy="joined")

    __table_args__ = (
        Index("idx_user_llm_config_user_agent", "user_id", "agent", unique=True),
    )

    def __repr__(self) -> str:
        return f"<UserLlmConfig(user_id={self.user_id}, agent='{self.agent}', provider='{self.provider}', model='{self.model}')>"
```

- [ ] **Step 4: 运行测试验证通过**

Run: `pytest tests/unit/data_access/test_user_llm_config_entity.py -v`
Expected: PASS

- [ ] **Step 5: 更新 entities/__init__.py**

在 `src/data_access/entities/__init__.py` 添加:
```python
from src.data_access.entities.user_llm_config import UserLlmConfig
```

- [ ] **Step 6: 更新 database.py 的 _import_all_entities()**

```python
# src/data_access/database.py
def _import_all_entities() -> tuple[str, ...]:
    from src.data_access.entities import interview, job, resume, user, user_llm_config
    _ = (interview, job, resume, user, user_llm_config)
    return ("user", "resume", "job", "interview", "user_llm_config")
```

- [ ] **Step 7: 提交**

```bash
git add src/data_access/entities/user_llm_config.py src/data_access/entities/__init__.py src/data_access/database.py tests/unit/data_access/test_user_llm_config_entity.py
git commit -m "feat: add UserLlmConfig SQLAlchemy entity"
```

---

## Task 3: Repository

**Files:**
- Create: `src/data_access/repositories/user_llm_config_repository.py`
- Modify: `src/data_access/repositories/__init__.py:1-20`
- Test: `tests/unit/data_access/test_user_llm_config_repository.py`

- [ ] **Step 1: 写测试**

```python
# tests/unit/data_access/test_user_llm_config_repository.py
import pytest
from unittest.mock import MagicMock
from src.data_access.entities.user_llm_config import UserLlmConfig
from src.data_access.repositories.user_llm_config_repository import user_llm_config_repository

def test_get_by_user_and_agent_returns_config():
    mock_db = MagicMock()
    mock_config = UserLlmConfig(id=1, user_id=10, agent="resume_agent", provider="openai", model="gpt-4o-mini", api_key_encrypted="x")
    mock_db.query.return_value.filter.return_value.first.return_value = mock_config

    result = user_llm_config_repository.get_by_user_and_agent(mock_db, 10, "resume_agent")

    assert result == mock_config
    assert result.user_id == 10
    assert result.agent == "resume_agent"

def test_get_by_user_and_agent_returns_none():
    mock_db = MagicMock()
    mock_db.query.return_value.filter.return_value.first.return_value = None

    result = user_llm_config_repository.get_by_user_and_agent(mock_db, 99, "nonexistent")
    assert result is None

def test_upsert_creates_new():
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
    mock_db = MagicMock()
    existing = UserLlmConfig(id=1, user_id=10, agent="resume_agent", provider="openai", model="gpt-4o-mini", api_key_encrypted="old_key")
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
```

- [ ] **Step 2: 运行测试验证失败**

Run: `pytest tests/unit/data_access/test_user_llm_config_repository.py -v`
Expected: FAIL - module not found

- [ ] **Step 3: 实现 Repository**

```python
# src/data_access/repositories/user_llm_config_repository.py
"""UserLlmConfig 数据访问层。"""

from typing import Any, Dict, List, Optional

from sqlalchemy.orm import Session

from src.data_access.database import Base
from src.data_access.entities.user_llm_config import UserLlmConfig


class UserLlmConfigRepository:
    """UserLlmConfig 的数据访问方法。"""

    def get_by_id(self, db: Session, id: int) -> Optional[UserLlmConfig]:
        return db.query(UserLlmConfig).filter(UserLlmConfig.id == id).first()

    def get_by_user_and_agent(
        self, db: Session, user_id: int, agent: str
    ) -> Optional[UserLlmConfig]:
        return (
            db.query(UserLlmConfig)
            .filter(UserLlmConfig.user_id == user_id, UserLlmConfig.agent == agent)
            .first()
        )

    def get_active_by_user(
        self, db: Session, user_id: int
    ) -> List[UserLlmConfig]:
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
        existing = self.get_by_user_and_agent(db, user_id, agent)
        if existing:
            existing.provider = provider
            existing.model = model
            existing.api_key_encrypted = api_key_encrypted
            existing.base_url = base_url
            if temperature is not None:
                existing.temperature = temperature
            db.commit()
            db.refresh(existing)
            return existing
        else:
            config = UserLlmConfig(
                user_id=user_id,
                agent=agent,
                provider=provider,
                model=model,
                api_key_encrypted=api_key_encrypted,
                base_url=base_url,
                temperature=temperature if temperature is not None else 0.7,
                is_active=True,
            )
            db.add(config)
            db.commit()
            db.refresh(config)
            return config

    def delete_by_user_and_agent(self, db: Session, user_id: int, agent: str) -> bool:
        config = self.get_by_user_and_agent(db, user_id, agent)
        if not config:
            return False
        db.delete(config)
        db.commit()
        return True


user_llm_config_repository = UserLlmConfigRepository()
```

- [ ] **Step 4: 运行测试验证通过**

Run: `pytest tests/unit/data_access/test_user_llm_config_repository.py -v`
Expected: PASS

- [ ] **Step 5: 更新 repositories/__init__.py**

```python
# src/data_access/repositories/__init__.py
from . import (
    interview_repository,
    job_match_result_repository,
    job_repository,
    resume_optimization_repository,
    resume_repository,
    user_llm_config_repository,
    user_repository,
)

__all__ = [
    "interview_repository",
    "job_match_result_repository",
    "job_repository",
    "resume_optimization_repository",
    "resume_repository",
    "user_llm_config_repository",
    "user_repository",
]
```

- [ ] **Step 6: 提交**

```bash
git add src/data_access/repositories/user_llm_config_repository.py src/data_access/repositories/__init__.py tests/unit/data_access/test_user_llm_config_repository.py
git commit -m "feat: add UserLlmConfigRepository"
```

---

## Task 4: Pydantic Schema

**Files:**
- Create: `src/presentation/schemas/user_llm_config.py`
- Test: `tests/unit/presentation/schemas/test_user_llm_config_schema.py`

- [ ] **Step 1: 写测试**

```python
# tests/unit/presentation/schemas/test_user_llm_config_schema.py
import pytest
from datetime import datetime
from pydantic import ValidationError
from src.presentation.schemas.user_llm_config import (
    UserLlmConfigBase,
    UserLlmConfigCreate,
    UserLlmConfigResponse,
)

def test_user_llm_config_create_valid():
    data = UserLlmConfigCreate(
        agent="resume_agent",
        provider="openai",
        model="gpt-4o-mini",
        api_key="sk-test-123",
        base_url=None,
        temperature=0.7,
    )
    assert data.agent == "resume_agent"
    assert data.api_key == "sk-test-123"

def test_user_llm_config_create_requires_agent():
    with pytest.raises(ValidationError):
        UserLlmConfigCreate(provider="openai", model="gpt-4o-mini", api_key="sk-test")

def test_user_llm_config_response_excludes_api_key():
    response = UserLlmConfigResponse(
        agent="resume_agent",
        provider="openai",
        model="gpt-4o-mini",
        base_url=None,
        temperature=0.7,
        is_active=True,
        updated_at=datetime.now(),
    )
    assert not hasattr(response, "api_key")
    assert not hasattr(response, "api_key_encrypted")

def test_temperature_range():
    data = UserLlmConfigCreate(
        agent="resume_agent",
        provider="openai",
        model="gpt-4o-mini",
        api_key="sk-test",
        temperature=1.5,
    )
    assert data.temperature == 1.5
```

- [ ] **Step 2: 运行测试验证失败**

Run: `pytest tests/unit/presentation/schemas/test_user_llm_config_schema.py -v`
Expected: FAIL - module not found

- [ ] **Step 3: 实现 Schema**

```python
# src/presentation/schemas/user_llm_config.py
"""UserLlmConfig 的 Pydantic Schema。"""

from datetime import datetime
from typing import Optional

from pydantic import BaseModel, ConfigDict, Field


class UserLlmConfigBase(BaseModel):
    """共享字段定义。"""

    agent: str = Field(..., description="Agent 标识：resume_agent / job_agent / interview_agent")
    provider: str = Field(..., description="Provider 标识")
    model: str = Field(..., description="模型名称")
    base_url: Optional[str] = Field(None, description="自定义 API endpoint")
    temperature: Optional[float] = Field(0.7, ge=0.0, le=2.0, description="生成温度 0-2")


class UserLlmConfigCreate(UserLlmConfigBase):
    """创建/更新配置时接收的 Schema（包含明文 api_key）。"""

    api_key: str = Field(..., description="API Key（明文，传输加密）")


class UserLlmConfigResponse(UserLlmConfigBase):
    """返回给前端的 Schema（不包含 api_key）。"""

    is_active: bool
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)
```

- [ ] **Step 4: 运行测试验证通过**

Run: `pytest tests/unit/presentation/schemas/test_user_llm_config_schema.py -v`
Expected: PASS

- [ ] **Step 5: 提交**

```bash
git add src/presentation/schemas/user_llm_config.py tests/unit/presentation/schemas/test_user_llm_config_schema.py
git commit -m "feat: add UserLlmConfig Pydantic schemas"
```

---

## Task 5: API 端点

**Files:**
- Create: `src/presentation/api/v1/user_llm_configs.py`
- Modify: `src/main.py:78-84`
- Test: `tests/integration/api/test_user_llm_configs_api.py`

- [ ] **Step 1: 写测试**

```python
# tests/integration/api/test_user_llm_configs_api.py
import pytest
from unittest.mock import MagicMock, patch
from datetime import datetime

def test_get_configs_returns_user_configs(client, authenticated_user):
    with patch("src.presentation.api.v1.user_llm_configs.user_llm_config_service") as mock_svc:
        mock_svc.get_user_configs.return_value = [
            MagicMock(
                agent="resume_agent",
                provider="openai",
                model="gpt-4o-mini",
                base_url=None,
                temperature=0.7,
                is_active=True,
                updated_at=datetime.now(),
            )
        ]
        response = client.get("/api/v1/users/llm-configs")
        assert response.status_code == 200

def test_post_config_creates_or_updates(client, authenticated_user):
    with patch("src.presentation.api.v1.user_llm_configs.user_llm_config_service") as mock_svc:
        mock_svc.save_config.return_value = MagicMock(
            agent="resume_agent",
            provider="deepseek",
            model="deepseek-chat",
            base_url=None,
            temperature=0.5,
            is_active=True,
            updated_at=datetime.now(),
        )
        response = client.post(
            "/api/v1/users/llm-configs",
            json={
                "agent": "resume_agent",
                "provider": "deepseek",
                "model": "deepseek-chat",
                "api_key": "sk-deepseek-123",
                "temperature": 0.5,
            },
        )
        assert response.status_code == 200
        data = response.json()
        assert data["provider"] == "deepseek"

def test_delete_config(client, authenticated_user):
    with patch("src.presentation.api.v1.user_llm_configs.user_llm_config_service") as mock_svc:
        mock_svc.delete_config.return_value = True
        response = client.delete("/api/v1/users/llm-configs/resume_agent")
        assert response.status_code == 204
```

- [ ] **Step 2: 运行测试验证失败**

Run: `pytest tests/integration/api/test_user_llm_configs_api.py -v`
Expected: FAIL - module not found

- [ ] **Step 3: 实现 Service 层**

```python
# src/business_logic/user_llm_config_service.py
"""UserLlmConfig 业务逻辑层。"""

from typing import List, Optional

from sqlalchemy.orm import Session

from src.data_access.repositories.user_llm_config_repository import user_llm_config_repository
from src.presentation.schemas.user_llm_config import UserLlmConfigCreate
from src.utils.crypto import decrypt_api_key, encrypt_api_key


class UserLlmConfigService:
    """UserLlmConfig 业务逻辑：加密存储、配置查询。"""

    def get_user_configs(self, db: Session, user_id: int) -> List:
        """获取用户所有启用的 Agent 配置（解密后的 api_key 不返回）。"""
        return user_llm_config_repository.get_active_by_user(db, user_id)

    def get_config_for_agent(
        self, db: Session, user_id: int, agent: str
    ) -> Optional[dict]:
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

    def save_config(
        self, db: Session, user_id: int, data: UserLlmConfigCreate
    ) ->:
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
```

- [ ] **Step 4: 实现 API 端点**

```python
# src/presentation/api/v1/user_llm_configs.py
"""用户 LLM 配置 CRUD API。"""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from src.business_logic.user_llm_config_service import user_llm_config_service
from src.presentation.api.deps import get_current_user, get_db
from src.presentation.schemas.user_llm_config import (
    UserLlmConfigCreate,
    UserLlmConfigResponse,
)

router = APIRouter()


@router.get("/", response_model=list[UserLlmConfigResponse])
async def get_llm_configs(
    current_user=Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """获取当前用户所有 Agent 的 LLM 配置。"""
    configs = user_llm_config_service.get_user_configs(db, current_user.id)
    return configs


@router.post("/", response_model=UserLlmConfigResponse)
async def save_llm_config(
    data: UserLlmConfigCreate,
    current_user=Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """创建或更新某个 Agent 的 LLM 配置。"""
    try:
        config = user_llm_config_service.save_config(db, current_user.id, data)
        return config
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Save config failed: {exc}",
        ) from exc


@router.delete("/{agent}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_llm_config(
    agent: str,
    current_user=Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """删除某个 Agent 的 LLM 配置（回退到系统默认）。"""
    deleted = user_llm_config_service.delete_config(db, current_user.id, agent)
    if not deleted:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Config not found",
        )
```

- [ ] **Step 5: 在 main.py 注册路由**

在 `src/main.py` 的路由注册部分添加:
```python
from src.presentation.api.v1 import auth, resume, jobs, interview, users, agent, user_llm_configs
app.include_router(auth.router, prefix="/api/v1/auth", tags=["认证"])
app.include_router(resume.router, prefix="/api/v1/resumes", tags=["简历管理"])
app.include_router(jobs.router, prefix="/api/v1/jobs", tags=["岗位管理"])
app.include_router(interview.router, prefix="/api/v1/interview", tags=["面试管理"])
app.include_router(users.router, prefix="/api/v1/users", tags=["用户管理"])
app.include_router(agent.router, prefix="/api/v1/agent", tags=["Agent"])
app.include_router(user_llm_configs.router, prefix="/api/v1/users/llm-configs", tags=["用户LLM配置"])
```

- [ ] **Step 6: 运行测试验证通过**

Run: `pytest tests/integration/api/test_user_llm_configs_api.py -v`
Expected: PASS

- [ ] **Step 7: 提交**

```bash
git add src/business_logic/user_llm_config_service.py src/presentation/api/v1/user_llm_configs.py src/main.py tests/integration/api/test_user_llm_configs_api.py
git commit -m "feat(api): add user LLM config CRUD endpoints"
```

---

## Task 6: 数据库迁移

**Files:**
- Create: `alembic/versions/008_user_llm_configs.py`

- [ ] **Step 1: 创建迁移文件**

```python
"""Add user_llm_configs table.

Revision ID: 008
Revises: 007_interview_sessions_resume_id
Create Date: 2026-04-08
"""
from alembic import op
import sqlalchemy as sa

revision = "008"
down_revision = "007_interview_sessions_resume_id"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "user_llm_configs",
        sa.Column("id", sa.Integer(), nullable=False, comment="主键"),
        sa.Column(
            "user_id",
            sa.Integer(),
            sa.ForeignKey("users.id", ondelete="CASCADE"),
            nullable=False,
            comment="用户 ID",
        ),
        sa.Column(
            "agent",
            sa.String(length=50),
            nullable=False,
            comment="Agent 标识：resume_agent / job_agent / interview_agent",
        ),
        sa.Column("provider", sa.String(length=100), nullable=False, comment="Provider 标识"),
        sa.Column("model", sa.String(length=100), nullable=False, comment="模型名称"),
        sa.Column(
            "api_key_encrypted",
            sa.String(length=500),
            nullable=False,
            comment="加密后的 API Key",
        ),
        sa.Column(
            "base_url",
            sa.String(length=255),
            nullable=True,
            comment="自定义 API endpoint",
        ),
        sa.Column(
            "temperature",
            sa.Float(),
            nullable=True,
            default=0.7,
            comment="生成温度",
        ),
        sa.Column(
            "is_active",
            sa.Boolean(),
            nullable=False,
            default=True,
            comment="是否启用",
        ),
        sa.Column(
            "created_at",
            sa.DateTime(),
            nullable=False,
            server_default=sa.func.now(),
            comment="创建时间",
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(),
            nullable=False,
            server_default=sa.func.now(),
            onupdate=sa.func.now(),
            comment="更新时间",
        ),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        "ix_user_llm_configs_id",
        "user_llm_configs",
        ["id"],
        unique=False,
    )
    op.create_index(
        "ix_user_llm_configs_user_id",
        "user_llm_configs",
        ["user_id"],
        unique=False,
    )
    op.create_index(
        "idx_user_llm_config_user_agent",
        "user_llm_configs",
        ["user_id", "agent"],
        unique=True,
    )


def downgrade() -> None:
    op.drop_index("idx_user_llm_config_user_agent", table_name="user_llm_configs")
    op.drop_index("ix_user_llm_configs_user_id", table_name="user_llm_configs")
    op.drop_index("ix_user_llm_configs_id", table_name="user_llm_configs")
    op.drop_table("user_llm_configs")
```

- [ ] **Step 2: 运行迁移验证**

Run: `python -m alembic upgrade head`
Expected: Running upgrade  -> 008

- [ ] **Step 3: 提交**

```bash
git add alembic/versions/008_user_llm_configs.py
git commit -m "feat(migration): add user_llm_configs table"
```

---

## Task 7: Agent 运行时集成

**Files:**
- Modify: `src/business_logic/agents/resume_agent/resume_agent.py:34-43`
- Modify: `src/business_logic/agents/job_agent/job_agent.py:34-43`
- Modify: `src/business_logic/agents/interview_agent/interview_agent.py:35-44`
- Modify: `src/business_logic/agent/agent_chat_service.py`

- [ ] **Step 1: 修改 ResumeAgent.__init__ 接受 user_id**

在 `resume_agent.py` 的 `__init__` 方法签名中添加 `user_id: Optional[int] = None`，在 `_build_llm()` 调用前插入用户配置查询逻辑：

```python
# resume_agent.py __init__ 部分改造
def __init__(
    self,
    config: Optional[Dict[str, Any]] = None,
    llm: Optional[BaseLLM] = None,
    allow_mock_fallback: bool = False,
    user_id: Optional[int] = None,
):
    super().__init__(config)
    self.config = self._merge_runtime_config(self.config, user_id=user_id)
    self.allow_mock_fallback = allow_mock_fallback
    self.llm = llm or self._build_llm()
    self._prompt_pack = self._load_prompt_pack()

@classmethod
def _merge_runtime_config(cls, config: Optional[Dict[str, Any]], user_id: Optional[int] = None) -> Dict[str, Any]:
    merged = cls._load_default_config()
    merged.update(config or {})

    # 查询用户自定义配置，优先使用
    if user_id is not None:
        from src.business_logic.user_llm_config_service import user_llm_config_service
        from src.data_access.database import SessionLocal
        db = SessionLocal()
        try:
            user_config = user_llm_config_service.get_config_for_agent(db, user_id, "resume_agent")
            if user_config:
                merged.update(user_config)
        finally:
            db.close()

    return {key: value for key, value in merged.items() if value is not None}
```

JobAgent 和 InterviewAgent 采用完全相同的模式，只需替换 agent 名称为 `"job_agent"` 和 `"interview_agent"`。

- [ ] **Step 2: 修改 AgentChatService 传入 user_id**

在 `agent_chat_service.py` 中，`_route_to_agent()` 或类似的调用点，找到创建 Agent 实例的位置，传入 `user_id=request_user_id`：

```python
# agent_chat_service.py - 在创建 Agent 实例时传入 user_id
if route == "resume":
    agent = ResumeAgent(user_id=user_id, ...)
elif route == "job":
    agent = JobAgent(user_id=user_id, ...)
elif route == "interview":
    agent = InterviewAgent(user_id=user_id, ...)
```

- [ ] **Step 3: 验证导入不报错**

Run: `python -c "from src.business_logic.agents.resume_agent.resume_agent import ResumeAgent; from src.business_logic.agents.job_agent.job_agent import JobAgent; from src.business_logic.agents.interview_agent.interview_agent import InterviewAgent; print('OK')"`
Expected: OK

- [ ] **Step 4: 提交**

```bash
git add src/business_logic/agents/resume_agent/resume_agent.py src/business_logic/agents/job_agent/job_agent.py src/business_logic/agents/interview_agent/interview_agent.py src/business_logic/agent/agent_chat_service.py
git commit -m "feat(agent): integrate user LLM config at runtime"
```

---

## Task 8: 前端 - API 客户端

**Files:**
- Modify: `frontend/src/lib/api.ts`

- [ ] **Step 1: 添加 API 方法到 api.ts**

```typescript
// frontend/src/lib/api.ts 添加以下方法

export async function getUserLlmConfigs(): Promise<UserLlmConfig[]> {
  const res = await fetch('/api/v1/users/llm-configs', { credentials: 'include' })
  if (!res.ok) throw new Error('Failed to fetch LLM configs')
  return res.json()
}

export async function saveUserLlmConfig(data: UserLlmConfigInput): Promise<UserLlmConfig> {
  const res = await fetch('/api/v1/users/llm-configs', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    credentials: 'include',
    body: JSON.stringify(data),
  })
  if (!res.ok) throw new Error('Failed to save LLM config')
  return res.json()
}

export async function deleteUserLlmConfig(agent: string): Promise<void> {
  const res = await fetch(`/api/v1/users/llm-configs/${agent}`, {
    method: 'DELETE',
    credentials: 'include',
  })
  if (!res.ok) throw new Error('Failed to delete LLM config')
}

export interface UserLlmConfig {
  agent: string
  provider: string
  model: string
  base_url: string | null
  temperature: number
  is_active: boolean
  updated_at: string
}

export interface UserLlmConfigInput {
  agent: string
  provider: string
  model: string
  api_key: string
  base_url?: string | null
  temperature?: number
}
```

- [ ] **Step 2: 提交**

```bash
git add frontend/src/lib/api.ts
git commit -m "feat(frontend): add user LLM config API methods"
```

---

## Task 9: 前端 - 配置页面

**Files:**
- Create: `frontend/src/pages/settings/agent-config-page.tsx`
- Modify: `frontend/src/layout/authenticated-app-shell.tsx:5-10`
- Modify: `frontend/src/app/router.tsx`

- [ ] **Step 1: 创建 Agent Config 页面**

```tsx
// frontend/src/pages/settings/agent-config-page.tsx
import { useState } from 'react'
import { useForm } from 'react-hook-form'
import { zodResolver } from '@hookform/resolvers/zod'
import { z } from 'zod'
import { getUserLlmConfigs, saveUserLlmConfig, deleteUserLlmConfig, type UserLlmConfig, type UserLlmConfigInput } from '../../lib/api'

const AGENTS = [
  { key: 'resume_agent', label: '简历 Agent', description: '简历摘要、改进建议' },
  { key: 'job_agent', label: '岗位 Agent', description: '岗位搜索、JD 匹配' },
  { key: 'interview_agent', label: '面试 Agent', description: '面试问题生成、答案评价' },
]

const PROVIDERS = [
  { value: 'openai', label: 'OpenAI' },
  { value: 'anthropic', label: 'Anthropic' },
  { value: 'minimax', label: 'MiniMax' },
  { value: 'deepseek', label: 'DeepSeek' },
  { value: 'zhipu', label: '智谱 AI' },
  { value: 'tongyi', label: '通义千问' },
  { value: 'moonshot', label: 'Moonshot' },
  { value: 'siliconflow', label: 'SiliconFlow' },
]

const configSchema = z.object({
  agent: z.string(),
  provider: z.string().min(1, '请选择或输入 Provider'),
  model: z.string().min(1, '请输入模型名称'),
  api_key: z.string().min(1, '请输入 API Key'),
  base_url: z.string().optional(),
  temperature: z.number().min(0).max(2).default(0.7),
})

type ConfigFormData = z.infer<typeof configSchema>

export function AgentConfigPage() {
  const [configs, setConfigs] = useState<Record<string, UserLlmConfig>>({})
  const [editing, setEditing] = useState<string | null>(null)
  const [saving, setSaving] = useState(false)
  const [message, setMessage] = useState<{ type: 'success' | 'error'; text: string } | null>(null)

  const { register, handleSubmit, reset, watch, setValue, formState: { errors } } = useForm<ConfigFormData>({
    resolver: zodResolver(configSchema),
    defaultValues: { temperature: 0.7 },
  })

  async function loadConfigs() {
    try {
      const data = await getUserLlmConfigs()
      const map: Record<string, UserLlmConfig> = {}
      for (const c of data) { map[c.agent] = c }
      setConfigs(map)
    } catch {
      setMessage({ type: 'error', text: '加载配置失败' })
    }
  }

  async function onSubmit(data: ConfigFormData) {
    setSaving(true)
    try {
      const saved = await saveUserLlmConfig(data as UserLlmConfigInput)
      setConfigs(prev => ({ ...prev, [saved.agent]: saved }))
      setEditing(null)
      setMessage({ type: 'success', text: '保存成功' })
    } catch {
      setMessage({ type: 'error', text: '保存失败' })
    } finally {
      setSaving(false)
    }
  }

  async function handleDelete(agent: string) {
    try {
      await deleteUserLlmConfig(agent)
      setConfigs(prev => { const m = { ...prev }; delete m[agent]; return m })
      setEditing(null)
      setMessage({ type: 'success', text: '已删除，回退到系统默认' })
    } catch {
      setMessage({ type: 'error', text: '删除失败' })
    }
  }

  function startEdit(agent: string) {
    const existing = configs[agent]
    if (existing) {
      reset({ agent, provider: existing.provider, model: existing.model, api_key: '', base_url: existing.base_url ?? '', temperature: existing.temperature })
    } else {
      reset({ agent, provider: '', model: '', api_key: '', base_url: '', temperature: 0.7 })
    }
    setEditing(agent)
  }

  return (
    <div className="max-w-3xl mx-auto space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-semibold">Agent 配置</h1>
          <p className="text-sm text-[var(--color-muted)] mt-1">为每个 Agent 配置自定义 LLM，回退到系统默认</p>
        </div>
        <button onClick={loadConfigs} className="text-sm text-[var(--color-primary)] hover:underline">刷新</button>
      </div>

      {message && (
        <div className={`text-sm px-4 py-3 rounded-xl ${message.type === 'success' ? 'bg-green-500/10 text-green-600' : 'bg-red-500/10 text-red-600'}`}>
          {message.text}
        </div>
      )}

      <div className="space-y-4">
        {AGENTS.map(({ key, label, description }) => {
          const config = configs[key]
          const isEditing = editing === key

          return (
            <div key={key} className="border border-[var(--color-border)] rounded-2xl p-6">
              <div className="flex items-start justify-between mb-4">
                <div>
                  <h2 className="font-medium">{label}</h2>
                  <p className="text-sm text-[var(--color-muted)]">{description}</p>
                </div>
                {!isEditing && (
                  <button
                    onClick={() => startEdit(key)}
                    className="text-sm px-4 py-2 rounded-xl border border-[var(--color-border)] hover:bg-[var(--color-surface)] transition"
                  >
                    {config ? '编辑' : '配置'}
                  </button>
                )}
              </div>

              {!isEditing && config && (
                <div className="grid grid-cols-3 gap-4 text-sm">
                  <div><span className="text-[var(--color-muted)]">Provider</span><div className="font-medium">{config.provider}</div></div>
                  <div><span className="text-[var(--color-muted)]">Model</span><div className="font-medium">{config.model}</div></div>
                  <div><span className="text-[var(--color-muted)]">Temperature</span><div className="font-medium">{config.temperature}</div></div>
                </div>
              )}

              {!isEditing && !config && (
                <p className="text-sm text-[var(--color-muted)]">使用系统默认配置</p>
              )}

              {isEditing && (
                <form onSubmit={handleSubmit(onSubmit)} className="space-y-4">
                  <input type="hidden" {...register('agent')} />

                  <div className="grid grid-cols-2 gap-4">
                    <div>
                      <label className="block text-sm font-medium mb-1">Provider</label>
                      <select
                        {...register('provider')}
                        className="w-full px-3 py-2 rounded-xl border border-[var(--color-border)] bg-[var(--color-canvas)]"
                      >
                        <option value="">选择或输入</option>
                        {PROVIDERS.map(p => <option key={p.value} value={p.value}>{p.label}</option>)}
                      </select>
                      <input
                        {...register('provider')}
                        placeholder="或输入自定义 Provider"
                        className="mt-2 w-full px-3 py-2 rounded-xl border border-[var(--color-border)] bg-[var(--color-canvas)]"
                      />
                      {errors.provider && <p className="text-red-500 text-xs mt-1">{errors.provider.message}</p>}
                    </div>

                    <div>
                      <label className="block text-sm font-medium mb-1">Model</label>
                      <input
                        {...register('model')}
                        placeholder="如 gpt-4o-mini"
                        className="w-full px-3 py-2 rounded-xl border border-[var(--color-border)] bg-[var(--color-canvas)]"
                      />
                      {errors.model && <p className="text-red-500 text-xs mt-1">{errors.model.message}</p>}
                    </div>
                  </div>

                  <div>
                    <label className="block text-sm font-medium mb-1">API Key</label>
                    <input
                      type="password"
                      {...register('api_key')}
                      placeholder={config ? '（不修改请留空）' : '输入 API Key'}
                      className="w-full px-3 py-2 rounded-xl border border-[var(--color-border)] bg-[var(--color-canvas)]"
                    />
                    {errors.api_key && <p className="text-red-500 text-xs mt-1">{errors.api_key.message}</p>}
                  </div>

                  <div>
                    <label className="block text-sm font-medium mb-1">Base URL（可选）</label>
                    <input
                      {...register('base_url')}
                      placeholder="如 https://api.openai.com/v1"
                      className="w-full px-3 py-2 rounded-xl border border-[var(--color-border)] bg-[var(--color-canvas)]"
                    />
                  </div>

                  <div>
                    <label className="block text-sm font-medium mb-1">Temperature: {watch('temperature')}</label>
                    <input
                      type="range"
                      min="0" max="2" step="0.1"
                      {...register('temperature', { valueAsNumber: true })}
                      className="w-full"
                    />
                  </div>

                  <div className="flex gap-3 pt-2">
                    <button
                      type="submit"
                      disabled={saving}
                      className="px-6 py-2 rounded-xl bg-[var(--color-primary)] text-white font-medium hover:opacity-90 disabled:opacity-50 transition"
                    >
                      {saving ? '保存中...' : '保存'}
                    </button>
                    <button
                      type="button"
                      onClick={() => setEditing(null)}
                      className="px-6 py-2 rounded-xl border border-[var(--color-border)] hover:bg-[var(--color-surface)] transition"
                    >
                      取消
                    </button>
                    {config && (
                      <button
                        type="button"
                        onClick={() => handleDelete(key)}
                        className="px-6 py-2 rounded-xl border border-red-300 text-red-500 hover:bg-red-50 transition ml-auto"
                      >
                        删除
                      </button>
                    )}
                  </div>
                </form>
              )}
            </div>
          )
        })}
      </div>
    </div>
  )
}
```

- [ ] **Step 2: 更新导航

在 `frontend/src/layout/authenticated-app-shell.tsx` 的 `navigationItems` 添加：
```typescript
{ to: '/settings/agent-config', label: 'Agent 配置' },
```

- [ ] **Step 3: 添加路由

在 `frontend/src/app/router.tsx` 添加：
```typescript
{ path: '/settings/agent-config', element: <AgentConfigPage /> },
```

从 `frontend/src/pages/settings/agent-config-page.tsx` 导入 `AgentConfigPage`。

- [ ] **Step 4: 提交**

```bash
git add frontend/src/pages/settings/agent-config-page.tsx frontend/src/layout/authenticated-app-shell.tsx frontend/src/app/router.tsx
git commit -m "feat(frontend): add agent config settings page"
```

---

## Task 10: 端到端验证

- [ ] **Step 1: 创建迁移**

Run: `python -m alembic upgrade head`
Expected: Running upgrade  -> 008

- [ ] **Step 2: 启动服务，测试 API**

```bash
# 后端
python -m uvicorn src.main:app --reload

# 测试 GET /api/v1/users/llm-configs (未登录302或401)
curl -s http://localhost:8000/api/v1/users/llm-configs | head -c 200

# 测试完整流程（登录后）
# 1. 登录获取 cookie
# 2. POST 创建配置
# 3. GET 确认配置存在
# 4. DELETE 删除配置
# 5. GET 确认配置已删除
```

- [ ] **Step 3: 访问前端页面**

打开 http://localhost:3000/settings/agent-config，确认：
- 三个 Agent 卡片正确渲染
- 点击"配置"展开表单
- 保存后正确回显 Provider + Model
- 删除后回退到"使用系统默认配置"

- [ ] **Step 4: 运行单元测试**

Run: `pytest tests/unit tests/integration -q --tb=short`
Expected: 所有测试通过

---

## 验证清单

| 检查项 | 预期结果 |
|--------|----------|
| GET /api/v1/users/llm-configs 未登录返回 401 | ✅ |
| POST /api/v1/users/llm-configs 返回体不含 api_key | ✅ |
| 同一 user_id + agent 重复 POST 执行 upsert | ✅ |
| DELETE 后 GET 返回 404 或空 | ✅ |
| Agent 不配置时回退到系统默认 | ✅ |
| API Key 加密存储（数据库中看不到明文） | ✅ |
| 前端三个 Agent 卡片完整渲染 | ✅ |
| 前端 Provider 下拉包含所有 8 个选项 | ✅ |

---

Plan complete and saved to `docs/superpowers/plans/2026-04-08-user-llm-config.md`. Two execution options:

**1. Subagent-Driven (recommended)** - I dispatch a fresh subagent per task, review between tasks, fast iteration

**2. Inline Execution** - Execute tasks in this session using executing-plans, batch execution with checkpoints

Which approach?
