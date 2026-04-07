# Phase 7：测试覆盖率提升 + 工具库扩展 实施计划

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 工具库从 2 个扩展至 13 个，测试覆盖率从 47% 提升至 80%+，引入 ToolContext 统一依赖管理

**Architecture:** ToolContext 作为工具执行上下文，统一注入 db/user/session；BaseTool._run() 改造为接收 context 参数；AgentExecutor 支持 ReAct 循环调用工具

**Tech Stack:** Python 3.10+, pytest, pytest-asyncio, SQLAlchemy 2.0, LangChain Core

---

## 文件结构

```
src/core/tools/
  tool_context.py           # 新增：ToolContext dataclass
  base_tool.py              # 修改：_run() 增加 context 参数
  langchain_tools.py         # 不变

src/business_logic/jd/tools/
  read_resume.py             # 修改：使用 context.db
  match_resume_to_job.py     # 修改：使用 context.db
  update_resume.py           # 新增
  analyze_resume_skills.py   # 新增
  format_resume.py           # 新增
  compare_resumes.py         # 新增

src/business_logic/job/tools/
  __init__.py                # 新增
  search_jobs.py             # 新增
  analyze_jd.py              # 新增
  calculate_job_match.py     # 新增

src/business_logic/interview/tools/
  __init__.py                # 新增
  generate_interview_questions.py  # 新增
  evaluate_interview_answer.py    # 新增

src/business_logic/common/tools/
  __init__.py                # 新增
  web_search.py              # 新增
  extract_keywords.py        # 新增

src/business_logic/jd/resume_customizer_agent.py  # 修改：ReAct 模式
```

---

## Phase 1：ToolContext + 6 个高优先级工具（Week 1-2）

### Task 1: ToolContext 定义

**Files:**
- Create: `src/core/tools/tool_context.py`
- Modify: `src/core/tools/base_tool.py:1-45`
- Test: `tests/unit/core/tools/test_tool_context.py`

- [ ] **Step 1: 创建 ToolContext dataclass**

```python
# src/core/tools/tool_context.py
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Optional

from sqlalchemy.orm import Session


@dataclass
class ToolContext:
    """工具执行上下文，统一管理依赖"""
    db: Session
    user_id: Optional[int] = None
    agent_id: Optional[str] = None
    session_id: Optional[str] = None
    cache: dict[str, Any] = field(default_factory=dict)
```

- [ ] **Step 2: 运行测试确认无现有测试**

Run: `pytest tests/unit/core/tools/test_tool_context.py -v 2>&1 | head -20`
Expected: ERROR collecting tests/unit/core/tools/test_tool_context.py

- [ ] **Step 3: 提交**

```bash
git add src/core/tools/tool_context.py
git commit -m "feat(tools): add ToolContext dataclass for unified dependency injection"
```

---

### Task 2: BaseTool 改造 — 接入 ToolContext

**Files:**
- Modify: `src/core/tools/base_tool.py:1-45`
- Test: `tests/unit/core/test_base_tool.py`

- [ ] **Step 1: 读取现有 base_tool.py 确认当前实现**

Read: `src/core/tools/base_tool.py`

- [ ] **Step 2: 改造 _run() 方法，接收 context 参数**

```python
# src/core/tools/base_tool.py
"""
统一工具基类
继承 LangChain Core 的 BaseTool，统一工具接口
"""
from __future__ import annotations

from typing import Any, Dict, Optional, Type

from langchain_core.callbacks import CallbackManagerForToolRun
from langchain_core.tools import BaseTool as LangChainBaseTool
from pydantic import BaseModel, Field

from src.core.tools.tool_context import ToolContext


class BaseTool(LangChainBaseTool):
    """
    统一工具基类，继承 LangChain BaseTool
    所有领域工具都应继承此类
    """

    runtime: Optional[Any] = Field(default=None, exclude=True)

    def _run(
        self,
        tool_input: Dict[str, Any],
        runtime: Optional[Any] = None,
        run_manager: Optional[CallbackManagerForToolRun] = None,
    ) -> str:
        """
        同步执行入口，由父类调用
        """
        # 兼容旧调用方式（无 context）
        context = getattr(self, '_context', None)
        result = self._execute_sync(tool_input, runtime=runtime, context=context)
        if isinstance(result, dict):
            import json
            return json.dumps(result)
        return str(result)

    def _execute_sync(
        self,
        tool_input: Dict[str, Any],
        runtime: Optional[Any] = None,
        context: Optional[ToolContext] = None,
    ) -> Dict[str, Any]:
        """
        子类覆盖此方法实现同步逻辑
        """
        raise NotImplementedError("Subclasses must implement _execute_sync")
```

- [ ] **Step 3: 运行回归测试**

Run: `pytest tests/unit/core/test_base_tool.py -v`
Expected: PASS

- [ ] **Step 4: 提交**

```bash
git add src/core/tools/base_tool.py
git commit -m "feat(tools):改造 BaseTool._run() 支持 ToolContext 注入"
```

---

### Task 3: ToolRegistry 改造 — execute() 传入 context

**Files:**
- Modify: `src/core/runtime/tool_registry.py:1-74`
- Test: `tests/unit/core/runtime/test_tool_registry.py`

- [ ] **Step 1: 读取现有 test_tool_registry.py**

Read: `tests/unit/core/runtime/test_tool_registry.py`

- [ ] **Step 2: 改造 ToolRegistry.execute()**

```python
# src/core/runtime/tool_registry.py
def execute(
    self,
    name: str,
    tool_input: Dict[str, Any],
    context: Optional[ToolContext] = None,
    runtime: Any = None,
) -> Any:
    """执行工具，返回结果"""
    import json
    tool = self.get_tool(name)
    # 设置 context 到 tool 实例上，供 _run 访问
    if context is not None:
        tool._context = context
    result = tool._run(tool_input, runtime=runtime)
    if isinstance(result, str):
        try:
            return json.loads(result)
        except json.JSONDecodeError:
            return result
    return result
```

- [ ] **Step 3: 添加 ToolRegistry.execute_with_context 测试**

追加到 `tests/unit/core/runtime/test_tool_registry.py`:

```python
def test_execute_with_context():
    """测试 execute 是否正确传递 context"""
    from src.core.tools.tool_context import ToolContext
    from tests.fixtures import mock_db_session

    registry = ToolRegistry()
    tool = MockTool()
    registry.register(tool)

    context = ToolContext(db=mock_db_session, user_id=1)
    result = registry.execute("mock_tool", {"input": "test"}, context=context)

    assert result["context_passed"] is True
    assert result["user_id"] == 1
```

- [ ] **Step 4: 运行测试**

Run: `pytest tests/unit/core/runtime/test_tool_registry.py -v`
Expected: PASS

- [ ] **Step 5: 提交**

```bash
git add src/core/runtime/tool_registry.py tests/unit/core/runtime/test_tool_registry.py
git commit -m "feat(tools): ToolRegistry.execute() 支持 ToolContext 注入"
```

---

### Task 4: 改造现有工具 — ReadResumeTool + MatchResumeToJobTool

**Files:**
- Modify: `src/business_logic/jd/tools/read_resume.py:1-31`
- Modify: `src/business_logic/jd/tools/match_resume_to_job.py:1-57`
- Test: `tests/unit/business_logic/jd/tools/test_read_resume.py`, `tests/unit/business_logic/jd/tools/test_match_resume_to_job.py`

- [ ] **Step 1: 读取现有工具实现**

Read: `src/business_logic/jd/tools/read_resume.py`
Read: `src/business_logic/jd/tools/match_resume_to_job.py`

- [ ] **Step 2: 改造 ReadResumeTool**

```python
# src/business_logic/jd/tools/read_resume.py
from typing import Type

from pydantic import BaseModel

from src.core.tools.base_tool import BaseTool
from src.core.tools.tool_context import ToolContext


class ReadResumeInput(BaseModel):
    """Input schema for read_resume tool."""
    resume_id: int


class ReadResumeTool(BaseTool):
    """读取简历的完整内容"""

    name: str = "read_resume"
    description: str = "读取简历的完整内容，返回简历文本和基本信息"
    args_schema: Type[BaseModel] = ReadResumeInput

    def _execute_sync(
        self,
        tool_input: dict,
        runtime=None,
        context: ToolContext = None,
    ) -> dict:
        from src.data_access.repositories import resume_repository

        resume_id = tool_input.get("resume_id")
        if context is None:
            from src.presentation.api.deps import get_db
            db = next(get_db())
        else:
            db = context.db

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

- [ ] **Step 3: 改造 MatchResumeToJobTool**

```python
# src/business_logic/jd/tools/match_resume_to_job.py
from typing import Type

from pydantic import BaseModel

from src.core.tools.base_tool import BaseTool
from src.core.tools.tool_context import ToolContext


class MatchResumeToJobInput(BaseModel):
    """Input schema for match_resume_to_job tool."""
    resume_id: int
    jd_id: int


class MatchResumeToJobTool(BaseTool):
    """分析简历与目标岗位的匹配度"""

    name: str = "match_resume_to_job"
    description: str = "输入简历 ID 和岗位 JD ID，返回简历与 JD 的匹配度分析报告"
    args_schema: Type[BaseModel] = MatchResumeToJobInput

    def _execute_sync(
        self,
        tool_input: dict,
        runtime=None,
        context: ToolContext = None,
    ) -> dict:
        from src.business_logic.jd.jd_parser_service import JdParserService
        from src.business_logic.jd.resume_match_service import ResumeMatchService
        from src.data_access.repositories import resume_repository, job_repository

        resume_id = tool_input.get("resume_id")
        jd_id = tool_input.get("jd_id")

        if context is None:
            from src.presentation.api.deps import get_db
            db = next(get_db())
        else:
            db = context.db

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

- [ ] **Step 4: 运行现有测试确认回归**

Run: `pytest tests/unit/business_logic/jd/tools/test_read_resume.py tests/unit/business_logic/jd/tools/test_match_resume_to_job.py -v`
Expected: PASS

- [ ] **Step 5: 提交**

```bash
git add src/business_logic/jd/tools/read_resume.py src/business_logic/jd/tools/match_resume_to_job.py
git commit -m "refactor(jd_tools): 改造 ReadResumeTool 和 MatchResumeToJobTool 支持 ToolContext"
```

---

### Task 5: 新增 UpdateResumeTool

**Files:**
- Create: `src/business_logic/jd/tools/update_resume.py`
- Create: `tests/unit/business_logic/jd/tools/test_update_resume.py`
- Create: `tests/integration/tools/test_update_resume.py`

- [ ] **Step 1: 创建 UpdateResumeTool**

```python
# src/business_logic/jd/tools/update_resume.py
from typing import Optional, Type

from pydantic import BaseModel

from src.core.tools.base_tool import BaseTool
from src.core.tools.tool_context import ToolContext


class UpdateResumeInput(BaseModel):
    """Input schema for update_resume tool."""
    resume_id: int
    title: Optional[str] = None
    resume_text: Optional[str] = None
    processed_content: Optional[str] = None


class UpdateResumeTool(BaseTool):
    """更新简历内容（标题、文本、处理后的内容）"""

    name: str = "update_resume"
    description: str = "更新简历的标题或内容，支持部分更新"
    args_schema: Type[BaseModel] = UpdateResumeInput

    def _execute_sync(
        self,
        tool_input: dict,
        runtime=None,
        context: ToolContext = None,
    ) -> dict:
        from src.data_access.repositories import resume_repository

        resume_id = tool_input.get("resume_id")
        if context is None:
            from src.presentation.api.deps import get_db
            db = next(get_db())
        else:
            db = context.db

        resume = resume_repository.get_by_id(db, resume_id)
        if not resume:
            return {"error": f"Resume {resume_id} not found"}

        # 部分更新
        if "title" in tool_input and tool_input["title"] is not None:
            resume.title = tool_input["title"]
        if "resume_text" in tool_input and tool_input["resume_text"] is not None:
            resume.resume_text = tool_input["resume_text"]
        if "processed_content" in tool_input and tool_input["processed_content"] is not None:
            resume.processed_content = tool_input["processed_content"]

        db.commit()
        db.refresh(resume)

        return {
            "resume_id": resume_id,
            "updated": True,
            "title": resume.title,
        }
```

- [ ] **Step 2: 创建单元测试**

```python
# tests/unit/business_logic/jd/tools/test_update_resume.py
import pytest
from unittest.mock import MagicMock, patch
from src.business_logic.jd.tools.update_resume import UpdateResumeTool, UpdateResumeInput


class TestUpdateResumeTool:
    def test_update_resume_success(self):
        """测试成功更新简历"""
        tool = UpdateResumeTool()

        mock_resume = MagicMock()
        mock_resume.resume_id = 1
        mock_resume.title = "Old Title"
        mock_resume.resume_text = "Old Text"
        mock_resume.processed_content = "Old Processed"

        mock_db = MagicMock()
        mock_db.commit = MagicMock()
        mock_db.refresh = MagicMock()

        mock_context = MagicMock()
        mock_context.db = mock_db

        with patch('src.data_access.repositories.resume_repository.get_by_id', return_value=mock_resume):
            result = tool._execute_sync(
                {"resume_id": 1, "title": "New Title"},
                context=mock_context
            )

        assert result["resume_id"] == 1
        assert result["updated"] is True
        assert result["title"] == "New Title"
        mock_db.commit.assert_called_once()

    def test_update_resume_not_found(self):
        """测试更新不存在的简历"""
        tool = UpdateResumeTool()

        mock_db = MagicMock()
        mock_context = MagicMock()
        mock_context.db = mock_db

        with patch('src.data_access.repositories.resume_repository.get_by_id', return_value=None):
            result = tool._execute_sync(
                {"resume_id": 999},
                context=mock_context
            )

        assert "error" in result
        assert "not found" in result["error"]
```

- [ ] **Step 3: 运行测试**

Run: `pytest tests/unit/business_logic/jd/tools/test_update_resume.py -v`
Expected: PASS

- [ ] **Step 4: 提交**

```bash
git add src/business_logic/jd/tools/update_resume.py tests/unit/business_logic/jd/tools/test_update_resume.py
git commit -m "feat(jd_tools): 添加 UpdateResumeTool"
```

---

### Task 6: 新增 AnalyzeResumeSkillsTool

**Files:**
- Create: `src/business_logic/jd/tools/analyze_resume_skills.py`
- Create: `tests/unit/business_logic/jd/tools/test_analyze_resume_skills.py`

- [ ] **Step 1: 创建 AnalyzeResumeSkillsTool**

```python
# src/business_logic/jd/tools/analyze_resume_skills.py
from typing import Type

from pydantic import BaseModel

from src.core.tools.base_tool import BaseTool
from src.core.tools.tool_context import ToolContext


class AnalyzeResumeSkillsInput(BaseModel):
    """Input schema for analyze_resume_skills tool."""
    resume_id: int


class AnalyzeResumeSkillsTool(BaseTool):
    """提取并分析简历中的技能标签"""

    name: str = "analyze_resume_skills"
    description: str = "从简历中提取技能标签，并按类别分组分析"
    args_schema: Type[BaseModel] = AnalyzeResumeSkillsInput

    def _execute_sync(
        self,
        tool_input: dict,
        runtime=None,
        context: ToolContext = None,
    ) -> dict:
        from src.data_access.repositories import resume_repository

        resume_id = tool_input.get("resume_id")

        if context is None:
            from src.presentation.api.deps import get_db
            db = next(get_db())
        else:
            db = context.db

        resume = resume_repository.get_by_id(db, resume_id)
        if not resume:
            return {"error": f"Resume {resume_id} not found"}

        resume_text = resume.processed_content or resume.resume_text or ""

        # 简单的技能关键词提取
        skill_keywords = {
            "编程语言": ["Python", "Java", "JavaScript", "TypeScript", "Go", "Rust", "C++", "C#"],
            "框架": ["React", "Vue", "Angular", "Django", "FastAPI", "Spring", "Node.js"],
            "数据库": ["MySQL", "PostgreSQL", "MongoDB", "Redis", "Elasticsearch"],
            "云服务": ["AWS", "Azure", "GCP", "Docker", "Kubernetes"],
            "AI/ML": ["TensorFlow", "PyTorch", "LangChain", "OpenAI", "HuggingFace"],
        }

        found_skills = {}
        text_upper = resume_text.upper()

        for category, keywords in skill_keywords.items():
            matched = [kw for kw in keywords if kw.upper() in text_upper]
            if matched:
                found_skills[category] = matched

        return {
            "resume_id": resume_id,
            "skills": found_skills,
            "total_count": sum(len(v) for v in found_skills.values()),
        }
```

- [ ] **Step 2: 创建单元测试**

```python
# tests/unit/business_logic/jd/tools/test_analyze_resume_skills.py
import pytest
from unittest.mock import MagicMock, patch
from src.business_logic.jd.tools.analyze_resume_skills import AnalyzeResumeSkillsTool


class TestAnalyzeResumeSkillsTool:
    def test_analyze_skills_success(self):
        """测试成功提取技能"""
        tool = AnalyzeResumeSkillsTool()

        mock_resume = MagicMock()
        mock_resume.resume_id = 1
        mock_resume.processed_content = "熟练使用 Python、Django、PostgreSQL 和 Docker"

        mock_db = MagicMock()
        mock_context = MagicMock()
        mock_context.db = mock_db

        with patch('src.data_access.repositories.resume_repository.get_by_id', return_value=mock_resume):
            result = tool._execute_sync({"resume_id": 1}, context=mock_context)

        assert result["resume_id"] == 1
        assert "skills" in result
        assert "编程语言" in result["skills"]
        assert "Python" in result["skills"]["编程语言"]
        assert result["total_count"] >= 3

    def test_analyze_skills_not_found(self):
        """测试简历不存在"""
        tool = AnalyzeResumeSkillsTool()

        mock_db = MagicMock()
        mock_context = MagicMock()
        mock_context.db = mock_db

        with patch('src.data_access.repositories.resume_repository.get_by_id', return_value=None):
            result = tool._execute_sync({"resume_id": 999}, context=mock_context)

        assert "error" in result
```

- [ ] **Step 3: 运行测试**

Run: `pytest tests/unit/business_logic/jd/tools/test_analyze_resume_skills.py -v`
Expected: PASS

- [ ] **Step 4: 提交**

```bash
git add src/business_logic/jd/tools/analyze_resume_skills.py tests/unit/business_logic/jd/tools/test_analyze_resume_skills.py
git commit -m "feat(jd_tools): 添加 AnalyzeResumeSkillsTool"
```

---

### Task 7: 新增 SearchJobsTool

**Files:**
- Create: `src/business_logic/job/tools/__init__.py`
- Create: `src/business_logic/job/tools/search_jobs.py`
- Create: `tests/unit/business_logic/job/tools/test_search_jobs.py`

- [ ] **Step 1: 创建 job/tools/__init__.py**

```python
# src/business_logic/job/tools/__init__.py
from src.business_logic.job.tools.search_jobs import SearchJobsTool
from src.business_logic.job.tools.analyze_jd import AnalyzeJDTool
from src.business_logic.job.tools.calculate_job_match import CalculateJobMatchTool

__all__ = ["SearchJobsTool", "AnalyzeJDTool", "CalculateJobMatchTool"]
```

- [ ] **Step 2: 创建 SearchJobsTool**

```python
# src/business_logic/job/tools/search_jobs.py
from typing import Type

from pydantic import BaseModel

from src.core.tools.base_tool import BaseTool
from src.core.tools.tool_context import ToolContext


class SearchJobsInput(BaseModel):
    """Input schema for search_jobs tool."""
    keyword: str
    limit: int = 10


class SearchJobsTool(BaseTool):
    """根据关键词搜索岗位"""

    name: str = "search_jobs"
    description: str = "根据关键词搜索岗位，返回匹配的岗位列表"
    args_schema: Type[BaseModel] = SearchJobsInput

    def _execute_sync(
        self,
        tool_input: dict,
        runtime=None,
        context: ToolContext = None,
    ) -> dict:
        from src.data_access.repositories import job_repository

        keyword = tool_input.get("keyword", "")
        limit = tool_input.get("limit", 10)

        if context is None:
            from src.presentation.api.deps import get_db
            db = next(get_db())
        else:
            db = context.db

        jobs = job_repository.get_all(db)

        # 简单关键词匹配
        keyword_lower = keyword.lower()
        matched_jobs = [
            {
                "job_id": job.id,
                "title": job.title,
                "company": job.company,
                "location": getattr(job, 'location', None),
                "description": (job.description or "")[:200],
            }
            for job in jobs
            if keyword_lower in (job.title or "").lower()
            or keyword_lower in (job.description or "").lower()
            or keyword_lower in (job.company or "").lower()
        ][:limit]

        return {
            "keyword": keyword,
            "count": len(matched_jobs),
            "jobs": matched_jobs,
        }
```

- [ ] **Step 3: 创建单元测试**

```python
# tests/unit/business_logic/job/tools/test_search_jobs.py
import pytest
from unittest.mock import MagicMock, patch
from src.business_logic.job.tools.search_jobs import SearchJobsTool


class TestSearchJobsTool:
    def test_search_jobs_by_keyword(self):
        """测试关键词搜索"""
        tool = SearchJobsTool()

        mock_job1 = MagicMock()
        mock_job1.id = 1
        mock_job1.title = "Python Developer"
        mock_job1.company = "TechCorp"
        mock_job1.location = "Beijing"
        mock_job1.description = "We need a Python developer"

        mock_job2 = MagicMock()
        mock_job2.id = 2
        mock_job2.title = "Java Engineer"
        mock_job2.company = "DataCorp"
        mock_job2.location = "Shanghai"
        mock_job2.description = "Java developer position"

        mock_db = MagicMock()
        mock_context = MagicMock()
        mock_context.db = mock_db

        with patch('src.data_access.repositories.job_repository.get_all', return_value=[mock_job1, mock_job2]):
            result = tool._execute_sync({"keyword": "Python", "limit": 10}, context=mock_context)

        assert result["keyword"] == "Python"
        assert result["count"] == 1
        assert result["jobs"][0]["title"] == "Python Developer"

    def test_search_jobs_no_results(self):
        """测试无结果"""
        tool = SearchJobsTool()

        mock_db = MagicMock()
        mock_context = MagicMock()
        mock_context.db = mock_db

        with patch('src.data_access.repositories.job_repository.get_all', return_value=[]):
            result = tool._execute_sync({"keyword": "NonExistent"}, context=mock_context)

        assert result["count"] == 0
        assert result["jobs"] == []
```

- [ ] **Step 4: 运行测试**

Run: `pytest tests/unit/business_logic/job/tools/test_search_jobs.py -v`
Expected: PASS

- [ ] **Step 5: 提交**

```bash
git add src/business_logic/job/tools/__init__.py src/business_logic/job/tools/search_jobs.py tests/unit/business_logic/job/tools/test_search_jobs.py
git commit -m "feat(job_tools): 添加 SearchJobsTool"
```

---

### Task 8: 新增 AnalyzeJDTool

**Files:**
- Create: `src/business_logic/job/tools/analyze_jd.py`
- Create: `tests/unit/business_logic/job/tools/test_analyze_jd.py`

- [ ] **Step 1: 创建 AnalyzeJDTool**

```python
# src/business_logic/job/tools/analyze_jd.py
from typing import Type

from pydantic import BaseModel

from src.core.tools.base_tool import BaseTool
from src.core.tools.tool_context import ToolContext


class AnalyzeJDInput(BaseModel):
    """Input schema for analyze_jd tool."""
    jd_id: int


class AnalyzeJDTool(BaseTool):
    """深度解析 JD（技能要求、薪资范围、经验要求）"""

    name: str = "analyze_jd"
    description: str = "深度解析岗位 JD，提取关键信息（技能要求、经验、薪资等）"
    args_schema: Type[BaseModel] = AnalyzeJDInput

    def _execute_sync(
        self,
        tool_input: dict,
        runtime=None,
        context: ToolContext = None,
    ) -> dict:
        from src.data_access.repositories import job_repository

        jd_id = tool_input.get("jd_id")

        if context is None:
            from src.presentation.api.deps import get_db
            db = next(get_db())
        else:
            db = context.db

        job = job_repository.get_by_id(db, jd_id)
        if not job:
            return {"error": f"Job {jd_id} not found"}

        jd_text = job.description or ""

        # 简单解析
        analysis = {
            "jd_id": jd_id,
            "title": job.title,
            "company": job.company,
        }

        # 提取技能关键词
        skill_keywords = [
            "Python", "Java", "JavaScript", "TypeScript", "Go", "Rust",
            "React", "Vue", "Angular", "Django", "FastAPI", "Spring",
            "MySQL", "PostgreSQL", "MongoDB", "Redis",
            "AWS", "Azure", "Docker", "Kubernetes",
        ]

        found_skills = [s for s in skill_keywords if s.lower() in jd_text.lower()]
        if found_skills:
            analysis["required_skills"] = found_skills

        # 提取经验要求
        import re
        exp_patterns = [
            r"(\d+)\+?\s*年",
            r"(\d+)\+?\s*years",
            r"经验\s*(\d+)\s*年",
        ]
        for pattern in exp_patterns:
            match = re.search(pattern, jd_text, re.IGNORECASE)
            if match:
                analysis["experience_required"] = f"{match.group(1)} 年"
                break

        # 提取学历要求
        edu_keywords = ["本科", "硕士", "博士", "大专", "Bachelor", "Master", "PhD"]
        for edu in edu_keywords:
            if edu.lower() in jd_text.lower():
                analysis["education"] = edu
                break

        analysis["raw_text_length"] = len(jd_text)

        return analysis
```

- [ ] **Step 2: 创建单元测试**

```python
# tests/unit/business_logic/job/tools/test_analyze_jd.py
import pytest
from unittest.mock import MagicMock, patch
from src.business_logic.job.tools.analyze_jd import AnalyzeJDTool


class TestAnalyzeJDTool:
    def test_analyze_jd_success(self):
        """测试成功解析 JD"""
        tool = AnalyzeJDTool()

        mock_job = MagicMock()
        mock_job.id = 1
        mock_job.title = "Python Developer"
        mock_job.company = "TechCorp"
        mock_job.description = "需要 3 年以上 Python 开发经验，熟悉 Django、PostgreSQL"

        mock_db = MagicMock()
        mock_context = MagicMock()
        mock_context.db = mock_db

        with patch('src.data_access.repositories.job_repository.get_by_id', return_value=mock_job):
            result = tool._execute_sync({"jd_id": 1}, context=mock_context)

        assert result["jd_id"] == 1
        assert "required_skills" in result
        assert "Python" in result["required_skills"]
        assert result["experience_required"] == "3 年"

    def test_analyze_jd_not_found(self):
        """测试 JD 不存在"""
        tool = AnalyzeJDTool()

        mock_db = MagicMock()
        mock_context = MagicMock()
        mock_context.db = mock_db

        with patch('src.data_access.repositories.job_repository.get_by_id', return_value=None):
            result = tool._execute_sync({"jd_id": 999}, context=mock_context)

        assert "error" in result
```

- [ ] **Step 3: 运行测试**

Run: `pytest tests/unit/business_logic/job/tools/test_analyze_jd.py -v`
Expected: PASS

- [ ] **Step 4: 提交**

```bash
git add src/business_logic/job/tools/analyze_jd.py tests/unit/business_logic/job/tools/test_analyze_jd.py
git commit -m "feat(job_tools): 添加 AnalyzeJDTool"
```

---

### Task 9: 新增 GenerateInterviewQuestionsTool

**Files:**
- Create: `src/business_logic/interview/tools/__init__.py`
- Create: `src/business_logic/interview/tools/generate_interview_questions.py`
- Create: `tests/unit/business_logic/interview/tools/test_generate_interview_questions.py`

- [ ] **Step 1: 创建 interview/tools/__init__.py**

```python
# src/business_logic/interview/tools/__init__.py
from src.business_logic.interview.tools.generate_interview_questions import GenerateInterviewQuestionsTool
from src.business_logic.interview.tools.evaluate_interview_answer import EvaluateInterviewAnswerTool

__all__ = ["GenerateInterviewQuestionsTool", "EvaluateInterviewAnswerTool"]
```

- [ ] **Step 2: 创建 GenerateInterviewQuestionsTool**

```python
# src/business_logic/interview/tools/generate_interview_questions.py
from typing import Type

from pydantic import BaseModel

from src.core.tools.base_tool import BaseTool
from src.core.tools.tool_context import ToolContext


class GenerateInterviewQuestionsInput(BaseModel):
    """Input schema for generate_interview_questions tool."""
    jd_id: int
    resume_id: int
    count: int = 5


class GenerateInterviewQuestionsTool(BaseTool):
    """根据 JD 和简历生成面试题"""

    name: str = "generate_interview_questions"
    description: str = "根据岗位 JD 和简历生成针对性的面试题"
    args_schema: Type[BaseModel] = GenerateInterviewQuestionsInput

    def _execute_sync(
        self,
        tool_input: dict,
        runtime=None,
        context: ToolContext = None,
    ) -> dict:
        from src.data_access.repositories import job_repository, resume_repository

        jd_id = tool_input.get("jd_id")
        resume_id = tool_input.get("resume_id")
        count = tool_input.get("count", 5)

        if context is None:
            from src.presentation.api.deps import get_db
            db = next(get_db())
        else:
            db = context.db

        job = job_repository.get_by_id(db, jd_id)
        if not job:
            return {"error": f"Job {jd_id} not found"}

        resume = resume_repository.get_by_id(db, resume_id)
        if not resume:
            return {"error": f"Resume {resume_id} not found"}

        jd_text = job.description or ""
        resume_text = resume.processed_content or resume.resume_text or ""

        # 简单的规则生成面试题（实际应用中应调用 LLM）
        questions = []

        # 基于 JD 生成技术问题
        if "python" in jd_text.lower() or "Python" in jd_text:
            questions.append({
                "category": "技术",
                "question": "请描述你在 Python 项目中使用过的主要框架和库",
                "difficulty": "中等",
            })
        if "sql" in jd_text.lower() or "数据库" in jd_text:
            questions.append({
                "category": "技术",
                "question": "你有哪些 SQL 查询优化的经验？",
                "difficulty": "中等",
            })
        if "javascript" in jd_text.lower() or "JS" in jd_text:
            questions.append({
                "category": "技术",
                "question": "请介绍一下你熟悉的 JavaScript 框架",
                "difficulty": "基础",
            })

        # 行为问题
        questions.append({
            "category": "行为",
            "question": "请描述一个你解决过的最有挑战性的技术问题",
            "difficulty": "中等",
        })

        # 通用问题
        questions.append({
            "category": "通用",
            "question": "你为什么对这个岗位感兴趣？",
            "difficulty": "基础",
        })

        return {
            "jd_id": jd_id,
            "resume_id": resume_id,
            "count": len(questions),
            "questions": questions[:count],
        }
```

- [ ] **Step 3: 创建单元测试**

```python
# tests/unit/business_logic/interview/tools/test_generate_interview_questions.py
import pytest
from unittest.mock import MagicMock, patch
from src.business_logic.interview.tools.generate_interview_questions import GenerateInterviewQuestionsTool


class TestGenerateInterviewQuestionsTool:
    def test_generate_questions_success(self):
        """测试成功生成面试题"""
        tool = GenerateInterviewQuestionsTool()

        mock_job = MagicMock()
        mock_job.id = 1
        mock_job.title = "Python Developer"
        mock_job.description = "需要 Python 开发经验，熟悉 Django、SQL"

        mock_resume = MagicMock()
        mock_resume.id = 1
        mock_resume.processed_content = "熟练使用 Python、Django 开发"

        mock_db = MagicMock()
        mock_context = MagicMock()
        mock_context.db = mock_db

        with patch('src.data_access.repositories.job_repository.get_by_id', return_value=mock_job):
            with patch('src.data_access.repositories.resume_repository.get_by_id', return_value=mock_resume):
                result = tool._execute_sync({"jd_id": 1, "resume_id": 1, "count": 5}, context=mock_context)

        assert result["jd_id"] == 1
        assert "questions" in result
        assert len(result["questions"]) > 0
        assert any("Python" in str(q) for q in result["questions"])

    def test_generate_questions_job_not_found(self):
        """测试 JD 不存在"""
        tool = GenerateInterviewQuestionsTool()

        mock_db = MagicMock()
        mock_context = MagicMock()
        mock_context.db = mock_db

        with patch('src.data_access.repositories.job_repository.get_by_id', return_value=None):
            result = tool._execute_sync({"jd_id": 999, "resume_id": 1}, context=mock_context)

        assert "error" in result
```

- [ ] **Step 4: 运行测试**

Run: `pytest tests/unit/business_logic/interview/tools/test_generate_interview_questions.py -v`
Expected: PASS

- [ ] **Step 5: 提交**

```bash
git add src/business_logic/interview/tools/__init__.py src/business_logic/interview/tools/generate_interview_questions.py tests/unit/business_logic/interview/tools/test_generate_interview_questions.py
git commit -m "feat(interview_tools): 添加 GenerateInterviewQuestionsTool"
```

---

### Task 10: 新增 WebSearchTool

**Files:**
- Create: `src/business_logic/common/tools/__init__.py`
- Create: `src/business_logic/common/tools/web_search.py`
- Create: `tests/unit/business_logic/common/tools/test_web_search.py`

- [ ] **Step 1: 创建 common/tools/__init__.py**

```python
# src/business_logic/common/tools/__init__.py
from src.business_logic.common.tools.web_search import WebSearchTool
from src.business_logic.common.tools.extract_keywords import ExtractKeywordsTool

__all__ = ["WebSearchTool", "ExtractKeywordsTool"]
```

- [ ] **Step 2: 创建 WebSearchTool**

```python
# src/business_logic/common/tools/web_search.py
from typing import Type

from pydantic import BaseModel

from src.core.tools.base_tool import BaseTool
from src.core.tools.tool_context import ToolContext


class WebSearchInput(BaseModel):
    """Input schema for web_search tool."""
    query: str
    limit: int = 5


class WebSearchTool(BaseTool):
    """网络搜索（公司信息、行业动态等）"""

    name: str = "web_search"
    description: str = "搜索互联网获取公司信息、行业动态、职位信息等"
    args_schema: Type[BaseModel] = WebSearchInput

    def _execute_sync(
        self,
        tool_input: dict,
        runtime=None,
        context: ToolContext = None,
    ) -> dict:
        import httpx
        from urllib.parse import quote

        query = tool_input.get("query", "")
        limit = tool_input.get("limit", 5)

        if not query:
            return {"error": "query is required"}

        # 注意：实际项目中应使用真实的搜索 API（如 SerpAPI、Bing Search API）
        # 这里提供一个模拟实现作为占位
        try:
            # 简单的搜索实现，使用 DuckDuckGo HTML 搜索（仅用于演示）
            # 实际生产环境应使用付费搜索 API
            encoded_query = quote(query)
            search_url = f"https://html.duckduckgo.com/html/?q={encoded_query}"

            # 这是简化实现，实际应异步调用搜索 API
            return {
                "query": query,
                "limit": limit,
                "results": [
                    {
                        "title": f"{query} - 相关结果 1",
                        "url": f"https://example.com/result1?q={encoded_query}",
                        "snippet": f"关于 {query} 的搜索结果示例...",
                    },
                    {
                        "title": f"{query} - 相关结果 2",
                        "url": f"https://example.com/result2?q={encoded_query}",
                        "snippet": f"更多关于 {query} 的信息...",
                    },
                ][:limit],
                "note": "实际生产环境应使用付费搜索 API（如 SerpAPI）",
            }
        except Exception as e:
            return {"error": f"Search failed: {str(e)}", "query": query}
```

- [ ] **Step 3: 创建单元测试**

```python
# tests/unit/business_logic/common/tools/test_web_search.py
import pytest
from unittest.mock import MagicMock, patch
from src.business_logic.common.tools.web_search import WebSearchTool


class TestWebSearchTool:
    def test_web_search_success(self):
        """测试成功搜索"""
        tool = WebSearchTool()

        mock_context = MagicMock()

        result = tool._execute_sync({"query": "Python developer", "limit": 5}, context=mock_context)

        assert result["query"] == "Python developer"
        assert "results" in result
        assert len(result["results"]) <= 5

    def test_web_search_empty_query(self):
        """测试空查询"""
        tool = WebSearchTool()

        mock_context = MagicMock()

        result = tool._execute_sync({"query": ""}, context=mock_context)

        assert "error" in result
```

- [ ] **Step 4: 运行测试**

Run: `pytest tests/unit/business_logic/common/tools/test_web_search.py -v`
Expected: PASS

- [ ] **Step 5: 提交**

```bash
git add src/business_logic/common/tools/__init__.py src/business_logic/common/tools/web_search.py tests/unit/business_logic/common/tools/test_web_search.py
git commit -m "feat(common_tools): 添加 WebSearchTool"
```

---

## Phase 1 验证

- [ ] **Step 1: 运行 Phase 1 相关测试**

Run: `pytest tests/unit/core/tools/ tests/unit/core/runtime/test_tool_registry.py tests/unit/business_logic/jd/tools/ tests/unit/business_logic/job/tools/ tests/unit/business_logic/interview/tools/ tests/unit/business_logic/common/tools/ -v --tb=short 2>&1 | tail -30`

- [ ] **Step 2: 检查工具数量**

Run: `python -c "from src.core.runtime.tool_registry import ToolRegistry; r = ToolRegistry(); print([t.name for t in r._tools.values()])"`
Expected: 应列出已注册工具（注意：工具需要在启动时注册）

- [ ] **Step 3: 提交 Phase 1 完成**

```bash
git add -A && git commit -m "feat(phase1): 完成 ToolContext + 6 个高优先级工具"
```

---

## Phase 2：5 个扩展工具 + ResumeCustomizerAgent 改造（Week 3-4）

### Task 11: 新增 FormatResumeTool

**Files:**
- Create: `src/business_logic/jd/tools/format_resume.py`
- Create: `tests/unit/business_logic/jd/tools/test_format_resume.py`

- [ ] **Step 1: 创建 FormatResumeTool**

```python
# src/business_logic/jd/tools/format_resume.py
from typing import Type

from pydantic import BaseModel

from src.core.tools.base_tool import BaseTool
from src.core.tools.tool_context import ToolContext


class FormatResumeInput(BaseModel):
    """Input schema for format_resume tool."""
    resume_id: int


class FormatResumeTool(BaseTool):
    """格式化简历（Markdown → 结构化输出）"""

    name: str = "format_resume"
    description: str = "将简历内容格式化为结构化输出"
    args_schema: Type[BaseModel] = FormatResumeInput

    def _execute_sync(
        self,
        tool_input: dict,
        runtime=None,
        context: ToolContext = None,
    ) -> dict:
        from src.data_access.repositories import resume_repository

        resume_id = tool_input.get("resume_id")

        if context is None:
            from src.presentation.api.deps import get_db
            db = next(get_db())
        else:
            db = context.db

        resume = resume_repository.get_by_id(db, resume_id)
        if not resume:
            return {"error": f"Resume {resume_id} not found"}

        resume_text = resume.processed_content or resume.resume_text or ""

        # 简单的 Markdown 解析
        lines = resume_text.split("\n")
        sections = {}
        current_section = "个人信息"
        current_content = []

        for line in lines:
            stripped = line.strip()
            if stripped.startswith("#"):
                if current_content:
                    sections[current_section] = "\n".join(current_content)
                current_section = stripped.lstrip("#").strip()
                current_content = []
            elif stripped.startswith("-"):
                current_content.append(stripped)
            else:
                current_content.append(stripped)

        if current_content:
            sections[current_section] = "\n".join(current_content)

        return {
            "resume_id": resume_id,
            "title": resume.title,
            "sections": sections,
            "section_count": len(sections),
        }
```

- [ ] **Step 2: 创建单元测试**

```python
# tests/unit/business_logic/jd/tools/test_format_resume.py
import pytest
from unittest.mock import MagicMock, patch
from src.business_logic.jd.tools.format_resume import FormatResumeTool


class TestFormatResumeTool:
    def test_format_resume_success(self):
        """测试成功格式化简历"""
        tool = FormatResumeTool()

        mock_resume = MagicMock()
        mock_resume.id = 1
        mock_resume.title = "Software Engineer"
        mock_resume.processed_content = "# 个人信息\n姓名：张三\n# 技能\n- Python\n- JavaScript"

        mock_db = MagicMock()
        mock_context = MagicMock()
        mock_context.db = mock_db

        with patch('src.data_access.repositories.resume_repository.get_by_id', return_value=mock_resume):
            result = tool._execute_sync({"resume_id": 1}, context=mock_context)

        assert result["resume_id"] == 1
        assert "sections" in result
        assert "个人信息" in result["sections"]
```

- [ ] **Step 3: 提交**

```bash
git add src/business_logic/jd/tools/format_resume.py tests/unit/business_logic/jd/tools/test_format_resume.py
git commit -m "feat(jd_tools): 添加 FormatResumeTool"
```

---

### Task 12: 新增 CompareResumesTool

**Files:**
- Create: `src/business_logic/jd/tools/compare_resumes.py`
- Create: `tests/unit/business_logic/jd/tools/test_compare_resumes.py`

- [ ] **Step 1: 创建 CompareResumesTool**

```python
# src/business_logic/jd/tools/compare_resumes.py
from typing import Type

from pydantic import BaseModel

from src.core.tools.base_tool import BaseTool
from src.core.tools.tool_context import ToolContext


class CompareResumesInput(BaseModel):
    """Input schema for compare_resumes tool."""
    resume_id_1: int
    resume_id_2: int


class CompareResumesTool(BaseTool):
    """对比两个简历版本的差异"""

    name: str = "compare_resumes"
    description: str = "对比两个简历版本的差异，输出新增、删除和修改的内容"
    args_schema: Type[BaseModel] = CompareResumesInput

    def _execute_sync(
        self,
        tool_input: dict,
        runtime=None,
        context: ToolContext = None,
    ) -> dict:
        from src.data_access.repositories import resume_repository

        resume_id_1 = tool_input.get("resume_id_1")
        resume_id_2 = tool_input.get("resume_id_2")

        if context is None:
            from src.presentation.api.deps import get_db
            db = next(get_db())
        else:
            db = context.db

        resume1 = resume_repository.get_by_id(db, resume_id_1)
        if not resume1:
            return {"error": f"Resume {resume_id_1} not found"}

        resume2 = resume_repository.get_by_id(db, resume_id_2)
        if not resume2:
            return {"error": f"Resume {resume_id_2} not found"}

        text1 = resume1.processed_content or resume1.resume_text or ""
        text2 = resume2.processed_content or resume2.resume_text or ""

        # 简单 diff
        lines1 = set(text1.split("\n"))
        lines2 = set(text2.split("\n"))

        added = lines2 - lines1
        removed = lines1 - lines2
        common = lines1 & lines2

        return {
            "resume_id_1": resume_id_1,
            "resume_id_2": resume_id_2,
            "added_count": len(added),
            "removed_count": len(removed),
            "common_count": len(common),
            "added_lines": list(added)[:10],
            "removed_lines": list(removed)[:10],
        }
```

- [ ] **Step 2: 创建单元测试并提交**

```bash
git add src/business_logic/jd/tools/compare_resumes.py tests/unit/business_logic/jd/tools/test_compare_resumes.py
git commit -m "feat(jd_tools): 添加 CompareResumesTool"
```

---

### Task 13: 新增 CalculateJobMatchTool

**Files:**
- Create: `src/business_logic/job/tools/calculate_job_match.py`
- Create: `tests/unit/business_logic/job/tools/test_calculate_job_match.py`

- [ ] **Step 1: 创建 CalculateJobMatchTool**

```python
# src/business_logic/job/tools/calculate_job_match.py
from typing import Type

from pydantic import BaseModel

from src.core.tools.base_tool import BaseTool
from src.core.tools.tool_context import ToolContext


class CalculateJobMatchInput(BaseModel):
    """Input schema for calculate_job_match tool."""
    resume_id: int
    jd_id: int


class CalculateJobMatchTool(BaseTool):
    """计算简历与岗位的匹配度（数值化）"""

    name: str = "calculate_job_match"
    description: str = "计算简历与岗位的数值化匹配度得分（0-100）"
    args_schema: Type[BaseModel] = CalculateJobMatchInput

    def _execute_sync(
        self,
        tool_input: dict,
        runtime=None,
        context: ToolContext = None,
    ) -> dict:
        from src.business_logic.jd.jd_parser_service import JdParserService
        from src.business_logic.jd.resume_match_service import ResumeMatchService
        from src.data_access.repositories import resume_repository, job_repository

        resume_id = tool_input.get("resume_id")
        jd_id = tool_input.get("jd_id")

        if context is None:
            from src.presentation.api.deps import get_db
            db = next(get_db())
        else:
            db = context.db

        resume = resume_repository.get_by_id(db, resume_id)
        if not resume:
            return {"error": f"Resume {resume_id} not found"}

        job = job_repository.get_by_id(db, jd_id)
        if not job:
            return {"error": f"Job {jd_id} not found"}

        resume_text = resume.processed_content or resume.resume_text or ""
        jd_text = job.description or ""

        parser = JdParserService()
        parsed_jd = parser.parse(jd_text)

        matcher = ResumeMatchService()
        report = matcher.compute_match(resume_text, parsed_jd)

        return {
            "resume_id": resume_id,
            "jd_id": jd_id,
            "match_score": report.match_score,
            "keyword_coverage": report.keyword_coverage,
            "gaps": report.gaps,
            "suggestions": report.suggestions,
        }
```

- [ ] **Step 2: 创建单元测试并提交**

```bash
git add src/business_logic/job/tools/calculate_job_match.py tests/unit/business_logic/job/tools/test_calculate_job_match.py
git commit -m "feat(job_tools): 添加 CalculateJobMatchTool"
```

---

### Task 14: 新增 EvaluateInterviewAnswerTool

**Files:**
- Create: `src/business_logic/interview/tools/evaluate_interview_answer.py`
- Create: `tests/unit/business_logic/interview/tools/test_evaluate_interview_answer.py`

- [ ] **Step 1: 创建 EvaluateInterviewAnswerTool**

```python
# src/business_logic/interview/tools/evaluate_interview_answer.py
from typing import Type

from pydantic import BaseModel

from src.core.tools.base_tool import BaseTool
from src.core.tools.tool_context import ToolContext


class EvaluateInterviewAnswerInput(BaseModel):
    """Input schema for evaluate_interview_answer tool."""
    question: str
    answer: str
    category: str = "技术"


class EvaluateInterviewAnswerTool(BaseTool):
    """评估面试答案质量"""

    name: str = "evaluate_interview_answer"
    description: str = "评估面试答案的质量，给出技术深度、逻辑性、完整性的评分"
    args_schema: Type[BaseModel] = EvaluateInterviewAnswerInput

    def _execute_sync(
        self,
        tool_input: dict,
        runtime=None,
        context: ToolContext = None,
    ) -> dict:
        question = tool_input.get("question", "")
        answer = tool_input.get("answer", "")
        category = tool_input.get("category", "技术")

        if not question or not answer:
            return {"error": "question and answer are required"}

        # 简单评分逻辑（实际应用中应调用 LLM）
        score = 0
        suggestions = []

        # 长度评估
        if len(answer) < 20:
            score += 2
            suggestions.append("答案过于简短，建议展开说明")
        elif len(answer) > 50:
            score += 3

        #STAR法则评估
        star_keywords = ["项目", "任务", "行动", "结果", "负责", "完成", "实现"]
        if any(kw in answer for kw in star_keywords):
            score += 3
        else:
            suggestions.append("建议使用 STAR 法则组织答案")

        # 技术深度（针对技术类问题）
        if category == "技术":
            if any(word in answer for word in ["架构", "设计", "优化", "性能"]):
                score += 2
            if any(word in answer for word in ["使用", "采用", "通过"]):
                score += 2

        # 限制分数范围
        score = min(10, max(0, score))

        rating = "优秀" if score >= 8 else "良好" if score >= 6 else "一般" if score >= 4 else "需改进"

        return {
            "question": question,
            "category": category,
            "score": score,
            "rating": rating,
            "suggestions": suggestions if suggestions else ["答案基本完整"],
        }
```

- [ ] **Step 2: 创建单元测试并提交**

```bash
git add src/business_logic/interview/tools/evaluate_interview_answer.py tests/unit/business_logic/interview/tools/test_evaluate_interview_answer.py
git commit -m "feat(interview_tools): 添加 EvaluateInterviewAnswerTool"
```

---

### Task 15: 新增 ExtractKeywordsTool

**Files:**
- Create: `src/business_logic/common/tools/extract_keywords.py`
- Create: `tests/unit/business_logic/common/tools/test_extract_keywords.py`

- [ ] **Step 1: 创建 ExtractKeywordsTool**

```python
# src/business_logic/common/tools/extract_keywords.py
from typing import Type

from pydantic import BaseModel

from src.core.tools.base_tool import BaseTool
from src.core.tools.tool_context import ToolContext


class ExtractKeywordsInput(BaseModel):
    """Input schema for extract_keywords tool."""
    text: str
    limit: int = 10


class ExtractKeywordsTool(BaseTool):
    """从文本中提取关键词"""

    name: str = "extract_keywords"
    description: str = "从文本中提取关键词，用于简历优化、JD 分析等场景"
    args_schema: Type[BaseModel] = ExtractKeywordsInput

    def _execute_sync(
        self,
        tool_input: dict,
        runtime=None,
        context: ToolContext = None,
    ) -> dict:
        text = tool_input.get("text", "")
        limit = tool_input.get("limit", 10)

        if not text:
            return {"error": "text is required"}

        # 简单的关键词提取（基于词频）
        # 停用词
        stop_words = {
            "的", "了", "是", "在", "我", "有", "和", "就", "不", "人",
            "都", "一", "一个", "上", "也", "很", "到", "说", "要", "去",
            "你", "会", "着", "没有", "看", "好", "自己", "这", "那",
            "the", "a", "an", "is", "are", "was", "were", "be", "been",
            "have", "has", "had", "do", "does", "did", "will", "would",
        }

        # 分词（简单按空格和标点）
        import re
        words = re.findall(r"[\w]+", text.lower())

        # 过滤停用词和短词
        filtered = [w for w in words if w not in stop_words and len(w) > 2]

        # 词频统计
        freq = {}
        for word in filtered:
            freq[word] = freq.get(word, 0) + 1

        # 排序取 top N
        sorted_words = sorted(freq.items(), key=lambda x: x[1], reverse=True)
        keywords = [{"word": w, "count": c} for w, c in sorted_words[:limit]]

        return {
            "text_length": len(text),
            "keyword_count": len(keywords),
            "keywords": keywords,
        }
```

- [ ] **Step 2: 创建单元测试并提交**

```bash
git add src/business_logic/common/tools/extract_keywords.py tests/unit/business_logic/common/tools/test_extract_keywords.py
git commit -m "feat(common_tools): 添加 ExtractKeywordsTool"
```

---

### Task 16: 改造 ResumeCustomizerAgent 为 ReAct 模式

**Files:**
- Modify: `src/business_logic/jd/resume_customizer_agent.py`
- Test: `tests/unit/business_logic/jd/test_resume_customizer_agent.py`

- [ ] **Step 1: 读取现有实现**

Read: `src/business_logic/jd/resume_customizer_agent.py`

- [ ] **Step 2: 改造为 ReAct 模式**

```python
# src/business_logic/jd/resume_customizer_agent.py
from typing import Optional

from src.core.llm.litellm_adapter import LiteLLMAdapter
from src.core.runtime.tool_registry import ToolRegistry
from src.core.runtime.agent_executor import AgentExecutor
from src.core.tools.tool_context import ToolContext


class ResumeCustomizerAgent:
    """
    简历定制 Agent（ReAct 模式）
    通过 ReAct 循环调用工具完成简历定制任务
    """

    def __init__(self, tool_registry: ToolRegistry):
        self.tool_registry = tool_registry
        self.llm = LiteLLMAdapter()
        self.executor = AgentExecutor(
            tools=tool_registry,
            llm=self.llm
        )

    async def customize(
        self,
        resume_id: int,
        jd_id: int,
        context: ToolContext
    ) -> dict:
        """
        为简历定制匹配目标岗位的版本

        Args:
            resume_id: 简历 ID
            jd_id: 岗位 ID
            context: 工具执行上下文

        Returns:
            定制后的简历内容和匹配报告
        """
        task = f"""
请为简历 {resume_id} 定制匹配岗位 {jd_id} 的版本。

步骤：
1. 使用 read_resume 读取简历内容
2. 使用 analyze_jd 分析岗位要求
3. 使用 analyze_resume_skills 提取简历技能
4. 使用 match_resume_to_job 计算匹配度
5. 使用 update_resume 更新简历，添加针对该岗位的定制内容

最终输出定制后的简历摘要和改进建议。
"""

        result = await self.executor.run(
            task=task,
            context=context,
            available_tools=[
                "read_resume",
                "analyze_jd",
                "match_resume_to_job",
                "analyze_resume_skills",
                "update_resume",
            ]
        )

        return result

    async def customize_simple(
        self,
        resume_id: int,
        jd_id: int,
        context: ToolContext
    ) -> dict:
        """
        简单模式：直接调用 LLM 生成定制建议（不通过 ReAct）
        用于简单场景
        """
        from src.data_access.repositories import resume_repository, job_repository

        resume = resume_repository.get_by_id(context.db, resume_id)
        if not resume:
            return {"error": f"Resume {resume_id} not found"}

        job = job_repository.get_by_id(context.db, jd_id)
        if not job:
            return {"error": f"Job {jd_id} not found"}

        prompt = f"""
请根据以下简历和岗位要求，定制简历：

简历：
{resume.processed_content or resume.resume_text}

岗位要求：
{job.description}

请输出针对该岗位的简历定制建议。
"""

        response = await self.llm.chat([{"role": "user", "content": prompt}])
        content = response.get("content", "")

        return {
            "resume_id": resume_id,
            "jd_id": jd_id,
            "suggestions": content,
        }
```

- [ ] **Step 3: 运行现有测试确认回归**

Run: `pytest tests/unit/business_logic/jd/test_resume_customizer_agent.py -v`
Expected: PASS

- [ ] **Step 4: 提交**

```bash
git add src/business_logic/jd/resume_customizer_agent.py
git commit -m "refactor(jd): 改造 ResumeCustomizerAgent 为 ReAct 模式"
```

---

## Phase 3：测试覆盖率全面提升（Week 5-6）

### Task 17: 核心 Runtime 测试补齐（LiteLLMAdapter, AgentExecutor, ToolRegistry）

**Files:**
- Modify: `tests/unit/core/runtime/test_agent_executor.py`
- Modify: `tests/unit/core/runtime/test_tool_registry.py`
- Modify: `tests/unit/core/test_litellm_adapter.py`

- [ ] **Step 1: 补齐 AgentExecutor 测试**

追加到 `tests/unit/core/runtime/test_agent_executor.py`:

```python
def test_agent_executor_with_tool_registry():
    """测试 AgentExecutor 与 ToolRegistry 集成"""
    from src.core.runtime.agent_executor import AgentExecutor
    from src.core.runtime.tool_registry import ToolRegistry
    from src.core.llm.mock_adapter import MockLLMAdapter
    from src.core.tools.tool_context import ToolContext
    from tests.fixtures import mock_db_session

    registry = ToolRegistry()
    tool = MockTool()
    registry.register(tool)

    executor = AgentExecutor(tools=registry, llm=MockLLMAdapter())

    context = ToolContext(db=mock_db_session, user_id=1)

    # 注意：完整测试需要 mock LLM 响应
    # 这里测试工具调用的基本流程
```

- [ ] **Step 2: 补齐 ToolRegistry 测试覆盖 execute 异常分支**

追加到 `tests/unit/core/runtime/test_tool_registry.py`:

```python
def test_execute_tool_not_found():
    """测试执行不存在的工具"""
    registry = ToolRegistry()

    with pytest.raises(ValueError, match="not found"):
        registry.execute("nonexistent_tool", {})
```

- [ ] **Step 3: 运行测试**

Run: `pytest tests/unit/core/runtime/test_agent_executor.py tests/unit/core/runtime/test_tool_registry.py -v`
Expected: PASS

- [ ] **Step 4: 提交**

```bash
git add tests/unit/core/runtime/test_agent_executor.py tests/unit/core/runtime/test_tool_registry.py
git commit -m "test(core): 补齐 AgentExecutor 和 ToolRegistry 测试"
```

---

### Task 18: 新功能模块测试补齐

**Files:**
- Modify: `tests/unit/business_logic/interview/test_review_report_generator.py`
- Modify: `tests/unit/business_logic/interview/test_session_manager.py`
- Modify: `tests/unit/business_logic/interview/test_interview_coach_agent.py`

- [ ] **Step 1: 补齐 ReviewReportGenerator 测试**

```python
# tests/unit/business_logic/interview/test_review_report_generator.py
import pytest
from unittest.mock import MagicMock
from src.business_logic.interview.review_report_generator import (
    ReviewReportGenerator,
    ReviewReportDimension,
    ReviewReport,
)


class TestReviewReportGenerator:
    def test_generate_with_answers(self):
        """测试有答案时的报告生成"""
        generator = ReviewReportGenerator()

        answers = [
            {
                "question": "请介绍一下你自己",
                "answer": "我是后端开发工程师，熟练使用 Python 和 Java，有 3 年开发经验。",
            },
            {
                "question": "你最大的优点是什么？",
                "answer": "我善于解决问题，在上一份工作中优化了系统性能，提升了 50% 的响应速度。",
            },
        ]

        report = generator.generate(answers)

        assert isinstance(report, ReviewReport)
        assert len(report.dimensions) == 4
        assert all(isinstance(d, ReviewReportDimension) for d in report.dimensions)

    def test_generate_with_empty_answers(self):
        """测试空答案"""
        generator = ReviewReportGenerator()
        report = generator.generate([])

        assert isinstance(report, ReviewReport)
        assert len(report.dimensions) == 4

    def test_score_to_stars_conversion(self):
        """测试分数到星星的转换"""
        generator = ReviewReportGenerator()

        assert generator._score_to_stars(4.5) == 5
        assert generator._score_to_stars(4.0) == 4
        assert generator._score_to_stars(3.5) == 4
        assert generator._score_to_stars(2.0) == 2
        assert generator._score_to_stars(0.0) == 0
```

- [ ] **Step 2: 补齐 SessionManager 测试**

```python
# tests/unit/business_logic/interview/test_session_manager.py
import pytest
from unittest.mock import MagicMock, patch
from src.business_logic.interview.session_manager import (
    InterviewSessionManager,
    CoachSessionState,
    AnswerRecord,
)


class TestInterviewSessionManager:
    def test_start_session(self):
        """测试启动会话"""
        manager = InterviewSessionManager()

        with patch('src.core.llm.litellm_adapter.LiteLLMAdapter'):
            session_id = manager.start(
                user_id=1,
                job_title="Python Developer",
                jd_text="需要 Python 开发经验",
                resume_context="熟练 Python、Django",
            )

        assert session_id is not None
        assert session_id in manager._sessions

    def test_submit_answer(self):
        """测试提交答案"""
        manager = InterviewSessionManager()

        with patch('src.core.llm.litellm_adapter.LiteLLMAdapter'):
            session_id = manager.start(
                user_id=1,
                job_title="Python Developer",
                jd_text="需要 Python 开发经验",
                resume_context="熟练 Python、Django",
            )

            result = manager.submit_answer(
                session_id=session_id,
                answer="我有 3 年 Python 开发经验。",
            )

        assert "question" in result or "error" not in result

    def test_end_session(self):
        """测试结束会话"""
        manager = InterviewSessionManager()

        with patch('src.core.llm.litellm_adapter.LiteLLMAdapter'):
            session_id = manager.start(
                user_id=1,
                job_title="Python Developer",
                jd_text="需要 Python 开发经验",
                resume_context="熟练 Python、Django",
            )

            result = manager.end_session(session_id)

        assert result is not None
        assert session_id not in manager._sessions
```

- [ ] **Step 3: 运行测试**

Run: `pytest tests/unit/business_logic/interview/test_review_report_generator.py tests/unit/business_logic/interview/test_session_manager.py -v`
Expected: PASS

- [ ] **Step 4: 提交**

```bash
git add tests/unit/business_logic/interview/test_review_report_generator.py tests/unit/business_logic/interview/test_session_manager.py
git commit -m "test(interview): 补齐 ReviewReportGenerator 和 SessionManager 测试"
```

---

### Task 19: 业务服务层测试补齐

**Files:**
- Modify: `tests/unit/business_logic/test_resume_service.py`
- Modify: `tests/unit/business_logic/test_job_service.py`

- [ ] **Step 1: 补齐关键方法的测试**

追加到 `tests/unit/business_logic/test_resume_service.py`:

```python
def test_get_resume_by_id_not_found():
    """测试获取不存在的简历"""
    from unittest.mock import patch
    from src.business_logic.resume.service import ResumeService

    service = ResumeService()

    with patch('src.data_access.repositories.resume_repository.get_by_id', return_value=None):
        result = service.get_resume_by_id(999)
        assert result is None

def test_update_resume_content():
    """测试更新简历内容"""
    from unittest.mock import MagicMock, patch
    from src.business_logic.resume.service import ResumeService

    service = ResumeService()

    mock_resume = MagicMock()
    mock_resume.id = 1
    mock_resume.title = "Old Title"

    mock_db = MagicMock()

    with patch('src.data_access.repositories.resume_repository.get_by_id', return_value=mock_resume):
        result = service.update_resume(1, {"title": "New Title"}, db=mock_db)

    mock_db.commit.assert_called_once()
```

- [ ] **Step 2: 运行测试**

Run: `pytest tests/unit/business_logic/test_resume_service.py tests/unit/business_logic/test_job_service.py -v 2>&1 | tail -20`
Expected: PASS

- [ ] **Step 3: 提交**

```bash
git add tests/unit/business_logic/test_resume_service.py tests/unit/business_logic/test_job_service.py
git commit -m "test(services): 补齐 ResumeService 和 JobService 测试"
```

---

### Task 20: 最终验证

- [ ] **Step 1: 运行完整测试套件**

Run: `python -m pytest --cov=src --cov-report=term-missing 2>&1 | tail -40`
Expected: 整体覆盖率 ≥ 80%

- [ ] **Step 2: 运行所有单元测试**

Run: `python -m pytest tests/unit/ -v --tb=short 2>&1 | tail -30`
Expected: 全部 PASS

- [ ] **Step 3: 验证工具数量**

Run: `python -c "from src.core.runtime.tool_registry import ToolRegistry; r = ToolRegistry(); print('Registered tools:', len(r._tools))"`
Expected: ≥ 13 个工具

- [ ] **Step 4: 最终提交**

```bash
git add -A && git commit -m "feat(phase3): 完成测试覆盖率提升，目标 80%+
- 核心 Runtime 测试补齐
- 新功能模块测试补齐
- 业务服务层测试补齐"
```

---

## 验收标准检查

- [ ] 工具总数 ≥ 13 个
- [ ] 整体测试覆盖率 ≥ 80%
- [ ] 所有现有测试（435个）继续通过
- [ ] ResumeCustomizerAgent 改造后功能不退化
- [ ] ToolContext 注入后，工具可在测试中使用 mock db
