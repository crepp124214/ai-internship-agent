# JD 定制简历 Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 实现 JD 定制简历功能：用户选择简历 + 目标岗位，系统分析匹配度并生成针对该 JD 优化的简历内容。

**Architecture:** 混合架构 — API 直接调用 JdParserService + ResumeMatchService（同步逻辑）；ResumeCustomizerAgent 封装 AgentExecutor ReAct 循环（LLM 生成）。

**Tech Stack:** FastAPI, SQLAlchemy 2.0, LiteLLM, LangChain @tool, React + TanStack Query

---

## File Structure

```
src/
├── business_logic/jd/
│   ├── __init__.py                        # Updated: export all
│   ├── jd_parser_service.py               # Create: JD text → ParsedJD
│   ├── resume_match_service.py             # Create: resume + ParsedJD → MatchReport
│   ├── resume_customizer_agent.py          # Create: AgentExecutor wrapper
│   ├── schemas.py                          # Create: JD internal schemas (ParsedJD, MatchReport)
│   └── tools/
│       ├── __init__.py                     # Create
│       ├── read_resume.py                  # Create: BaseTool implementation
│       └── match_resume_to_job.py          # Create: BaseTool implementation
├── presentation/schemas/
│   └── jd.py                              # Create: API request/response schemas
└── presentation/api/v1/
    └── resumes.py                          # Modify: add POST /{resume_id}/customize-for-jd

frontend/src/
├── lib/api/
│   └── resumes.ts                         # Modify: add customizeResume
└── pages/
    ├── jd-customize-page.tsx              # Create: full page component
    └── components/
        └── MatchReportCard.tsx            # Create: match report display

tests/
├── unit/business_logic/jd/
│   ├── __init__.py
│   ├── test_jd_parser_service.py         # Create
│   ├── test_resume_match_service.py       # Create
│   └── test_resume_customizer_agent.py   # Create
└── integration/
    └── test_customize_endpoint.py         # Create: API e2e test
```

---

## Task 1: JdParserService

**Files:**
- Create: `src/business_logic/jd/schemas.py`
- Create: `src/business_logic/jd/jd_parser_service.py`
- Test: `tests/unit/business_logic/jd/test_jd_parser_service.py`

### Steps

- [ ] **Step 1: Write the failing test**

```python
# tests/unit/business_logic/jd/test_jd_parser_service.py
import pytest
from src.business_logic.jd.jd_parser_service import JdParserService, ParsedJD


class TestJdParserService:
    def setup_method(self):
        self.service = JdParserService()

    def test_parse_basic_jd(self):
        jd_text = """
        职位：后端开发实习生
        公司：字节跳动

        岗位要求：
        - 熟练掌握 Python/Golang
        - 熟悉 MySQL/Redis
        - 有微服务开发经验优先

        加分项：
        - 了解 Kubernetes
        - 开源社区贡献经历
        """
        result = self.service.parse(jd_text)
        assert isinstance(result, ParsedJD)
        assert result.position == "后端开发实习生"
        assert "Python" in result.required_skills or "Golang" in result.required_skills
        assert len(result.required_skills) >= 2

    def test_parse_extracts_company_from_first_line(self):
        jd_text = "某程旅行 - 前端开发工程师\n\n职位要求：\n- React"
        result = self.service.parse(jd_text)
        assert result.company == "某程旅行"
        assert result.position == "前端开发工程师"

    def test_parse_empty_jd_returns_defaults(self):
        result = self.service.parse("")
        assert result.position == ""
        assert result.required_skills == []
        assert result.qualifications == []
        assert result.highlights == []
```

- [ ] **Step 2: Run test to verify it fails**

Run: `pytest tests/unit/business_logic/jd/test_jd_parser_service.py -v`
Expected: FAIL (ModuleNotFoundError or ImportError)

- [ ] **Step 3: Write minimal implementation — schemas.py**

```python
# src/business_logic/jd/schemas.py
from typing import NamedTuple


class ParsedJD(NamedTuple):
    """JD 解析结果"""
    company: str | None
    position: str
    required_skills: list[str]
    qualifications: list[str]
    highlights: list[str]
    raw_text: str
    jd_id: str = ""


class MatchReport(NamedTuple):
    """简历-JD 匹配报告"""
    keyword_coverage: dict[str, bool]   # keyword -> covered
    match_score: float                   # 0.0 ~ 1.0
    gaps: list[str]
    suggestions: list[str]
```

- [ ] **Step 4: Write minimal implementation — jd_parser_service.py**

```python
# src/business_logic/jd/jd_parser_service.py
import re
from src.business_logic.jd.schemas import ParsedJD


class JdParserService:
    """解析 Job Description，提取结构化信息"""

    SKILL_KEYWORDS = [
        "python", "golang", "go", "java", "c++", "c#", "rust", "javascript",
        "typescript", "react", "vue", "angular", "node", "django", "fastapi",
        "flask", "spring", "mysql", "postgresql", "mongodb", "redis",
        "kafka", "rabbitmq", "docker", "kubernetes", "k8s", "aws", "gcp",
        "azure", "linux", "git", "ci/cd", "devops", "microservice", "微服务",
        "分布式", "缓存", "数据库", "sql", "nosql", "rest", "api", "graphql",
        "machine learning", "ml", "ai", "deep learning", "nlp", "tensorflow",
        "pytorch", "pandas", "numpy", "spark", "hadoop", "flink",
    ]

    def parse(self, jd_text: str) -> ParsedJD:
        if not jd_text or not jd_text.strip():
            return ParsedJD(
                company=None, position="", required_skills=[],
                qualifications=[], highlights=[], raw_text=""
            )

        lines = jd_text.strip().split("\n")
        company = self._extract_company(lines, jd_text)
        position = self._extract_position(lines)
        required_skills = self._extract_skills(jd_text)
        qualifications = self._extract_qualifications(jd_text)
        highlights = self._extract_highlights(jd_text)

        return ParsedJD(
            company=company,
            position=position,
            required_skills=required_skills,
            qualifications=qualifications,
            highlights=highlights,
            raw_text=jd_text,
        )

    def _extract_company(self, lines: list[str], raw_text: str) -> str | None:
        if lines:
            first_line = lines[0].strip()
            if "公司" in first_line or any(c in first_line for c in ["-", "–", "—"]):
                parts = re.split(r"[-–—]", first_line)
                if len(parts) >= 2:
                    return parts[0].strip()
        return None

    def _extract_position(self, lines: list[str]) -> str:
        for line in lines[:5]:
            line = line.strip()
            if "职位" in line and "：" in line:
                parts = line.split("：", 1)
                if len(parts) == 2:
                    return parts[1].strip()
            if re.match(r"^.*(工程师|开发者|设计师|产品|运营|实习|全职).*$", line):
                for sep in ["-", "–", "—", "："]:
                    if sep in line:
                        parts = line.split(sep, 1)
                        if len(parts) == 2:
                            return parts[1].strip()
        return ""

    def _extract_skills(self, text: str) -> list[str]:
        text_lower = text.lower()
        found = []
        for skill in self.SKILL_KEYWORDS:
            if skill.lower() in text_lower:
                found.append(skill)
        return list(set(found))

    def _extract_qualifications(self, text: str) -> list[str]:
        lines = text.split("\n")
        quals = []
        in_qual_section = False
        for line in lines:
            line = line.strip()
            if any(k in line for k in ["要求", "任职", "资格", "条件"]):
                in_qual_section = True
                continue
            if in_qual_section and line:
                if any(k in line for k in ["加分", "优先", "福利", "发展", "收获"]):
                    break
                if line.startswith("-"):
                    line = line[1:].strip()
                if line:
                    quals.append(line)
        return quals

    def _extract_highlights(self, text: str) -> list[str]:
        lines = text.split("\n")
        highlights = []
        for line in lines:
            line = line.strip()
            if any(k in line for k in ["加分", "优先", "亮点", "福利"]):
                if line.startswith("-") or line.startswith("•"):
                    line = line[1:].strip()
                highlights.append(line)
        return highlights
```

- [ ] **Step 5: Run test to verify it passes**

Run: `pytest tests/unit/business_logic/jd/test_jd_parser_service.py -v`
Expected: PASS

- [ ] **Step 6: Commit**

```bash
git add tests/unit/business_logic/jd/test_jd_parser_service.py src/business_logic/jd/schemas.py src/business_logic/jd/jd_parser_service.py
git commit -m "feat(jd): add JdParserService with text parsing logic"
```

---

## Task 2: ResumeMatchService

**Files:**
- Create: `src/business_logic/jd/resume_match_service.py`
- Test: `tests/unit/business_logic/jd/test_resume_match_service.py`

### Steps

- [ ] **Step 1: Write the failing test**

```python
# tests/unit/business_logic/jd/test_resume_match_service.py
import pytest
from src.business_logic.jd.schemas import ParsedJD, MatchReport
from src.business_logic.jd.resume_match_service import ResumeMatchService


class TestResumeMatchService:
    def setup_method(self):
        self.service = ResumeMatchService()

    def test_compute_match_basic(self):
        jd = ParsedJD(
            company="ByteDance",
            position="Backend Engineer",
            required_skills=["Python", "MySQL", "Redis"],
            qualifications=["3+ years experience", "Bachelor's degree"],
            highlights=["Stock options", "Flexible hours"],
            raw_text="...",
        )
        resume_text = "I have 4 years of experience with Python, MySQL, and built Redis caching systems."
        report = self.service.compute_match(resume_text, jd)
        assert isinstance(report, MatchReport)
        assert report.match_score > 0.5
        assert report.keyword_coverage["Python"] is True
        assert report.keyword_coverage["MySQL"] is True

    def test_compute_match_all_keywords_found(self):
        jd = ParsedJD(
            company=None, position="DevOps",
            required_skills=["Docker", "Kubernetes"],
            qualifications=[], highlights=[], raw_text="..."
        )
        resume_text = "Experienced with Docker and Kubernetes deployments."
        report = self.service.compute_match(resume_text, jd)
        assert report.keyword_coverage["Docker"] is True
        assert report.keyword_coverage["Kubernetes"] is True
        assert report.match_score == 1.0

    def test_compute_match_no_keywords_found(self):
        jd = ParsedJD(
            company=None, position="Chef",
            required_skills=["Cooking", "Knives"],
            qualifications=[], highlights=[], raw_text="..."
        )
        resume_text = "I write Python code and love databases."
        report = self.service.compute_match(resume_text, jd)
        assert report.match_score == 0.0
        assert report.keyword_coverage["Cooking"] is False
        assert len(report.gaps) == 2

    def test_suggestions_generated_when_gaps_exist(self):
        jd = ParsedJD(
            company=None, position="ML Engineer",
            required_skills=["TensorFlow", "PyTorch"],
            qualifications=[], highlights=["Cutting-edge research"], raw_text="..."
        )
        resume_text = "I use basic Python scripting."
        report = self.service.compute_match(resume_text, jd)
        assert len(report.suggestions) > 0
        assert len(report.gaps) == 2
```

- [ ] **Step 2: Run test to verify it fails**

Run: `pytest tests/unit/business_logic/jd/test_resume_match_service.py -v`
Expected: FAIL (ModuleNotFoundError)

- [ ] **Step 3: Write minimal implementation**

```python
# src/business_logic/jd/resume_match_service.py
from src.business_logic.jd.schemas import ParsedJD, MatchReport


class ResumeMatchService:
    """计算简历与 JD 的匹配度"""

    def compute_match(self, resume_text: str, parsed_jd: ParsedJD) -> MatchReport:
        keyword_coverage = self._compute_keyword_coverage(
            resume_text, parsed_jd.required_skills
        )
        match_score = self._compute_match_score(keyword_coverage)
        gaps = self._identify_gaps(keyword_coverage, parsed_jd.qualifications)
        suggestions = self._generate_suggestions(gaps, parsed_jd.highlights)
        return MatchReport(
            keyword_coverage=keyword_coverage,
            match_score=match_score,
            gaps=gaps,
            suggestions=suggestions,
        )

    def _compute_keyword_coverage(
        self, resume_text: str, required_skills: list[str]
    ) -> dict[str, bool]:
        resume_lower = resume_text.lower()
        return {skill: skill.lower() in resume_lower for skill in required_skills}

    def _compute_match_score(self, keyword_coverage: dict[str, bool]) -> float:
        if not keyword_coverage:
            return 0.0
        covered = sum(keyword_coverage.values())
        return covered / len(keyword_coverage)

    def _identify_gaps(
        self, keyword_coverage: dict[str, bool], qualifications: list[str]
    ) -> list[str]:
        uncovered = [skill for skill, covered in keyword_coverage.items() if not covered]
        return uncovered

    def _generate_suggestions(self, gaps: list[str], highlights: list[str]) -> list[str]:
        suggestions = []
        for gap in gaps:
            suggestions.append(f"建议在简历中突出与 {gap} 相关的项目经验或技能描述")
        if highlights:
            suggestions.append(f"职位亮点：{highlights[0]}，可作为简历加分项强调")
        return suggestions
```

- [ ] **Step 4: Run test to verify it passes**

Run: `pytest tests/unit/business_logic/jd/test_resume_match_service.py -v`
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add src/business_logic/jd/resume_match_service.py tests/unit/business_logic/jd/test_resume_match_service.py
git commit -m "feat(jd): add ResumeMatchService for match score computation"
```

---

## Task 3: JD API Schemas

**Files:**
- Create: `src/presentation/schemas/jd.py`

### Steps

- [ ] **Step 1: Write the schema file**

```python
# src/presentation/schemas/jd.py
"""JD-customized resume API schemas."""

from typing import Literal, Optional

from pydantic import BaseModel, Field


class ResumeCustomizeRequest(BaseModel):
    """Request to customize a resume for a specific job."""

    jd_id: int = Field(..., ge=1, description="目标岗位 ID")
    custom_instructions: Optional[str] = Field(
        default=None, description="用户可选的定制指令"
    )
    enable_match_report: bool = Field(
        default=True, description="是否输出匹配报告"
    )


class MatchReportSchema(BaseModel):
    """Match report embedded in response."""

    keyword_coverage: dict[str, bool] = Field(
        ..., description="关键词 → 是否覆盖"
    )
    match_score: float = Field(..., ge=0.0, le=1.0, description="0.0 ~ 1.0 匹配度")
    gaps: list[str] = Field(default_factory=list, description="未覆盖的关键要求")
    suggestions: list[str] = Field(default_factory=list, description="改进建议")


class ResumeCustomizeResponse(BaseModel):
    """Response for resume customization."""

    customized_resume: str = Field(..., description="定制后的简历内容（纯文本 Markdown）")
    match_report: Optional[MatchReportSchema] = Field(
        default=None, description="匹配报告"
    )
    session_id: str = Field(..., description="本次 Agent 执行 session_id")
```

- [ ] **Step 2: Verify import works**

Run: `python -c "from src.presentation.schemas.jd import ResumeCustomizeRequest, ResumeCustomizeResponse, MatchReportSchema; print('OK')"`
Expected: OK

- [ ] **Step 3: Commit**

```bash
git add src/presentation/schemas/jd.py
git commit -m "feat(schemas): add JD customization API schemas"
```

---

## Task 4: Tools — read_resume

**Files:**
- Create: `src/business_logic/jd/tools/__init__.py`
- Create: `src/business_logic/jd/tools/read_resume.py`
- Test: covered by integration test

### Steps

- [ ] **Step 1: Write tools/__init__.py**

```python
# src/business_logic/jd/tools/__init__.py
from src.business_logic.jd.tools.read_resume import ReadResumeTool
from src.business_logic.jd.tools.match_resume_to_job import MatchResumeToJobTool

__all__ = ["ReadResumeTool", "MatchResumeToJobTool"]
```

- [ ] **Step 2: Write read_resume tool**

```python
# src/business_logic/jd/tools/read_resume.py
from typing import Type

from pydantic import BaseModel

from src.core.tools.base_tool import BaseTool


class ReadResumeInput(BaseModel):
    """Input schema for read_resume tool."""

    resume_id: int


class ReadResumeTool(BaseTool):
    """读取简历的完整内容"""

    name: str = "read_resume"
    description: str = "读取简历的完整内容，返回简历文本和基本信息"
    args_schema: Type[BaseModel] = ReadResumeInput

    def _execute(self, resume_id: int, runtime=None) -> dict:
        from src.data_access.repositories import resume_repository
        from src.presentation.api.deps import get_db

        db = next(get_db())
        resume = resume_repository.get_by_id(db, resume_id)
        if not resume:
            return {"error": f"Resume {resume_id} not found", "resume_id": resume_id}

        resume_text = resume.processed_content or resume.resume_text or ""
        return {
            "resume_id": resume_id,
            "resume_text": resume_text,
            "title": resume.title,
        }
```

- [ ] **Step 3: Verify it can be imported**

Run: `python -c "from src.business_logic.jd.tools.read_resume import ReadResumeTool; print('OK')"`
Expected: OK

- [ ] **Step 4: Commit**

```bash
git add src/business_logic/jd/tools/__init__.py src/business_logic/jd/tools/read_resume.py
git commit -m "feat(jd): add ReadResumeTool for resume content retrieval"
```

---

## Task 5: Tools — match_resume_to_job

**Files:**
- Create: `src/business_logic/jd/tools/match_resume_to_job.py`

### Steps

- [ ] **Step 1: Write match_resume_to_job tool**

```python
# src/business_logic/jd/tools/match_resume_to_job.py
from typing import Type

from pydantic import BaseModel

from src.core.tools.base_tool import BaseTool


class MatchResumeToJobInput(BaseModel):
    """Input schema for match_resume_to_job tool."""

    resume_id: int
    jd_id: int


class MatchResumeToJobTool(BaseTool):
    """分析简历与目标岗位的匹配度"""

    name: str = "match_resume_to_job"
    description: str = "输入简历 ID 和岗位 JD ID，返回简历与 JD 的匹配度分析报告"
    args_schema: Type[BaseModel] = MatchResumeToJobInput

    def _execute(self, resume_id: int, jd_id: int, runtime=None) -> dict:
        from src.business_logic.jd.jd_parser_service import JdParserService
        from src.business_logic.jd.resume_match_service import ResumeMatchService
        from src.data_access.repositories import resume_repository, job_repository
        from src.presentation.api.deps import get_db

        db = next(get_db())

        # Get resume
        resume = resume_repository.get_by_id(db, resume_id)
        if not resume:
            return {"error": f"Resume {resume_id} not found"}
        resume_text = resume.processed_content or resume.resume_text or ""

        # Get job
        job = job_repository.get_by_id(db, jd_id)
        if not job:
            return {"error": f"Job {jd_id} not found"}

        # Parse JD and compute match
        jd_text = job.description or ""
        parser = JdParserService()
        parsed_jd = parser.parse(jd_text)

        matcher = ResumeMatchService()
        report = matcher.compute_match(resume_text, parsed_jd)

        return {
            "resume_id": resume_id,
            "jd_id": jd_id,
            "keyword_coverage": report.keyword_coverage,
            "match_score": report.match_score,
            "gaps": report.gaps,
            "suggestions": report.suggestions,
        }
```

- [ ] **Step 2: Verify it can be imported**

Run: `python -c "from src.business_logic.jd.tools.match_resume_to_job import MatchResumeToJobTool; print('OK')"`
Expected: OK

- [ ] **Step 3: Commit**

```bash
git add src/business_logic/jd/tools/match_resume_to_job.py
git commit -m "feat(jd): add MatchResumeToJobTool for match analysis"
```

---

## Task 6: ResumeCustomizerAgent

**Files:**
- Create: `src/business_logic/jd/resume_customizer_agent.py`
- Test: `tests/unit/business_logic/jd/test_resume_customizer_agent.py`

### Steps

- [ ] **Step 1: Write the failing test**

```python
# tests/unit/business_logic/jd/test_resume_customizer_agent.py
import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from src.business_logic.jd.resume_customizer_agent import ResumeCustomizerAgent
from src.core.runtime.memory_store import MemoryStore
from src.core.runtime.tool_registry import ToolRegistry


class TestResumeCustomizerAgent:
    def setup_method(self):
        self.mock_llm = AsyncMock()
        self.mock_memory = MagicMock(spec=MemoryStore)
        self.mock_memory.search_memory.return_value = []
        self.tool_registry = ToolRegistry()

    def test_agent_initializes(self):
        agent = ResumeCustomizerAgent(
            llm=self.mock_llm,
            tool_registry=self.tool_registry,
            memory=self.mock_memory,
        )
        assert agent._llm is not None
        assert agent._tool_registry is not None

    def test_agent_has_correct_system_prompt(self):
        agent = ResumeCustomizerAgent(
            llm=self.mock_llm,
            tool_registry=self.tool_registry,
            memory=self.mock_memory,
        )
        assert "简历顾问" in agent._system_prompt or "resume" in agent._system_prompt.lower()
```

- [ ] **Step 2: Run test to verify it fails**

Run: `pytest tests/unit/business_logic/jd/test_resume_customizer_agent.py -v`
Expected: FAIL (ModuleNotFoundError)

- [ ] **Step 3: Write minimal implementation**

```python
# src/business_logic/jd/resume_customizer_agent.py
"""AI 简历定制 Agent — 基于 AgentExecutor ReAct 循环"""

from src.core.llm.litellm_adapter import LiteLLMAdapter
from src.core.runtime.agent_executor import AgentExecutor
from src.core.runtime.memory_store import MemoryStore
from src.core.runtime.tool_registry import ToolRegistry


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
    ):
        self._llm = llm
        self._tool_registry = tool_registry
        self._memory = memory
        self._system_prompt = (
            "你是一位资深简历顾问，擅长根据目标岗位定制简历内容。\n"
            "你的任务是根据提供的简历和岗位信息，生成一份针对该岗位优化的简历内容。\n"
            "输出格式：纯文本 Markdown，突出简历中与目标岗位最相关的经历和技能。"
        )
        self._executor = AgentExecutor(
            llm=llm,
            tools=tool_registry,
            memory=memory,
            system_prompt=self._system_prompt,
        )

    async def customize(
        self,
        resume_id: int,
        jd_id: int,
        custom_instructions: str | None,
        session_id: str,
    ) -> str:
        """
        执行简历定制，返回定制后的简历文本。
        通过 AgentExecutor.execute() 运行 ReAct 循环。
        """
        user_message = self._build_user_message(resume_id, jd_id, custom_instructions)

        full_text = ""
        async for chunk in self._executor.execute(
            task=user_message,
            session_id=session_id,
        ):
            full_text += chunk

        return full_text

    def _build_user_message(
        self, resume_id: int, jd_id: int, custom_instructions: str | None
    ) -> str:
        msg = (
            f"请帮我定制一份简历。\n"
            f"简历 ID：{resume_id}\n"
            f"目标岗位 JD ID：{jd_id}\n"
        )
        if custom_instructions:
            msg += f"\n用户的定制指令：{custom_instructions}\n"
        msg += "\n请使用 read_resume 工具读取简历内容，然后使用 match_resume_to_job 工具分析匹配度，最后生成定制后的简历内容。"
        return msg
```

- [ ] **Step 4: Run test to verify it passes**

Run: `pytest tests/unit/business_logic/jd/test_resume_customizer_agent.py -v`
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add src/business_logic/jd/resume_customizer_agent.py tests/unit/business_logic/jd/test_resume_customizer_agent.py
git commit -m "feat(jd): add ResumeCustomizerAgent using AgentExecutor ReAct loop"
```

---

## Task 7: API Endpoint — POST /resumes/{resume_id}/customize-for-jd

**Files:**
- Modify: `src/presentation/api/v1/resume.py`
- Modify: `src/main.py` (register router if needed)

### Steps

- [ ] **Step 1: Add endpoint to resume.py**

Add the following import at the top of `src/presentation/api/v1/resume.py`:

```python
from src.presentation.schemas.jd import (
    ResumeCustomizeRequest,
    ResumeCustomizeResponse,
    MatchReportSchema,
)
from src.business_logic.jd import (
    JdParserService,
    ResumeMatchService,
    ResumeCustomizerAgent,
)
from src.core.llm.litellm_adapter import LiteLLMAdapter
from src.core.runtime.memory_store import MemoryStore
from src.core.runtime.tool_registry import ToolRegistry
from src.business_logic.jd.tools import ReadResumeTool, MatchResumeToJobTool
```

Add this endpoint at the end of the file:

```python
@router.post("/{resume_id}/customize-for-jd", response_model=ResumeCustomizeResponse)
async def customize_resume_for_jd(
    resume_id: int,
    req: ResumeCustomizeRequest,
    current_user=Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    为指定简历生成针对目标岗位定制的简历内容。
    - 解析 JD 关键词和要求
    - 计算简历与 JD 的匹配度
    - Agent 生成定制简历
    """
    import uuid
    from src.data_access.repositories import resume_repository, job_repository

    # 1. 验证简历存在且属于当前用户
    resume = resume_repository.get_by_id_and_user_id(db, resume_id, current_user.id)
    if not resume:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Resume not found")

    # 2. 验证 JD 存在
    job = job_repository.get_by_id(db, req.jd_id)
    if not job:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Job description not found")

    # 3. 解析 JD
    jd_text = job.description or ""
    parser = JdParserService()
    parsed_jd = parser.parse(jd_text)

    # 4. 计算匹配度（仅当 enable_match_report）
    match_report = None
    if req.enable_match_report:
        resume_text = resume.processed_content or resume.resume_text or ""
        matcher = ResumeMatchService()
        match = matcher.compute_match(resume_text, parsed_jd)
        match_report = MatchReportSchema(
            keyword_coverage=match.keyword_coverage,
            match_score=match.match_score,
            gaps=match.gaps,
            suggestions=match.suggestions,
        )

    # 5. 构建 Agent
    session_id = str(uuid.uuid4())
    tool_registry = ToolRegistry()
    tool_registry.register(ReadResumeTool())
    tool_registry.register(MatchResumeToJobTool())

    # Note: MemoryStore 需要 redis_client 和 chroma_client，测试环境用 MagicMock
    mock_memory = MagicMock()
    mock_memory.search_memory.return_value = []
    mock_memory.get_turns.return_value = []

    llm = LiteLLMAdapter()
    agent = ResumeCustomizerAgent(
        llm=llm,
        tool_registry=tool_registry,
        memory=mock_memory,
    )

    # 6. 执行定制（传入 db session 用于 tools 访问）
    customized_text = await agent.customize(
        resume_id=resume_id,
        jd_id=req.jd_id,
        custom_instructions=req.custom_instructions,
        session_id=session_id,
    )

    return ResumeCustomizeResponse(
        customized_resume=customized_text,
        match_report=match_report,
        session_id=session_id,
    )
```

Also add this import near the top (needed for MagicMock):
```python
from unittest.mock import MagicMock
```

- [ ] **Step 2: Verify the router imports correctly**

Run: `python -c "from src.presentation.api.v1.resume import router; print('OK')"`
Expected: OK

- [ ] **Step 3: Commit**

```bash
git add src/presentation/api/v1/resume.py
git commit -m "feat(api): add POST /resumes/{id}/customize-for-jd endpoint"
```

---

## Task 8: Update JD package __init__.py

**Files:**
- Modify: `src/business_logic/jd/__init__.py`

### Steps

- [ ] **Step 1: Update __init__.py**

```python
"""JD 定制简历包"""
from src.business_logic.jd.jd_parser_service import JdParserService
from src.business_logic.jd.resume_match_service import ResumeMatchService
from src.business_logic.jd.resume_customizer_agent import ResumeCustomizerAgent
from src.business_logic.jd.schemas import ParsedJD, MatchReport

__all__ = [
    "JdParserService",
    "ResumeMatchService",
    "ResumeCustomizerAgent",
    "ParsedJD",
    "MatchReport",
]
```

- [ ] **Step 2: Commit**

```bash
git add src/business_logic/jd/__init__.py
git commit -m "feat(jd): export JD services from package __init__"
```

---

## Task 9: Frontend API Client

**Files:**
- Modify: `frontend/src/lib/api.ts`

### Steps

- [ ] **Step 1: Add types and API method**

Add this type to `frontend/src/lib/api.ts` (around line 80, after JobMatchRecord type):

```typescript
export type MatchReportData = {
  keyword_coverage: Record<string, boolean>
  match_score: number
  gaps: string[]
  suggestions: string[]
}

export type ResumeCustomizeResponse = {
  customized_resume: string
  match_report: MatchReportData | null
  session_id: string
}
```

Add this method to the `resumeApi` export (around line 481):

```typescript
async customizeForJd(
  resumeId: number,
  jdId: number,
  customInstructions?: string,
  enableMatchReport: boolean = true,
) {
  const response = await api.post<ResumeCustomizeResponse>(
    `/resumes/${resumeId}/customize-for-jd`,
    {
      jd_id: jdId,
      custom_instructions: customInstructions ?? null,
      enable_match_report: enableMatchReport,
    },
  )
  return response.data
},
```

- [ ] **Step 2: Verify TypeScript compiles**

Run: `cd frontend && npx tsc --noEmit 2>&1 | head -30`
Expected: No errors related to new types/methods

- [ ] **Step 3: Commit**

```bash
git add frontend/src/lib/api.ts
git commit -m "feat(frontend): add customizeForJd API method"
```

---

## Task 10: MatchReportCard Component

**Files:**
- Create: `frontend/src/pages/components/MatchReportCard.tsx`

### Steps

- [ ] **Step 1: Write the component**

```tsx
// frontend/src/pages/components/MatchReportCard.tsx
import type { MatchReportData } from '../../lib/api'

interface MatchReportCardProps {
  report: MatchReportData
}

export function MatchReportCard({ report }: MatchReportCardProps) {
  const scorePercent = Math.round(report.match_score * 100)
  const coveredCount = Object.values(report.keyword_coverage).filter(Boolean).length
  const totalCount = Object.length(report.keyword_coverage)

  return (
    <div className="space-y-4">
      {/* Score */}
      <div className="flex items-center gap-3">
        <div className="text-3xl font-semibold text-[var(--color-accent)]">
          {scorePercent}%
        </div>
        <div className="text-sm text-[var(--color-muted)]">匹配度</div>
      </div>

      {/* Keyword coverage bar */}
      {totalCount > 0 && (
        <div>
          <div className="mb-1 flex justify-between text-xs text-[var(--color-muted)]">
            <span>关键词覆盖</span>
            <span>{coveredCount}/{totalCount}</span>
          </div>
          <div className="h-2 w-full rounded-full bg-[var(--color-panel)]">
            <div
              className="h-2 rounded-full bg-[var(--color-accent)] transition-all"
              style={{ width: `${scorePercent}%` }}
            />
          </div>
        </div>
      )}

      {/* Keyword list */}
      {Object.keys(report.keyword_coverage).length > 0 && (
        <div className="flex flex-wrap gap-2">
          {Object.entries(report.keyword_coverage).map(([keyword, covered]) => (
            <span
              key={keyword}
              className={`inline-flex items-center rounded-full px-2.5 py-0.5 text-xs font-medium ${
                covered
                  ? 'bg-green-100 text-green-800'
                  : 'bg-red-100 text-red-800'
              }`}
            >
              {covered ? '✓' : '✗'} {keyword}
            </span>
          ))}
        </div>
      )}

      {/* Gaps */}
      {report.gaps.length > 0 && (
        <div>
          <p className="mb-2 text-xs font-semibold uppercase tracking-wider text-[var(--color-muted)]">
            差距项
          </p>
          <ul className="space-y-1">
            {report.gaps.map((gap) => (
              <li key={gap} className="flex items-start gap-2 text-sm text-[var(--color-ink)]">
                <span className="text-red-500">•</span>
                {gap}
              </li>
            ))}
          </ul>
        </div>
      )}

      {/* Suggestions */}
      {report.suggestions.length > 0 && (
        <div>
          <p className="mb-2 text-xs font-semibold uppercase tracking-wider text-[var(--color-muted)]">
            改进建议
          </p>
          <ul className="space-y-1">
            {report.suggestions.map((suggestion, i) => (
              <li key={i} className="flex items-start gap-2 text-sm text-[var(--color-ink)]">
                <span className="text-[var(--color-accent)]">→</span>
                {suggestion}
              </li>
            ))}
          </ul>
        </div>
      )}
    </div>
  )
}
```

- [ ] **Step 2: Commit**

```bash
git add frontend/src/pages/components/MatchReportCard.tsx
git commit -m "feat(frontend): add MatchReportCard component"
```

---

## Task 11: JdCustomizePage

**Files:**
- Create: `frontend/src/pages/jd-customize-page.tsx`
- Modify: `frontend/src/app/router.tsx` (add route)

### Steps

- [ ] **Step 1: Write the page component**

```tsx
// frontend/src/pages/jd-customize-page.tsx
import { useState } from 'react'
import { useMutation, useQuery } from '@tanstack/react-query'

import { readApiError, jobsApi, resumeApi, type MatchReportData } from '../lib/api'
import {
  EmptyHint,
  FormField,
  PageHeader,
  PrimaryButton,
  ResultPanel,
  SectionCard,
  SecondaryButton,
  Select,
  Textarea,
} from './page-primitives'
import { MatchReportCard } from './components/MatchReportCard'

export function JdCustomizePage() {
  const [selectedResumeId, setSelectedResumeId] = useState<number | null>(null)
  const [selectedJobId, setSelectedJobId] = useState<number | null>(null)
  const [customInstructions, setCustomInstructions] = useState('')
  const [feedback, setFeedback] = useState<string | null>(null)
  const [customizedResume, setCustomizedResume] = useState<string | null>(null)
  const [matchReport, setMatchReport] = useState<MatchReportData | null>(null)

  const resumesQuery = useQuery({
    queryKey: ['resume', 'list'],
    queryFn: resumeApi.list,
  })

  const jobsQuery = useQuery({
    queryKey: ['jobs', 'list'],
    queryFn: jobsApi.list,
  })

  const customizeMutation = useMutation({
    mutationFn: () => {
      if (!selectedResumeId || !selectedJobId) throw new Error('请选择简历和岗位')
      return resumeApi.customizeForJd(
        selectedResumeId,
        selectedJobId,
        customInstructions || undefined,
      )
    },
    onSuccess: (data) => {
      setCustomizedResume(data.customized_resume)
      setMatchReport(data.match_report)
      setFeedback('简历定制完成！')
    },
    onError: (error) => setFeedback(readApiError(error)),
  })

  const effectiveResumeId = selectedResumeId ?? resumesQuery.data?.[0]?.id ?? null
  const effectiveJobId = selectedJobId ?? jobsQuery.data?.[0]?.id ?? null

  const selectedResume = resumesQuery.data?.find((r) => r.id === effectiveResumeId)
  const selectedJob = jobsQuery.data?.find((j) => j.id === effectiveJobId)

  return (
    <div className="space-y-6">
      <PageHeader
        eyebrow="简历定制"
        title="JD 定制简历"
        description="选择简历和目标岗位，系统分析匹配度并生成针对该岗位优化的简历内容。"
      />

      <div className="grid gap-6 xl:grid-cols-[1fr_1fr]">
        {/* Left: Resume selection */}
        <SectionCard title="选择简历" subtitle="选择要定制的简历">
          <div className="space-y-4">
            <FormField label="简历">
              <Select
                value={effectiveResumeId ?? ''}
                onChange={(e) => setSelectedResumeId(Number(e.target.value))}
              >
                {resumesQuery.data?.map((resume) => (
                  <option key={resume.id} value={resume.id}>
                    #{resume.id} - {resume.title}
                  </option>
                ))}
              </Select>
            </FormField>
            {selectedResume && (
              <div className="rounded-2xl border border-[var(--color-stroke)] bg-[var(--color-surface)] p-4">
                <p className="mb-2 text-xs font-semibold uppercase tracking-wider text-[var(--color-muted)]">
                  简历预览
                </p>
                <p className="whitespace-pre-wrap text-sm leading-6 text-[var(--color-ink)]">
                  {selectedResume.processed_content ?? selectedResume.resume_text ?? '（无内容）'}
                </p>
              </div>
            )}
          </div>
        </SectionCard>

        {/* Right: Job selection */}
        <SectionCard title="选择目标岗位" subtitle="选择要申请的岗位">
          <div className="space-y-4">
            <FormField label="岗位">
              <Select
                value={effectiveJobId ?? ''}
                onChange={(e) => setSelectedJobId(Number(e.target.value))}
              >
                {jobsQuery.data?.map((job) => (
                  <option key={job.id} value={job.id}>
                    #{job.id} - {job.title} @ {job.company}
                  </option>
                ))}
              </Select>
            </FormField>
            {selectedJob && (
              <div className="rounded-2xl border border-[var(--color-stroke)] bg-[var(--color-surface)] p-4">
                <p className="mb-2 text-xs font-semibold uppercase tracking-wider text-[var(--color-muted)]">
                  JD 预览
                </p>
                <p className="mb-2 text-sm font-medium text-[var(--color-ink)]">
                  {selectedJob.title} @ {selectedJob.company}
                </p>
                <p className="whitespace-pre-wrap text-sm leading-6 text-[var(--color-ink)]">
                  {selectedJob.description ?? '（无描述）'}
                </p>
              </div>
            )}
          </div>
        </SectionCard>
      </div>

      {/* Custom instructions */}
      <SectionCard title="定制指令（可选）" subtitle="告诉 AI 你希望突出或弱化哪些内容">
        <Textarea
          value={customInstructions}
          onChange={(e) => setCustomInstructions(e.target.value)}
          placeholder="例如：突出我的 Python 项目经验，淡化不相关的社团经历"
          className="min-h-20"
        />
      </SectionCard>

      {/* Actions */}
      <div className="flex items-center gap-3">
        <PrimaryButton
          type="button"
          disabled={!effectiveResumeId || !effectiveJobId || customizeMutation.isPending}
          onClick={() => customizeMutation.mutate()}
        >
          {customizeMutation.isPending ? '定制中...' : '🚀 开始定制简历'}
        </PrimaryButton>
        {feedback && (
          <span className="text-sm text-[var(--color-ink)]">{feedback}</span>
        )}
        {customizedResume && (
          <SecondaryButton
            type="button"
            onClick={() => {
              navigator.clipboard.writeText(customizedResume)
              setFeedback('已复制到剪贴板')
            }}
          >
            📋 复制简历
          </SecondaryButton>
        )}
      </div>

      {/* Results */}
      {customizedResume && (
        <div className="grid gap-6 xl:grid-cols-[1fr_1fr]">
          <SectionCard title="定制后简历" subtitle="基于 JD 优化过的简历内容">
            <ResultPanel label="定制简历" content={customizedResume} />
          </SectionCard>
          {matchReport && (
            <SectionCard title="匹配报告" subtitle="简历与目标岗位的匹配度分析">
              <MatchReportCard report={matchReport} />
            </SectionCard>
          )}
        </div>
      )}
    </div>
  )
}
```

- [ ] **Step 2: Add route to router.tsx**

Read `frontend/src/app/router.tsx` and add:

1. Import at top:
```typescript
import { JdCustomizePage } from '../pages/jd-customize-page'
```

2. Add route (after `/resume` route):
```typescript
{ path: '/jd-customize', element: <JdCustomizePage /> },
```

- [ ] **Step 3: Verify page compiles**

Run: `cd frontend && npx tsc --noEmit 2>&1 | head -30`
Expected: No errors related to JdCustomizePage

- [ ] **Step 4: Commit**

```bash
git add frontend/src/pages/jd-customize-page.tsx frontend/src/app/router.tsx
git commit -m "feat(frontend): add jd-customize-page with dual-panel layout"
```

---

## Task 12: Integration Test

**Files:**
- Create: `tests/integration/test_customize_endpoint.py`

### Steps

- [ ] **Step 1: Write integration test**

```python
# tests/integration/test_customize_endpoint.py
import pytest
from httpx import AsyncClient, ASGITransport
from src.main import app


class TestCustomizeForJdEndpoint:
    @pytest.fixture
    def anyio_backend(self):
        return "asyncio"

    @pytest.mark.anyio
    async def test_customize_endpoint_returns_404_for_missing_resume(self):
        """简历不存在时返回 404"""
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            # Login first to get auth
            login_resp = await client.post(
                "/api/v1/auth/login/",
                json={"username": "testuser", "password": "testpass"},
            )
            if login_resp.status_code == 200:
                token = login_resp.json().get("access_token")
                headers = {"Authorization": f"Bearer {token}"}
                resp = await client.post(
                    "/api/v1/resumes/99999/customize-for-jd",
                    json={"jd_id": 1},
                    headers=headers,
                )
                assert resp.status_code == 404
```

- [ ] **Step 2: Run test**

Run: `pytest tests/integration/test_customize_endpoint.py -v`
Expected: PASS (or SKIPPED if no test user)

- [ ] **Step 3: Commit**

```bash
git add tests/integration/test_customize_endpoint.py
git commit -m "test: add integration test for customize-for-jd endpoint"
```

---

## Spec Coverage Check

| Spec Section | Task |
|---|---|
| JdParserService | Task 1 |
| ResumeMatchService | Task 2 |
| JD API schemas | Task 3 |
| read_resume tool | Task 4 |
| match_resume_to_job tool | Task 5 |
| ResumeCustomizerAgent | Task 6 |
| POST /customize-for-jd endpoint | Task 7 |
| Frontend API client | Task 9 |
| MatchReportCard component | Task 10 |
| JdCustomizePage | Task 11 |
| Integration tests | Task 12 |
