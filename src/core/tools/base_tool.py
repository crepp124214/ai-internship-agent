"""
统一工具基类
继承 LangChain Core 的 BaseTool，统一工具接口
"""
from __future__ import annotations

from typing import Any, Dict, Optional

from langchain_core.callbacks import CallbackManagerForToolRun
from langchain_core.tools import BaseTool as LangChainBaseTool
from pydantic import BaseModel, Field


class BaseTool(LangChainBaseTool):
    """
    统一工具基类，继承 LangChain BaseTool
    所有领域工具都应继承此类
    """

    runtime: Optional[Any] = Field(default=None, exclude=True)

    def _run(
        self,
        tool_input: Dict[str, Any],
        runtime: Optional[Any] = None,
        run_manager: Optional[CallbackManagerForToolRun] = None,
    ) -> str:
        """
        同步执行入口，由父类调用
        """
        result = self._execute_sync(tool_input, runtime=runtime)
        if isinstance(result, dict):
            import json
            return json.dumps(result)
        return str(result)

    def _execute_sync(
        self,
        tool_input: Dict[str, Any],
        runtime: Optional[Any] = None,
    ) -> Dict[str, Any]:
        """
        子类覆盖此方法实现同步逻辑
        """
        raise NotImplementedError("Subclasses must implement _execute_sync")