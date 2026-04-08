# Agent 驱动简历/岗位页面 — 设计文档

> **创建时间：** 2026-04-08
> **状态：** 草稿

---

## 1. 背景与目标

### 1.1 当前问题

简历和岗位功能缺乏 Agent 智能，主流交互模式是"点一下按钮 → 一次 LLM 调用 → 返回结果"，用户没有感受到 Agent 的推理和规划能力。

具体问题：
- **简历匹配**：用户手动录入岗位，再选简历匹配，逻辑鸡肋（自己填的岗位当然知道为什么投）
- **岗位搜索**：搜的是用户自己录入的本地库，不是真实可投递的机会
- **Agent 缺位**：AgentExecutor、ToolRegistry 等基础设施已实现，但简历/岗位页面没有使用

### 1.2 目标

将简历和岗位页面改造为 **Agent 驱动** 的智能界面：

| 界面 | 改造目标 |
|------|----------|
| `/resume` | Agent 助手面板：分析建议、解读简历 |
| `/jobs` | Agent 助手面板：网络搜索公司招聘官网 + 分析 |
| `/workspace` | 保持对话式 ReAct 多步推理 |

核心设计原则：**简历是核心数据，Agent 围绕简历主动推理，网络搜索提供外部岗位信息。**

---

## 2. 设计方案

### 2.1 整体布局

简历页面和岗位页面采用 **主区域 + 右侧助手面板** 的双栏布局：

```
┌─────────────────────────────────────────────────────────┐
│  页面标题                                                │
├────────────────────────────┬────────────────────────────┤
│                            │                            │
│  主区域（现有功能不变）       │  Agent 助手面板            │
│                            │                            │
│  - 简历/岗位列表            │  - 对话历史                 │
│  - 详情预览                 │  - 分析结果展示             │
│  - 表单操作                 │  - 快捷建议按钮            │
│                            │  - 输入框                  │
│                            │                            │
└────────────────────────────┴────────────────────────────┘
```

**助手面板职责：** 提供基于当前选中资源的智能分析、建议、解读。**不改变左侧主区域的内容**。

### 2.2 Agent 助手面板

#### 组件结构

```
AgentAssistantPanel
├── Header（固定标题："Agent 助手"）
├── MessageList（对话历史 + 分析结果，只读）
├── QuickActions（快捷建议按钮，用户可点击触发动作）
└── InputBar（输入框，用户可随时提问）
```

#### 能力范围

1. **对话**：用户输入问题，Agent 根据当前页面上下文（简历/岗位列表）回答
2. **动作触发**：用户点击快捷按钮，Agent 执行动作，结果展示在面板内
3. **主动建议**：Agent 根据当前状态主动给出建议（如"检测到简历缺少项目经验，建议补充"）

#### 上下文感知

- 面板知道当前页面类型（`resume` 或 `job`）
- 面板知道当前选中的资源 ID（简历 ID 或岗位 ID）
- 用户在面板里选择"分析简历A"，Agent 就分析简历A（**显式指定**）

#### 对话历史

- **跟随页面切换清除**：切换到简历页面，面板清空；切换到岗位页面，重新开始
- 原因：实现简单，符合用户心理模型（每个页面有独立的 Agent 助手）

### 2.3 简历页面 (`/resume`) 改造

#### 左侧（不变）

- 简历列表 + 详情预览
- 上传新简历功能
- JD 定制简历入口

#### 右侧 Agent 助手面板

**打开页面时：**
1. Agent 自动读取当前选中的简历
2. 分析后给出摘要和问题提示（主动）

**用户可触发：**
- "分析这份简历" → 深度分析，给出优势/劣势/建议
- "我适合什么岗位？" → 基于简历生成岗位方向建议
- "这份简历有什么问题？" → 诊断问题，列出优先级

**对话能力：**
- 用户随时输入问题，Agent 基于当前简历上下文回答

### 2.4 岗位页面 (`/jobs`) 改造

#### 左侧（不变）

- 我的岗位列表（手动录入）
- 添加岗位入口
- 现有 CRUD 功能

#### 右侧 Agent 助手面板

**"搜索岗位"流程（核心新功能）：**

```
用户点击"🔍 搜索岗位"按钮
  ↓
Agent 询问："您想找什么类型的工作？在哪里？"
  ↓
用户输入："深圳 Python 实习"
  ↓
Agent 调用 web_search：
  搜索词："深圳 Python 实习 2026 校招 官网"
  ↓
返回搜索结果（公司 + 官网链接），以内嵌列表形式展示：
  1. 字节跳动校园招聘 → https://jobs.bytedance.com/campus
  2. 腾讯校园招聘 → https://careers.qq.com
  3. 虾皮春招 → https://careers.shopee.cn
  ↓
用户点击某个公司官网
  ↓
Agent 访问该官网 → 搜索该公司的 Python 实习岗位
  ↓
展示该公司具体岗位列表
  ↓
用户选择一个岗位
  ↓
Agent 分析：该岗位与用户简历的匹配度
  ↓
用户可选择：保存到"我的岗位" / 继续分析 / 定制简历
```

**关键设计点：**
- 搜索结果返回的是**公司招聘官网链接**，不是具体岗位列表
- Agent 负责在官网内进一步获取/分析岗位信息
- 全程在右侧面板内完成，不需要切换到主区域

**我的岗位列表中的作用：**
- 用户在官网找到感兴趣的岗位后，可复制 JD 文本，手动录入"我的岗位"
- 或者：Agent 辅助生成 JD 文本，用户确认后保存

### 2.5 Agent Workspace (`/workspace`) 改造

#### 保持现有交互

- ChatPanel + ToolPalette 对话式交互
- 支持复杂多步任务（JD 定制简历、面试对练等）

#### ToolPalette 改造

**问题：** 当前工具列表是硬编码的，没有从后端动态获取。

**改造：**
- API 端点：`GET /api/v1/agent/tools` 返回当前用户可用的工具列表
- 前端 ToolPalette 调用该 API 获取工具（缓存在组件状态）
- 工具按 category 分组展示（resume / job / interview / common）

---

## 3. 技术架构

### 3.1 组件清单

| 组件 | 文件路径 | 说明 |
|------|----------|------|
| `AgentAssistantPanel` | `frontend/src/components/agent/AgentAssistantPanel.tsx` | 可复用组件，简历/岗位页面共用 |
| `useAgentAssistant` | `frontend/src/hooks/useAgentAssistant.ts` | 面板逻辑 Hook，管理对话历史、上下文、API 调用 |
| 简历页面改造 | `frontend/src/pages/resume-page.tsx` | 嵌入 AgentAssistantPanel |
| 岗位页面改造 | `frontend/src/pages/jobs-page.tsx` | 嵌入 AgentAssistantPanel |
| API 端点（工具列表） | `src/presentation/api/v1/agent.py` | GET `/agent/tools` |
| 后端助手服务 | `src/business_logic/agent/assistant_service.py` | 新建，处理助手面板的对话请求 |

### 3.2 API 设计

#### GET `/api/v1/agent/tools`

返回当前用户可用的工具列表。

**响应：**
```json
{
  "tools": [
    { "name": "read_resume", "description": "读取简历内容", "category": "resume" },
    { "name": "analyze_resume_skills", "description": "分析简历技能标签", "category": "resume" },
    { "name": "search_jobs", "description": "搜索公司招聘官网", "category": "job" },
    { "name": "analyze_jd", "description": "解析 JD 关键要求", "category": "job" },
    { "name": "web_search", "description": "网络搜索", "category": "common" }
  ]
}
```

#### POST `/api/v1/agent/assistant/chat`

助手面板的对话接口。

**请求：**
```json
{
  "message": "帮我分析这份简历",
  "context": {
    "page": "resume",
    "resource_id": 123,
    "resource_ids": [123, 456]
  },
  "history": [
    { "role": "user", "content": "我适合什么岗位？" },
    { "role": "assistant", "content": "根据您的简历..." }
  ]
}
```

**响应：** SSE 流式，返回 Agent 的推理过程和最终结果。

### 3.3 后端助手服务

`AssistantService` 的职责：

1. 接收用户消息 + 当前上下文（页面类型、资源 ID）
2. 构建 System Prompt（注入当前简历/岗位上下文）
3. 调用 `AgentExecutor` 执行 ReAct 循环
4. 流式返回推理过程和结果

**System Prompt 策略：**
```
你是简历/岗位页面的智能助手。
当前用户正在查看 {page} 页面，选中的资源 ID：{resource_id}。
你可以使用以下工具：{available_tools}。
```

### 3.4 工具链

#### 简历类工具

| 工具 | 功能 | 实现文件 |
|------|------|----------|
| `read_resume` | 读取简历完整内容 | `src/business_logic/jd/tools/read_resume.py` |
| `analyze_resume_skills` | 提取并分析技能标签 | `src/business_logic/jd/tools/analyze_resume_skills.py` |
| `format_resume` | 格式化简历为结构化输出 | `src/business_logic/jd/tools/format_resume.py` |

#### 岗位类工具

| 工具 | 功能 | 实现文件 |
|------|------|----------|
| `search_jobs` | 网络搜索公司招聘官网 | `src/business_logic/job/tools/search_jobs.py` |
| `analyze_jd` | 深度解析 JD（技能、经验要求） | `src/business_logic/job/tools/analyze_jd.py` |

#### 通用工具

| 工具 | 功能 | 实现文件 |
|------|------|----------|
| `web_search` | 网络搜索 | `src/business_logic/common/tools/web_search.py` |

**注意：** `search_jobs` 工具内部调用 `web_search`，专门负责"搜索公司招聘官网"这个语义任务。

---

## 4. 数据流

### 4.1 简历页面 Agent 对话流程

```
用户打开简历页面
  ↓
前端加载当前选中简历 ID
  ↓
AgentAssistantPanel 初始化
  ↓
发送"auto_analyze"请求（含简历 ID）
  ↓
后端 AssistantService
  → 读取简历内容
  → 构建分析 prompt
  → AgentExecutor 执行（可能调用 read_resume, analyze_resume_skills）
  → 流式返回分析结果
  ↓
前端在面板内展示："检测到以下问题..."
  ↓
用户输入："我应该怎么改？"
  ↓
继续对话，Agent 基于同一简历上下文回答
```

### 4.2 岗位页面搜索流程

```
用户点击"🔍 搜索岗位"
  ↓
面板输入框自动获得焦点
  ↓
用户输入："深圳 Python 实习"
  ↓
POST /agent/assistant/chat
  {
    "message": "帮我搜索深圳 Python 实习的公司招聘官网",
    "context": { "page": "job" }
  }
  ↓
后端 AssistantService
  → 调用 web_search（搜索词："深圳 Python 实习 2026 校招 官网"）
  → 格式化结果为列表
  → 流式返回
  ↓
前端以内嵌列表展示搜索结果（公司名 + 官网链接）
  ↓
用户点击"字节跳动"
  ↓
POST /agent/assistant/chat
  {
    "message": "查看字节跳动的 Python 实习岗位",
    "context": { "page": "job", "selected_url": "https://jobs.bytedance.com/campus" }
  }
  ↓
后端 AssistantService
  → Agent 访问该 URL，搜索 Python 实习
  → 返回具体岗位列表
  ↓
用户选择一个岗位
  ↓
POST /agent/assistant/chat
  {
    "message": "这个岗位和我的简历匹配吗？",
    "context": { "page": "job", "selected_url": "...", "resume_id": 123 }
  }
  ↓
后端读取简历 + 分析 JD → 返回匹配度 + 理由
```

---

## 5. 实现顺序

### Phase 1: Agent 助手面板基础设施

1. 创建 `AgentAssistantPanel` 组件（可复用）
2. 创建 `useAgentAssistant` Hook
3. 创建后端 `assistant_service.py`
4. 实现 `POST /api/v1/agent/assistant/chat` 接口
5. 实现 `GET /api/v1/agent/tools` 接口
6. 简历页面嵌入 AgentAssistantPanel

### Phase 2: 简历页面 Agent 功能

7. 实现 `analyze_resume_skills` 工具（如果尚未完成）
8. Agent 自动分析当前选中简历
9. 对话能力集成

### Phase 3: 岗位页面 Agent + 搜索功能

10. 实现 `search_jobs` 工具（调用 web_search）
11. 岗位页面嵌入 AgentAssistantPanel
12. 搜索结果内展示流程

### Phase 4: ToolPalette 动态化

13. 前端 ToolPalette 调用 `/agent/tools` 获取工具列表
14. 工具按 category 分组展示

---

## 6. 测试策略

| 测试类型 | 覆盖内容 |
|----------|----------|
| 单元测试 | `AssistantService` 逻辑、工具函数 |
| 集成测试 | API 端点（`/agent/assistant/chat`, `/agent/tools`）|
| E2E 测试 | 简历页面 Agent 对话、岗位页面搜索流程 |
| 手动测试 | Agent 面板交互、搜索结果验证 |

---

## 7. 风险与约束

1. **网络搜索稳定性**：依赖外部搜索结果质量，需要考虑超时和结果为空的处理
2. **官网访问限制**：部分公司官网可能需要登录或有人机验证，Agent 无法自动获取岗位
3. **Panel vs 主区域状态**：助手面板不改变主区域状态，用户需要手动将感兴趣的岗位录入"我的岗位"
4. **实现范围**：Phase 1-3 完成后，简历和岗位页面有实质性 Agent 能力提升
