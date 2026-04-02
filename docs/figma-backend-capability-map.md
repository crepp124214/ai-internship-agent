# Figma 页面与后端能力映射总览

这份文档用于把当前项目的 **Figma 产品设计** 和 **已实现后端能力** 对齐成一份可讲解、可交接、可落前端的桥接说明。

它面向三类读者：

- 你本人在面试或作品集讲解时快速说明“页面背后到底接了什么能力”
- 后续前端实现者在切页面和接接口时减少猜测
- 后续子代理或协作者在继续扩展产品时，避免把“设计展示”误当成“后端已支持的新能力”

## 1. 项目定位

当前项目不是“纯设计概念稿”，也不是“前后端都已完整落地的最终产品”。

它更准确的定位是：

- 后端主能力已实现
- Figma 页面已建立完整产品观感
- 作品集演示路径已经清楚
- 前端实现仍是下一阶段工作

当前产品主线固定为 4 条业务能力：

- Resume
- Jobs
- Interview
- Tracker

再加上 1 条用户入口能力：

- Login / Current User

## 2. 全局映射规则

### 2.1 三类能力语义

- `preview`
  - 代表纯生成 / 纯分析
  - 会返回结果，但不会把结果写入持久化对象
- `persist`
  - 代表生成结果并写入数据库
  - 返回的是持久化后的记录或实体
- `history`
  - 代表读取已有历史结果
  - 不触发新的 AI 生成

### 2.2 页面展示边界

Figma 页面允许做“汇总展示”，但这不代表后端已经有专门的聚合接口。

尤其是：

- `Dashboard`
  - 当前按“组合现有能力结果”来展示
  - 不额外定义新的 Dashboard 聚合 API

### 2.3 状态判定

文档中的能力状态统一分为三类：

- `已实现并可调用`
  - 当前已有后端接口或明确 service 能力
- `已设计但依赖现有组合能力`
  - 页面可以展示，但依赖前端组合已有接口结果
- `未纳入当前范围`
  - 当前设计中不应被当成已支持主能力

## 3. 页面级映射

### 3.1 `01 Dashboard`

页面职责：

- 作为产品主入口
- 汇总四条业务线当前状态
- 告诉用户“下一步该做什么”

核心模块与映射：

| 页面模块 | 对应能力 | 数据来源 | 当前状态 |
|---|---|---|---|
| Hero 概览 | 产品级概览文案 | 前端静态文案 + 现有结果组合 | 已设计但依赖现有组合能力 |
| Resume 摘要卡 | Resume summary / improvements / history 的最近状态 | Resume 相关接口组合 | 已设计但依赖现有组合能力 |
| Jobs 摘要卡 | Job match preview / persist / history 的最近状态 | Jobs 相关接口组合 | 已设计但依赖现有组合能力 |
| Interview 摘要卡 | 题目生成、答案评估、记录评估结果 | Interview 相关接口组合 | 已设计但依赖现有组合能力 |
| Tracker 摘要卡 | advice preview / persist / history 的最近状态 | Tracker 相关接口组合 | 已设计但依赖现有组合能力 |
| Recent AI output | 最近一次 summary / match / evaluation / advice | 各模块结果组合 | 已设计但依赖现有组合能力 |
| Quick actions | 跳转到各模块主要动作 | 前端导航行为 | 已设计但依赖现有组合能力 |

结论：

- Dashboard 本身不要求新增后端接口
- 它是现有能力的组合展示页

### 3.2 `02 Resume`

页面职责：

- 管理简历内容
- 查看 AI 摘要
- 查看 AI 优化建议
- 查看历史记录

核心模块与映射：

| 页面模块 | 对应能力 | 数据来源 | 当前状态 |
|---|---|---|---|
| 当前简历 / 基本信息 | Resume CRUD | `GET /api/v1/resumes/{resume_id}` 等 | 已实现并可调用 |
| 已处理内容 | Resume 实体中的 `processed_content / resume_text` | Resume CRUD | 已实现并可调用 |
| AI 摘要预览 | `summary preview` | `POST /api/v1/resumes/{resume_id}/summary/` | 已实现并可调用 |
| 摘要持久化 | `summary persist` | `POST /api/v1/resumes/{resume_id}/summary/persist/` | 已实现并可调用 |
| 摘要历史 | `summary history` | `GET /api/v1/resumes/{resume_id}/summary/history/` 或 `summary-history` 路径 | 已实现并可调用 |
| 优化建议预览 | `improvements preview` | `POST /api/v1/resumes/{resume_id}/improvements/` | 已实现并可调用 |
| 优化建议持久化 | `improvements persist` | `POST /api/v1/resumes/{resume_id}/improvements/persist/` | 已实现并可调用 |
| 优化建议历史 | `optimizations / history` | `GET /api/v1/resumes/{resume_id}/optimizations/` | 已实现并可调用 |

前端实现建议：

- Resume 页优先落地
- 因为它已经具备完整的 `preview + persist + history`

### 3.3 `03 Jobs`

页面职责：

- 浏览岗位
- 查看岗位详情
- 查看与当前简历的匹配结果
- 查看匹配历史

核心模块与映射：

| 页面模块 | 对应能力 | 数据来源 | 当前状态 |
|---|---|---|---|
| 岗位列表 | Job CRUD / 列表能力 | Jobs 基础接口 | 已实现并可调用 |
| 岗位详情 | 单岗位查看 | Jobs 基础接口 | 已实现并可调用 |
| 匹配结果预览 | `match preview` | `POST /api/v1/jobs/{job_id}/match/` | 已实现并可调用 |
| 匹配结果持久化 | `match persist` | `POST /api/v1/jobs/{job_id}/match/persist/` | 已实现并可调用 |
| 匹配历史 | `match history` | `GET /api/v1/jobs/{job_id}/match-history/` | 已实现并可调用 |

页面实现重点：

- 中间详情区是 Job 页面核心
- 匹配结果与历史是右侧或下方的 AI 结果区

### 3.4 `04 Interview`

页面职责：

- 生成练习题
- 评估答案
- 查看评估记录

核心模块与映射：

| 页面模块 | 对应能力 | 数据来源 | 当前状态 |
|---|---|---|---|
| 题目生成 | `generate interview questions` | Interview 题目生成接口 | 已实现并可调用 |
| 答案评估预览 | `evaluate answer preview` | `POST /api/v1/interview/answers/evaluate/` | 已实现并可调用 |
| 记录评估持久化 | `record evaluation persist` | `POST /api/v1/interview/records/{record_id}/evaluate/` | 已实现并可调用 |
| 评估记录 / 历史 | Interview records / sessions / persisted evaluation | Interview 记录接口 | 已实现并可调用 |

映射说明：

- Interview 是当前四条业务线里唯一一条“评估结果主要写回业务记录”的链路
- 页面里可以把“历史”理解为 records / sessions 的读取，而不是独立 AI 结果表

### 3.5 `05 Tracker`

页面职责：

- 展示投递列表与阶段
- 生成下一步建议
- 保存并查询建议历史

核心模块与映射：

| 页面模块 | 对应能力 | 数据来源 | 当前状态 |
|---|---|---|---|
| 投递列表 | Tracker / Application CRUD | Tracker 基础接口 | 已实现并可调用 |
| 当前阶段 | Application 状态信息 | Tracker 基础接口 | 已实现并可调用 |
| advice 预览 | `tracker advice preview` | `POST /api/v1/tracker/applications/{application_id}/advice/` | 已实现并可调用 |
| advice 持久化 | `tracker advice persist` | `POST /api/v1/tracker/applications/{application_id}/advice/persist/` | 已实现并可调用 |
| advice 历史 | `tracker advice history` | `GET /api/v1/tracker/applications/{application_id}/advice-history/` | 已实现并可调用 |

页面实现重点：

- Tracker 页核心不是数据大盘
- 而是“当前阶段 + 下一步行动建议”

### 3.6 `06 Login`

页面职责：

- 作为产品入口
- 登录并进入受保护工作台

核心模块与映射：

| 页面模块 | 对应能力 | 数据来源 | 当前状态 |
|---|---|---|---|
| 登录表单 | 用户登录 | `POST /api/v1/users/login/` | 已实现并可调用 |
| 当前用户校验 | 登录后身份确认 | `GET /api/v1/users/me` | 已实现并可调用 |
| 产品定位文案 | 作品集展示文案 | 前端静态文案 | 已设计但依赖现有组合能力 |

## 4. API / 能力总表

| 页面模块名 | 对应后端能力 | 结果类型 | 是否持久化 |
|---|---|---|---|
| Resume summary | Resume summary preview | 结构化分析结果 | 否 |
| Resume summary history | Resume summary persisted result | `ResumeOptimization` | 是 |
| Resume improvements | Resume improvements preview | 结构化分析结果 | 否 |
| Resume improvements history | Resume improvements persisted result | `ResumeOptimization` | 是 |
| Job match | Job match preview | 匹配结果 | 否 |
| Job match history | Job match persisted result | `JobMatchResult` | 是 |
| Interview answer evaluation | Interview answer preview | 评估结果 | 否 |
| Interview record evaluation | Interview record persisted evaluation | `InterviewRecord` 内联结果 | 是 |
| Tracker advice | Tracker advice preview | 建议结果 | 否 |
| Tracker advice history | Tracker advice persisted result | `TrackerAdvice` | 是 |
| Login | 用户登录 | Token / 登录结果 | 否 |
| Current user | 当前用户信息 | User 视图 | 否 |

## 5. 实现状态判定表

| 能力类别 | 说明 | 当前状态 |
|---|---|---|
| 页面主模块对应的基础后端能力 | Resume / Jobs / Interview / Tracker / Users | 已实现并可调用 |
| Dashboard 聚合展示 | 组合多个已有接口结果形成首页 | 已设计但依赖现有组合能力 |
| Figma 视觉中的品牌文案与说明区 | 产品表达和叙事 | 已设计但依赖现有组合能力 |
| K8s / 运维后台 | 设计中不应作为主流程展示 | 未纳入当前范围 |
| 完整 token 生命周期 / refresh token 体系 | 当前不作为前端主流程前提 | 未纳入当前范围 |
| worker / 异步任务控制面板 | 当前未作为产品主界面能力 | 未纳入当前范围 |
| 多角色协作后台 / AI 聊天中心 | 当前后端无对应主能力 | 未纳入当前范围 |

## 6. 前端实现建议

### 6.1 建议前端路由

- `/login`
- `/dashboard`
- `/resume`
- `/jobs`
- `/interview`
- `/tracker`

### 6.2 页面进入顺序

建议用户主流程为：

1. 登录
2. 进入 Dashboard
3. 打开 Resume，确认简历内容和 AI 摘要
4. 打开 Jobs，查看岗位匹配
5. 打开 Interview，做题和看评估
6. 打开 Tracker，查看下一步建议

### 6.3 首版前端实现优先顺序

推荐按下面顺序落地：

1. `Login`
2. `Dashboard`
3. `Resume`
4. `Jobs`
5. `Interview`
6. `Tracker`

这样做的原因是：

- Login + Dashboard 先建立完整产品骨架
- Resume / Jobs 最容易形成直接可演示主路径
- Interview / Tracker 放在第二批补齐完整工作流

## 7. 结论

当前这套 Figma 设计不是脱离实现的“概念图”。

它已经能够稳定映射到现有后端能力，并且满足：

- 作品集讲解
- 前端切页规划
- 后续子代理继续开发

真正要记住的核心原则只有一条：

> 页面可以比接口更完整，但页面不能假装后端已经支持当前并不存在的能力。
