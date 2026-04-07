# AI 实习求职 Agent 系统 — 重构设计文档

> 版本: v0.3.0 | 状态: 设计中 | 日期: 2026-04-06

---

## 一、项目定位与愿景

**定位：** 围绕实习求职全流程的智能 Agent 工作台

**愿景：** 从"LLM 调用包装器"进化为"真正的自主 Agent 系统"——能够感知上下文、执行多步任务、记忆学习、持续迭代

---

## 二、现状问题

| 缺陷 | 说明 | 严重度 |
|------|------|--------|
| **伪 Agent** | 仅有 `execute() → LLM generate()`，无工具、无规划、无记忆 | 🔴 致命 |
| **贫血服务层** | Service = CRUD + LLM 调用，无业务流程编排 | 🔴 致命 |
| **缺失 Runtime** | 无 Agent 执行器、工具注册表、状态机、记忆存储 | 🔴 致命 |
| **前端非 Agent 化** | 纯表单提交，无流式响应、无思维过程可视化 | 🟡 高 |
| **无企业特性** | 多租户、审计、提示词版本、Webhook 缺失 | 🟡 中 |
| **Tracker 鸡肋** | 手动状态管理 + LLM 生成废话，无实际价值 | 🔴 致命 |

### 2.1 Tracker 模块处理

**决策：移除 Tracker 模块**，替换为以下两个高价值功能：

1. **JD 定制简历** — 读 JD → 定制化简历 → 匹配度报告
2. **AI 面试官对练** — 多轮对话、追问、实时评分、复盘报告

---

## 三、重构目标架构

```
┌─────────────────────────────────────────────────────────────┐
│                    Frontend — Agent Workspace                │
│   AgentChat (流式) │ ToolPalette │ MemoryInspector │ Trace  │
└─────────────────────────────────────────────────────────────┘
                              │ SSE / WebSocket
┌─────────────────────────────────────────────────────────────┐
│                    Backend — Agent Runtime                   │
│  AgentExecutor │ ToolRegistry │ StateMachine │ MemoryStore  │
└─────────────────────────────────────────────────────────────┘
                              │
┌─────────────────────────────────────────────────────────────┐
│                    Business Logic — Agent Skills             │
│  ResumeCustomizer │ JDAnalizer │ InterviewCoach │ JobAgent  │
└─────────────────────────────────────────────────────────────┘
```

---

## 四、核心模块设计

### 4.1 Agent Runtime (`src/core/runtime/`)

| 模块 | 职责 |
|------|------|
| `agent_executor.py` | ReAct 执行循环：Plan → Action → Observe → Reflect |
| `tool_registry.py` | 工具注册、发现、版本管理 |
| `state_machine.py` | 求职流程状态机（投递 → 面试 → offer → 入职） |
| `memory_store.py` | 记忆存储（短期会话 + 长期向量） |
| `context_builder.py` | RAG 上下文构建 |

### 4.2 Tool System (`src/core/tools/`)

- 统一工具抽象
- Resume 工具：读取、更新、分析简历
- Job 工具：搜索岗位、匹配岗位、发起投递
- Interview 工具：生成问题、评估答案

### 4.3 Agent Skills (`src/business_logic/`)

| Agent | 核心能力 |
|-------|----------|
| `ResumeCustomizerAgent` | JD 解析、匹配度分析、简历定制化重写 |
| `InterviewCoachAgent` | 多轮对话面试、追问、评分、复盘报告 |
| `JobAgent` | 岗位搜索、匹配度评估、投递 |

---

## 五、新增功能详细设计

### 5.1 功能一：JD 定制简历

- 输入：用户简历 + 岗位 JD
- 输出：针对性优化的简历 + 匹配度报告 + 差异说明
- 关键服务：
  - `JdParserService`
  - `ResumeMatchService`
  - `ResumeCustomizerAgent`

### 5.2 功能二：AI 面试官对练

- 输入：岗位/公司信息、简历上下文、面试配置
- 输出：多轮问答、即时评分、复盘报告
- 关键能力：
  - 创建面试会话
  - 处理用户回答
  - 生成评估与追问
  - 汇总复盘报告

---

## 六、数据流设计

```
用户输入 → AgentExecutor
    ↓
ContextBuilder (RAG 检索 + 会话记忆)
    ↓
Agent.plan() (分解任务，选择工具)
    ↓
循环: ToolRegistry.execute() → 观察结果 → 反思修正
    ↓
流式输出 (SSE) → Frontend AgentChat
    ↓
结果存入 MemoryStore
```

---

## 七、技术选型

| 层面 | 当前 | 重构后 |
|------|------|--------|
| Agent Runtime | 手写 `execute()` | ReAct 框架 |
| 记忆存储 | 无 | Redis + Vector DB (ChromaDB) |
| 流式输出 | 无 | SSE + Server-Sent Events |
| 工具调用 | 直接 LLM | ToolRegistry + JSON Schema 验证 |
| 前端状态 | React Query | React Query + Agent State |

---

## 八、实施计划

| 阶段 | 内容 | 周期 |
|------|------|------|
| **Phase 1** | Agent Runtime 基础设施（Executor, ToolRegistry, BaseTool） | 4 周 |
| **Phase 2** | JD 定制简历（JD解析 + 匹配度评分 + 基础重写） | 2 周 |
| **Phase 3** | AI 面试对练（单轮 Q&A + 立即评分 + 基本复盘） | 2 周 |
| **Phase 4** | AI 面试对练（多轮追问 + 维度评分 + 完整报告） | 2 周 |
| **Phase 5** | Memory & State（MemoryStore, StateMachine, ContextBuilder） | 3 周 |
| **Phase 6** | Frontend Agent Workspace（流式 UI、ToolPalette、Trace） | 3 周 |
| **Phase 7** | JD 定制简历（对比视图 + 关键词注入优化 + 批量优化） | 1 周 |
| **Phase 8** | 企业特性（多租户、审计、Webhook） | 2 周 |

---

## 九、重构验收标准

| 指标 | 目标 |
|------|------|
| 工具数量 | ≥ 15 个 |
| 多步推理 | 平均 ≥ 3 步 |
| 上下文保留 | ≥ 10 轮对话 |
| 流式首字延迟 | < 500ms |
| 测试覆盖率 | ≥ 85% |
| JD 匹配度评分 | 准确率 ≥ 80% |
| 面试评分合理性 | 用户满意度 ≥ 4/5 |

---

## 十、风险与依赖

| 风险 | 影响 | 应对 |
|------|------|------|
| LLM 调用延迟 | 体验下降 | 预加载 + 缓存 |
| 工具 Schema 变更 | 破坏兼容 | 版本化管理 |
| 前端 SSE 连接 | 断开重连 | 自动重连 + 状态同步 |
| JD 解析准确率 | 关键词提取错误 | 提供手动修正 UI |
| 面试评分一致性 | 不同模型评分差异大 | 统一评分 prompt + few-shot |

---

## 十一、文件变更清单

- 删除 `Tracker` 相关后后端、前端和数据访问代码
- 新增 JD 与 interview 的重构目录
- 新增运行时、工具、前端页面与组件

---

*文档版本: v0.3.0 | 待实现*
