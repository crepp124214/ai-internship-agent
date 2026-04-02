# Codex Project Rules

本文件是 Codex 接手 `AI实习求职Agent系统` 后的项目规则总入口。
它定义后续开发时默认遵循的项目定位、架构要求、编码规范、测试标准和文档使用原则。

项目记忆和历史上下文统一维护在 [PROJECT_MEMORY.md](./PROJECT_MEMORY.md)。

## 1. 项目定位

- 项目名称：`AI实习求职Agent系统`
- 项目类型：Python 后端工程
- 项目目标：构建一个围绕实习求职流程提供智能辅助能力的后端系统

默认能力范围包括：

- 简历上传、解析、优化
- 岗位管理、搜索、匹配
- 面试准备、题库、记录
- 求职进度追踪
- 多 Agent 协作

默认工作目标：

- 优先保证结构清晰、边界稳定、测试可验证
- 以可维护的工程系统为目标，而不是一次性脚本堆叠
- 重要判断优先依据代码现状，其次才参考文档和历史记录

## 2. 架构要求

项目默认采用三层架构，加一个公共基础设施层。

### 2.1 表现层

目录：`src/presentation/`

职责：

- FastAPI 路由
- 请求响应处理
- Pydantic schema
- 依赖注入
- HTTP 异常转换

### 2.2 控制逻辑层

目录：`src/business_logic/`

职责：

- 业务服务
- 任务编排
- 领域逻辑
- Agent 协作

当前结构要求：

- `business_logic` 内部优先按业务域组织
- 当前主要业务域包括：
  - `resume`
  - `job`
  - `interview`
  - `tracker`
  - `user`

### 2.3 数据持久层

目录：`src/data_access/`

职责：

- 数据库连接
- ORM 实体
- Repository
- 迁移相关的数据访问逻辑

### 2.4 核心基础设施层

目录：`src/core/`

职责：

- Agent 基类
- LLM 抽象
- memory
- tools
- 其他跨层公共能力

### 2.5 依赖方向

允许：

- `presentation -> business_logic -> data_access`
- `core` 作为公共基础层被复用

禁止：

- 表现层直接访问 Repository 或 ORM
- 数据持久层反向依赖业务层或表现层
- 随意跨层耦合
- 在 API 层直接编排复杂业务逻辑

如果现有代码违反这些规则，修改时优先做最小范围修正，不做无关大重构。

## 3. 编码规范

### 3.1 Python 规范

默认遵循：

- Black
- isort
- PEP 8

统一约束：

- 目标最大行宽：`100`
- 命名保持稳定统一
- 函数、类、模块职责清晰
- 文件尽量单一职责，不混杂无关逻辑

### 3.2 代码组织要求

- 业务逻辑优先放在服务层或领域模块中
- 路由层主要负责参数接收、依赖注入和异常转换
- Repository 负责数据访问，不负责业务判断
- Agent、LLM、memory、tools 这类能力应通过正式模块边界接入，不要在路由中直接拼接

### 3.3 注释与类型标注

- 新增或重构代码时，优先补充必要类型标注
- 只写高价值注释，不写低信息量废话注释
- 对边界复杂、行为不明显的逻辑，可以补简短说明

### 3.4 API 规范

- API 默认保持版本意识，沿用现有 `v1` 路径结构
- 错误处理应尽量避免直接暴露内部实现细节
- schema、service、entity、repository 之间的命名和契约要保持一致

## 4. 测试标准

### 4.1 测试分层

项目测试按以下层级组织：

- `tests/unit/`
- `tests/integration/`
- `tests/e2e/`

当前进一步按职责细分为：

- `tests/unit/business_logic/`
- `tests/unit/core/`
- `tests/unit/data_access/`
- `tests/integration/api/`
- `tests/integration/data_access/`
- `tests/e2e/`

### 4.2 默认测试要求

- 改功能尽量同步补测试
- 修 bug 优先补回归测试
- 完成前尽量运行与改动直接相关的最小必要测试
- 如果无法完成验证，必须明确记录未验证项

### 4.3 覆盖率目标

- 项目整体目标覆盖率：`>= 80%`

这个阈值是交付目标，不代表当前项目已经稳定达到该标准。

### 4.4 测试原则

- 单元测试优先覆盖服务逻辑、核心抽象、数据访问边界
- 集成测试优先覆盖 API 与数据库契约
- E2E 测试优先覆盖最小真实用户链路
- 测试文件路径和导入路径应与当前目录结构一致

## 5. 文档与记忆规则

- 长期有效的规则写在本文件
- 长期稳定的项目认知写入 `PROJECT_MEMORY.md`
- 架构级、长期有效的信息可以同步到 `docs/`
- 一次性会话痕迹、过时状态、已失效计划，不应继续堆进根规则文件

当前事实判断优先级：

1. 代码和测试
2. 配置、迁移、脚本
3. `PROJECT_MEMORY.md`
4. `docs/` 历史文档

## 6. 处理 docs 的方式

`docs/` 是项目历史知识库，不是当前事实的唯一来源。

默认使用方式：

- `architecture.md` 与 `three-tier-architecture.md`
  - 主要用于理解目标架构
- `superpowers/plans/`
  - 主要用于理解路线图
- `superpowers/planning/`
  - 主要用于理解历史过程，不直接等同于当前状态

如果文档与代码冲突，以代码现状为准，并在必要时更新记忆文件。

## 7. 默认开发流程

对于中大型任务，优先遵循以下顺序：

1. 先理解相关模块和影响范围
2. 明确数据流和层次边界
3. 再实施代码修改
4. 补测试或更新验证
5. 最后同步文档或记忆

对于小任务：

- 可以轻量处理
- 但仍应尊重架构边界和测试纪律

### 7.1 目标与非目标

每个中大型任务开始前，必须先明确：

- 目标：这次改动要真正交付什么
- 非目标：这次明确不解决什么

默认要求：

- 先写清楚目标，再开始扩展实现
- 不因为“顺手”把任务范围扩大
- 当项目处于不稳定阶段时，优先收敛范围

### 7.2 单模块改动原则

默认优先一次只推进一个明确模块或一个明确闭环。

推荐粒度：

- 一个业务域
- 一个契约修复
- 一个最小功能链路
- 一个测试基线问题

不推荐：

- 同时跨多个域做无关重构
- 在没有稳定验证的情况下并行扩展多个核心能力

### 7.3 结构与契约优先

在当前项目中，默认优先级是：

1. 结构清晰
2. 契约一致
3. 测试可验证
4. 功能扩展

如果结构、契约和测试都不稳，不应继续堆新功能。

### 7.4 文档即上下文

文档不是事后补充物，而是开发上下文的一部分。

默认沉淀位置：

- `CLAUDE.md`：长期规则
- `PROJECT_MEMORY.md`：长期稳定记忆
- `docs/superpowers/plans/`：执行计划
- `docs/decisions/`：关键设计决策
- `docs/prompts/`：后续 Agent 提示词与提示词草案

### 7.5 统一命令入口

项目后续应逐步统一开发命令入口，优先通过 `Makefile` 或等效入口封装日常动作。

目标命令包括：

- `make lint`
- `make test`
- `make test-unit`
- `make test-integration`
- `make test-e2e`
- `make dev`
- `make migrate`

在统一入口未完全建立前，新增脚本和命令时也应尽量保持命名一致。

### 7.6 调试表达标准

调试和问题记录时，默认使用以下结构：

- 预期行为
- 实际行为
- 最小复现路径
- 当前判断

避免只说“坏了”或“这里有 bug”而没有上下文。

## 8. 当前默认判断

- 这是一个已有工程骨架、但仍处于持续建设中的项目
- 许多模块已经存在，但不默认视为“完整实现”
- LLM、memory、tools、多 Agent 协作等能力需要逐项验证，不能仅凭文档假定已完成

## 9. 修改本文件的原则

只有当以下信息发生明显变化时，才更新本文件：

- 项目核心定位改变
- 架构主规则改变
- 默认编码规范改变
- 默认测试标准改变
- Codex 的接手方式和协作约束改变

普通开发进度、阶段状态和一次性问题，不写入本文件。
## Long-Term Team Workflow

## Mixed-Mode Delivery Rule

From now on, the default delivery order is **mixed-mode**, not pure layer-by-layer waterfall and not repeated business-lane-only slicing.

The fixed sequence is:

1. `Layer-first`
   - align shared `data_access` rules
   - align shared `business_logic` service semantics
   - align shared `presentation` error and route semantics
   - keep `core` as the only shared AI infrastructure entrypoint
2. `Domain-delivery`
   - expand one bounded business lane using the already-aligned shared rules

Mandatory rules:

- Do not run multiple consecutive stages that only deepen one business lane without first checking shared-layer drift.
- Do not design a new persistence model from the API layer downward.
- For new persisted AI capabilities, the order must be:
  - data model or repository contract first
  - service behavior second
  - API exposure last
- `persist`, `history`, and preview-style routes should keep stable naming semantics once introduced.
- `LLM/Core` remains the only allowed owner of shared provider/runtime patterns.

Default collaboration should reuse the permanent team defined in [`AGENT_TEAM.md`](./AGENT_TEAM.md).

Rules:

- Do not redesign the team structure for every task.
- The main agent acts as project manager and final integrator by default.
- Only activate the fixed roles needed for the current task.
- Use [`docs/prompts/agent_team_bootstrap.md`](./docs/prompts/agent_team_bootstrap.md) as the startup template for task routing.
- Use mixed-mode execution by default:
  - `Layer-first` for shared foundation and cross-cutting consistency
  - `Domain-delivery` for one bounded business lane at a time
- All sub-agents must report in a fixed structure:
  - changed files
  - implemented capability
  - remaining risk
  - tests run
  - test result
  - downstream dependency
- Cross-module ownership conflicts are escalated to the main agent only.
- `LLM/Core lead` and `Data/Test lead` should be pulled in first for any foundation-oriented stage.
- Business leads should not expand a lane until the main agent has locked that stage's shared layer rules.
- After completing any meaningful task or stage, always report the next recommended task explicitly.

Fixed roster:

- `Main agent / PM`
- `User lead`
- `Resume lead`
- `Job lead`
- `Interview lead`
- `Tracker lead`
- `LLM/Core lead`
- `Data/Test lead`

## Skill routing

When the user's request matches an available gstack skill, invoke that skill workflow first instead of answering ad hoc.

Key routing rules:
- Product ideas, value judgment, or brainstorming -> invoke `office-hours`
- Bugs, runtime errors, broken behavior, or "why is this broken" -> invoke `investigate`
- QA, browser verification, live-flow testing, or bug hunting -> invoke `qa`
- Code review, diff review, or pre-landing checks -> invoke `review`
- Ship, deploy, push, or create a release/PR -> invoke `ship`
- Update docs after shipping -> invoke `document-release`
- Weekly recap or shipped-work summary -> invoke `retro`
- Architecture or implementation-plan review -> invoke `plan-eng-review`
- Design system, brand, or visual identity work -> invoke `design-consultation`
- Visual polish or UI audit of a live surface -> invoke `design-review`
- Save progress, checkpoint, or resume later -> invoke `checkpoint`
- Code quality or repo health check -> invoke `health`
- Upgrade gstack itself -> invoke `gstack-upgrade`

If no matching gstack skill exists, continue with the normal project workflow defined above.
