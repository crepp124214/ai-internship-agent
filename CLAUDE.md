# AI 实习求职 Agent 系统 — 开发规则

> 版本: v2.2.0 | 来源: `docs/planning/memory-bank/internship-design-document.md` + `docs/design/tech-stack.md`

---

## 上下文优先级

按以下顺序理解和执行任务：

1. `docs/planning/memory-bank/internship-design-document.md`
2. `docs/design/tech-stack.md`
3. `docs/planning/memory-bank/architecture.md`
4. `docs/planning/memory-bank/implementation-plan.md`
5. `docs/planning/memory-bank/progress.md`

如果执行层文档与设计方案冲突，以设计方案和技术栈文档为准。

## 必读规则

- 写任何代码前，必须完整阅读 `docs/planning/memory-bank/internship-design-document.md`
- 写任何代码前，必须完整阅读 `docs/design/tech-stack.md`
- 写任何代码前，必须完整阅读 `docs/planning/memory-bank/architecture.md`
- 执行任务前，必须先对照 `docs/planning/memory-bank/implementation-plan.md`
- 每完成一个重要步骤，必须更新 `docs/planning/memory-bank/progress.md`
- 每完成一个重要功能或重构里程碑，必须更新 `docs/planning/memory-bank/architecture.md`

## 架构红线

- 依赖方向必须保持：`presentation -> business_logic -> data_access`
- `core` 只承载共享能力，不承载领域业务
- API 层不得直接操作 ORM / Repository
- 数据层不得反向依赖上层
- 路由层不得堆积业务逻辑
- 前端不得直接调用 LLM
- **工具层禁止从 `presentation` 层导入**（P0 修复要求）

## Agent 重构原则

- 已实现：Agent Runtime（AgentExecutor、ToolRegistry、StateMachine、MemoryStore、ContextBuilder）
- 已实现：BaseTool 统一工具抽象 + ToolContext 依赖注入
- 不继续扩写旧式 `execute() -> LLM generate()` 模式
- 新增工具必须遵循 ToolRegistry 模式

## 架构原则

- 依赖方向必须保持：`presentation -> business_logic -> data_access`
- `core` 只承载共享能力，不承载领域业务
- API 层不得直接操作 ORM / Repository
- 数据层不得反向依赖上层
- 路由层不得堆积业务逻辑
- 前端不得直接调用 LLM
- 工具层禁止从 `presentation` 层导入

## 功能状态

### 已上线功能

| 功能 | 阶段 | 状态 |
|------|------|------|
| JD 定制简历 | Phase 3 | ✅ |
| AI 面试教练（多轮） | Phase 4 | ✅ |
| Agent Workspace 前端 | Phase 6 | ✅ |
| 数据初始化 | Phase 7.5 | ✅ |
| Docker 多环境 | Phase 9 | ✅ |
| 用户体验流程 v2.0 设计 | Phase 14 | ✅ 设计完成，待 Phase 15 实施 |

### 待实施

| 功能 | 说明 |
|------|------|
| Phase 15 前端页面重构 | 仪表盘 + 岗位探索 + 简历优化 |

## 技术栈约束

### 后端

- Python 3.10+
- FastAPI
- SQLAlchemy 2.0
- Alembic
- LangChain BaseTool（工具抽象）
- LLMFactory + Adapter（OpenAI/Minimax/Mock）
- Redis
- PostgreSQL

### 前端

- React 18 + TypeScript
- React Router 6
- Vite
- TanStack Query
- Zustand
- React Hook Form + Zod

### 基础设施

- Docker + Docker Compose
- GitHub Actions
- pytest + Playwright

## 交付方式

- 一次只改一个模块
- 先改文档与边界，再改实现
- 每一步都要有验证
- 不做与当前阶段无关的大范围扩展

## 测试要求

- 测试分层：`unit / integration / e2e`
- 修改功能必须补测试
- 修复 bug 优先补回归
- 目标覆盖率：至少达到 80%

## 文档职责

- `docs/planning/memory-bank/internship-design-document.md`：正式设计源文档
- `docs/design/tech-stack.md`：正式技术栈源文档
- `docs/planning/memory-bank/architecture.md`：执行层架构映射
- `docs/planning/memory-bank/implementation-plan.md`：当前可执行步骤
- `docs/planning/memory-bank/progress.md`：执行进度记录

## 回复要求

- 强制使用中文回复，不能使用英文回复

---

*版本: v2.2.0*
