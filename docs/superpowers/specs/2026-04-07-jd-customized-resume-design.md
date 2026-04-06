# JD 定制简历功能设计

> 日期：2026-04-07 | 状态：已批准

## 1. 概述与目标

**功能名称：** JD 定制简历（JD-Customized Resume）

**核心价值：** 用户选择一份已有简历和目标岗位，系统自动分析简历与 JD 的匹配度，生成针对该岗位定制的简历内容，并输出匹配报告。

**用户场景：**
1. 用户上传/已有简历 + 选择目标岗位 JD
2. 系统解析 JD 关键词和要求
3. 系统计算简历与 JD 的匹配度
4. Agent 生成针对该 JD 优化过的简历内容
5. 用户获得定制简历 + 匹配报告

---

## 2. 系统架构

### 2.1 架构决策：混合架构

```
API Layer (presentation)
    │
    ├── JdParserService     ← 直接调用（同步解析，无 LLM）
    ├── ResumeMatchService  ← 直接调用（匹配度计算，无 LLM）
    │
    └── ResumeCustomizerAgent ← AgentExecutor ReAct 循环（LLM 生成）
             │
             ├── read_resume      (Tool)
             └── match_resume_to_job (Tool)
```

**决策理由：**
- JD 解析和匹配度计算为确定性逻辑，无需 LLM，直接服务调用更简洁高效
- 简历生成需要 LLM 能力，使用 AgentExecutor 复用已建立的 ReAct 循环基础设施
- 两者分离便于独立测试和演进

### 2.2 目录结构

```
src/business_logic/jd/
├── __init__.py
├── jd_parser_service.py      # JD 解析服务
├── resume_match_service.py   # 简历匹配服务
├── resume_customizer_agent.py # AI 定制 Agent
├── schemas.py                # JD/匹配相关 Pydantic Schema
└── tools/
    ├── __init__.py
    ├── read_resume.py        # 读取简历内容 Tool
    └── match_resume_to_job.py # 简历-JD 匹配 Tool

src/presentation/api/v1/
└── resumes.py                # 新增 /customize-for-jd 端点

frontend/src/pages/
└── jd-customize-page.tsx     # 定制简历页面

frontend/src/lib/
├── api/
│   └── resumes.ts            # 前端 API 客户端
└── components/
    └── MatchReportCard.tsx   # 匹配报告卡片组件
```

---

## 3. Backend 详细设计

### 3.1 API 端点

**端点：** `POST /api/v1/resumes/{resume_id}/customize-for-jd`

**请求 Schema：**

```python
class ResumeCustomizeRequest(BaseModel):
    jd_id: int                          # 目标岗位 ID
    custom_instructions: str | None     # 用户可选的定制指令
    enable_match_report: bool = True    # 是否输出匹配报告
```

**响应 Schema：**

```python
class ResumeCustomizeResponse(BaseModel):
    customized_resume: str              # 定制后的简历内容（纯文本）
    match_report: MatchReport | None     # 匹配报告
    session_id: str                     # 本次 Agent 执行 session_id（用于追踪）

class MatchReport(BaseModel):
    keyword_coverage: dict[str, bool]   # 关键词 → 是否覆盖
    match_score: float                   # 0.0 ~ 1.0 匹配度
    gaps: list[str]                     # 未覆盖的关键要求
    suggestions: list[str]              # 改进建议
```

**错误响应：**
- `404` — 简历或 JD 不存在
- `400` — 简历与 JD 不匹配（ Resume 与 Job 不同用户）
- `500` — Agent 执行失败

### 3.2 JdParserService

**文件：** `src/business_logic/jd/jd_parser_service.py`

```python
class JdParserService:
    """解析 Job Description，提取结构化信息"""

    def parse(self, jd_text: str) -> ParsedJD:
        """
        输入: JD 纯文本
        输出: ParsedJD(含公司信息、职位、关键技能要求、资质等)
        """

class ParsedJD(NamedTuple):
    company: str | None
    position: str
    required_skills: list[str]     # 关键技术/工具关键词
    qualifications: list[str]      # 资质/经验要求
    highlights: list[str]          # 职位亮点/加分项
    raw_text: str
    jd_id: str = ""                # 用于追踪的临时 ID
```

**解析规则：**
- 按行解析，识别 `要求`、`必备`、`加分`、`优先` 等关键词
- 使用正则提取技能关键词（技术栈、工具名）
- 公司名和职位名从开头行推断

### 3.3 ResumeMatchService

**文件：** `src/business_logic/jd/resume_match_service.py`

```python
class ResumeMatchService:
    """计算简历与 JD 的匹配度"""

    def compute_match(
        self,
        resume_text: str,
        parsed_jd: ParsedJD,
    ) -> MatchReport:
        """
        输入: 简历文本 + 解析后的 JD
        输出: MatchReport(keyword_coverage, match_score, gaps, suggestions)
        """

    def _compute_keyword_coverage(
        self,
        resume_text: str,
        required_skills: list[str],
    ) -> dict[str, bool]: ...

    def _compute_match_score(
        self,
        keyword_coverage: dict[str, bool],
    ) -> float: ...  # 返回 0.0 ~ 1.0

    def _identify_gaps(
        self,
        keyword_coverage: dict[str, bool],
        qualifications: list[str],
    ) -> list[str]: ...

    def _generate_suggestions(
        self,
        gaps: list[str],
        highlights: list[str],
    ) -> list[str]: ...
```

### 3.4 ResumeCustomizerAgent

**文件：** `src/business_logic/jd/resume_customizer_agent.py`

```python
class ResumeCustomizerAgent:
    """
    基于 AgentExecutor 的简历定制 Agent
    使用 ReAct 循环：read_resume → match_resume_to_job → 生成定制内容
    """

    def __init__(
        self,
        llm: LiteLLMAdapter,
        tool_registry: ToolRegistry,
        memory: MemoryStore,
    ): ...

    async def customize(
        self,
        resume_id: int,
        jd_id: int,
        custom_instructions: str | None,
        session_id: str,
    ) -> str:
        """
        执行简历定制，返回定制后的简历文本
        通过 AgentExecutor.run() 运行 ReAct 循环
        """
```

**Agent Prompt 策略：**
- System Prompt：设定为资深简历顾问角色
- User Context：注入简历原文、JD 关键信息、MatchReport、用户指令
- 输出格式：纯文本简历，使用 Markdown 格式便于阅读

**使用的 Tools：**
| Tool | 用途 |
|------|------|
| `read_resume` | 获取简历原文内容 |
| `match_resume_to_job` | 获取匹配度分析结果 |

### 3.5 Tools 定义

**read_resume** (`src/business_logic/jd/tools/read_resume.py`)

```python
class ReadResumeTool(BaseTool):
    name: str = "read_resume"
    description: str = "读取简历的完整内容"
    args_schema: Type[BaseModel] = ReadResumeInput

    def _execute(self, resume_id: int, runtime: AgentRuntime) -> dict:
        # 调用 ResumeRepository 获取简历
        # 返回 {"resume_text": "...", "resume_id": resume_id}
```

**match_resume_to_job** (`src/business_logic/jd/tools/match_resume_to_job.py`)

```python
class MatchResumeToJobTool(BaseTool):
    name: str = "match_resume_to_job"
    description: str = "分析简历与目标岗位的匹配度"
    args_schema: Type[BaseModel] = MatchResumeToJobInput

    def _execute(self, resume_id: int, jd_id: int, runtime: AgentRuntime) -> dict:
        # 调用 JdParserService + ResumeMatchService
        # 返回 MatchReport dict
```

---

## 4. Frontend 详细设计

### 4.1 页面布局

**文件：** `frontend/src/pages/jd-customize-page.tsx`

**布局：双栏式**

```
┌─────────────────────────────────────────────────────────┐
│  JD 定制简历                                             │
├──────────────────────────┬────────────────────────────┤
│  简历选择                   │  目标岗位 JD 选择             │
│  [下拉选择已有简历 ▼]        │  [下拉选择岗位 ▼]             │
│  [简历预览区]               │  [JD 预览区]                 │
│                          │                             │
│  定制指令（可选）            │                             │
│  [在此输入特殊要求...]       │                             │
│                          │                             │
│  [🚀 开始定制简历]           │                             │
├──────────────────────────┴────────────────────────────┤
│  定制结果                                               │
│  ┌─────────────────┐  ┌─────────────────────────────┐ │
│  │  定制后简历        │  │  匹配报告                    │ │
│  │  [Markdown 展示]  │  │  匹配度：85%                 │ │
│  │                  │  │  关键词覆盖：8/10            │ │
│  │                  │  │  差距项：React、TypeScript   │ │
│  │                  │  │  建议：加强 TS 项目经验...   │ │
│  └─────────────────┘  └─────────────────────────────┘ │
│  [📋 复制简历]  [💾 保存]                               │
└─────────────────────────────────────────────────────────┘
```

### 4.2 组件清单

| 组件 | 文件 | 职责 |
|------|------|------|
| `JdCustomizePage` | `jd-customize-page.tsx` | 页面容器，状态管理 |
| `MatchReportCard` | `MatchReportCard.tsx` | 匹配度可视化卡片 |
| `ResumePreview` | `ResumePreview.tsx` | 简历预览（上下对比用） |
| `JdPreview` | `JdPreview.tsx` | JD 预览 |

### 4.3 API 交互

```typescript
// frontend/src/lib/api/resumes.ts
export const customizeResume = (resumeId: number, jdId: number, customInstructions?: string) =>
  api.post<ResumeCustomizeResponse>(
    `/resumes/${resumeId}/customize-for-jd`,
    { jd_id: jdId, custom_instructions: customInstructions }
  )
```

---

## 5. 数据流

```
User
  │
  ▼
POST /api/v1/resumes/{resume_id}/customize-for-jd
  │
  ▼
┌─────────────────────────────────────────────┐
│ resumes.py 路由处理器                        │
│  1. 验证 resume_id 和 jd_id 存在性           │
│  2. 调用 JdParserService.parse(jd_text)     │
│  3. 调用 ResumeMatchService.compute_match() │
│  4. 调用 ResumeCustomizerAgent.customize()  │
│  5. 组装 ResumeCustomizeResponse             │
└─────────────────────────────────────────────┘
  │
  ▼
ResumeCustomizeResponse
  ├── customized_resume: str  (Agent 生成)
  ├── match_report: MatchReport (计算得出)
  └── session_id: str
```

---

## 6. 错误处理

| 错误场景 | HTTP 状态码 | 错误信息 |
|----------|-------------|----------|
| 简历不存在 | 404 | `Resume not found` |
| JD 不存在 | 404 | `Job description not found` |
| 简历与 JD 非同一用户 | 400 | `Resume and JD must belong to the same user` |
| Agent 生成失败 | 500 | `Resume customization failed: {detail}` |
| LLM Provider 超时 | 504 | `LLM request timeout` |

---

## 7. 测试策略

| 测试类型 | 覆盖目标 |
|----------|----------|
| `tests/unit/business_logic/jd/test_jd_parser_service.py` | JD 解析逻辑 |
| `tests/unit/business_logic/jd/test_resume_match_service.py` | 匹配度计算 |
| `tests/unit/business_logic/jd/test_resume_customizer_agent.py` | Agent prompt 构造 |
| `tests/integration/jd/test_customize_endpoint.py` | API 端到端集成测试 |

---

## 8. 技术约束

- **输出格式：** 定制简历为纯文本（Markdown），非 JSON
- **Agent 复用：** ResumeCustomizerAgent 复用 `src/core/runtime/agent_executor.py` 的 ReAct 循环
- **无前端直接 LLM 调用：** 所有 LLM 调用经过后端 API
- **兼容性：** 本功能为 `JD 定制简历` 主线第一步，后续可扩展为"Agent Workspace"形态
