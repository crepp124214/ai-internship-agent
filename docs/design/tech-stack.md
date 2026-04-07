# 技术栈选型文档

> 版本: v1.1.0 | 状态: 已采纳 | 日期: 2026-04-07

---

## 一、选型原则

| 原则 | 说明 |
|------|------|
| **保持连贯** | 后端继续用 Python，前端继续用 React/TypeScript |
| **AI-Native** | 优先选择对 LLM/Agent 友好的工具 |
| **生产就绪** | 选型需经生产验证，避免实验性依赖 |
| **团队适配** | 考虑现有技术储备，避免过高学习曲线 |

---

## 二、后端技术栈

### 2.1 核心框架

| 组件 | 选择 | 理由 |
|------|------|------|
| **语言** | Python 3.10+ | AI/LLM 生态最成熟，团队已有积累 |
| **Web 框架** | FastAPI (保持) | 异步原生，SSE 支持，内置 OpenAPI |
| **ORM** | SQLAlchemy 2.0 (保持) | 类型安全，社区成熟 |
| **数据库** | PostgreSQL 15+ | 生产级关系数据库，支持 JSON |
| **迁移工具** | Alembic (保持) | SQLAlchemy 官方推荐 |

### 2.2 Agent Runtime

| 组件 | 选择 | 理由 |
|------|------|------|
| **Agent 框架** | LangChain + LangGraph | 支持 ReAct、Tool Calling、持久化 |
| **Tool Calling** | LangChain Tool Interface | 原生支持工具 Schema |
| **提示词管理** | LangSmith | 提示词版本、评估、追踪 |
| **备选** | Jinja2 + YAML 模板 | 轻量场景使用 |

### 2.3 LLM 集成

| 组件 | 选择 | 状态 | 理由 |
|------|------|------|------|
| **LLM 客户端** | OpenAI SDK / 各 Provider SDK | ✅ 已采纳 | 官方 SDK 稳定 |
| **多模型路由** | LLMFactory + Adapter 模式 | ✅ 已采纳 | 统一接口，支持 mock/openai/minimax |
| **向量数据库** | ChromaDB | ✅ 已采纳 | 开发友好 |
| **嵌入模型** | text-embedding-3-small | 🔄 待集成 | 性价比高 |
| **缓存** | Redis | ✅ 已采纳 | 响应缓存与会话缓存 |
| **备选方案** | LiteLLM | 🔄 评估中 | 后续可考虑迁移 |

### 2.4 流式输出

| 组件 | 选择 | 理由 |
|------|------|------|
| **SSE** | FastAPI StreamingResponse | 原生支持 |
| **WebSocket** | FastAPI WebSocket | 实时对话备选 |

### 2.5 任务队列

| 组件 | 选择 | 理由 |
|------|------|------|
| **队列** | Celery + Redis | 异步任务解耦 |
| **定时任务** | Celery Beat | 定时处理 |

---

## 三、前端技术栈

### 3.1 核心框架

| 组件 | 选择 | 理由 |
|------|------|------|
| **框架** | React 18 + TypeScript | 已有基础 |
| **路由** | React Router 6 | 团队熟悉 |
| **构建** | Vite | 已使用 |

### 3.2 状态管理

| 组件 | 选择 | 理由 |
|------|------|------|
| **服务端状态** | TanStack Query | 已用 |
| **Agent 状态** | Zustand | 轻量、适配流式场景 |
| **表单** | React Hook Form + Zod | 类型安全 |

### 3.3 UI 与渲染

| 组件 | 选择 | 理由 |
|------|------|------|
| **组件库** | Tailwind CSS + Headless UI | 可定制 |
| **图标** | Lucide React | 一致性好 |
| **动画** | Framer Motion | 支持对话动画 |
| **Markdown** | react-markdown + remark-gfm | 渲染 AI 输出 |

---

## 四、基础设施

| 领域 | 选择 |
|------|------|
| 容器化 | Docker + Docker Compose |
| CI/CD | GitHub Actions |
| 测试 | pytest + Playwright |
| 日志 | structlog |
| 指标 | Prometheus + Grafana |
| 错误追踪 | Sentry |

---

## 五、关键决策

### 已采纳（v1.1.0）

| 决策 | 实现 | 说明 |
|------|------|------|
| LangChain BaseTool | ✅ | `src/core/tools/base_tool.py` |
| LLMFactory + Adapter | ✅ | `src/core/llm/factory.py` + adapters |
| Redis | ✅ | 会话缓存 + MemoryStore |
| PostgreSQL | ✅ | 生产数据库 |
| SSE 流式 | ✅ | `src/presentation/api/v1/agent_chat.py` |
| Zustand | ✅ | 前端 Agent 状态 |
| ChromaDB | ✅ | 向量存储 |
| Docker Compose 多环境 | ✅ | `.env.dev` / `.env.prod` |

### 可选（待评估）

| 决策 | 状态 |
|------|------|
| LiteLLM 替代 LLMFactory | 🔄 评估中 |
| Qdrant 替代 ChromaDB | 🔄 评估中 |
| LangChain + LangGraph 完整迁移 | 🔄 后续考虑 |
| PromptLayer | 🔄 评估中 |
| Kubernetes | 🔄 预发布/生产 |

### 不推荐

- AutoGen / CrewAI（复杂度高，定制性低）
- LlamaIndex（RAG 场景当前不需要完整框架）
- Elasticsearch（当前规模无需）

---

## 六、环境矩阵

| 环境 | 用途 | 数据库 | 缓存 | LLM |
|------|------|--------|------|-----|
| 开发 | 本地开发 | SQLite | Memory | Mock |
| 测试 | CI/CD + Playwright | SQLite | Redis | Mock |
| 预发布 | 集成测试 | PostgreSQL | Redis | MiniMax/DeepSeek |
| 生产 | 正式环境 | PostgreSQL | Redis | OpenAI/MiniMax |

### 已实现的环境配置

```
.env              # 本地开发（LLM_PROVIDER=mock）
.env.dev          # Docker开发环境（mock LLM、热重载）
.env.prod         # Docker生产环境（真实LLM）
.env.test         # 测试环境（Mock LLM）
.env.local.example # 本地默认示例
```

---

*文档版本: v1.1.0 | 已采纳*
