# Frontend Agent Workspace 设计文档

> 版本: v1.0.0 | 状态: 设计完成 | 日期: 2026-04-07

---

## 一、目标

将 Dashboard 页面从静态数据展示改造为**交互式 Agent 工作台**。用户带着具体求职任务进来，通过 SSE 流式获取 AI 处理结果，支持 ReAct 推理步骤可视化。

---

## 二、核心架构

```
用户输入（任务） → POST /agent/chat (SSE)
                         ↓
                   AgentExecutor (ReAct 循环)
                         ↓
              ToolRegistry → JD/Interview Agent
                         ↓
                   SSE Stream → Frontend 流式渲染
```

### 后端新增文件

- `src/presentation/api/v1/agent.py` — SSE 流式对话端点
- `src/business_logic/agent/agent_chat_service.py` — 任务路由服务

### 前端改造文件

- `frontend/src/pages/dashboard-page.tsx` — 改造为 Agent Workspace
- `frontend/src/pages/components/AgentChatPanel.tsx` — 新增：流式对话面板
- `frontend/src/pages/components/ToolPalette.tsx` — 新增：工具面板（侧边抽屉）
- `frontend/src/pages/components/TracePanel.tsx` — 新增：ReAct 推理步骤面板
- `frontend/src/pages/components/QuickTaskCard.tsx` — 新增：快捷任务卡片

---

## 三、后端设计

### 3.1 API 端点

**`POST /api/v1/agent/chat`**

请求体：
```json
{
  "task": "帮我定制简历",
  "context": {
    "resume_id": 1,
    "jd_id": 2
  },
  "session_id": "optional-session-id"
}
```

响应：`text/event-stream` (SSE)

事件格式：
```
data: {"type":"step","step":"planning","content":"正在分析任务..."}
data: {"type":"step","step":"tool_call","content":"调用 read_resume 工具"}
data: {"type":"step","step":"observation","content":"简历已读取，共 823 字"}
data: {"type":"step","step":"final","content":"简历定制建议如下..."}
data: {"type":"done"}
```

### 3.2 任务路由逻辑

`AgentChatService` 根据 `task` 内容路由到具体 Agent：

| 任务关键词 | 路由目标 |
|-----------|---------|
| 简历、JD、定制 | JDCustomizerAgent |
| 面试、对练、练习 | InterviewCoachAgent |
| 投递、进度、追踪 | TrackerAgent (已有) |
| 其他通用求职问题 | 通用 LLM 回答 |

### 3.3 AgentExecutor 复用

- 复用 `src/core/runtime/agent_executor.py` 的 ReAct 循环
- 复用 `src/core/runtime/tool_registry.py` 的工具注册
- SSE 通过 `FastAPI StreamingResponse` 实现

---

## 四、前端设计

### 4.1 布局结构

```
┌─────────────────────────────────────────────────────┐
│  Header: "AI 求职助手"  [ToolPalette] [Trace]       │
├─────────────────────────────────────────────────────┤
│  快捷任务区（4个卡片网格）                            │
│  ┌──────────┐ ┌──────────┐ ┌──────────┐ ┌────────┐ │
│  │ JD定制简历│ │ 面试对练 │ │ 岗位推荐  │ │ 投递建议│ │
│  └──────────┘ └──────────┘ └──────────┘ └────────┘ │
├─────────────────────────────────────────────────────┤
│  对话区域（flex-grow，滚动）                         │
│  用户: 帮我定制简历                                  │
│  AI:  正在为你分析简历和JD...█ (streaming)           │
├─────────────────────────────────────────────────────┤
│  底部输入框 + 发送按钮                               │
└─────────────────────────────────────────────────────┘
```

### 4.2 组件说明

**AgentChatPanel**
- 管理 SSE 连接（EventSource 或 fetch stream）
- 实时渲染 AI 输出（逐字或逐行追加）
- 消息历史（当前会话）
- 输入框 + 发送按钮

**ToolPalette**（侧边抽屉）
- 展示可用工具列表（read_resume, jd_parser, match_resume_to_job 等）
- 点击工具可插入对应任务模板到输入框
- 折叠/展开切换

**TracePanel**（底部抽屉，可折叠）
- 显示 ReAct 推理步骤
- 格式：`[Step] 内容`，颜色区分 step/observation/tool_call
- 调试用，非核心用户主要功能

**QuickTaskCard**
- 4 个固定快捷任务入口
- 点击后自动填充输入框并发送

### 4.3 状态管理

使用 Zustand 管理 Agent 状态：
```typescript
interface AgentState {
  messages: Array<{role: 'user'|'ai', content: string}>
  currentTask: string | null
  traceSteps: Array<{step: string, content: string}>
  isStreaming: boolean
  toolPaletteOpen: boolean
  tracePanelOpen: boolean
}
```

---

## 五、数据流

1. 用户输入任务 → 前端发送 POST `/agent/chat`
2. 后端 `AgentChatService` 路由到对应 Agent
3. `AgentExecutor` 执行 ReAct 循环，每步通过 `StreamingResponse` yield SSE 事件
4. 前端 EventSource 接收 SSE，逐条渲染到 `AgentChatPanel`
5. 完整结束后，前端将结果存入 MessageHistory

---

## 六、API 契约

### 请求

```typescript
// POST /api/v1/agent/chat
{
  task: string          // 用户任务描述
  context: {            // 可选上下文
    resume_id?: number
    jd_id?: number
    session_id?: string
  }
}
```

### SSE 事件类型

| type | 说明 |
|------|------|
| `step` | 推理步骤，`step` 字段：`planning`/`tool_call`/`observation`/`final` |
| `done` | 结束信号 |
| `error` | 错误信息 |

---

## 七、文件变更

### 新增

- `src/presentation/api/v1/agent.py`
- `src/business_logic/agent/agent_chat_service.py`
- `frontend/src/pages/components/AgentChatPanel.tsx`
- `frontend/src/pages/components/ToolPalette.tsx`
- `frontend/src/pages/components/TracePanel.tsx`
- `frontend/src/pages/components/QuickTaskCard.tsx`

### 修改

- `frontend/src/pages/dashboard-page.tsx` — 改造为 Agent Workspace
- `frontend/src/lib/api.ts` — 添加 `agentChat()` 方法

---

## 八、测试策略

- 后端 SSE 端点：集成测试（`test_agent_chat_sse.py`）
- 前端流式渲染：Playwright E2E 测试
- 任务路由逻辑：单元测试覆盖各路由分支
