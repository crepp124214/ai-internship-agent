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

```python
# 工具基类
class BaseTool(ABC):
    name: str
    description: str
    input_schema: dict
    output_schema: dict

    async def execute(self, input: dict, context: Context) -> ToolResult: ...

# 内置工具集
class ResumeTools:
    - read_resume(resume_id) -> Resume
    - update_resume(resume_id, content) -> Resume
    - analyze_resume(resume_text) -> Analysis

class JobTools:
    - search_jobs(query, filters) -> List[Job]
    - match_resume_to_job(resume_id, job_id) -> MatchResult
    - apply_to_job(job_id, resume_id) -> Application

class InterviewTools:
    - generate_questions(job_context, count) -> List[Question]
    - evaluate_answer(question_id, answer) -> Evaluation
```

### 4.3 Agent Skills (`src/business_logic/`)

| Agent | 核心能力 |
|-------|----------|
| `ResumeCustomizerAgent` | JD 解析、匹配度分析、简历定制化重写 |
| `InterviewCoachAgent` | 多轮对话面试、追问、评分、复盘报告 |
| `JobAgent` | 岗位搜索、匹配度评估、投递 |

---

## 五、新增功能详细设计

### 5.1 功能一：JD 定制简历

#### 功能概述

```
输入: 用户简历 + 岗位 JD
输出: 针对性优化的简历 + 匹配度报告 + 差异说明
```

#### API 设计

```python
# POST /api/v1/resumes/{resume_id}/customize-for-jd
Request:
{
    "jd_text": "岗位描述全文",
    "jd_source": "linkedin | zhipin | manual",
    "customization_level": "keyword_injection | partial_rewrite | full_rewrite"
}

Response:
{
    "customized_resume": {
        "original": "原始简历文本",
        "optimized": "优化后简历文本",
        "changes": [
            {
                "section": "项目经历",
                "original": "负责后台开发",
                "optimized": "设计并实现高并发后台系统，支持日均千万级请求",
                "reason": "嵌入 JD 关键词'高并发'"
            }
        ]
    },
    "match_report": {
        "overall_score": 72,
        "keyword_coverage": {
            "required": [{"word": "Python", "covered": true}, {"word": "Redis", "covered": false}],
            "preferred": [{"word": "团队管理", "covered": false}]
        },
        "gaps": ["缺少分布式系统设计经验", "未体现带队经验"],
        "suggestions": ["在项目经历中加入并发相关描述", "补充团队协作经历"]
    }
}
```

#### 核心 Service

| Service | 职责 |
|---------|------|
| `JdParserService` | 解析 JD → 结构化关键词 + 技能权重 |
| `ResumeMatchService` | 对比简历与 JD → 匹配度评分 + 差距分析 |
| `ResumeCustomizerAgent` | 基于分析结果重写简历内容 |

#### JD 解析逻辑

```python
# JdParserService
def parse_jd(jd_text: str) -> JDStructure:
    # 1. 提取硬技能关键词 (Python, Redis, MySQL...)
    hard_skills = extract_skills(jd_text, category="technical")

    # 2. 提取软技能关键词 (团队协作, 沟通...)
    soft_skills = extract_skills(jd_text, category="soft")

    # 3. 提取职责描述
    responsibilities = extract_responsibilities(jd_text)

    # 4. 区分 required vs preferred
    required_skills = filter_required(hard_skills)
    preferred_skills = filter_preferred(hard_skills)

    # 5. 提取职位级别线索 (senior/junior/3-5年)
    level = infer_level(jd_text)

    return JDStructure(
        skills={"required": required_skills, "preferred": preferred_skills},
        responsibilities=responsibilities,
        level=level,
        company_context=extract_company_info(jd_text)
    )
```

#### 匹配度算法

```python
# ResumeMatchService
def calculate_match_score(resume_text: str, jd: JDStructure) -> MatchReport:
    resume_lower = resume_text.lower()

    # 1. 关键词覆盖率
    required_coverage = sum(
        1 for skill in jd.skills["required"]
        if skill.lower() in resume_lower
    ) / len(jd.skills["required"]) * 100

    preferred_coverage = sum(
        1 for skill in jd.skills["preferred"]
        if skill.lower() in resume_lower
    ) / len(jd.skills["preferred"]) * 100

    # 2. 加权总分
    overall = required_coverage * 0.7 + preferred_coverage * 0.3

    # 3. 差距分析
    gaps = []
    for skill in jd.skills["required"]:
        if skill.lower() not in resume_lower:
            gaps.append(f"缺少: {skill}")

    return MatchReport(
        overall_score=round(overall, 1),
        keyword_coverage={"required": required_coverage, "preferred": preferred_coverage},
        gaps=gaps,
        suggestions=generate_suggestions(gaps, jd)
    )
```

#### 前端 UI

```
┌─────────────────────────────────────────────────────────────────────┐
│  JD 定制简历                                    [保存] [一键复制]    │
├──────────────────────────────────┬──────────────────────────────────┤
│  📄 简历                          │  📋 岗位 JD                      │
│  ┌────────────────────────────┐  │  ┌────────────────────────────┐  │
│  │                            │  │  │                            │  │
│  │  [原始简历内容]            │  │  │  粘贴 JD 内容...            │  │
│  │                            │  │  │                            │  │
│  └────────────────────────────┘  │  └────────────────────────────┘  │
│                                  │                                  │
│  匹配度: ████████████░░░ 72%    │  缺失关键词: Redis, 分布式系统   │
│                                  │                                  │
├──────────────────────────────────┴──────────────────────────────────┤
│  ✨ 优化结果                                                      │
│  ┌─────────────────────────────────────────────────────────────┐  │
│  │ [左右对比视图]                                              │  │
│  │ 原始                                      │ 优化版           │  │
│  │ 负责后台开发                              │ 设计并实现...     │  │
│  └─────────────────────────────────────────────────────────────┘  │
│                                                                  │
│  📊 匹配报告                                        [查看详情 ▼]  │
│  ├── 硬技能覆盖: 5/7                                           │
│  ├── 软技能覆盖: 2/3                                           │
│  └── 建议: 在项目中强调并发设计经验                              │
└──────────────────────────────────────────────────────────────────┘
```

---

### 5.2 功能二：AI 面试官对练

#### 功能概述

```
输入: 选择岗位/公司，开始练习
AI: 扮演真实面试官，多轮对话，追问，评分
输出: 全程复盘报告 + 改进建议
```

#### 核心 API

```python
# 1. 创建面试会话
# POST /api/v1/interview/sessions
Request:
{
    "job_id": 123,
    "resume_id": 456,
    "session_type": "technical | hr | behavior | stress | full",
    "difficulty": "easy | medium | hard",
    "company": "目标公司名",
    "focus_areas": ["算法", "系统设计"]
}

Response:
{
    "session_id": "sess_abc123",
    "status": "in_progress",
    "current_question": {
        "id": "q1",
        "type": "behavior",
        "text": "请介绍一下你在最近项目中遇到的最大技术挑战，以及你是如何解决的？",
        "hint": "建议使用 STAR 法则回答",
        "expected_duration": "2-3分钟"
    }
}

# 2. 用户回答
# POST /api/v1/interview/sessions/{session_id}/answer
Request:
{
    "answer": "在那个项目中，我遇到了..."
}

Response:
{
    "status": "continue | completed",
    "evaluation": {
        "score": 78,
        "strengths": ["逻辑清晰", "有具体例子"],
        "improvements": ["可以更具体地描述技术细节", "STAR 结构可以更完整"],
        "follow_up_question": "能具体说说你是如何优化那个性能问题的吗？"
    },
    "next_question": {
        "id": "q2",
        "type": "technical",
        "text": "能描述一下你当时使用的系统架构吗？",
        "hint": null
    }
}

# 3. 获取复盘报告
# GET /api/v1/interview/sessions/{session_id}/report
Response:
{
    "session_id": "sess_abc123",
    "duration_minutes": 25,
    "total_questions": 8,
    "overall_score": 76,
    "dimension_scores": {
        "technical_depth": {"score": 72, "max": 100},
        "communication": {"score": 82, "max": 100},
        "problem_solving": {"score": 75, "max": 100},
        "culture_fit": {"score": 80, "max": 100}
    },
    "question_evaluations": [
        {
            "question": "请介绍...",
            "answer": "我...",
            "score": 78,
            "feedback": "STAR 结构完整...",
            "follow_up_answers": ["追问1的回答", "追问2的回答"]
        }
    ],
    "strengths": [
        "项目经验描述具体，有数据支撑",
        "沟通表达清晰有条理"
    ],
    "areas_for_improvement": [
        "系统设计深度不足",
        "对分布式理论理解需加强"
    ],
    "preparation_suggestions": [
        "建议深入学习 CAP 理论",
        "准备一个高并发场景的设计方案"
    ],
    "company_specific_tips": [
        "该公司在面试中常考 LRU 算法",
        "建议准备一个项目深入讲解"
    ]
}
```

#### 数据模型

```python
class InterviewSession:
    id: int
    user_id: int
    job_id: Optional[int]
    resume_id: Optional[int]
    session_type: str
    difficulty: str
    company: Optional[str]
    status: str
    current_question_index: int
    started_at: datetime
    completed_at: Optional[datetime]
    total_duration: Optional[int]

class InterviewQuestion:
    id: int
    session_id: int
    question_type: str
    difficulty: str
    question_text: str
    hint: Optional[str]
    expected_answer: Optional[str]
    order_index: int

class InterviewAnswer:
    id: int
    session_id: int
    question_id: int
    user_answer: str
    score: Optional[int]
    evaluation: Optional[str]
    follow_up_count: int
    created_at: datetime

class InterviewRecord:
    id: int
    session_id: int
    user_id: int
    overall_score: int
    dimension_scores: dict
    strengths: List[str]
    improvements: List[str]
    suggestions: List[str]
    raw_report: dict
    created_at: datetime
```

#### 多轮对话引擎

```python
class InterviewCoachService:
    def __init__(self, interview_agent: InterviewAgent):
        self.agent = interview_agent
        self.conversation_context: List[dict] = []

    async def start_session(self, config: SessionConfig) -> Session:
        context = await self._build_context(config)
        first_question = await self.agent.generate_first_question(context, config)
        session = await self._create_session(config, first_question)
        return session

    async def process_answer(self, session_id: str, answer: str) -> AnswerResponse:
        session = await self._get_session(session_id)
        evaluation = await self.agent.evaluate_answer(
            question=session.current_question,
            answer=answer,
            context=session.context
        )
        await self._save_answer(session, evaluation)

        if evaluation.score < 60:
            follow_up = await self.agent.generate_follow_up(
                question=session.current_question,
                answer=answer,
                evaluation=evaluation
            )
            await self._add_follow_up(session, follow_up)
            return AnswerResponse(status="continue", next_question=follow_up)

        elif self._should_transition(evaluation):
            next_question = await self.agent.generate_next_question(
                session=session,
                completed_type=session.current_question.type
            )
            await self._advance_session(session, next_question)
            return AnswerResponse(status="continue", next_question=next_question)

        else:
            report = await self._generate_report(session)
            await self._complete_session(session, report)
            return AnswerResponse(status="completed", report=report)
```

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

### 删除模块

```
删除:
  src/business_logic/tracker/
  src/business_logic/agents/tracker_agent/
  src/presentation/api/v1/tracker.py
  src/data_access/entities/tracker.py
  src/data_access/repositories/tracker_repository.py
  src/data_access/repositories/tracker_advice_repository.py
  frontend/src/pages/tracker-page.tsx
```

### 新增目录与文件

```
新增目录:
  src/business_logic/jd/
  src/business_logic/interview/

新增后端文件:
  src/business_logic/jd/
    ├── __init__.py
    ├── parser_service.py
    ├── match_service.py
    └── customizer_service.py

  src/business_logic/interview/
    ├── __init__.py
    ├── coach_service.py
    ├── question_generator.py
    └── scoring_service.py

  src/data_access/entities/
    ├── interview_session.py
    └── interview_record.py

新增前端文件:
  frontend/src/pages/
    ├── jd-customize-page.tsx
    └── interview-coach-page.tsx

  frontend/src/components/
    ├── jd-input-panel.tsx
    ├── resume-diff-view.tsx
    ├── match-report.tsx
    ├── interview-chat.tsx
    ├── question-card.tsx
    ├── answer-input.tsx
    ├── evaluation-panel.tsx
    └── interview-report.tsx

重构前端文件:
  frontend/src/app/router.tsx
```

---

*文档版本: v0.3.0 | 待实现*
