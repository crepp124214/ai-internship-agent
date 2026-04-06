# Agent Runtime 基础设施 — 实施计划

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 构建完整的 Agent Runtime 基础设施：ReAct 执行循环、工具注册、状态机、记忆存储、上下文构建器

**Architecture:** 以 LiteLLM 为统一 LLM 调用层，LangChain @tool 为工具定义规范，ReAct 循环为核心执行模式。短期会话记忆用 Redis，长期向量记忆用 ChromaDB，纯向量相似度做 RAG 检索。

**Tech Stack:** Python 3.10+, litellm, langchain-core, langchain-community, redis, chromadb, pydantic v2

---

## 文件结构

```
src/core/llm/
└── litellm_adapter.py          # 新增：LiteLLM 统一 adapter

src/core/runtime/
├── state_machine.py            # 替换占位：Agent 执行状态机
├── memory_store.py             # 替换占位：Redis + ChromaDB 记忆存储
├── context_builder.py         # 替换占位：RAG 上下文构建
├── tool_registry.py           # 替换占位：工具注册表
└── agent_executor.py          # 替换占位：ReAct 执行器

src/core/tools/
├── base_tool.py               # 替换占位：LangChain BaseTool 封装
└── langchain_tools.py        # 新增：@tool 装饰器辅助函数

tests/unit/core/runtime/
├── test_state_machine.py      # 新增
├── test_memory_store.py       # 新增
├── test_context_builder.py    # 新增
├── test_tool_registry.py      # 新增
└── test_agent_executor.py     # 新增

requirements.txt               # 修改：添加 litellm, langchain-core, langchain-community
```

---

## Task 1: StateMachine — Agent 执行状态机

**Files:**
- Create: `tests/unit/core/runtime/test_state_machine.py`
- Modify: `src/core/runtime/state_machine.py`（替换占位内容）

- [ ] **Step 1: 写失败的测试**

```python
# tests/unit/core/runtime/test_state_machine.py
import pytest
from src.core.runtime.state_machine import StateMachine, StateTransition

def test_initial_state_is_idle():
    sm = StateMachine()
    assert sm.get_state() == "idle"

def test_valid_transition_idle_to_planning():
    sm = StateMachine()
    sm.transition("planning")
    assert sm.get_state() == "planning"

def test_invalid_transition_raises():
    sm = StateMachine()
    with pytest.raises(ValueError):
        sm.transition("done")  # idle cannot go directly to done

def test_history_records_transitions():
    sm = StateMachine()
    sm.transition("planning", reason="starting task")
    history = sm.get_history()
    assert len(history) == 1
    assert history[0].from_state == "idle"
    assert history[0].to_state == "planning"
    assert history[0].reason == "starting task"

def test_reset_returns_to_idle():
    sm = StateMachine()
    sm.transition("planning")
    sm.reset()
    assert sm.get_state() == "idle"
```

- [ ] **Step 2: 运行测试验证失败**

Run: `cd "D:\agent开发项目\AI实习求职Agent系统\ai-internship-agent" && python -m pytest tests/unit/core/runtime/test_state_machine.py -v`
Expected: FAIL — `state_machine.py` 只有 `pass`

- [ ] **Step 3: 写 StateMachine 实现**

```python
# src/core/runtime/state_machine.py
from datetime import datetime, timezone
from typing import NamedTuple


class StateTransition(NamedTuple):
    from_state: str
    to_state: str
    timestamp: datetime
    reason: str | None


class StateMachine:
    """
    Agent 执行状态机
    状态：idle | planning | tool_use | responding | done
    """

    VALID_TRANSITIONS = {
        "idle": {"planning"},
        "planning": {"tool_use", "responding", "done"},
        "tool_use": {"planning", "responding", "done"},
        "responding": {"done", "planning"},
        "done": {"idle"},
    }

    ALL_STATES = {"idle", "planning", "tool_use", "responding", "done"}

    def __init__(self) -> None:
        self._state = "idle"
        self._history: list[StateTransition] = []

    def transition(self, to: str, reason: str | None = None) -> None:
        if to not in self.ALL_STATES:
            raise ValueError(f"Unknown state: {to}")
        allowed = self.VALID_TRANSITIONS.get(self._state, set())
        if to not in allowed:
            raise ValueError(
                f"Invalid transition from '{self._state}' to '{to}'. "
                f"Allowed: {allowed or 'none'}"
            )
        self._history.append(StateTransition(
            from_state=self._state,
            to_state=to,
            timestamp=datetime.now(timezone.utc),
            reason=reason,
        ))
        self._state = to

    def get_state(self) -> str:
        return self._state

    def get_history(self) -> list[StateTransition]:
        return list(self._history)

    def reset(self) -> None:
        self._state = "idle"
        self._history.clear()
```

- [ ] **Step 4: 运行测试验证通过**

Run: `python -m pytest tests/unit/core/runtime/test_state_machine.py -v`
Expected: PASS（5 tests）

- [ ] **Step 5: 提交**

```bash
git add tests/unit/core/runtime/test_state_machine.py src/core/runtime/state_machine.py
git commit -m "feat: implement StateMachine for Agent execution state"
```

---

## Task 2: LiteLLM Adapter — 统一 LLM 调用层

**Files:**
- Create: `src/core/llm/litellm_adapter.py`
- Create: `tests/unit/core/test_litellm_adapter.py`

- [ ] **Step 1: 写失败的测试**

```python
# tests/unit/core/test_litellm_adapter.py
import pytest
from unittest.mock import AsyncMock, patch, MagicMock

from src.core.llm.litellm_adapter import LiteLLMAdapter

@pytest.fixture
def adapter():
    return LiteLLMAdapter(model="gpt-4o-mini", api_key="test-key")

def test_adapter_stores_model_and_key(adapter):
    assert adapter.model == "gpt-4o-mini"
    assert adapter.api_key == "test-key"

@pytest.mark.asyncio
async def test_chat_returns_content():
    adapter = LiteLLMAdapter(model="gpt-4o-mini", api_key="test-key")
    mock_response = MagicMock()
    mock_response.choices = [MagicMock(message=MagicMock(content="hello"))]

    with patch.object(adapter._client, "chat.completions.create", new_callable=AsyncMock) as mock_create:
        mock_create.return_value = mock_response
        result = await adapter.chat(messages=[{"role": "user", "content": "hi"}])
        assert result["content"] == "hello"
        mock_create.assert_called_once()
        call_kwargs = mock_create.call_args.kwargs
        assert call_kwargs["model"] == "gpt-4o-mini"
        assert call_kwargs["messages"] == [{"role": "user", "content": "hi"}]

@pytest.mark.asyncio
async def test_chat_with_tools_includes_tools_param():
    adapter = LiteLLMAdapter(model="gpt-4o-mini", api_key="test-key")
    tools = [{"type": "function", "function": {"name": "get_weather", "description": "Get weather", "parameters": {"type": "object", "properties": {"city": {"type": "string"}}, "required": ["city"]}}}]

    mock_response = MagicMock()
    mock_response.choices = [MagicMock(message=MagicMock(content="It is sunny"))]

    with patch.object(adapter._client, "chat.completions.create", new_callable=AsyncMock) as mock_create:
        mock_create.return_value = mock_response
        await adapter.chat(messages=[{"role": "user", "content": "weather"}], tools=tools)
        call_kwargs = mock_create.call_args.kwargs
        assert "tools" in call_kwargs
        assert call_kwargs["tools"] == tools
```

- [ ] **Step 2: 运行测试验证失败**

Run: `python -m pytest tests/unit/core/test_litellm_adapter.py -v`
Expected: FAIL — `LiteLLMAdapter` 未定义

- [ ] **Step 3: 写 LiteLLMAdapter 实现**

```python
# src/core/llm/litellm_adapter.py
"""
LiteLLM 统一 adapter
通过 litellm 调用所有主流 LLM provider，统一接口
"""
from __future__ import annotations

from typing import Any, AsyncIterator, Dict, List, Literal, Optional, Union

import litellm
from litellm import aembedding, aimage_generation, chat_completions, completion
from litellm.types.utils import Choices, ModelResponse

from src.core.llm.exceptions import LLMConfigurationError, LLMRequestError

# 禁止 litellm 的默认重试（我们用 adapter 自带的 retry 机制）
litellm.max_retries = 0
litellm.num_retries = 0


class LiteLLMAdapter:
    """
    通过 LiteLLM 调用所有 LLM provider，统一 chat 接口。
    与旧 LLMFactory/LLMAdapter 解耦，专供 Agent Runtime 使用。
    """

    def __init__(
        self,
        model: str = "gpt-4o-mini",
        api_key: Optional[str] = None,
        base_url: Optional[str] = None,
        api_version: Optional[str] = None,
        timeout: Optional[float] = None,
        max_tokens: Optional[int] = None,
        temperature: float = 0.7,
        **kwargs: Any,
    ) -> None:
        self.model = model
        self.api_key = api_key or litellm.api_key  # 从环境变量读取
        self.base_url = base_url
        self.api_version = api_version
        self.timeout = timeout
        self.max_tokens = max_tokens
        self.temperature = temperature
        self._extra_kwargs = kwargs

    def _build_litellm_params(
        self,
        messages: List[Dict[str, Any]],
        tools: Optional[List[Dict[str, Any]]] = None,
        tool_choice: Optional[Union[str, Dict[str, Any]]] = None,
        **kwargs: Any,
    ) -> Dict[str, Any]:
        params: Dict[str, Any] = {
            "model": self.model,
            "messages": messages,
            "temperature": self.temperature,
            **self._extra_kwargs,
            **kwargs,
        }
        if self.api_key:
            params["api_key"] = self.api_key
        if self.base_url:
            params["base_url"] = self.base_url
        if self.api_version:
            params["api_version"] = self.api_version
        if self.timeout:
            params["timeout"] = self.timeout
        if self.max_tokens:
            params["max_tokens"] = self.max_tokens
        if tools:
            params["tools"] = tools
        if tool_choice:
            params["tool_choice"] = tool_choice
        return params

    async def chat(
        self,
        messages: List[Dict[str, Any]],
        tools: Optional[List[Dict[str, Any]]] = None,
        tool_choice: Optional[Union[str, Dict[str, Any]]] = None,
        **kwargs: Any,
    ) -> Dict[str, Any]:
        """
        发送 chat 请求，返回 {"role": "assistant", "content": str}
        如果 LLM 返回 tool_call，返回 {"role": "assistant", "tool_calls": [...]}
        """
        params = self._build_litellm_params(messages, tools, tool_choice, **kwargs)
        try:
            response: ModelResponse = await chat_completions(**params)
        except Exception as exc:
            raise LLMRequestError(f"LiteLLM chat failed: {exc}") from exc

        # 兼容不同响应格式
        choices: List[Choices] = getattr(response, "choices", [])
        if not choices:
            raise LLMRequestError("LiteLLM response has no choices")

        choice = choices[0]
        message = getattr(choice, "message", None)
        if message is None:
            raise LLMRequestError("LiteLLM response choice has no message")

        result: Dict[str, Any] = {
            "role": getattr(message, "role", "assistant"),
            "content": getattr(message, "content", ""),
        }

        # tool_calls
        tool_calls = getattr(message, "tool_calls", None)
        if tool_calls is not None:
            result["tool_calls"] = [
                {
                    "id": getattr(tc, "id", ""),
                    "type": getattr(tc, "type", "function"),
                    "function": {
                        "name": getattr(getattr(tc, "function", None) or MagicMock(), "name", ""),
                        "arguments": getattr(getattr(tc, "function", None) or MagicMock(), "arguments", "{}"),
                    },
                }
                for tc in tool_calls
            ]

        return result

    async def generate(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        **kwargs: Any,
    ) -> str:
        """单轮生成，用 prompt + 可选 system_prompt"""
        messages: List[Dict[str, Any]] = []
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        messages.append({"role": "user", "content": prompt})

        result = await self.chat(messages, **kwargs)
        return result.get("content", "")

    async def get_embedding(self, text: str, **kwargs: Any) -> List[float]:
        """通过 LiteLLM 获取文本 embedding"""
        try:
            response = await aembedding(
                model=self.model,
                input=text,
                api_key=self.api_key,
                base_url=self.base_url,
                **kwargs,
            )
        except Exception as exc:
            raise LLMRequestError(f"LiteLLM embedding failed: {exc}") from exc

        data = getattr(response, "data", [])
        if not data:
            raise LLMRequestError("LiteLLM embedding response has no data")
        embedding = getattr(data[0], "embedding", None)
        if embedding is None:
            raise LLMRequestError("LiteLLM embedding has no vector")
        return [float(x) for x in embedding]
```

> **注意**：上述代码中 `MagicMock` 需要 `from unittest.mock import MagicMock`，需要在文件顶部添加 import。

- [ ] **Step 4: 运行测试验证通过**

Run: `python -m pytest tests/unit/core/test_litellm_adapter.py -v`
Expected: PASS

- [ ] **Step 5: 提交**

```bash
git add src/core/llm/litellm_adapter.py tests/unit/core/test_litellm_adapter.py
git commit -m "feat: add LiteLLM adapter for unified LLM calls"
```

---

## Task 3: MemoryStore — Redis + ChromaDB 记忆存储

**Files:**
- Create: `tests/unit/core/runtime/test_memory_store.py`
- Modify: `src/core/runtime/memory_store.py`（替换占位内容）

- [ ] **Step 1: 写失败的测试**

```python
# tests/unit/core/runtime/test_memory_store.py
import pytest
from unittest.mock import MagicMock, AsyncMock, patch

from src.core.runtime.memory_store import MemoryStore, Turn, MemoryEntry

@pytest.fixture
def mock_redis():
    return MagicMock()

@pytest.fixture
def mock_chroma():
    return MagicMock()

@pytest.fixture
def memory(mock_redis, mock_chroma):
    with patch("src.core.runtime.memory_store.redis") as mock_redis_module, \
         patch("src.core.runtime.memory_store.chromadb") as mock_chroma_module:
        mock_redis_module.Redis.return_value = mock_redis
        mock_chroma_module.PersistentClient.return_value = mock_chroma
        store = MemoryStore(redis_client=mock_redis, chroma_client=mock_chroma)
        return store

def test_add_turn_stores_in_redis(memory, mock_redis):
    memory.add_turn("session-1", "user", "hello")
    mock_redis.rpush.assert_called_once()
    mock_redis.expire.assert_called_once()

def test_get_turns_returns_reversed_order(memory, mock_redis):
    mock_redis.lrange.return_value = [
        '{"role": "user", "content": "hi", "timestamp": "2026-01-01T00:00:00Z"}',
        '{"role": "assistant", "content": "hello", "timestamp": "2026-01-01T00:00:01Z"}',
    ]
    turns = memory.get_turns("session-1")
    assert len(turns) == 2
    assert turns[0].role == "user"
    assert turns[0].content == "hi"
    assert turns[1].role == "assistant"

def test_add_memory_calls_chroma(memory, mock_chroma):
    mock_collection = MagicMock()
    mock_chroma.get_or_create_collection.return_value = mock_collection
    memory.add_memory("session-1", "user submitted resume", {"source": "resume"})
    mock_collection.add.assert_called_once()
    call_args = mock_collection.add.call_args
    assert "user submitted resume" in call_args.kwargs["documents"]

def test_search_memory_returns_filtered_results(memory, mock_chroma):
    mock_collection = MagicMock()
    mock_collection.query.return_value = {
        "ids": [["mem-1"]],
        "documents": [["resume experience with Python"]],
        "metadatas": [[{"source": "resume"}]],
        "distances": [[0.3]],
    }
    mock_chroma.get_or_create_collection.return_value = mock_collection
    results = memory.search_memory("Python experience", session_id="session-1", threshold=0.5)
    assert len(results) == 1
    assert results[0].score == 0.3
    assert "Python" in results[0].content

def test_search_memory_filters_by_threshold(memory, mock_chroma):
    mock_collection = MagicMock()
    mock_collection.query.return_value = {
        "ids": [["mem-1", "mem-2"]],
        "documents": [["relevant content"], ["less relevant content"]],
        "metadatas": [[{}], {}],
        "distances": [[0.2], [0.9]],  # 0.9 > 0.7 threshold
    }
    mock_chroma.get_or_create_collection.return_value = mock_collection
    results = memory.search_memory("query", threshold=0.7)
    assert len(results) == 1
    assert results[0].score == 0.2

def test_clear_session_removes_redis_keys(memory, mock_redis):
    memory.clear_session("session-1")
    mock_redis.delete.assert_called()

def test_turn_namedtuple_fields():
    turn = Turn(role="user", content="hi", timestamp="2026-01-01T00:00:00Z")
    assert turn.role == "user"
    assert turn.content == "hi"

def test_memory_entry_namedtuple_fields():
    entry = MemoryEntry(id="mem-1", content="hello", metadata={"k": "v"}, score=0.5)
    assert entry.id == "mem-1"
    assert entry.score == 0.5
```

- [ ] **Step 2: 运行测试验证失败**

Run: `python -m pytest tests/unit/core/runtime/test_memory_store.py -v`
Expected: FAIL — `MemoryStore` 只有 `pass`

- [ ] **Step 3: 写 MemoryStore 实现**

```python
# src/core/runtime/memory_store.py
"""
记忆存储：短期会话记忆（Redis）+ 长期向量记忆（ChromaDB）
"""
from __future__ import annotations

import json
from datetime import datetime, timezone
from typing import Any, Dict, List, Literal, NamedTuple, Optional

import redis as redis_lib
import chromadb
from chromadb.config import Settings as ChromaSettings

TURNS_KEY_PREFIX = "agent:turns:"
TURNS_TTL_SECONDS = 7 * 24 * 3600  # 7 days
DEFAULT_COLLECTION = "agent_memory"


class Turn(NamedTuple):
    """一次对话回合"""
    role: str
    content: str
    timestamp: str


class MemoryEntry(NamedTuple):
    """一条长期记忆"""
    id: str
    content: str
    metadata: Dict[str, Any]
    score: float


class MemoryStore:
    """
    短期会话记忆（Redis）+ 长期向量记忆（ChromaDB）
    """

    def __init__(
        self,
        redis_client: Optional[redis_lib.Redis] = None,
        chroma_client: Optional[chromadb.PersistentClient] = None,
        collection_name: str = DEFAULT_COLLECTION,
        turns_ttl: int = TURNS_TTL_SECONDS,
    ) -> None:
        self._redis = redis_client
        self._chroma = chroma_client
        self._collection_name = collection_name
        self._turns_ttl = turns_ttl

    def _redis_key(self, session_id: str) -> str:
        return f"{TURNS_KEY_PREFIX}{session_id}"

    def _now_iso(self) -> str:
        return datetime.now(timezone.utc).isoformat()

    # --- 短期会话记忆 ---

    def add_turn(self, session_id: str, role: str, content: str) -> None:
        """往 Redis 存储一条对话"""
        if self._redis is None:
            return
        key = self._redis_key(session_id)
        turn_data = json.dumps({"role": role, "content": content, "timestamp": self._now_iso()})
        self._redis.rpush(key, turn_data)
        self._redis.expire(key, self._turns_ttl)

    def get_turns(self, session_id: str, limit: int = 20) -> list[Turn]:
        """从 Redis 取最近 N 条对话"""
        if self._redis is None:
            return []
        key = self._redis_key(session_id)
        raw = self._redis.lrange(key, -limit, -1)
        turns = []
        for item in raw:
            try:
                data = json.loads(item) if isinstance(item, str) else json.loads(item.decode())
                turns.append(Turn(
                    role=data.get("role", ""),
                    content=data.get("content", ""),
                    timestamp=data.get("timestamp", ""),
                ))
            except Exception:
                continue
        return turns

    def clear_session(self, session_id: str) -> None:
        """清除会话的所有记忆"""
        if self._redis:
            self._redis.delete(self._redis_key(session_id))

    # --- 长期向量记忆 ---

    def _get_collection(self):
        if self._chroma is None:
            return None
        return self._chroma.get_or_create_collection(
            name=self._collection_name,
            metadata={"description": "Agent long-term memory"},
        )

    def add_memory(
        self,
        session_id: str,
        content: str,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> str:
        """往 ChromaDB 存储一条记忆，返回 memory_id"""
        collection = self._get_collection()
        if collection is None:
            return ""
        import uuid
        memory_id = str(uuid.uuid4())
        collection.add(
            ids=[memory_id],
            documents=[content],
            metadatas=[{**(metadata or {}), "session_id": session_id}],
        )
        return memory_id

    def search_memory(
        self,
        query: str,
        session_id: Optional[str] = None,
        top_k: int = 5,
        threshold: float = 0.7,
    ) -> list[MemoryEntry]:
        """在 ChromaDB 中检索记忆，返回相似度 >= threshold 的结果"""
        collection = self._get_collection()
        if collection is None:
            return []

        where_filter = {"session_id": session_id} if session_id else None

        results = collection.query(
            query_texts=[query],
            n_results=top_k,
            where=where_filter,
        )

        ids: List[List[str]] = results.get("ids", [])
        docs: List[List[str]] = results.get("documents", [])
        metas: List[List[Dict]] = results.get("metadatas", [])
        dists: List[List[float]] = results.get("distances", [])

        if not ids or not ids[0]:
            return []

        entries = []
        for i, (mid, doc, meta, dist) in enumerate(zip(ids[0], docs[0], metas[0], dists[0])):
            # ChromaDB distances are L2 distance; convert to similarity-like score
            # distance 0 = identical, max ~2 (L2 of normalized vectors)
            # We use 1 - normalized_distance as similarity
            similarity = max(0.0, 1.0 - dist)
            if similarity >= threshold:
                entries.append(MemoryEntry(
                    id=mid,
                    content=doc,
                    metadata=meta or {},
                    score=round(similarity, 4),
                ))
        return entries

    def delete_memory(self, memory_id: str) -> None:
        """从 ChromaDB 删除一条记忆"""
        collection = self._get_collection()
        if collection:
            collection.delete(ids=[memory_id])
```

- [ ] **Step 4: 运行测试验证通过**

Run: `python -m pytest tests/unit/core/runtime/test_memory_store.py -v`
Expected: PASS（9 tests）

- [ ] **Step 5: 提交**

```bash
git add src/core/runtime/memory_store.py tests/unit/core/runtime/test_memory_store.py
git commit -m "feat: implement MemoryStore with Redis (session) + ChromaDB (vector)"
```

---

## Task 4: ContextBuilder — RAG 上下文构建

**Files:**
- Create: `tests/unit/core/runtime/test_context_builder.py`
- Modify: `src/core/runtime/context_builder.py`（替换占位内容）

- [ ] **Step 1: 写失败的测试**

```python
# tests/unit/core/runtime/test_context_builder.py
import pytest
from unittest.mock import MagicMock, AsyncMock, patch

from src.core.runtime.context_builder import ContextBuilder
from src.core.runtime.memory_store import Turn, MemoryEntry

@pytest.fixture
def mock_memory():
    memory = MagicMock()
    memory.get_turns = MagicMock(return_value=[
        Turn(role="user", content="I want to customize my resume", timestamp="2026-01-01T00:00:00Z"),
        Turn(role="assistant", content="Please paste your JD", timestamp="2026-01-01T00:00:01Z"),
    ])
    memory.search_memory = AsyncMock(return_value=[
        MemoryEntry(id="mem-1", content="user has Python experience", metadata={}, score=0.85),
    ])
    return memory

@pytest.fixture
def builder(mock_memory):
    return ContextBuilder(memory=mock_memory)

def test_build_includes_system_prompt(builder):
    messages = builder.build_sync("session-1", "You are a helpful assistant")
    assert messages[0]["role"] == "system"
    assert "helpful assistant" in messages[0]["content"]

def test_build_includes_turns(builder, mock_memory):
    messages = builder.build_sync("session-1", "You are a helpful assistant")
    roles = [m["role"] for m in messages]
    contents = [m["content"] for m in messages]
    assert "user" in roles
    assert "I want to customize my resume" in contents
    assert "Please paste your JD" in contents

def test_build_includes_memory_results(builder, mock_memory):
    messages = builder.build_sync("session-1", "You are a helpful assistant")
    # memory content should be included
    full_content = " ".join(m["content"] for m in messages)
    assert "Python experience" in full_content

def test_build_respects_max_turns_limit(builder, mock_memory):
    mock_memory.get_turns = MagicMock(return_value=[
        Turn(role="user", content=f"turn {i}", timestamp="2026-01-01T00:00:00Z")
        for i in range(10)
    ])
    messages = builder.build_sync("session-1", "system prompt", max_turns=5)
    # Should only include last 5 turns
    user_turns = [m for m in messages if m["role"] == "user"]
    assert len(user_turns) == 5

def test_build_no_memory_below_threshold(builder, mock_memory):
    mock_memory.search_memory = AsyncMock(return_value=[
        MemoryEntry(id="mem-1", content="low relevance", metadata={}, score=0.4),  # below 0.7
    ])
    messages = builder.build_sync("session-1", "system prompt", memory_threshold=0.7)
    full_content = " ".join(m["content"] for m in messages)
    assert "low relevance" not in full_content
```

- [ ] **Step 2: 运行测试验证失败**

Run: `python -m pytest tests/unit/core/runtime/test_context_builder.py -v`
Expected: FAIL — `ContextBuilder` 只有 `pass`

- [ ] **Step 3: 写 ContextBuilder 实现**

```python
# src/core/runtime/context_builder.py
"""
RAG 上下文构建器
从 MemoryStore 组装 LLM 可用的 messages
"""
from __future__ import annotations

from typing import Any, AsyncIterator, List, Optional

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
        for turn in turns:
            messages.append({"role": turn.role, "content": turn.content})

        # 2. 从 ChromaDB 检索相关记忆（同步版本）
        try:
            import asyncio
            memory_results = asyncio.get_event_loop().run_until_complete(
                self._memory.search_memory(
                    query=system_prompt,
                    session_id=session_id,
                    top_k=max_memory_results,
                    threshold=memory_threshold,
                )
            )
        except Exception:
            memory_results = []

        # 3. 将记忆片段注入为 system 补充
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
        if memory_results:
            memory_context = "\n\n".join(
                f"[相关记忆 {r.score:.2f}]: {r.content}"
                for r in memory_results
            )
            messages[0]["content"] = (
                f"{system_prompt}\n\n以下是与当前任务相关的历史上下文：\n{memory_context}"
            )

        return messages
```

- [ ] **Step 4: 运行测试验证通过**

Run: `python -m pytest tests/unit/core/runtime/test_context_builder.py -v`
Expected: PASS（5 tests）

- [ ] **Step 5: 提交**

```bash
git add src/core/runtime/context_builder.py tests/unit/core/runtime/test_context_builder.py
git commit -m "feat: implement ContextBuilder for RAG context assembly"
```

---

## Task 5: ToolRegistry + BaseTool

**Files:**
- Modify: `src/core/tools/base_tool.py`（替换占位内容）
- Modify: `src/core/runtime/tool_registry.py`（替换占位内容）
- Create: `src/core/tools/langchain_tools.py`
- Create: `tests/unit/core/runtime/test_tool_registry.py`

- [ ] **Step 1: 写失败的测试**

```python
# tests/unit/core/runtime/test_tool_registry.py
import pytest
from unittest.mock import MagicMock

from src.core.tools.base_tool import BaseTool
from src.core.runtime.tool_registry import ToolRegistry


class MockToolInput:
    pass  # simplified


class FakeTool(BaseTool):
    name: str = "fake_tool"
    description: str = "A fake tool for testing"

    def _run(self, tool_input: dict, runtime=None) -> dict:
        return {"result": f"fake result for {tool_input.get('input', '')}"}


@pytest.fixture
def registry():
    return ToolRegistry()


def test_register_adds_tool(registry):
    tool = FakeTool()
    registry.register(tool)
    assert registry.get_tool("fake_tool") is tool


def test_get_tool_not_found_raises(registry):
    with pytest.raises(ValueError, match="Tool.*not found"):
        registry.get_tool("nonexistent")


def test_list_tools_returns_schemas(registry):
    tool = FakeTool()
    registry.register(tool)
    schemas = registry.list_tools()
    assert len(schemas) == 1
    assert schemas[0]["name"] == "fake_tool"
    assert schemas[0]["description"] == "A fake tool for testing"


def test_get_schemas_for_llm(registry):
    tool = FakeTool()
    registry.register(tool)
    schemas = registry.get_schemas()
    assert len(schemas) == 1
    assert schemas[0]["type"] == "function"
    assert "fake_tool" in schemas[0]["function"]["name"]


def test_execute_tool_calls_run(registry):
    tool = FakeTool()
    registry.register(tool)
    result = registry.execute("fake_tool", {"input": "test"})
    assert result["result"] == "fake result for test"


def test_execute_unknown_tool_raises(registry):
    with pytest.raises(ValueError, match="Tool.*not found"):
        registry.execute("unknown_tool", {})
```

- [ ] **Step 2: 运行测试验证失败**

Run: `python -m pytest tests/unit/core/runtime/test_tool_registry.py -v`
Expected: FAIL — `ToolRegistry` 和 `BaseTool` 只有 `pass`

- [ ] **Step 3: 写 BaseTool 实现**

```python
# src/core/tools/base_tool.py
"""
统一工具基类
继承 LangChain Core 的 BaseTool，统一工具接口
"""
from __future__ import annotations

from typing import Any, Dict, Optional, Type

from langchain_core.callbacks import CallbackManagerForToolRun
from langchain_core.tools import BaseTool as LangChainBaseTool
from pydantic import BaseModel, Field


class ToolInput(BaseModel):
    """工具输入 Schema 基类"""
    pass


class BaseTool(LangChainBaseTool):
    """
    统一工具基类，继承 LangChain BaseTool
    所有领域工具都应继承此类
    """

    runtime: Optional[Any] = Field(default=None, exclude=True)
    # runtime 由 AgentExecutor 注入，不传递给 LLM

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
```

```python
# src/core/tools/langchain_tools.py
"""
LangChain @tool 装饰器辅助函数
提供从 @tool 装饰器函数转换为 BaseTool 的能力
"""
from __future__ import annotations

from typing import Any, Callable, Dict, Type

from langchain_core.tools import convert_to_openai_tool

from src.core.tools.base_tool import BaseTool


def langchain_tool_to_basetool(
    langchain_tool: Any,
    runtime: Any = None,
) -> BaseTool:
    """
    将 LangChain @tool 装饰器创建的工具转换为我们的 BaseTool
    包装后保持统一接口
    """

    class WrappedBaseTool(BaseTool):
        name: str = langchain_tool.name
        description: str = langchain_tool.description

        def _execute_sync(self, tool_input: Dict[str, Any], runtime: Any = None) -> Dict[str, Any]:
            result = langchain_tool.invoke(tool_input, config={"tool_call": True})
            if isinstance(result, str):
                return {"result": result}
            return result if isinstance(result, dict) else {"result": result}

    return WrappedBaseTool()


def get_openai_tool_schemas(tools: list[BaseTool]) -> list[Dict[str, Any]]:
    """
    从 BaseTool 列表生成 OpenAI function calling 格式的 schemas
    """
    return [convert_to_openai_tool(tool) for tool in tools]
```

- [ ] **Step 4: 写 ToolRegistry 实现**

```python
# src/core/runtime/tool_registry.py
"""
工具注册表
负责工具的注册、发现、schema 导出
"""
from __future__ import annotations

from typing import Any, Dict, List, Optional

from src.core.tools.base_tool import BaseTool


class ToolRegistry:
    """
    全局工具注册表
    """

    def __init__(self) -> None:
        self._tools: Dict[str, BaseTool] = {}

    def register(self, tool: BaseTool) -> None:
        if not tool.name:
            raise ValueError("Tool must have a name")
        if tool.name in self._tools:
            raise ValueError(f"Tool '{tool.name}' is already registered")
        self._tools[tool.name] = tool

    def get_tool(self, name: str) -> BaseTool:
        tool = self._tools.get(name)
        if tool is None:
            raise ValueError(f"Tool '{name}' not found")
        return tool

    def list_tools(self) -> List[Dict[str, Any]]:
        """返回所有工具的描述性信息列表"""
        return [
            {
                "name": tool.name,
                "description": tool.description,
                "args_schema": tool.args_schema.schema() if tool.args_schema else {},
            }
            for tool in self._tools.values()
        ]

    def get_schemas(self) -> List[Dict[str, Any]]:
        """
        返回 LangChain / OpenAI function calling 格式的 tool schemas
        用于 llm.chat(tools=get_schemas())
        """
        return [
            {
                "type": "function",
                "function": {
                    "name": tool.name,
                    "description": tool.description,
                    "parameters": tool.args_schema.schema() if tool.args_schema else {
                        "type": "object",
                        "properties": {},
                        "required": [],
                    },
                },
            }
            for tool in self._tools.values()
        ]

    def execute(self, name: str, tool_input: Dict[str, Any], runtime: Any = None) -> Any:
        """执行工具，返回结果"""
        tool = self.get_tool(name)
        return tool._run(tool_input, runtime=runtime)
```

- [ ] **Step 5: 运行测试验证通过**

Run: `python -m pytest tests/unit/core/runtime/test_tool_registry.py -v`
Expected: PASS（6 tests）

- [ ] **Step 6: 提交**

```bash
git add src/core/tools/base_tool.py src/core/tools/langchain_tools.py src/core/runtime/tool_registry.py tests/unit/core/runtime/test_tool_registry.py
git commit -m "feat: implement ToolRegistry and BaseTool with LangChain integration"
```

---

## Task 6: AgentExecutor — ReAct 执行循环

**Files:**
- Modify: `src/core/runtime/agent_executor.py`（替换占位内容）
- Create: `tests/unit/core/runtime/test_agent_executor.py`

- [ ] **Step 1: 写失败的测试**

```python
# tests/unit/core/runtime/test_agent_executor.py
import pytest
from unittest.mock import MagicMock, AsyncMock, patch

from src.core.runtime.agent_executor import AgentExecutor
from src.core.runtime.state_machine import StateMachine
from src.core.runtime.memory_store import MemoryStore, Turn
from src.core.runtime.context_builder import ContextBuilder
from src.core.runtime.tool_registry import ToolRegistry


@pytest.fixture
def mock_llm():
    llm = MagicMock()
    llm.chat = AsyncMock(return_value={"role": "assistant", "content": "Hello, how can I help?"})
    return llm


@pytest.fixture
def mock_memory():
    memory = MagicMock(spec=MemoryStore)
    memory.get_turns = MagicMock(return_value=[])
    memory.add_turn = MagicMock()
    return memory


@pytest.fixture
def mock_context_builder():
    builder = MagicMock(spec=ContextBuilder)
    builder.build_sync = MagicMock(return_value=[
        {"role": "system", "content": "You are a helpful assistant."}
    ])
    return builder


@pytest.fixture
def executor(mock_llm, mock_memory, mock_context_builder):
    sm = StateMachine()
    registry = ToolRegistry()
    return AgentExecutor(
        llm=mock_llm,
        tools=registry,
        memory=mock_memory,
        state_machine=sm,
        context_builder=mock_context_builder,
    )


def test_executor_initial_state(executor):
    assert executor._state_machine.get_state() == "idle"


def test_executor_stores_dependencies(executor, mock_llm, mock_memory, mock_context_builder):
    assert executor._llm is mock_llm
    assert executor._memory is mock_memory
    assert executor._context_builder is mock_context_builder


@pytest.mark.asyncio
async def test_execute_yields_text_response(executor, mock_llm, mock_context_builder):
    mock_llm.chat.return_value = {"role": "assistant", "content": "Done!"}
    results = []
    async for chunk in executor.execute("Hello", "session-1"):
        results.append(chunk)
    assert "".join(results) == "Done!"
    assert executor._state_machine.get_state() == "done"


@pytest.mark.asyncio
async def test_execute_calls_context_builder(executor, mock_context_builder):
    mock_llm.chat.return_value = {"role": "assistant", "content": "Hi"}
    async for _ in executor.execute("Hi", "session-1", system_prompt="You are a tutor"):
        pass
    mock_context_builder.build_sync.assert_called()
    call_args = mock_context_builder.build_sync.call_args
    assert call_args[0][0] == "session-1"
    assert "tutor" in call_args[0][1]


@pytest.mark.asyncio
async def test_execute_adds_turns_to_memory(executor, mock_memory):
    mock_llm.chat.return_value = {"role": "assistant", "content": "Reply"}
    async for _ in executor.execute("Hi", "session-1"):
        pass
    assert mock_memory.add_turn.call_count >= 2  # user turn + assistant turn


@pytest.mark.asyncio
async def test_execute_transitions_state(executor):
    mock_llm.chat.return_value = {"role": "assistant", "content": "Result"}
    states = []
    async for _ in executor.execute("task", "session-1"):
        states.append(executor._state_machine.get_state())
    assert "idle" in states[0] if states else True
    assert executor._state_machine.get_state() == "done"
```

- [ ] **Step 2: 运行测试验证失败**

Run: `python -m pytest tests/unit/core/runtime/test_agent_executor.py -v`
Expected: FAIL — `AgentExecutor` 只有 `pass`

- [ ] **Step 3: 写 AgentExecutor 实现**

```python
# src/core/runtime/agent_executor.py
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
      3a. tool_call  — 执行工具，获取 observation，回到 planning
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
```

- [ ] **Step 4: 运行测试验证通过**

Run: `python -m pytest tests/unit/core/runtime/test_agent_executor.py -v`
Expected: PASS（6 tests）

- [ ] **Step 5: 提交**

```bash
git add src/core/runtime/agent_executor.py tests/unit/core/runtime/test_agent_executor.py
git commit -m "feat: implement AgentExecutor ReAct loop"
```

---

## Task 7: 添加 litellm 依赖 + 目录初始化

**Files:**
- Modify: `requirements.txt`
- 创建目录: `tests/unit/core/runtime/__init__.py`

- [ ] **Step 1: 更新 requirements.txt**

在 requirements.txt 末尾添加：
```
# Agent Runtime
litellm>=1.0.0
langchain-core>=0.3.0
langchain-community>=0.2.0
```

- [ ] **Step 2: 创建测试目录 __init__.py**

```bash
# tests/unit/core/runtime/__init__.py
# tests/unit/core/__init__.py
# tests/unit/core/runtime/.gitkeep 都不是 Python 包，只是不含 __init__.py 的目录
# 跳过，创建实际的 __init__.py 以便 pytest 能收集测试
```

Write: `tests/unit/core/runtime/__init__.py`
```python
"""Core runtime unit tests"""
```

Write: `tests/unit/core/__init__.py`
```python
"""Core module unit tests"""
```

- [ ] **Step 3: 验证所有测试通过**

Run: `python -m pytest tests/unit/core/runtime/ tests/unit/core/test_litellm_adapter.py -v --tb=short`
Expected: 全部 PASS

- [ ] **Step 4: 提交**

```bash
git add requirements.txt tests/unit/core/runtime/__init__.py tests/unit/core/__init__.py
git commit -m "chore: add litellm, langchain-core, langchain-community to requirements"
```

---

## Task 8: 集成测试 — 端到端 ReAct 循环

**Files:**
- Create: `tests/integration/runtime/test_agent_executor_integration.py`

- [ ] **Step 1: 写集成测试**

```python
# tests/integration/runtime/test_agent_executor_integration.py
"""
端到端集成测试：验证完整的 ReAct 循环
使用 mock LLM，验证状态流转和工具调用
"""
import pytest
from unittest.mock import MagicMock, AsyncMock

from src.core.runtime.agent_executor import AgentExecutor
from src.core.runtime.state_machine import StateMachine
from src.core.runtime.memory_store import MemoryStore
from src.core.runtime.context_builder import ContextBuilder
from src.core.runtime.tool_registry import ToolRegistry
from src.core.llm.litellm_adapter import LiteLLMAdapter
from src.core.tools.base_tool import BaseTool


class DummyToolInput:
    pass


class EchoTool(BaseTool):
    name: str = "echo"
    description: str = "Echoes back the input"

    def _execute_sync(self, tool_input: dict, runtime=None) -> dict:
        return {"echoed": tool_input.get("message", "")}


@pytest.fixture
def memory_store():
    redis_mock = MagicMock()
    redis_mock.rpush = MagicMock()
    redis_mock.expire = MagicMock()
    redis_mock.lrange = MagicMock(return_value=[])
    redis_mock.delete = MagicMock()

    chroma_mock = MagicMock()
    return MemoryStore(redis_client=redis_mock, chroma_client=chroma_mock)


@pytest.fixture
def tool_registry():
    registry = ToolRegistry()
    registry.register(EchoTool())
    return registry


@pytest.mark.asyncio
async def test_react_loop_with_tool_call(memory_store, tool_registry):
    """验证 ReAct 循环中工具调用的完整流程"""
    # 状态机
    sm = StateMachine()

    # Mock LLM：第一次返回 tool_call，第二次返回文本
    call_count = 0
    async def mock_chat(messages, tools=None, **kwargs):
        nonlocal call_count
        call_count += 1
        if call_count == 1:
            # LLM 选择调用工具
            return {
                "role": "assistant",
                "content": "",
                "tool_calls": [{
                    "id": "call-1",
                    "type": "function",
                    "function": {
                        "name": "echo",
                        "arguments": '{"message": "hello world"}',
                    },
                }],
            }
        else:
            return {"role": "assistant", "content": "Tool returned: hello world"}

    mock_llm = MagicMock(spec=LiteLLMAdapter)
    mock_llm.chat = mock_chat

    # Context builder
    context_builder = MagicMock(spec=ContextBuilder)
    context_builder.build_sync = MagicMock(return_value=[
        {"role": "system", "content": "You are a test agent."}
    ])

    executor = AgentExecutor(
        llm=mock_llm,
        tools=tool_registry,
        memory=memory_store,
        state_machine=sm,
        context_builder=context_builder,
    )

    results = []
    async for chunk in executor.execute("test task", "session-1"):
        results.append(chunk)

    # 验证最终状态
    assert sm.get_state() == "done"
    # 验证 LLM 被调用了 2 次（tool → text）
    assert call_count == 2
    # 验证返回了工具结果
    assert any("hello world" in r for r in results)


@pytest.mark.asyncio
async def test_react_loop_text_only(memory_store, tool_registry):
    """验证纯文本响应（无工具调用）的 ReAct 循环"""
    sm = StateMachine()

    mock_llm = MagicMock(spec=LiteLLMAdapter)
    mock_llm.chat = AsyncMock(return_value={
        "role": "assistant",
        "content": "This is a direct answer.",
    })

    context_builder = MagicMock(spec=ContextBuilder)
    context_builder.build_sync = MagicMock(return_value=[
        {"role": "system", "content": "You are a test agent."}
    ])

    executor = AgentExecutor(
        llm=mock_llm,
        tools=tool_registry,
        memory=memory_store,
        state_machine=sm,
        context_builder=context_builder,
    )

    results = []
    async for chunk in executor.execute("what is 2+2", "session-2"):
        results.append(chunk)

    assert "".join(results) == "This is a direct answer."
    assert sm.get_state() == "done"
    assert mock_llm.chat.call_count == 1
```

- [ ] **Step 2: 运行集成测试**

Run: `python -m pytest tests/integration/runtime/test_agent_executor_integration.py -v --tb=short`
Expected: PASS

- [ ] **Step 3: 提交**

```bash
git add tests/integration/runtime/test_agent_executor_integration.py
git commit -m "test: add integration test for ReAct loop with tool calls"
```

---

## 依赖顺序

```
Task 1: StateMachine        ← 最基础无依赖
Task 2: LiteLLMAdapter      ← 被 Task 6 调用
Task 3: MemoryStore         ← 被 Task 4、6 调用
Task 4: ContextBuilder      ← 被 Task 6 调用
Task 5: ToolRegistry+BaseTool ← 被 Task 6 调用
Task 6: AgentExecutor       ← 组合以上所有
Task 7: 依赖添加+验证       ← 收尾
Task 8: 集成测试            ← 验证完整循环
```

## 验收标准

- [ ] StateMachine 状态流转正确，无效转换抛出 ValueError
- [ ] LiteLLMAdapter.chat() 支持 tools 参数，返回 tool_calls
- [ ] MemoryStore Redis 存/取 turn 正常，ChromaDB 检索按 threshold 过滤
- [ ] ContextBuilder 组装 messages 包含 system + turns + memory context
- [ ] ToolRegistry.register/get/execute/get_schemas 全部正常
- [ ] AgentExecutor ReAct 循环：tool_call → 执行 → observation → 继续；text → yield → done
- [ ] 集成测试：完整 ReAct 循环端到端通过
