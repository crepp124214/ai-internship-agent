"""
Agent 执行器 — ReAct (Reasoning + Acting) 循环
"""
from __future__ import annotations

import asyncio
import json
from typing import Any, AsyncIterator, Dict, List, Optional

from src.core.llm.litellm_adapter import LiteLLMAdapter
from src.core.runtime.context_builder import ContextBuilder
from src.core.runtime.memory_store import MemoryStore
from src.core.runtime.state_machine import StateMachine
from src.core.runtime.tool_registry import ToolRegistry


class AgentExecutor:
    """
    ReAct (Reasoning + Acting) 执行器
    状态流转：idle → planning → tool_use → responding → done

    ReAct 循环:
      1. planning   — 构建 context，准备 prompt
      2. llm.chat() — 调用 LLM，传入 tools
      3a. tool_call — 执行工具，获取 observation，回到 planning
      3b. text       — yield 返回，状态切到 done
    """

    MAX_REACT_STEPS = 20  # 防止无限循环

    def __init__(
        self,
        llm: LiteLLMAdapter,
        tools: ToolRegistry,
        memory: MemoryStore,
        state_machine: StateMachine,
        context_builder: ContextBuilder,
    ) -> None:
        self._llm = llm
        self._tools = tools
        self._memory = memory
        self._state_machine = state_machine
        self._context_builder = context_builder

    async def execute(
        self,
        task: str,
        session_id: str,
        system_prompt: Optional[str] = "You are a helpful agent.",
        max_steps: int = MAX_REACT_STEPS,
    ) -> AsyncIterator[str]:
        """
        执行任务，yield 每一步的文本输出（流式）
        """
        # 添加用户输入到记忆
        self._memory.add_turn(session_id, "user", task)

        try:
            self._state_machine.transition("planning", reason="start")
            messages = self._context_builder.build_sync(
                session_id=session_id,
                system_prompt=system_prompt,
            )

            step = 0
            while step < max_steps:
                step += 1

                # 调用 LLM
                tool_schemas = self._tools.get_schemas() if self._tools._tools else None
                response = await self._llm.chat(
                    messages=messages,
                    tools=tool_schemas,
                )

                tool_calls = response.get("tool_calls")
                content = response.get("content", "")

                if tool_calls:
                    # 有工具调用
                    self._state_machine.transition("tool_use", reason=f"step {step}")
                    for tc in tool_calls:
                        tool_name = tc.get("function", {}).get("name", "")
                        raw_args = tc.get("function", {}).get("arguments", "{}")
                        try:
                            tool_args = json.loads(raw_args) if isinstance(raw_args, str) else raw_args
                        except json.JSONDecodeError:
                            tool_args = {}

                        # 执行工具
                        observation = self._tools.execute(tool_name, tool_args)

                        # 将 assistant message 和 tool result 加入 messages
                        messages.append({
                            "role": "assistant",
                            "tool_calls": [tc],
                        })
                        messages.append({
                            "role": "tool",
                            "tool_call_id": tc.get("id", ""),
                            "content": str(observation),
                        })

                        self._memory.add_turn(session_id, "assistant", f"[tool:{tool_name}] {observation}")

                    # 回到 planning 继续
                    self._state_machine.transition("planning", reason="continue after tool")
                    messages = self._context_builder.build_sync(
                        session_id=session_id,
                        system_prompt=system_prompt,
                    )

                else:
                    # 无工具调用，文本响应
                    if content:
                        self._state_machine.transition("responding", reason="text response")
                        self._memory.add_turn(session_id, "assistant", content)
                        messages.append({"role": "assistant", "content": content})
                        yield content

                    self._state_machine.transition("done", reason="task complete")
                    return

            # 超过最大步数
            self._state_machine.transition("done", reason="max steps reached")
            yield "[Agent reached maximum steps]"

        except Exception as exc:
            self._state_machine.transition("done", reason=f"error: {exc}")
            yield f"[Error: {exc}]"