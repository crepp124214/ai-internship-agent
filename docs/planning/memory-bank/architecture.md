# Architecture

## 目的

本文件把 `internship-design-document.md` 的目标架构映射到当前仓库，作为执行层架构说明。

## 源文档

- 设计源文档：`internship-design-document.md`
- 技术栈源文档：`tech-stack.md`

## 当前核心层

- `src/presentation/`
  - 负责 API、请求响应、Schema、依赖注入、认证与错误转换
- `src/business_logic/`
  - 负责业务流程、服务编排、领域能力
- `src/data_access/`
  - 负责实体、仓储、持久化
- `src/core/`
  - 负责共享 LLM 能力、运行时基础能力、通用抽象

## 目标增强层

根据设计文档，后续应逐步补齐：

- `src/core/runtime/`
  - `agent_executor` — ReAct 执行循环
  - `tool_registry` — 工具注册与发现
  - `state_machine` — Agent 执行状态管理
  - `memory_store` — Redis(会话) + ChromaDB(向量)
  - `context_builder` — RAG 上下文构建
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

## 已完成重点变更

| 变更 | 状态 | 提交 |
|------|------|------|
| Tracker 路由入口断开 | ✅ | `c760ee2` |
| Tracker 残留代码物理删除（Phase 12） | ✅ | `2026-04-07` |
| 基础域稳定（用户/简历/岗位/面试） | ✅ | Phase 1 |
| Agent Runtime Phase 1 实现（含 Memory & State） | ✅ | Phase 2 |
| JD 定制简历功能 | ✅ | Phase 3 |
| Interview Coach 多轮对练 | ✅ | Phase 4 |
| Test & Tools 增强 | ✅ | Phase 5 |
| Agent Workspace 前端 | ✅ | Phase 6 |
| Docker 多环境配置 | ✅ | Phase 9 |
| P0: 架构违规修复（工具层禁止从 presentation 导入） | ✅ | `db57d6f` |
| P0: Exception swallowing 修复 | ✅ | `d2ad37c` |
| 测试修复（Phase 13） | ✅ | `2026-04-07` |
| 用户体验流程 v2.0 设计（Phase 14） | ✅ | `2026-04-08` |
| Phase 15 前端页面重构（设置中心/岗位/简历/面试） | ✅ | `9767fd5`（2026-04-09合并）|

## 用户体验流程 v2.0（Phase 14 设计）

### 页面架构

| 页面 | 路由 | 核心职责 |
|------|------|----------|
| 仪表盘 | `/` | 导入简历 + 统计卡片 + 最近活动 + 右下角AI入口 |
| 岗位探索 | `/jobs-explore` | Agent对话搜索公司招聘官网 + 岗位卡片 + 收藏 |
| 简历优化 | `/resume` | 选择简历（已导入）+ 上传JD + Agent优化 |
| 面试准备 | `/interview` | 生成题目 + AI教练对练（独立流程） |
| 设置 | `/settings` | LLM配置 |

### 核心数据流

```
仪表盘（统一简历导入）
    ↓
岗位探索（Agent分析简历 → 搜索招聘官网 → 返回公司链接）
    ↓ 收藏岗位
简历优化（上传JD → Agent优化简历）
    ↓
面试准备（独立流程）
```

### Agent 工作模式

- **半自动 + 对话问答**：Agent 可自动执行任务，用户也可主动询问
- **主动建议**：Agent 根据当前状态主动给出建议
- **多轮推理**：ReAct 循环执行多步任务

## Agent Runtime 详细设计

> 状态：Phase 1 完成 | 日期：2026-04-07

### 架构概览

```
src/core/runtime/
├── agent_executor.py     # ReAct 执行循环
├── tool_registry.py      # 工具注册与发现
├── state_machine.py      # Agent 执行状态管理
├── memory_store.py       # Redis(会话) + ChromaDB(向量)
└── context_builder.py    # RAG 上下文构建

src/core/tools/
├── base_tool.py          # LangChain BaseTool 封装
└── tool_context.py       # 工具执行上下文（含 db session）

src/core/llm/
├── factory.py            # LLM 工厂（OpenAI/Minimax/Mock）
├── openai_adapter.py     # OpenAI/Minimax 兼容 adapter
└── mock_adapter.py       # 确定性 Mock adapter（测试用）
```

### LLM Adapter 设计

| Adapter | 用途 |
|---------|------|
| `OpenAIAdapter` | 调用 OpenAI/Minimax API，支持 function calling |
| `MockLLMAdapter` | 本地测试/开发， deterministic 输出 |
| `LLMFactory` | 根据 `LLM_PROVIDER` 环境变量创建对应 adapter |

**Provider 支持：** `openai`, `minimax`, `mock`, `stub`

**配置方式：**
```bash
LLM_PROVIDER=mock        # 本地开发
LLM_PROVIDER=minimax     # 生产环境
```

### ToolRegistry + BaseTool

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

    def _run(self, tool_input: dict, runtime=None, context: ToolContext = None) -> dict: ...
    async def _arun(self, tool_input: dict, runtime=None, context: ToolContext = None) -> dict: ...
```

**ToolContext：** 通过 `context.db` 获取数据库会话，禁止工具直接调用 `get_db()`

文件：`src/core/runtime/tool_registry.py`

```python
class ToolRegistry:
    """全局工具注册表"""

    def register(self, tool: BaseTool) -> None: ...
    def get_tool(self, name: str) -> BaseTool: ...
    def list_tools(self) -> list[dict]: ...
    def get_schemas(self) -> list[dict]: ...
```

### AgentExecutor — ReAct 循环

文件：`src/core/runtime/agent_executor.py`

```python
class AgentExecutor:
    """
    ReAct (Reasoning + Acting) 执行器
    状态流转：idle → planning → tool_use → responding → done
    """

    def __init__(
        self,
        llm: BaseLLM,
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
```

### StateMachine

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
```

### MemoryStore

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

    # --- 短期会话记忆 ---
    def add_turn(self, session_id: str, role: str, content: str) -> None: ...
    def get_turns(self, session_id: str, limit: int = 20) -> list[Turn]: ...

    # --- 长期向量记忆 ---
    def add_memory(self, session_id: str, content: str, metadata: dict | None = None) -> str: ...
    def search_memory(self, query: str, session_id: str | None = None, top_k: int = 5, threshold: float = 0.7) -> list[MemoryEntry]: ...
```

### ContextBuilder

文件：`src/core/runtime/context_builder.py`

```python
class ContextBuilder:
    """
    RAG 上下文构建器
    负责从 MemoryStore 组装 LLM 可用的 messages
    """

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
        """
```

## 更新规则

- 每完成一个重构里程碑，更新本文件
- 如果仓库结构与设计方案出现偏差，先更新本文件记录，再推进实现
