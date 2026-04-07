# AI 面试官对练功能设计

> 日期：2026-04-07 | 状态：已批准

## 1. 概述与目标

**功能名称：** AI 面试官对练（Interview Coach）

**核心价值：** 用户选择简历和目标岗位，与 AI 面试官进行多轮真实面试练习，包含统一追问轮、实时评分和结构化复盘报告。

**用户场景：**
1. 用户选择简历 + 目标岗位 JD
2. AI 面试官开场自我介绍，介绍岗位背景
3. 用户逐一回答主问题，每题提交后实时显示得分
4. 主问题轮结束后进入统一追问轮
5. 用户回答追问
6. 练习结束，输出结构化复盘报告
7. 会话记录保存，可回看历史

---

## 2. 核心流程

```
用户开始练习
    ↓
AI 面试官开场（自我介绍 + 岗位背景）
    ↓
主问题轮（N 个问题，用户逐一回答，每题实时评分）
    ↓
追问轮（全部回答完后，AI 统一追问一轮）
    ↓
结构化复盘报告（技术深度、逻辑表达、岗位匹配度、沟通能力）
    ↓
保存本次会话记录
```

---

## 3. 后端架构

### 3.1 核心组件

**InterviewCoachAgent** (`src/business_logic/interview/interview_coach_agent.py`)
- 封装 AgentExecutor 的多轮面试 Agent
- 使用 ReAct 循环
- 持有多轮状态（当前问题索引、是否已追问、已收集的回答）
- Tools: `read_resume`、`generate_next_question`、`ask_followup`、`provide_score`

**InterviewSessionManager** (`src/business_logic/interview/session_manager.py`)
- 管理会话状态和流程编排
- 驱动整个对话流程（开场 → 主问题轮 → 追问轮 → 评分 → 复盘）
- 不直接做 LLM 调用，委托给 Agent

**ReviewReportGenerator** (`src/business_logic/interview/review_report_generator.py`)
- 生成结构化复盘报告
- 按维度评分：技术深度、逻辑表达、岗位匹配度、沟通能力
- 生成改进建议列表
- 输出纯文本 Markdown

### 3.2 API 端点

| 端点 | 方法 | 说明 |
|------|------|------|
| `/interview/sessions/{session_id}/start` | POST | 基于 JD + 简历启动练习，返回开场白 |
| `/interview/sessions/{session_id}/answer` | POST | 提交回答，返回下一题或追问 |
| `/interview/sessions/{session_id}/end` | POST | 结束练习，返回完整复盘报告 |
| `/interview/sessions/{session_id}/report` | GET | 获取历史复盘报告 |

### 3.3 数据模型

**InterviewSession** — 增加字段：
- `jd_text: str` — 岗位 JD 全文
- `resume_id: int` — 关联简历 ID
- `status: str` — `active` / `completed`

**InterviewRecord** — 增加字段：
- `question_index: int` — 问题序号
- `is_followup: bool` — 是否为追问（True 则为追问轮）

---

## 4. 前端架构

### 4.1 页面改造

改造现有 `interview-page.tsx`，复用其简历/JD 选择逻辑，新增三个子区域：

- **ChatBubble** — 渲染 AI 提问和用户回答，带实时分数字段
- **ReviewReportCard** — 渲染结构化评分 + 改进建议
- **ScoreTag** — 每题提交后显示的实时得分标签

### 4.2 状态管理

- `useInterviewSession` — 管理当前会话状态（session_id、question_index、answers[]）
- `useReviewReport` — 获取复盘报告
- 提交回答后立即乐观更新本地分数字段

---

## 5. 错误处理

| 场景 | HTTP 状态码 | 处理方式 |
|------|-------------|---------|
| 简历不存在 | 400 | 返回错误提示"简历不存在" |
| JD 描述为空 | 400 | 提示"岗位描述不能为空" |
| 简历与 JD 非同一用户 | 400 | 提示"简历和岗位必须属于当前用户" |
| LLM 调用超时 | 200 | 返回已收集的回答 + 追问轮标记，提示"连接超时，AI 追问暂不可用" |
| 会话已结束再提交回答 | 409 | 提示"面试已结束" |
| 实时评分 LLM 调用失败 | 200 | 降级为无评分，提示"评分暂不可用" |
| 数据库保存失败 | 200 | 不阻塞复盘报告返回，记录错误日志 |
| 追问轮 LLM 失败 | 200 | 跳过追问轮，直接进入复盘，保证核心功能不阻塞 |

---

## 6. 测试策略

| 测试类型 | 覆盖目标 |
|----------|---------|
| `tests/unit/business_logic/interview/test_interview_coach_agent.py` | Agent 初始化、流程状态转换 |
| `tests/unit/business_logic/interview/test_review_report_generator.py` | 报告生成逻辑、维度评分 |
| `tests/unit/business_logic/interview/test_session_manager.py` | 会话状态管理、流程驱动 |
| `tests/integration/interview/test_interview_flow.py` | 完整流程端到端（start → answer → end） |

---

## 7. 与现有实现的差异

| | 现有 interview_agent | 新设计 |
|---|---|---|
| 对话形态 | 单轮问答，无追问 | 主问题轮 → 追问轮 |
| 评分时机 | 全部结束 | 每题实时 + 全局复盘 |
| 输入 | 仅 JD | JD + 简历（Agent 读取） |
| 报告 | 无结构化复盘 | 结构化评分 + 改进建议 |
| 记忆 | 无 | 会话持久化，可回看历史 |
