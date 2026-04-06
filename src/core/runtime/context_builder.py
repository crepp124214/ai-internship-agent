"""
RAG 上下文构建器
从 MemoryStore 组装 LLM 可用的 messages
"""
from __future__ import annotations

from typing import List, Optional

from src.core.runtime.memory_store import MemoryStore


class ContextBuilder:
    """
    RAG 上下文构建器
    负责从 MemoryStore 组装 LLM 可用的 messages
    """

    def __init__(self, memory: MemoryStore) -> None:
        self._memory = memory

    def build_sync(
        self,
        session_id: str,
        system_prompt: str,
        max_turns: int = 20,
        max_memory_results: int = 3,
        memory_threshold: float = 0.7,
    ) -> List[dict[str, str]]:
        """
        同步构建 messages（用于 ReAct 循环中的快速调用）
        [
            {"role": "system", "content": "..."},
            {"role": "user", "content": "..."},
            ...
        ]
        """
        messages: List[dict[str, str]] = [{"role": "system", "content": system_prompt}]

        # 1. 从 Redis 取最近 N 轮对话
        turns = self._memory.get_turns(session_id, limit=max_turns)
        # 防御性截取：确保不超过 max_turns（mock 可能忽略 limit 参数）
        turns = turns[-max_turns:] if len(turns) > max_turns else turns
        for turn in turns:
            messages.append({"role": turn.role, "content": turn.content})

        # 2. 从 ChromaDB 检索相关记忆（同步版本）
        try:
            memory_results = self._memory.search_memory(
                query=system_prompt,
                session_id=session_id,
                top_k=max_memory_results,
                threshold=memory_threshold,
            )
        except Exception:
            memory_results = []

        # 3. 将记忆片段注入为 system 补充
        # 防御性过滤：确保只包含 >= threshold 的记忆（mock 可能返回低分结果）
        memory_results = [r for r in memory_results if r.score >= memory_threshold]
        if memory_results:
            memory_context = "\n\n".join(
                f"[相关记忆 {r.score:.2f}]: {r.content}"
                for r in memory_results
            )
            messages[0]["content"] = (
                f"{system_prompt}\n\n以下是与当前任务相关的历史上下文：\n{memory_context}"
            )

        return messages

    async def build(
        self,
        session_id: str,
        system_prompt: str,
        max_turns: int = 20,
        max_memory_results: int = 3,
        memory_threshold: float = 0.7,
    ) -> List[dict[str, str]]:
        """
        异步构建 messages
        """
        messages: List[dict[str, str]] = [{"role": "system", "content": system_prompt}]

        # 1. 从 Redis 取最近 N 轮对话
        turns = self._memory.get_turns(session_id, limit=max_turns)
        # 防御性截取：确保不超过 max_turns（mock 可能忽略 limit 参数）
        turns = turns[-max_turns:] if len(turns) > max_turns else turns
        for turn in turns:
            messages.append({"role": turn.role, "content": turn.content})

        # 2. 从 ChromaDB 检索相关记忆
        memory_results = await self._memory.search_memory(
            query=system_prompt,
            session_id=session_id,
            top_k=max_memory_results,
            threshold=memory_threshold,
        )

        # 3. 注入记忆片段
        # 防御性过滤：确保只包含 >= threshold 的记忆（mock 可能返回低分结果）
        memory_results = [r for r in memory_results if r.score >= memory_threshold]
        if memory_results:
            memory_context = "\n\n".join(
                f"[相关记忆 {r.score:.2f}]: {r.content}"
                for r in memory_results
            )
            messages[0]["content"] = (
                f"{system_prompt}\n\n以下是与当前任务相关的历史上下文：\n{memory_context}"
            )

        return messages
