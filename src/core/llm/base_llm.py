"""
LLM抽象基类
定义大语言模型的统一接口
"""

from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional


class BaseLLM(ABC):
    """LLM抽象基类"""

    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """
        初始化LLM

        Args:
            config: 配置字典
        """
        self.config = config or {}

    @abstractmethod
    async def generate(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        max_tokens: Optional[int] = None,
        temperature: float = 0.7,
        **kwargs: Any,
    ) -> str:
        """
        生成文本

        Args:
            prompt: 用户提示词
            system_prompt: 系统提示词
            max_tokens: 最大生成token数
            temperature: 温度参数
            **kwargs: 其他参数

        Returns:
            生成的文本
        """
        pass

    @abstractmethod
    async def chat(
        self,
        messages: List[Dict[str, str]],
        max_tokens: Optional[int] = None,
        temperature: float = 0.7,
        **kwargs: Any,
    ) -> Dict[str, Any]:
        """
        对话模式

        Args:
            messages: 消息列表
            max_tokens: 最大生成token数
            temperature: 温度参数
            **kwargs: 其他参数

        Returns:
            响应字典
        """
        pass

    @abstractmethod
    async def get_embedding(self, text: str) -> List[float]:
        """
        获取文本嵌入向量

        Args:
            text: 输入文本

        Returns:
            嵌入向量列表
        """
        pass
