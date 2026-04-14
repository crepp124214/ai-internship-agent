# 技术栈文档

> 版本: v1.0.0 | 状态: 已完成 | 日期: 2026-04-14

---

## 一、后端技术栈

### 1.1 核心框架

| 组件 | 选择 | 说明 |
|------|------|------|
| **语言** | Python 3.10+ | AI/LLM 生态最成熟 |
| **Web 框架** | FastAPI | 异步原生，SSE 支持，内置 OpenAPI 文档 |
| **ORM** | SQLAlchemy 2.0 | 类型安全，社区成熟 |
| **数据库** | PostgreSQL 15+ | 生产级关系数据库 |
| **迁移工具** | Alembic | SQLAlchemy 官方推荐 |
| **缓存** | Redis | 会话缓存与响应缓存 |

### 1.2 Agent 架构

| 组件 | 选择 | 说明 |
|------|------|------|
| **Agent 框架** | LangChain BaseTool | 统一工具抽象接口 |
| **执行器** | AgentExecutor | ReAct 执行循环（Plan → Action → Observe → Reflect） |
| **工具注册** | ToolRegistry | 工具注册、发现、版本管理 |
| **状态管理** | StateMachine | 求职流程状态机 |
| **记忆存储** | MemoryStore | 会话记忆 + 持久化存储 |

### 1.3 LLM 集成

| 组件 | 选择 | 状态 |
|------|------|------|
| **LLM 客户端** | OpenAI SDK / 各 Provider SDK | ✅ 已实现 |
| **多模型路由** | LLMFactory + Adapter 模式 | ✅ 已实现 |
| **Mock 模式** | MockAdapter | ✅ 已实现（无需 API Key） |

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
| **路由** | React Router 6 | SPA 路由管理 |
| **构建** | Vite | 快速开发与热重载 |
| **服务端状态** | TanStack Query | 数据获取、缓存、同步 |
| **前端状态** | Zustand | 轻量级状态管理 |
| **表单** | React Hook Form + Zod | 类型安全的表单验证 |
| **UI** | Tailwind CSS + Headless UI | 可定制的组件库 |
| **图标** | Lucide React | 一致的图标风格 |

---

## 三、基础设施

| 领域 | 选择 |
|------|------|
| 容器化 | Docker + Docker Compose |
| CI/CD | GitHub Actions |
| 测试框架 | pytest (后端) + Playwright (E2E) |
| 代码规范 | ESLint + Prettier + Black |

---

## 四、项目结构

```
backend/
├── app/
│   └── api/v1/           # RESTful API 端点
│       ├── auth.py       # 认证
│       ├── resumes.py    # 简历管理
│       ├── jobs.py       # 岗位管理
│       └── interviews.py  # 面试管理
├── domain/              # 领域逻辑
│   ├── agent/           # Agent 运行时
│   ├── jd/              # JD 定制
│   ├── interview/       # 面试教练
│   ├── resume/          # 简历
│   └── job/             # 岗位
├── infrastructure/      # 基础设施
│   ├── database/        # 数据库实体与仓库
│   └── llm/             # LLM 适配器
└── shared/              # 共享能力
    ├── runtime/         # Agent Runtime
    ├── tools/           # 基础工具
    └── errors/          # 错误处理

frontend/
├── src/
│   ├── pages/          # 页面组件
│   ├── components/     # 可复用组件
│   ├── hooks/          # React Hooks
│   ├── lib/            # 工具库 (API 客户端)
│   └── app/            # 应用配置
└── tests/              # 前端测试
```

---

## 五、环境配置

| 环境 | 数据库 | LLM | 说明 |
|------|--------|-----|------|
| 开发 | SQLite | Mock | 本地开发，无需外部依赖 |
| 测试 | SQLite | Mock | CI/CD 使用 |
| 生产 | PostgreSQL | OpenAI/MiniMax | 真实环境 |

---

## 六、技术决策

### 已实现

| 决策 | 说明 |
|------|------|
| LangChain BaseTool | 统一工具抽象 |
| LLMFactory + Adapter | 多模型统一接口 |
| ToolRegistry | 工具注册与发现 |
| AgentExecutor | ReAct 执行循环 |
| Docker Compose | 多环境部署 |

### 技术选型理由

- **FastAPI** vs Django：更轻量，异步支持好，SSE 原生
- **SQLAlchemy 2.0** vs ORM 其他：类型安全，社区成熟
- **TanStack Query** vs SWR：更强大的缓存和同步能力
- **Zustand** vs Redux：更轻量，TypeScript 支持好

---

*文档版本: v1.0.0 | 已完成*
