from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Optional

from sqlalchemy.orm import Session


@dataclass
class ToolContext:
    """工具执行上下文，统一管理依赖"""
    db: Session
    user_id: Optional[int] = None
    agent_id: Optional[str] = None
    session_id: Optional[str] = None
    cache: dict[str, Any] = field(default_factory=dict)