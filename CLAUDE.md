# AI 实习求职 Agent 系统 — 开发规则

> 版本: v2.0.0 | 来源: `internship-design-document.md` + `tech-stack.md`

---

## 上下文优先级

按以下顺序理解和执行任务：

1. `internship-design-document.md`
2. `tech-stack.md`
3. `AGENTS.md`
4. `memory-bank/architecture.md`
5. `memory-bank/implementation-plan.md`
6. `memory-bank/progress.md`

如果执行层文档与设计方案冲突，以设计方案和技术栈文档为准。

## 必读规则

- 写任何代码前，必须完整阅读 `internship-design-document.md`
- 写任何代码前，必须完整阅读 `tech-stack.md`
- 写任何代码前，必须完整阅读 `memory-bank/architecture.md`
- 执行任务前，必须先对照 `memory-bank/implementation-plan.md`
- 每完成一个重要步骤，必须更新 `memory-bank/progress.md`
- 每完成一个重要功能或重构里程碑，必须更新 `memory-bank/architecture.md`

## 当前项目定位

- 项目：AI 实习求职 Agent 系统
- 目标：将当前项目从“伪 Agent 应用”重构为真正可演进的 Agent 系统
- 当前主线：先完成基础重构与基础能力收敛，再逐步实现完整 Agent Runtime 与高级功能

## 当前阶段判断

当前处于重构阶段，不是发布收尾阶段。

当前优先级：

1. 收敛架构
2. 清理旧模块
3. 稳定基础域
4. 为后续 Agent 化扩展预留正确边界

## 架构红线

- 依赖方向必须保持：`presentation -> business_logic -> data_access`
- `core` 只承载共享能力，不承载领域业务
- API 层不得直接操作 ORM / Repository
- 数据层不得反向依赖上层
- 路由层不得堆积业务逻辑
- 前端不得直接调用 LLM

## Agent 重构原则

- 当前问题核心是“伪 Agent”，所以重构方向必须围绕：
  - Agent Runtime
  - Tool Registry
  - State Machine
  - Memory Store
- 新的 Agent 相关能力优先遵循 `LangChain + LangGraph`
- 不继续扩写旧式 `execute() -> LLM generate()` 模式

## 功能优先级

### 旧能力处理

- `Tracker` 视为低价值旧模块，应逐步退场

### 新能力主线

1. JD 定制简历
2. AI 面试官对练

## 技术栈约束

### 后端

- Python 3.10+
- FastAPI
- SQLAlchemy 2.0
- Alembic
- LangChain + LangGraph
- LiteLLM
- Redis
- PostgreSQL（重构目标）

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
- 目标覆盖率：至少达到设计目标，重构过程中不能倒退

## 文档职责

- `internship-design-document.md`：正式设计源文档
- `tech-stack.md`：正式技术栈源文档
- `memory-bank/architecture.md`：执行层架构映射
- `memory-bank/implementation-plan.md`：当前可执行步骤
- `memory-bank/progress.md`：执行进度记录

## 回复要求

- 强制使用中文回复，不能使用英文回复

---

*版本: v2.0.0*
