"""
Agent抽象基类
定义所有Agent的统一接口
"""

from abc import ABC, abstractmethod
from typing import Any, Dict, Optional


class BaseAgent(ABC):
    """Agent抽象基类"""

    name: str = "base_agent"
    description: str = "基础Agent"

    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """
        初始化Agent

        Args:
            config: Agent配置字典
        """
        self.config = config or {}
        self._is_initialized = False

    async def initialize(self) -> None:
        """初始化Agent资源"""
        self._is_initialized = True

    async def cleanup(self) -> None:
        """清理Agent资源"""
        self._is_initialized = False

    @abstractmethod
    async def execute(self, task: Dict[str, Any]) -> Dict[str, Any]:
        """
        执行Agent任务

        Args:
            task: 任务描述字典

        Returns:
            执行结果字典
        """
        pass

    def get_status(self) -> Dict[str, Any]:
        """获取Agent状态"""
        return {
            "name": self.name,
            "description": self.description,
            "initialized": self._is_initialized,
        }
