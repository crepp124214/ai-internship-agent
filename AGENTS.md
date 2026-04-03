# 项目规则

本文件是项目的唯一配置入口。所有规则、团队、记忆、阶段信息均在此定义。

## 项目定位

- 项目：AI 实习求职 Agent 系统
- 类型：Python 后端 + React 前端工作台
- 目标：围绕求职流程提供可验证、可维护的智能辅助能力

## 架构约束

```
src/
├── presentation/    # API 与请求响应
├── business_logic/  # 业务服务与编排
├── data_access/     # 实体与持久化
└── core/            # LLM/Agent 共享能力
```

依赖方向：`presentation -> business_logic -> data_access`，`core` 可被复用。

禁止：API 直接访问 ORM/Repository、数据层反向依赖上层、在路由层堆积业务逻辑。

## 测试标准

- 分层：unit / integration / e2e
- 修改功能需补测试
- 修复 bug 优先补回归
- 覆盖率目标：>= 80%

## 团队协作

固定角色：

- Main agent / PM — 项目管理、跨模块协调
- User lead — 用户模块与前端
- Resume lead — 简历域
- Job lead — 岗位域
- Interview lead — 面试域
- Tracker lead — 追踪域
- LLM/Core lead — LLM 抽象、核心能力
- Data/Test lead — 数据库、测试

协作规则：

- 一个阶段只有一个主责
- 支持角色只做辅助，不平级接管
- 跨模块冲突由 Main agent 裁决

子代理回报格式（6 段）：

1. changed files
2. implemented capability
3. remaining risk
4. tests run
5. test result
6. downstream dependency

## 阶段状态

- Wave 1 ~ Wave 7：已完成（冻结）
- Wave 8：进行中（稳定性与发布就绪）
- 详细计划：`.sisyphus/plans/PLAN.md`
- 进度快照：`.sisyphus/plans/progress.md`

## 文档结构

```
README.md                    # 项目入口（自包含）
AGENTS.md                    # 本文件（规则、团队、阶段）
.sisyphus/plans/             # 计划与进度
docs/internal/               # 内部工作区（设计稿、提示词、决策）
```

## 协作基线

- 支持 git worktree
- 默认使用 gstack 工作流
- 重要判断优先依据代码现状，其次才参考文档
