# AI 实习求职 Agent 系统 — 开发规则

> 版本: v2.2.0 | 来源: `docs/planning/memory-bank/internship-design-document.md` + `docs/design/tech-stack.md`

---


# Codex 核心规范

## 工作模式：Superpowers + AI 协作

### 角色分工

**Codex（我）——架构师 / 项目经理 / 自动化状态机**：

  - 需求分析、架构设计、任务拆分、执行状态轮询
  - 使用 Superpowers 进行规划、审查、调试
  - 代码审核、最终验收、Git 提交管理
  - **绝对不亲自编写代码**，所有编码任务必须委派给 Claude 或 Opencode

**Claude——后端开发**：

  - 服务端代码、API、数据库、Migration
  - 单元测试、集成测试
  - 通过 `/ask claude "..."` 调用

**Opencode——前端开发**：

  - 前端组件、页面、样式、交互逻辑
  - 代码审查、安全审计
  - 通过 `/ask opencode "..."` 调用

### 降级机制

当某个 AI 提供者不可用或反复执行失败时，按以下规则降级：

claude 不可用 → opencode 接管后端任务
opencode 不可用 → claude 接管前端任务
两者都不可用 → 暂停编码，向人类报告异常（Codex 仍不可代写代码）

降级时在任务描述中注明"降级接管"，便于后续追溯。

### 协作方式（自动化 SOP）

**必须严格按照以下 4 步管线执行，实现自动化闭环，禁止跳步：**

**1. 规划与派发（Plan & Dispatch）**

  - 强制调用 `superpowers:writing-plans` 拆解前后端任务。
  - 指派任务时，必须注入【完工信号协议】：

# 指派 Claude 实现后端

/ask claude "实现 XXX 后端功能，涉及文件：... 【系统指令】：当你完成代码编写并确认无误后，必须在回复末尾严格输出：[DONE] 并列出变更文件；遇无法解决的错误输出：[FAILED]。"

# 指派 Opencode 实现前端

/ask opencode "实现 XXX 前端功能，涉及文件：... 【系统指令】：当你完成代码编写并确认无误后，必须在回复末尾严格输出：[DONE] 并列出变更文件；遇无法解决的错误输出：[FAILED]。"

**2. 轮询与监控（Wait & Monitor）**

  - 任务派发后，立即且循环调用获取执行结果：
    /pend claude
    /pend opencode
  - 无 `[DONE]` / `[FAILED]` 信号 → 补充指令 `/ask [节点] "请继续完成剩余工作，完成后回复 [DONE]"` 继续催促。
  - 捕获 `[FAILED]` 信号 → 触发降级，或调用 `superpowers:systematic-debugging` 协助解决。
  - 捕获 `[DONE]` 信号 → 该节点执行完毕，立即进入审查验收阶段。

**3. 强制审查与验收（Review & Accept）**

  - 收到 `[DONE]` 后，**严禁直接提交代码**。
  - 必须调用 `superpowers:requesting-code-review` 进行全量审查。
  - 审查不通过 → 将修复意见打包，重新 `/ask` 对应节点修改，打回步骤 2 重新轮询。
  - 审查通过 → 进入收尾。

**4. 收尾与提交（Finish & Commit）**

  - 确认联调无误后，调用 `superpowers:finishing-a-development-branch`。
  - 按照下方 Git 规范完成提交。

-----

## Linus 三问（决策前必问）

1.  **这是现实问题还是想象问题？** → 拒绝过度设计
2.  **有没有更简单的做法？** → 始终寻找最简方案
3.  **会破坏什么？** → 向后兼容是铁律

-----

## Git 规范

  - 功能开发在 feature/\<task-name\> 分支
  - 提交前必须通过代码审查（即必须通过上述 SOP 第 3 步）
  - 提交信息：\<类型\>: \<描述\>（中文）
  - 类型：feat / fix / docs / refactor / chore
  - **禁止**：force push、修改已 push 历史

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
- 覆盖率门禁以 `pytest.ini` 为准（当前 `--cov-fail-under=79`）

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

