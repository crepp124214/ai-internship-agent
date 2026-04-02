# Agent 团队启动模板

当有新任务到来、并且项目需要复用 [`AGENT_TEAM.md`](../../AGENT_TEAM.md) 中定义的长期团队时，就使用这份模板。

## 1. 主代理启动流程

主代理收到新任务后，先固定执行这些步骤：

1. 阅读 [`AGENT_TEAM.md`](../../AGENT_TEAM.md)
2. 判断任务类型：
   - 单模块任务
   - 双模块并行任务
   - 跨模块阶段任务
3. 把任务映射到固定团队角色
4. 只激活本次真正需要的角色
5. 明确：
   - 目标
   - 非目标
   - 边界
   - 必须运行的测试
   - 最终验收规则
6. 给每个被选中的模块负责人发送标准化任务
7. 收集标准化回报
8. 由主代理统一输出一份汇总给用户

## 2. 默认角色映射

- 认证 / 登录 / 当前用户上下文 -> `User lead`
- resume CRUD / resume 智能能力 / resume API -> `Resume lead`
- job CRUD / 搜索 / 筛选 / 岗位侧业务逻辑 -> `Job lead`
- interview CRUD / session / record / interview 智能能力 -> `Interview lead`
- 投递生命周期 / 状态流转 / tracker API -> `Tracker lead`
- provider 适配器 / factory / 共享 agent 基础设施 -> `LLM/Core lead`
- 回归安全 / 合同漂移 / 测试对齐 -> `Data/Test lead`

无论什么任务，都默认包含 `Main agent / PM` 做协调和最终验收。

## 3. 工作模式

### A. 单模块任务

当只有一个模块真正拥有这次改动时，使用这种模式。

默认激活角色：

- `Main agent / PM`
- 一个模块负责人
- 如果测试风险单独需要处理，再加 `Data/Test lead`

例子：

- 修登录 bug -> `User lead`

### B. 双模块并行任务

当两个写入范围互不冲突、但任务彼此相关时，使用这种模式。

默认激活角色：

- `Main agent / PM`
- 两个模块负责人
- 如果回归风险不低，再加 `Data/Test lead`

例子：

- 新增 resume 智能能力并更新共享 provider -> `Resume lead` + `LLM/Core lead`

### C. 跨模块阶段任务

当任务会触及两个以上模块或共享合同，且需要分阶段推进时，使用这种模式。

默认激活角色：

- `Main agent / PM`
- 当前阶段真正需要的模块负责人
- `Data/Test lead` 负责回归与合同检查

例子：

- 在多个 API 中铺开 current-user context

## 4. 标准任务模板

发给每个子代理的任务应固定成这个形状：

```text
你是 <角色名称>。

写入范围：
- <只列出该角色负责的文件或模块>

目标：
- <这个角色必须交付的内容>

非目标：
- <这个角色不能顺手扩展的范围>

约束：
- 遵守 AGENT_TEAM 边界
- 未明确分配时，不修改别的模块
- 遇到跨模块问题时回报给 Main agent

测试：
- <必须运行的测试文件或命令>

最终回报：
- changed files
- implemented capability
- remaining risk
- tests run
- test result
- downstream dependency
```

## 5. 标准子代理回报格式

所有模块负责人回报时都固定按这个顺序：

1. changed files
2. implemented capability
3. remaining risk
4. tests run
5. test result
6. downstream dependency

## 6. 主代理汇总格式

收齐所有回报后，主代理按这个顺序汇总：

1. 当前阶段目标
2. 激活了哪些角色
3. 各角色分别交付了什么
4. 主代理做了哪些跨模块决策
5. 已完成哪些验证
6. 剩余风险
7. 推荐下一阶段

## 7. Dry-run 示例

### 示例 1：单模块任务

任务：

- “修复 resume 更新 bug”

激活角色：

- `Main agent / PM`
- `Resume lead`
- 若回归风险较高，再加 `Data/Test lead`

### 示例 2：双模块并行任务

任务：

- “基于共享 provider 增加 resume AI 能力”

激活角色：

- `Main agent / PM`
- `Resume lead`
- `LLM/Core lead`
- `Data/Test lead`

### 示例 3：跨模块阶段任务

任务：

- “把 current-user context 铺到剩余 API”

激活角色：

- `Main agent / PM`
- `User lead`
- 当前受影响的模块负责人
- `Data/Test lead`

## 8. 长期使用规则

这份模板是后续任务的默认启动协议。

这支团队应该被当成：

- 一个持久的项目定义
- 一个可复用的协作模型
- 而不是每个会话里都重新造一遍的一次性团队设计
