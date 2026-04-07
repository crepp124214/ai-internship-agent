# AI 实习求职 Agent 系统

帮助计算机专业学生系统化准备实习申请的工具。

---

## 能做什么

**1. JD 定制简历** — 上传简历，根据目标岗位 JD 获得优化建议

**2. AI 面试对练** — 和 AI 面试官多轮对话，实时获得评分和改进建议

**3. 岗位匹配** — 分析简历与岗位的匹配度，优先准备最有价值的申请

---

## 快速体验

### Docker（一行启动）

```bash
cp .env.local.example .env
docker compose -f docker/docker-compose.yml up --build
# 访问 http://localhost:3000
```

演示账号：`demo / demo123`

### 本地开发

```bash
pip install -r requirements.txt -r requirements-dev.txt
cp .env.local.example .env
python scripts/migrate.py && python scripts/seed_demo.py
uvicorn src.main:app --reload
cd frontend && npm install && npm run dev
```

---

## 技术架构

```
Frontend (React + TypeScript)
        │ HTTP / SSE
        ▼
Agent Runtime
  · AgentExecutor（ReAct Loop）
  · StateMachine（状态机）
  · MemoryStore（会话记忆）
  · ToolRegistry（工具注册）
        │ tool call
        ▼
Business Logic（简历 / 面试 / 岗位）
        │
        ▼
Data Access（SQLAlchemy + PostgreSQL）
```

### AgentExecutor — ReAct 执行循环

AgentExecutor 是系统的核心执行器，通过 **Reasoning（推理） → Acting（行动） → Observation（观察）** 循环驱动 Agent 完成复杂任务：

- `idle → planning → tool_use → responding → done`
- 每个状态转换都有完整记录，可追踪可回放
- 支持中断和恢复执行上下文

### StateMachine — 状态管理

```python
VALID_TRANSITIONS = {
    "idle": {"planning"},
    "planning": {"tool_use", "responding", "done"},
    "tool_use": {"planning", "responding", "done"},
    "responding": {"done", "planning"},
    "done": {"idle"},
}
```

状态转换过程全程记录到 `StateTransition`，包含 `from_state`、`to_state`、`reason`、`timestamp`。

### ToolRegistry — 统一工具抽象

所有业务工具（简历解析、JD 解析、技能分析、面试题生成、回答评估）通过 BaseTool 统一注册：

```python
class ToolRegistry:
    def register(self, tool: BaseTool) -> None: ...
    def get_tool(self, name: str) -> BaseTool: ...
    def get_schemas(self) -> list[dict]: ...  # for LLM function calling
```

工具层强制依赖注入 `ToolContext`，禁止从 API 层导入，架构分层清晰。

### MemoryStore — 短期 + 长期记忆

- **短期会话记忆**（Redis）：保存当前对话上下文，支持跨请求恢复
- **长期向量记忆**（ChromaDB）：存储用户画像、偏好、历史匹配结果，支持语义检索

### SSE 流式输出

Agent 的思考过程通过 Server-Sent Events 实时推送，前端无轮询，体验流畅。

### 多 LLM Provider 支持

通过 `LLM_PROVIDER` 环境变量切换：OpenAI / MiniMax / Mock，自动适配 function calling 协议。

---

## 技术栈

| 层级 | 技术 |
|------|------|
| 后端 | Python 3.10+ / FastAPI / SQLAlchemy 2.0 / Alembic |
| 前端 | React 18 + TypeScript / Vite / TanStack Query / Zustand |
| 数据库 | PostgreSQL / Redis |
| Agent | LangChain BaseTool / LLMFactory / ReAct Loop |
| 容器 | Docker + Docker Compose |
| 测试 | pytest / Playwright（覆盖率 80%） |

---

## License

MIT
