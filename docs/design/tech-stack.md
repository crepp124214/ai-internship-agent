# 技术栈文档

> 版本: v1.0.0 | 状态: 已完成 | 日期: 2026-04-14

---

## 一、后端技术栈

| 组件 | 选择 | 说明 |
|------|------|------|
| **语言** | Python 3.10+ | AI/LLM 生态最成熟 |
| **Web 框架** | FastAPI | 异步原生，SSE 支持 |
| **ORM** | SQLAlchemy 2.0 | 类型安全 |
| **数据库** | PostgreSQL 15+ / SQLite (开发) | 生产级关系数据库 |
| **迁移工具** | Alembic | SQLAlchemy 官方推荐 |

### Agent Runtime

| 组件 | 选择 | 说明 |
|------|------|------|
| **Agent 框架** | LangChain BaseTool | 统一工具抽象 |
| **工具注册** | ToolRegistry | 工具注册与发现 |
| **执行器** | AgentExecutor | ReAct 执行循环 |
| **状态管理** | StateMachine | 流程状态机 |

### LLM 集成

| 组件 | 选择 | 状态 |
|------|------|------|
| **LLM 客户端** | OpenAI SDK / 各 Provider SDK | ✅ 已实现 |
| **多模型路由** | LLMFactory + Adapter 模式 | ✅ 已实现 |
| **缓存** | Redis / Memory | ✅ 已实现 |
| **Mock 模式** | MockAdapter | ✅ 已实现 |

**支持的 LLM：**
- OpenAI (GPT-4, GPT-3.5)
- MiniMax (abab6.5-chat)
- DeepSeek (deepseek-chat)
- 智谱 AI (glm-4)
- 通义千问 (qwen-turbo)
- Moonshot (moonshot-v1)
- SiliconFlow

---

## 二、前端技术栈

| 组件 | 选择 | 说明 |
|------|------|------|
| **框架** | React 18 + TypeScript | 主流前端框架 |
| **路由** | React Router 6 | 团队熟悉 |
| **构建** | Vite | 快速开发 |
| **服务端状态** | TanStack Query | 数据获取与缓存 |
| **前端状态** | Zustand | 轻量状态管理 |
| **表单** | React Hook Form + Zod | 类型安全表单 |
| **UI** | Tailwind CSS + Headless UI | 可定制组件 |
| **图标** | Lucide React | 一致性好 |

---

## 三、基础设施

| 领域 | 选择 |
|------|------|
| 容器化 | Docker + Docker Compose |
| CI/CD | GitHub Actions |
| 测试 | pytest + Playwright |
| 日志 | structlog |

---

## 四、环境配置

| 环境 | 用途 | 数据库 | LLM |
|------|------|--------|-----|
| 开发 | 本地开发 | SQLite | Mock |
| 测试 | CI/CD | SQLite | Mock |
| 生产 | 正式环境 | PostgreSQL | OpenAI/MiniMax |

---

## 五、技术决策

### 已实现

| 决策 | 实现 |
|------|------|
| LangChain BaseTool | `backend/shared/tools/base_tool.py` |
| LLMFactory + Adapter | `backend/infrastructure/llm/` |
| ToolRegistry | `backend/shared/runtime/tool_registry.py` |
| AgentExecutor | `backend/shared/runtime/agent_executor.py` |
| Docker 多环境 | `docker/docker-compose.yml` |

### 不推荐

- AutoGen / CrewAI（复杂度高，定制性低）
- LlamaIndex（当前规模无需完整框架）

---

*文档版本: v1.0.0 | 已完成*
