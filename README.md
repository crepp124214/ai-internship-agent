# AI 实习求职 Agent 系统

> 基于 FastAPI + React 18 的 Agent Runtime 工程实践

---

## 一句话描述

支持 ReAct 循环、工具注册、状态机、多模态记忆的 AI Agent 运行时，具备 SSE 流式输出与完整业务工具链。

## 核心价值主张

- **工程化 Agent 框架**：自研 AgentExecutor（ReAct Loop）+ StateMachine + MemoryStore，可独立运行、测试、替换 LLM Provider
- **依赖注入式工具架构**：基于 LangChain BaseTool 的统一工具抽象，工具层禁止从 Presentation 层导入，架构分层清晰
- **SSE 流式对话**：后端 Agent Chat 支持 StreamingResponse，前端 AgentChatPanel 实时渲染 LLM 输出

---

## 技术架构

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                              Frontend                                       │
│                    React 18 + TypeScript + Vite                             │
│         TanStack Query · Zustand · React Hook Form + Zod                    │
└────────────────────────────┬────────────────────────────────────────────────┘
                             │ HTTP / SSE
                             ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                         Agent Runtime (core/runtime)                        │
│                                                                              │
│   ┌──────────────┐    ┌──────────────┐    ┌──────────────┐                  │
│   │ AgentExecutor │───▶│ StateMachine  │    │ MemoryStore   │                  │
│   │  (ReAct Loop) │    │ idle/plan/   │    │ Redis +       │                  │
│   │               │    │ tool_use/     │    │ ChromaDB      │                  │
│   └──────┬───────┘    │ responding/   │    └──────────────┘                  │
│          │           │ done         │                                     │
│          ▼           └──────────────┘    ┌──────────────┐                  │
│   ┌──────────────┐                       │ContextBuilder │                  │
│   │ ToolRegistry  │◀─────────────────────│ (RAG)        │                  │
│   │  (BaseTool)   │                       └──────────────┘                  │
│   └──────┬───────┘                                                       │
│          │ tool call                                                      │
└──────────┼─────────────────────────────────────────────────────────────────┘
           │
           ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                       Business Logic                                        │
│                                                                              │
│   JD定制简历                    AI面试教练              Agent Chat           │
│   ─────────                    ──────────             ──────────           │
│   · FormatResumeTool           · GenerateInterview    · ChatAgent           │
│   · CompareResumesTool             QuestionsTool      · TaskRouter          │
│   · AnalyzeResumeSkillsTool    · ReviewReport         (SSE Stream)        │
│   · CalculateJobMatchTool          Generator                                 │
│   · MatchResumeToJobTool                                                                │
└────────────────────────────┬────────────────────────────────────────────────┘
                             │
                             ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                         Data Access                                          │
│                SQLAlchemy 2.0 + PostgreSQL + Alembic                        │
│                      Redis Cache · ChromaDB Vector Store                      │
└─────────────────────────────────────────────────────────────────────────────┘
```

**架构原则**：`presentation -> business_logic -> data_access`，`core` 为共享能力层，API 层禁止直接操作 ORM。

---

## 核心技术亮点

### AgentExecutor — ReAct 执行循环

```python
# src/core/runtime/agent_executor.py
class AgentExecutor:
    async def execute(
        self,
        task: str,
        session_id: str,
        system_prompt: str | None = None,
    ) -> AsyncIterator[str]:
        # 状态流转: idle → planning → tool_use → responding → done
```

### StateMachine — 状态管理

```python
# src/core/runtime/state_machine.py
VALID_TRANSITIONS = {
    "idle": {"planning"},
    "planning": {"tool_use", "responding", "done"},
    "tool_use": {"planning", "responding", "done"},
    "responding": {"done", "planning"},
    "done": {"idle"},
}
```

### ToolRegistry — 统一工具抽象

```python
# src/core/runtime/tool_registry.py
class ToolRegistry:
    def register(self, tool: BaseTool) -> None: ...
    def get_tool(self, name: str) -> BaseTool: ...
    def get_schemas(self) -> list[dict]: ...  # for LLM function calling
```

### MemoryStore — 短期 + 长期记忆

```python
# src/core/runtime/memory_store.py
class MemoryStore:
    # 短期会话记忆（Redis）
    def add_turn(self, session_id: str, role: str, content: str) -> None: ...
    def get_turns(self, session_id: str, limit: int = 20) -> list[Turn]: ...
    # 长期向量记忆（ChromaDB）
    def add_memory(self, session_id: str, content: str, metadata: dict | None = None) -> str: ...
    def search_memory(self, query: str, session_id: str | None = None, top_k: int = 5) -> list[MemoryEntry]: ...
```

### SSE 流式输出

```python
# src/presentation/api/v1/agent_chat.py
@router.post("/stream")
async def agent_chat_stream(request: AgentChatRequest, ...):
    return StreamingResponse(agent_executor.execute(...), media_type="text/event-stream")
```

### LLMFactory — 多 Provider 适配

```python
# src/core/llm/factory.py
LLMFactory.create(provider: str) -> BaseLLM  # openai | minimax | mock | stub
```

---

## 快速开始

### 本地开发

```bash
# 1. 安装依赖
cp .env.example .env
cp frontend/.env.example frontend/.env
pip install -r requirements.txt -r requirements-dev.txt

# 2. 初始化数据库
python scripts/migrate.py
python scripts/seed_demo.py

# 3. 启动后端（Linux/macOS）
make dev

# 3. 启动后端（Windows）
scripts\start_backend.bat

# 4. 启动前端
cd frontend && npm install && npm run dev
```

### Docker Compose

```bash
cp .env.compose.example .env.compose
docker compose -f docker/docker-compose.yml up --build
```

- 后端：`http://127.0.0.1:8000`
- 前端：`http://127.0.0.1:5173`（dev）/ `http://127.0.0.1:3000`（compose）
- 演示账号：`demo / demo123`

---

## API 示例

完整 API 文档见 `/docs`（启动后访问 `http://127.0.0.1:8000/docs`）。

### 登录获取 Token

```bash
curl -X POST http://127.0.0.1:8000/api/v1/users/login/ \
  -H "Content-Type: application/json" \
  -d '{"username": "demo", "password": "demo123"}'
```

响应：

```json
{"access_token":"eyJhbGc..."}
```

### 启动 Agent Workspace 对话（SSE 流式）

```bash
curl -X POST http://127.0.0.1:8000/api/v1/agent/chat/stream \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer <TOKEN>" \
  -d '{"message": "帮我优化简历并生成面试题", "session_id": "demo-session-1"}' \
  --no-buffer
```

### 创建简历

```bash
curl -X POST http://127.0.0.1:8000/api/v1/resumes/ \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer <TOKEN>" \
  -d '{"title": "后端实习简历", "content": "熟悉 Python/FastAPI，参与过..."}'
```

### 搜索岗位

```bash
curl -X GET http://127.0.0.1:8000/api/v1/jobs/ \
  -H "Authorization: Bearer <TOKEN>"
```

### 启动 AI 面试

```bash
curl -X POST http://127.0.0.1:8000/api/v1/interview/coach/start \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer <TOKEN>" \
  -d '{"job_title": "后端开发", "difficulty": "medium"}'
```

### 提交面试回答并获取评分

```bash
curl -X POST http://127.0.0.1:8000/api/v1/interview/coach/answer \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer <TOKEN>" \
  -d '{"session_id": "<SESSION_ID>", "answer": "我的项目经验是..."}'
```

### 生成面试报告

```bash
curl -X POST http://127.0.0.1:8000/api/v1/interview/coach/report \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer <TOKEN>" \
  -d '{"session_id": "<SESSION_ID>"}'
```

---

## 技术栈

### 后端

| 组件 | 技术 |
|------|------|
| 语言 | Python 3.10+ |
| 框架 | FastAPI |
| ORM | SQLAlchemy 2.0 |
| 迁移 | Alembic |
| Agent 抽象 | LangChain BaseTool |
| LLM | LLMFactory + Adapter（OpenAI / MiniMax / Mock） |
| 会话缓存 | Redis |
| 向量存储 | ChromaDB |
| 数据库 | PostgreSQL |

### 前端

| 组件 | 技术 |
|------|------|
| 框架 | React 18 + TypeScript |
| 路由 | React Router 6 |
| 构建 | Vite |
| 服务端状态 | TanStack Query |
| 前端状态 | Zustand |
| 表单 | React Hook Form + Zod |
| 样式 | Tailwind CSS + Headless UI |
| 流式渲染 | react-markdown + remark-gfm |

### 基础设施

| 组件 | 技术 |
|------|------|
| 容器化 | Docker + Docker Compose |
| CI/CD | GitHub Actions |
| 测试 | pytest + Playwright |
| 日志 | structlog |

---

## 项目结构

```
src/
├── presentation/               # 路由、Schema、依赖注入、异常转换
│   └── api/v1/               # API 端点（users, resumes, jobs, interview, agent）
├── business_logic/            # 业务服务、流程编排、领域逻辑
│   ├── jd/                   # JD 解析、简历定制、匹配
│   ├── interview/            # 面试会话、评分、报告生成
│   └── agents/               # Agent 业务编排
├── data_access/              # 实体、Repository、持久化
│   ├── entities/             # SQLAlchemy 实体
│   ├── repositories/          # 数据仓储
│   └── parsers/              # 简历/JD 解析器
└── core/                     # 共享能力层
    ├── runtime/              # AgentExecutor, StateMachine, MemoryStore, ContextBuilder
    ├── tools/                # BaseTool, ToolContext
    └── llm/                  # LLMFactory, OpenAI/MiniMax/Mock Adapter

frontend/
├── src/
│   ├── app/                  # 路由配置
│   ├── pages/                # 页面（Resume, Jobs, Interview, AgentWorkspace）
│   ├── components/           # UI 组件
│   └── lib/                  # 共享基础能力
└── ...

docker/
├── docker-compose.yml         # 主 Compose 配置
└── ...

tests/
├── unit/                     # 单元测试（489 passed）
├── integration/              # 集成测试
└── e2e/                      # Playwright E2E 测试
```

---

## 相关文件

- [AGENTS.md](AGENTS.md) — Agent 系统设计说明
- [CLAUDE.md](CLAUDE.md) — 项目规则与上下文
- [CONTRIBUTING.md](CONTRIBUTING.md) — 贡献指南

## License

MIT License
