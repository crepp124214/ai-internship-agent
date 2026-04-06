# Architecture

## 目的

本文件把 `internship-design-document.md` 的目标架构映射到当前仓库，作为执行层架构说明。

## 源文档

- 设计源文档：`internship-design-document.md`
- 技术栈源文档：`tech-stack.md`

## 当前到目标的映射

### 当前核心层

- `src/presentation/`
  - 负责 API、请求响应、Schema、依赖注入、认证与错误转换
- `src/business_logic/`
  - 负责业务流程、服务编排、领域能力
- `src/data_access/`
  - 负责实体、仓储、持久化
- `src/core/`
  - 负责共享 LLM 能力、运行时基础能力、通用抽象

### 目标增强层

根据设计文档，后续应逐步补齐：

- `src/core/runtime/`
  - `agent_executor`
  - `tool_registry`
  - `state_machine`
  - `memory_store`
  - `context_builder`
- `src/core/tools/`
  - 统一工具抽象与领域工具集
- `src/business_logic/jd/`
  - JD 解析、匹配、定制化能力
- `src/business_logic/interview/`
  - AI 面试会话、评分、复盘能力

## 前端映射

- `frontend/src/app/`
  - 应用装配与路由
- `frontend/src/auth/`
  - 鉴权与登录态
- `frontend/src/pages/`
  - 页面级入口
- `frontend/src/lib/`
  - 共享基础能力

目标上会逐步向设计文档中的 Agent Workspace 靠拢，但当前阶段不直接实现完整形态。

## 当前结构原则

- API 层不下沉到 Repository
- 业务逻辑不下沉到路由层
- `core` 不承载领域业务
- 所有新能力都要为后续 LangChain + LangGraph 路线兼容

## 当前重点变更

1. 识别并移除 `Tracker` 相关结构
2. 保留并稳定基础域
3. 为 `JD 定制简历` 和 `AI 面试官对练` 预留目录与职责边界
4. 逐步把 LLM 调用统一到共享抽象层

## Agent Runtime 详细设计

> 状态：已设计，待实现 | 日期：2026-04-07

### 架构概览

```
src/core/runtime/
├── agent_executor.py     # ReAct 执行循环
├── tool_registry.py     # 工具注册与发现
├── state_machine.py     # Agent 执行状态管理
├── memory_store.py      # Redis(会话) + ChromaDB(向量)
└── context_builder.py   # RAG 上下文构建

src/core/tools/
├── base_tool.py         # LangChain BaseTool 封装
└── langchain_tools.py   # LangChain @tool 装饰器工具定义

src/core/llm/
└── litellm_adapter.py   # LiteLLM 统一 adapter（新增）
```

### 设计决策

| 决策项 | 选择 | 理由 |
|--------|------|------|
| LLM 调用层 | LiteLLM | 统一接口，支持所有主流 provider，切换模型改配置即可 |
| Tool 定义 | LangChain @tool | 原生 function calling 支持，Executor 直接对接 |
| StateMachine | 只管 Agent 执行状态 | idle→planning→tool_use→responding→done |
| 短期记忆 | Redis | 快速存取会话上下文 |
| 长期记忆 | ChromaDB | 向量相似度检索，RAG 核心 |
| RAG 检索 | 纯向量相似度 | threshold 过滤，无需复杂混合检索 |

### 1. LiteLLM Adapter（新增）

文件：`src/core/llm/litellm_adapter.py`

```python
class LiteLLMAdapter:
    """通过 litellm 调用所有 LLM provider，统一接口"""

    async def chat(
        self,
        messages: list[dict],
        tools: list[dict] | None = None,
        model: str | None = None,
        **kwargs
    ) -> LLMResponse: ...

    async def generate(
        self,
        prompt: str,
        system_prompt: str | None = None,
        **kwargs
    ) -> str: ...
```

**与现有 LLMFactory 的关系：**
- 现有 `LLMFactory` + 各 adapter 保持不动，确保向后兼容
- 新 `LiteLLMAdapter` 专供 Runtime 使用，与旧系统隔离
- 后续 JD/Interview Agent 可逐步迁移到新 adapter

### 2. ToolRegistry + BaseTool

文件：`src/core/tools/base_tool.py`

```python
from langchain_core.tools import BaseTool as LangChainBaseTool
from pydantic import BaseModel

class ToolInput(BaseModel):
    """工具输入 Schema 基类"""
    pass

class BaseTool(LangChainBaseTool):
    """统一工具基类，继承 LangChain BaseTool"""

    name: str
    description: str
    args_schema: Type[BaseModel]

    def _run(self, tool_input: dict, runtime: "AgentRuntime") -> dict: ...
    async def _arun(self, tool_input: dict, runtime: "AgentRuntime") -> dict: ...
```

文件：`src/core/runtime/tool_registry.py`

```python
class ToolRegistry:
    """全局工具注册表"""

    def register(self, tool: BaseTool) -> None: ...
    def get_tool(self, name: str) -> BaseTool: ...
    def list_tools(self) -> list[dict]: ...  # 返回 [{name, description, schema}, ...]
    def get_schemas(self) -> list[dict]: ...  # 返回 LangChain 格式 tool schemas
```

### 3. AgentExecutor — ReAct 循环

文件：`src/core/runtime/agent_executor.py`

```python
class AgentExecutor:
    """
    ReAct (Reasoning + Acting) 执行器
    状态流转：idle → planning → tool_use → responding → done
    """

    def __init__(
        self,
        llm: LiteLLMAdapter,
        tools: ToolRegistry,
        memory: "MemoryStore",
        state_machine: "StateMachine",
        context_builder: "ContextBuilder",
    ): ...

    async def execute(
        self,
        task: str,
        session_id: str,
        system_prompt: str | None = None,
    ) -> AsyncIterator[str]:
        """
        执行任务，yield 每一步的文本输出
        """
        # ReAct 循环:
        # 1. state_machine.transition("planning")
        # 2. context_builder.build() → messages
        # 3. llm.chat(messages, tools=registry.get_schemas())
        # 4a. 如果是 tool_call → registry.execute(name, args) → observation → 回到步骤1
        # 4b. 如果是 text → yield → state_machine.transition("done")
```

### 4. StateMachine

文件：`src/core/runtime/state_machine.py`

```python
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

    def __init__(self): ...
    def transition(self, to: str, reason: str | None = None) -> None: ...
    def get_state(self) -> str: ...
    def get_history(self) -> list[StateTransition]: ...
    def reset(self) -> None: ...
```

### 5. MemoryStore

文件：`src/core/runtime/memory_store.py`

```python
class Turn(NamedTuple):
    """一次对话回合"""
    role: str      # "user" | "assistant" | "system"
    content: str
    timestamp: datetime

class MemoryEntry(NamedTuple):
    """一条长期记忆"""
    id: str
    content: str
    metadata: dict
    score: float   # 向量相似度分数

class MemoryStore:
    """
    短期会话记忆（Redis）+ 长期向量记忆（ChromaDB）
    """

    def __init__(self, redis_client, chroma_client, collection_name: str = "agent_memory"): ...

    # --- 短期会话记忆 ---
    def add_turn(self, session_id: str, role: str, content: str) -> None: ...
    def get_turns(self, session_id: str, limit: int = 20) -> list[Turn]: ...
    def clear_session(self, session_id: str) -> None: ...

    # --- 长期向量记忆 ---
    def add_memory(
        self,
        session_id: str,
        content: str,
        metadata: dict | None = None,
    ) -> str: ...  # 返回 memory_id

    def search_memory(
        self,
        query: str,
        session_id: str | None = None,
        top_k: int = 5,
        threshold: float = 0.7,
    ) -> list[MemoryEntry]: ...

    def delete_memory(self, memory_id: str) -> None: ...
```

### 6. ContextBuilder

文件：`src/core/runtime/context_builder.py`

```python
class ContextBuilder:
    """
    RAG 上下文构建器
    负责从 MemoryStore 组装 LLM 可用的 messages
    """

    def __init__(self, memory: MemoryStore): ...

    async def build(
        self,
        session_id: str,
        system_prompt: str,
        max_turns: int = 20,
        max_memory_results: int = 5,
        memory_threshold: float = 0.7,
    ) -> list[dict[str, str]]:
        """
        返回格式化的 messages 列表
        [
            {"role": "system", "content": "..."},
            {"role": "user", "content": "..."},
            ...
        ]
        """
        # 1. 从 Redis 取最近 max_turns 轮对话
        # 2. 从 ChromaDB 检索相关历史记忆（相似度 > threshold）
        # 3. 组装 messages，记忆片段插入为补充 context
```

## 更新规则

- 每完成一个重构里程碑，更新本文件
- 如果仓库结构与设计方案出现偏差，先更新本文件记录，再推进实现
