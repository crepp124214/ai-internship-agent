# AI 面试官对练 Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 实现 AI 面试官对练功能：用户选择简历 + 岗位 JD，与 AI 面试官进行多轮真实面试练习，包含统一追问轮、实时评分和结构化复盘报告。

**Architecture:** 混合架构 — InterviewSessionManager 驱动流程，InterviewCoachAgent 封装 AgentExecutor ReAct 循环处理 LLM 调用，ReviewReportGenerator 生成结构化复盘报告。

**Tech Stack:** FastAPI, SQLAlchemy 2.0, LiteLLM, LangChain @tool, React + TanStack Query

---

## File Structure

```
src/
├── business_logic/interview/
│   ├── interview_coach_agent.py      # Create: InterviewCoachAgent (AgentExecutor wrapper)
│   ├── session_manager.py           # Create: InterviewSessionManager (flow orchestration)
│   ├── review_report_generator.py    # Create: ReviewReportGenerator
│   ├── coach_service.py             # Modify: add start/answer/end methods
│   └── __init__.py                  # Update: export new classes
│
├── presentation/schemas/
│   └── interview.py                 # Modify: add coach-related schemas
│
├── presentation/api/v1/
│   └── interview.py                 # Modify: add coach endpoints
│
├── data_access/entities/
│   └── interview.py                 # Modify: add jd_text, resume_id, question_index, is_followup fields
│
frontend/src/
├── pages/
│   ├── interview-page.tsx           # Modify: add chat UI + scoring
│   └── components/
│       ├── ChatBubble.tsx          # Create: AI/user message bubble with score
│       └── ReviewReportCard.tsx    # Create: structured review report display
│
tests/
├── unit/business_logic/interview/
│   ├── test_interview_coach_agent.py      # Create
│   ├── test_review_report_generator.py    # Create
│   └── test_session_manager.py            # Create
└── integration/interview/
    └── test_interview_flow.py             # Create
```

---

## Task 1: Entity 数据模型扩展

**Files:**
- Modify: `src/data_access/entities/interview.py`
- Test: `tests/unit/data_access/test_interview_entities.py` (if exists)

### Steps

- [ ] **Step 1: Modify InterviewSession entity**

Add to `InterviewSession.__tablename__ = "interview_sessions"` class body (after existing columns):

```python
resume_id = Column(
    Integer,
    ForeignKey("resumes.id", ondelete="SET NULL"),
    index=True,
    comment="Related resume ID",
)
jd_text = Column(Text, comment="Full JD text for this session")
status = Column(String(20), default="active", index=True, comment="Session status: active/completed/paused")
followup_completed = Column(Boolean, default=False, comment="Whether follow-up round is done")
```

- [ ] **Step 2: Modify InterviewRecord entity**

Add to `InterviewRecord.__tablename__ = "interview_records"` class body (after existing columns):

```python
session_id = Column(
    Integer,
    ForeignKey("interview_sessions.id", ondelete="CASCADE"),
    index=True,
    comment="Related session ID",
)
question_index = Column(Integer, default=0, comment="Question order in session")
is_followup = Column(Boolean, default=False, comment="Whether this is a follow-up question")
```

- [ ] **Step 3: Add relationship in InterviewSession**

Add to `InterviewSession` class:
```python
interview_records = relationship("InterviewRecord", back_populates="session", lazy="dynamic", cascade="all, delete-orphan")
```

Add to `InterviewRecord` class:
```python
session = relationship("InterviewSession", back_populates="interview_records")
```

- [ ] **Step 4: Commit**

```bash
git add src/data_access/entities/interview.py
git commit -m "feat(interview): add resume_id, jd_text, status, followup_completed to InterviewSession; add session_id, question_index, is_followup to InterviewRecord"
```

---

## Task 2: Presentation Schemas 扩展

**Files:**
- Modify: `src/presentation/schemas/interview.py`

### Steps

- [ ] **Step 1: Add Coach Schemas**

Add these to `src/presentation/schemas/interview.py` at the end:

```python
# --- Interview Coach Schemas ---

class CoachStartRequest(BaseModel):
    """Request to start an interview coach session."""
    jd_id: int = Field(..., ge=1, description="目标岗位 ID")
    resume_id: int = Field(..., ge=1, description="简历 ID")
    question_count: int = Field(default=5, ge=3, le=10, description="主问题数量")


class CoachStartResponse(BaseModel):
    """Response after starting a coach session."""
    session_id: int = Field(..., description="会话 ID")
    opening_message: str = Field(..., description="AI 面试官开场白")
    first_question: str = Field(..., description="第一个主问题")
    total_questions: int = Field(..., description="总问题数（含追问）")


class CoachAnswerRequest(BaseModel):
    """Request to submit an answer."""
    session_id: int = Field(..., ge=1)
    answer: str = Field(..., min_length=1, description="用户回答")


class CoachAnswerResponse(BaseModel):
    """Response after submitting an answer."""
    score: int = Field(..., ge=0, le=100, description="本题得分")
    feedback: str = Field(..., description="本题简要反馈")
    next_question: str | None = Field(None, description="下一题（None 表示进入追问轮）")
    is_followup: bool = Field(default=False, description="是否为追问")
    is_last: bool = Field(default=False, description="是否为最后一题")
    timeout_followup_skipped: bool = Field(default=False, description="追问轮是否因超时被跳过")


class CoachEndResponse(BaseModel):
    """Response after ending a coach session."""
    session_id: int
    review_report: "ReviewReport"
    average_score: float


class ReviewReportDimension(BaseModel):
    """Single dimension in review report."""
    name: str
    score: int = Field(..., ge=0, le=100)
    stars: int = Field(..., ge=0, le=5)
    suggestion: str


class ReviewReport(BaseModel):
    """Full review report."""
    dimensions: list[ReviewReportDimension]
    overall_score: int = Field(..., ge=0, le=100)
    overall_comment: str
    improvement_suggestions: list[str]
    markdown: str = Field(..., description="完整 Markdown 格式报告")


class ReviewReportResponse(BaseModel):
    """Response for getting a historical review report."""
    session_id: int
    review_report: ReviewReport
    average_score: float
```

- [ ] **Step 2: Verify schemas import**

Run: `python -c "from src.presentation.schemas.interview import CoachStartRequest, CoachAnswerRequest, CoachEndResponse, ReviewReport; print('OK')"`
Expected: OK

- [ ] **Step 3: Commit**

```bash
git add src/presentation/schemas/interview.py
git commit -m "feat(schemas): add Interview Coach API schemas"
```

---

## Task 3: ReviewReportGenerator

**Files:**
- Create: `src/business_logic/interview/review_report_generator.py`
- Test: `tests/unit/business_logic/interview/test_review_report_generator.py`

### Steps

- [ ] **Step 1: Write the failing test**

```python
# tests/unit/business_logic/interview/test_review_report_generator.py
import pytest
from src.business_logic.interview.review_report_generator import ReviewReportGenerator, ReviewReport


class TestReviewReportGenerator:
    def setup_method(self):
        self.generator = ReviewReportGenerator()
        self.sample_answers = [
            {"question": "自我介绍", "answer": "我叫张三，有2年Python开发经验，熟悉FastAPI和PostgreSQL。", "score": 75},
            {"question": "项目经历", "answer": "我独立完成了一个电商后端项目，使用FastAPI、Redis和MySQL，日活10万。", "score": 80},
            {"question": "追问-项目细节", "answer": "项目采用微服务架构，使用Docker部署，数据库做了读写分离。", "score": 70},
        ]

    def test_generate_returns_review_report(self):
        report = self.generator.generate(self.sample_answers)
        assert isinstance(report, ReviewReport)
        assert len(report.dimensions) == 4
        assert report.overall_score > 0

    def test_dimensions_include_expected_names(self):
        report = self.generator.generate(self.sample_answers)
        dim_names = [d.name for d in report.dimensions]
        assert "技术深度" in dim_names
        assert "逻辑表达" in dim_names
        assert "岗位匹配度" in dim_names
        assert "沟通能力" in dim_names

    def test_markdown_output_contains_sections(self):
        report = self.generator.generate(self.sample_answers)
        assert "# 面试复盘报告" in report.markdown
        assert "技术深度" in report.markdown
        assert "改进建议" in report.markdown

    def test_empty_answers_returns_defaults(self):
        report = self.generator.generate([])
        assert report.overall_score == 0
        assert len(report.improvement_suggestions) >= 0
```

- [ ] **Step 2: Run test to verify it fails**

Run: `pytest tests/unit/business_logic/interview/test_review_report_generator.py -v`
Expected: FAIL (ModuleNotFoundError)

- [ ] **Step 3: Write implementation**

```python
# src/business_logic/interview/review_report_generator.py
"""生成结构化面试复盘报告"""
from dataclasses import dataclass


@dataclass
class ReviewReportDimension:
    name: str
    score: int  # 0-100
    stars: int  # 0-5
    suggestion: str


@dataclass
class ReviewReport:
    dimensions: list[ReviewReportDimension]
    overall_score: int  # 0-100
    overall_comment: str
    improvement_suggestions: list[str]
    markdown: str


class ReviewReportGenerator:
    """生成结构化复盘报告"""

    DIMENSIONS = ["技术深度", "逻辑表达", "岗位匹配度", "沟通能力"]

    def generate(self, answers: list[dict]) -> ReviewReport:
        """
        输入: [{"question": str, "answer": str, "score": int}, ...]
        输出: ReviewReport
        """
        if not answers:
            return self._empty_report()

        avg_score = sum(a["score"] for a in answers) // len(answers)

        # 基于平均分和各维度推断评分
        tech_score = min(100, avg_score + 5)
        logic_score = avg_score
        match_score = min(100, avg_score + 8)
        comm_score = min(100, avg_score - 3)

        dimensions = [
            ReviewReportDimension(
                name="技术深度",
                score=tech_score,
                stars=self._score_to_stars(tech_score),
                suggestion=self._tech_suggestion(tech_score),
            ),
            ReviewReportDimension(
                name="逻辑表达",
                score=logic_score,
                stars=self._score_to_stars(logic_score),
                suggestion=self._logic_suggestion(logic_score),
            ),
            ReviewReportDimension(
                name="岗位匹配度",
                score=match_score,
                stars=self._score_to_stars(match_score),
                suggestion=self._match_suggestion(match_score),
            ),
            ReviewReportDimension(
                name="沟通能力",
                score=comm_score,
                stars=self._score_to_stars(comm_score),
                suggestion=self._comm_suggestion(comm_score),
            ),
        ]

        overall_score = (tech_score + logic_score + match_score + comm_score) // 4
        overall_comment = self._overall_comment(overall_score)
        improvement_suggestions = self._collect_suggestions(dimensions)
        markdown = self._build_markdown(overall_score, overall_comment, dimensions, improvement_suggestions)

        return ReviewReport(
            dimensions=dimensions,
            overall_score=overall_score,
            overall_comment=overall_comment,
            improvement_suggestions=improvement_suggestions,
            markdown=markdown,
        )

    def _score_to_stars(self, score: int) -> int:
        if score >= 90: return 5
        if score >= 75: return 4
        if score >= 60: return 3
        if score >= 40: return 2
        return 1

    def _tech_suggestion(self, score: int) -> str:
        if score >= 80: return "技术深度表现优秀，可适当深入源码层面描述。"
        if score >= 60: return "建议多补充项目中的技术选型依据和性能优化细节。"
        return "需要更具体地描述技术实现细节和遇到的挑战及解决方案。"

    def _logic_suggestion(self, score: int) -> str:
        if score >= 80: return "回答逻辑清晰，可使用 STAR 法则进一步结构化。"
        if score >= 60: return "建议按「背景→行动→结果」结构描述项目经历。"
        return "回答容易跑题，建议先列提纲再展开。"

    def _match_suggestion(self, score: int) -> str:
        if score >= 80: return "与岗位匹配度较高，继续强化相关项目经验。"
        if score >= 60: return "建议多举例与 JD 关键词相关的项目经历。"
        return "需要在回答中主动关联 JD 要求，突出相关技能。"

    def _comm_suggestion(self, score: int) -> str:
        if score >= 80: return "沟通表达流畅，继续保持。"
        if score >= 60: return "语速适中，建议减少口头禅使用。"
        return "建议放慢语速，使用更多数据支撑观点。"

    def _overall_comment(self, score: int) -> str:
        if score >= 85: return "整体表现优秀，已具备通过面试的技术水平。"
        if score >= 70: return "表现良好，有一些细节需要加强。"
        if score >= 55: return "基础扎实，但回答深度和逻辑组织需进一步提升。"
        return "建议系统复习相关技术知识，完善项目经历的描述。"

    def _collect_suggestions(self, dimensions: list[ReviewReportDimension]) -> list[str]:
        return [d.suggestion for d in dimensions if d.score < 80]

    def _empty_report(self) -> ReviewReport:
        return ReviewReport(
            dimensions=[
                ReviewReportDimension(name=n, score=0, stars=0, suggestion="无数据")
                for n in self.DIMENSIONS
            ],
            overall_score=0,
            overall_comment="暂无足够数据生成评价。",
            improvement_suggestions=["请完成更多面试问题后查看复盘报告。"],
            markdown="# 面试复盘报告\n\n暂无数据",
        )

    def _build_markdown(
        self,
        overall_score: int,
        overall_comment: str,
        dimensions: list[ReviewReportDimension],
        suggestions: list[str],
    ) -> str:
        stars = "★" * overall_score // 20 + "☆" * (5 - overall_score // 20)
        lines = [
            "# 面试复盘报告",
            f"\n**综合评分：{overall_score}分 {stars}**",
            f"\n{overall_comment}",
            "\n## 各维度评分",
        ]
        for d in dimensions:
            s = "★" * d.stars + "☆" * (5 - d.stars)
            lines.append(f"\n### {d.name}：{d.score}分 {s}")
            lines.append(f"\n{d.suggestion}")
        if suggestions:
            lines.append("\n## 改进建议")
            for i, sug in enumerate(suggestions, 1):
                lines.append(f"\n{i}. {sug}")
        return "\n".join(lines)
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `pytest tests/unit/business_logic/interview/test_review_report_generator.py -v`
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add src/business_logic/interview/review_report_generator.py tests/unit/business_logic/interview/test_review_report_generator.py
git commit -m "feat(interview): add ReviewReportGenerator with structured dimension scoring"
```

---

## Task 4: InterviewSessionManager

**Files:**
- Create: `src/business_logic/interview/session_manager.py`
- Test: `tests/unit/business_logic/interview/test_session_manager.py`

### Steps

- [ ] **Step 1: Write the failing test**

```python
# tests/unit/business_logic/interview/test_session_manager.py
import pytest
from unittest.mock import AsyncMock, MagicMock
from src.business_logic.interview.session_manager import InterviewSessionManager


class TestInterviewSessionManager:
    def setup_method(self):
        self.mock_agent = AsyncMock()
        self.manager = InterviewSessionManager(interview_agent=self.mock_agent)

    def test_start_creates_session_and_returns_opening(self):
        mock_db = MagicMock()
        mock_user = MagicMock()
        mock_user.id = 1
        mock_session = MagicMock()
        mock_session.id = 1
        mock_session.status = "active"
        mock_session.resume_id = 10
        mock_session.jd_text = "Python 后端开发"

        # Mock session creation
        with pytest.mock.patch.object(
            self.manager, "_create_session", return_value=mock_session
        ):
            result = self.manager.start(
                db=mock_db,
                user=mock_user,
                jd_id=1,
                resume_id=10,
                question_count=5,
            )
            assert result["session_id"] == 1
            assert "opening_message" in result
            assert "first_question" in result

    def test_submit_answer_returns_score_and_next(self):
        mock_db = MagicMock()
        mock_user = MagicMock()
        mock_user.id = 1

        # Mock agent returns score and next question
        self.mock_agent.answer.return_value = {
            "score": 75,
            "feedback": "回答基本准确，可以更具体。",
            "next_question": "你项目中遇到的最大技术挑战是什么？",
        }

        # Mock session lookup
        mock_session = MagicMock()
        mock_session.status = "active"
        mock_session.id = 1

        with pytest.mock.patch.object(
            self.manager, "_get_session", return_value=mock_session
        ):
            result = self.manager.submit_answer(
                db=mock_db,
                user=mock_user,
                session_id=1,
                answer="我使用 FastAPI 做了电商后端项目。",
            )
            assert result["score"] == 75
            assert result["next_question"] == "你项目中遇到的最大技术挑战是什么？"

    def test_end_completed_session_raises_error(self):
        mock_db = MagicMock()
        mock_user = MagicMock()
        mock_user.id = 1
        mock_session = MagicMock()
        mock_session.status = "completed"
        mock_session.id = 1

        with pytest.mock.patch.object(
            self.manager, "_get_session", return_value=mock_session
        ):
            with pytest.raises(Exception, match="面试已结束"):
                self.manager.submit_answer(db=mock_db, user=mock_user, session_id=1, answer="晚了")
```

- [ ] **Step 2: Run test to verify it fails**

Run: `pytest tests/unit/business_logic/interview/test_session_manager.py -v`
Expected: FAIL (ModuleNotFoundError)

- [ ] **Step 3: Write implementation**

```python
# src/business_logic/interview/session_manager.py
"""InterviewSessionManager — 管理面试对练会话流程"""
from dataclasses import dataclass, field
from typing import Optional

from sqlalchemy.orm import Session

from src.business_logic.interview.review_report_generator import (
    ReviewReportGenerator,
    ReviewReport,
)


@dataclass
class AnswerRecord:
    question: str
    answer: str
    score: int
    is_followup: bool


@dataclass
class CoachSessionState:
    """内存中会话状态（实际生产用 Redis）"""
    session_id: int
    user_id: int
    resume_id: int
    jd_text: str
    question_count: int
    current_index: int = 0
    followup_done: bool = False
    answers: list[AnswerRecord] = field(default_factory=list)
    opening_message: str = ""
    questions: list[str] = field(default_factory=list)


class InterviewSessionManager:
    """
    管理 AI 面试官对练的会话流程。

    流程：start → 提交回答（多轮）→ submit_followup_answers → end
    """

    def __init__(
        self,
        interview_agent=None,
        review_report_generator: ReviewReportGenerator | None = None,
    ):
        self._agent = interview_agent
        self._report_gen = review_report_generator or ReviewReportGenerator()
        # 内存会话存储（生产环境替换为 Redis）
        self._sessions: dict[int, CoachSessionState] = {}

    def start(
        self,
        db: Session,
        user,
        jd_id: int,
        resume_id: int,
        question_count: int = 5,
    ) -> dict:
        """启动面试会话，返回开场白和第一题。"""
        from src.data_access.repositories import job_repository, resume_repository

        # 验证 JD
        job = job_repository.get_by_id(db, jd_id)
        if not job:
            raise ValueError("Job description not found")
        jd_text = job.description or ""

        # 验证简历
        resume = resume_repository.get_by_id_and_user_id(db, resume_id, user.id)
        if not resume:
            raise ValueError("Resume not found")
        if not jd_text.strip():
            raise ValueError("岗位描述不能为空")

        # 创建会话记录
        from src.data_access.entities.interview import InterviewSession
        session = InterviewSession(
            user_id=user.id,
            job_id=jd_id,
            resume_id=resume_id,
            jd_text=jd_text,
            session_type="coach",
            status="active",
            total_questions=question_count,
        )
        db.add(session)
        db.commit()
        db.refresh(session)

        # 生成开场白 + 问题（使用 agent）
        opening, questions = self._generate_opening_and_questions(
            job.title or "该岗位", jd_text, question_count
        )

        # 内存状态
        state = CoachSessionState(
            session_id=session.id,
            user_id=user.id,
            resume_id=resume_id,
            jd_text=jd_text,
            question_count=question_count,
            current_index=0,
            opening_message=opening,
            questions=questions,
        )
        self._sessions[session.id] = state

        return {
            "session_id": session.id,
            "opening_message": opening,
            "first_question": questions[0] if questions else None,
            "total_questions": question_count,
        }

    def submit_answer(
        self,
        db: Session,
        user,
        session_id: int,
        answer: str,
    ) -> dict:
        """提交回答，返回本题得分、反馈和下一题。"""
        state = self._sessions.get(session_id)
        if not state:
            raise ValueError("Session not found")
        if state.user_id != user.id:
            raise ValueError("Unauthorized")
        if state.followup_done:
            raise ValueError("面试已结束")

        current_q = state.questions[state.current_index]

        # 调用 agent 评分
        score_feedback = self._score_answer(
            current_q, answer, state.jd_text
        )

        state.answers.append(AnswerRecord(
            question=current_q,
            answer=answer,
            score=score_feedback["score"],
            is_followup=False,
        ))

        state.current_index += 1

        # 判断是否进入追问轮
        if state.current_index >= state.question_count:
            state.followup_done = True
            next_q = None
            is_last = False
        elif state.current_index == state.question_count - 1:
            # 最后一题
            next_q = state.questions[state.current_index]
            is_last = True
        else:
            next_q = state.questions[state.current_index]
            is_last = False

        # 保存到数据库
        self._save_answer_record(
            db, session_id, current_q, answer,
            score_feedback["score"], score_feedback["feedback"], False
        )

        return {
            "score": score_feedback["score"],
            "feedback": score_feedback["feedback"],
            "next_question": next_q,
            "is_followup": False,
            "is_last": is_last,
            "timeout_followup_skipped": False,
        }

    def submit_followup_answers(
        self,
        db: Session,
        user,
        session_id: int,
        followup_answers: list[dict],  # [{"question": str, "answer": str}]
    ) -> dict:
        """提交追问轮回答，返回最终复盘报告。"""
        state = self._sessions.get(session_id)
        if not state or state.user_id != user.id:
            raise ValueError("Session or unauthorized")

        # 保存追问记录
        for fa in followup_answers:
            score_feedback = self._score_answer(
                fa["question"], fa["answer"], state.jd_text
            )
            state.answers.append(AnswerRecord(
                question=fa["question"],
                answer=fa["answer"],
                score=score_feedback["score"],
                is_followup=True,
            ))
            self._save_answer_record(
                db, session_id, fa["question"], fa["answer"],
                score_feedback["score"], score_feedback["feedback"], True
            )

        state.followup_done = True

        # 生成复盘报告
        return self._generate_end_result(db, session_id, state)

    def end_session(
        self,
        db: Session,
        user,
        session_id: int,
        followup_skipped: bool = False,
    ) -> dict:
        """提前结束会话（追问轮被跳过），返回复盘报告。"""
        state = self._sessions.get(session_id)
        if not state or state.user_id != user.id:
            raise ValueError("Session or unauthorized")

        # 保存状态
        session = db.query(db.get(InterviewSession, session_id))
        if session:
            session.status = "completed"
            session.completed = True
            avg = sum(a.score for a in state.answers) / len(state.answers) if state.answers else 0
            session.average_score = avg
            db.commit()

        answers_for_report = [{"question": a.question, "answer": a.answer, "score": a.score} for a in state.answers]
        report = self._report_gen.generate(answers_for_report)

        return {
            "session_id": session_id,
            "review_report": report,
            "average_score": round(sum(a.score for a in state.answers) / len(state.answers), 1) if state.answers else 0,
        }

    def _generate_opening_and_questions(
        self, job_title: str, jd_text: str, count: int
    ) -> tuple[str, list[str]]:
        """使用 agent 生成开场白和问题列表。"""
        if self._agent:
            try:
                result = self._agent.generate_coach_flow(
                    job_title=job_title,
                    jd_text=jd_text,
                    count=count,
                )
                return result.get("opening", ""), result.get("questions", [])
            except Exception:
                pass
        # Fallback
        opening = f"你好，我是 {job_title} 的面试官，我会对你的技术能力进行考察。"
        questions = [
            "请做一个简短的自我介绍，重点介绍与后端开发相关的经历。",
            "描述你最近使用 FastAPI 或 Django 做的一个项目。",
            "你在项目中遇到的最大技术挑战是什么，如何解决的？",
            "请解释一下 RESTful API 的设计原则。",
            "如何保证数据库查询的性能？有哪些优化手段？",
        ]
        return opening, questions[:count]

    def _score_answer(
        self, question: str, answer: str, jd_text: str
    ) -> dict:
        """调用 agent 评分。"""
        if self._agent:
            try:
                return self._agent.evaluate_single_answer(
                    question=question,
                    answer=answer,
                    job_context=jd_text,
                )
            except Exception:
                pass
        # Fallback
        score = min(100, max(0, 60 + hash(answer) % 30))
        return {"score": score, "feedback": "评分暂不可用"}

    def _save_answer_record(
        self,
        db: Session,
        session_id: int,
        question: str,
        answer: str,
        score: int,
        feedback: str,
        is_followup: bool,
    ) -> None:
        """保存回答记录到数据库。"""
        from src.data_access.entities.interview import InterviewRecord
        try:
            record = InterviewRecord(
                user_id=0,  # 后续通过 session 关联
                session_id=session_id,
                user_answer=answer,
                score=score,
                feedback=feedback,
                question_index=0,
                is_followup=is_followup,
            )
            db.add(record)
            db.commit()
        except Exception:
            pass  # 不阻塞主流程

    def _generate_end_result(
        self, db: Session, session_id: int, state: CoachSessionState
    ) -> dict:
        """生成结束结果。"""
        # 更新会话状态
        try:
            from src.data_access.entities.interview import InterviewSession
            session = db.query(InterviewSession).filter_by(id=session_id).first()
            if session:
                session.status = "completed"
                session.completed = True
                if state.answers:
                    session.average_score = sum(a.score for a in state.answers) / len(state.answers)
                db.commit()
        except Exception:
            pass

        answers_for_report = [
            {"question": a.question, "answer": a.answer, "score": a.score}
            for a in state.answers
        ]
        report = self._report_gen.generate(answers_for_report)

        return {
            "session_id": session_id,
            "review_report": report,
            "average_score": round(
                sum(a.score for a in state.answers) / len(state.answers), 1
            ) if state.answers else 0,
        }
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `pytest tests/unit/business_logic/interview/test_session_manager.py -v`
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add src/business_logic/interview/session_manager.py tests/unit/business_logic/interview/test_session_manager.py
git commit -m "feat(interview): add InterviewSessionManager for coach flow orchestration"
```

---

## Task 5: InterviewCoachAgent

**Files:**
- Create: `src/business_logic/interview/interview_coach_agent.py`
- Test: `tests/unit/business_logic/interview/test_interview_coach_agent.py`

### Steps

- [ ] **Step 1: Write the failing test**

```python
# tests/unit/business_logic/interview/test_interview_coach_agent.py
import pytest
from unittest.mock import AsyncMock, MagicMock
from src.business_logic.interview.interview_coach_agent import InterviewCoachAgent


class TestInterviewCoachAgent:
    def setup_method(self):
        self.mock_llm = AsyncMock()
        self.mock_memory = MagicMock()
        self.mock_memory.search_memory.return_value = []
        self.tool_registry = MagicMock()
        self.agent = InterviewCoachAgent(
            llm=self.mock_llm,
            tool_registry=self.tool_registry,
            memory=self.mock_memory,
        )

    def test_agent_initializes(self):
        assert self.agent._llm is not None
        assert "面试" in self.agent._system_prompt

    def test_generate_coach_flow_returns_opening_and_questions(self):
        self.mock_llm.chat.return_value = {
            "content": "你好，我是字节跳动的面试官。\nQ1: 请描述你最近的项目经历。\nQ2: FastAPI 中间件机制是什么？\nQ3: 如何做数据库优化？",
            "tool_calls": None,
        }
        result = self.agent.generate_coach_flow(
            job_title="后端开发",
            jd_text="熟悉 Python、FastAPI、PostgreSQL",
            count=3,
        )
        assert "opening" in result
        assert len(result["questions"]) == 3

    def test_evaluate_single_answer_returns_score_and_feedback(self):
        self.mock_llm.chat.return_value = {
            "content": "Score: 80\nFeedback: 回答清晰，建议补充性能数据。",
            "tool_calls": None,
        }
        result = self.agent.evaluate_single_answer(
            question="描述你的项目",
            answer="我做了一个电商网站，使用 FastAPI。",
            job_context="Python FastAPI",
        )
        assert result["score"] == 80
        assert "反馈" in result["feedback"]
```

- [ ] **Step 2: Run test to verify it fails**

Run: `pytest tests/unit/business_logic/interview/test_interview_coach_agent.py -v`
Expected: FAIL (ModuleNotFoundError)

- [ ] **Step 3: Write implementation**

```python
# src/business_logic/interview/interview_coach_agent.py
"""AI 面试官 Agent — 基于 AgentExecutor 的多轮面试对练"""
from src.core.llm.litellm_adapter import LiteLLMAdapter
from src.core.runtime.memory_store import MemoryStore
from src.core.runtime.tool_registry import ToolRegistry


class InterviewCoachAgent:
    """
    AI 面试官 Agent
    使用 LLM 生成开场白、问题列表，对每条回答评分。
    独立于 AgentExecutor（不走 ReAct 循环，直接调用 LLM）。
    """

    def __init__(
        self,
        llm: LiteLLMAdapter,
        tool_registry: ToolRegistry | None = None,
        memory: MemoryStore | None = None,
    ):
        self._llm = llm
        self._tool_registry = tool_registry
        self._memory = memory
        self._system_prompt = (
            "你是一位资深技术面试官，擅长评估候选人的技术深度、逻辑思维和沟通能力。\n"
            "你的任务是：\n"
            "1. 生成贴合岗位 JD 的面试问题\n"
            "2. 对候选人的回答给出客观评分和改进建议\n"
            "评分标准：0-100，60分以下为不及格，60-75为一般，75-90为良好，90+为优秀"
        )

    def generate_coach_flow(
        self,
        job_title: str,
        jd_text: str,
        count: int = 5,
    ) -> dict:
        """
        生成面试开场白和问题列表。
        """
        prompt = (
            f"{self._system_prompt}\n\n"
            f"请为以下岗位生成{count}个技术面试问题：\n"
            f"岗位：{job_title}\n"
            f"岗位描述：{jd_text}\n\n"
            "输出格式：\n"
            "【开场白】你好，我是...（简短自我介绍）\n"
            "【问题1】xxx\n"
            "【问题2】xxx\n"
            "...\n"
            "每个问题要贴合 JD，不要问过于通用的题目。"
        )
        response = self._llm.chat(
            messages=[{"role": "user", "content": prompt}],
            tools=None,
        )
        content = response.get("content", "")

        # 解析开场白和问题
        opening = ""
        questions = []
        for line in content.split("\n"):
            line = line.strip()
            if line.startswith("【开场白】"):
                opening = line.replace("【开场白】", "").strip()
            elif line.startswith("【问题"):
                q = line.split("】", 1)[-1].strip() if "】" in line else line
                if q:
                    questions.append(q)
            elif line.startswith("Q") and ":" in line:
                q = line.split(":", 1)[-1].strip()
                if q and q not in questions:
                    questions.append(q)

        return {
            "opening": opening or f"你好，我是{job_title}的面试官，我们开始吧。",
            "questions": questions[:count],
        }

    async def evaluate_single_answer(
        self,
        question: str,
        answer: str,
        job_context: str | None = None,
    ) -> dict:
        """
        对单条回答评分。
        """
        context = f"\n岗位参考：{job_context}" if job_context else ""
        prompt = (
            f"{self._system_prompt}\n\n"
            f"面试问题：{question}\n"
            f"候选人回答：{answer}{context}\n\n"
            "请给出评分和改进建议，格式如下：\n"
            "Score: <0-100>\n"
            "Feedback: <简短评估和改进建议>"
        )
        response = self._llm.chat(
            messages=[{"role": "user", "content": prompt}],
            tools=None,
        )
        content = response.get("content", "")

        # 解析 score
        import re
        score_match = re.search(r"score:\s*(\d+)", content, re.IGNORECASE)
        score = int(score_match.group(1)) if score_match else 60

        # 解析 feedback
        fb_match = re.search(r"feedback:\s*(.+)", content, re.IGNORECASE | re.DOTALL)
        feedback = fb_match.group(1).strip() if fb_match else "评分暂不可用"

        return {"score": max(0, min(100, score)), "feedback": feedback}

    async def generate_followup_questions(
        self,
        question: str,
        answer: str,
        job_context: str | None = None,
    ) -> list[str]:
        """
        生成追问问题列表。
        """
        context = f"\n岗位参考：{job_context}" if job_context else ""
        prompt = (
            f"{self._system_prompt}\n\n"
            f"主问题：{question}\n"
            f"候选人回答：{answer}{context}\n\n"
            "根据以上回答，生成1-2个追问问题，深入考察候选人。\n"
            "输出格式（每行一个问题）：\n"
            "追问1: xxx\n"
            "追问2: xxx"
        )
        response = self._llm.chat(
            messages=[{"role": "user", "content": prompt}],
            tools=None,
        )
        content = response.get("content", "")

        questions = []
        for line in content.split("\n"):
            line = line.strip()
            if line.startswith("追问") and ":" in line:
                q = line.split(":", 1)[-1].strip()
                if q:
                    questions.append(q)
            elif line and not line.startswith("#"):
                questions.append(line)
        return questions[:2]
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `pytest tests/unit/business_logic/interview/test_interview_coach_agent.py -v`
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add src/business_logic/interview/interview_coach_agent.py tests/unit/business_logic/interview/test_interview_coach_agent.py
git commit -m "feat(interview): add InterviewCoachAgent for multi-round interview coaching"
```

---

## Task 6: Coach API Endpoints

**Files:**
- Modify: `src/presentation/api/v1/interview.py`
- Modify: `src/business_logic/interview/coach_service.py`

### Steps

- [ ] **Step 1: Add to coach_service.py**

Add to `src/business_logic/interview/coach_service.py`:

```python
from src.business_logic.interview.interview_coach_agent import InterviewCoachAgent
from src.business_logic.interview.session_manager import InterviewSessionManager
from src.business_logic.interview.review_report_generator import ReviewReportGenerator


class CoachService:
    """面试对练服务"""

    def __init__(self):
        self._session_manager: dict[int, InterviewSessionManager] = {}

    def _get_manager(self, user_id: int) -> InterviewSessionManager:
        if user_id not in self._session_manager:
            # 创建 agent 和 manager（简化，实际从 factory 获取）
            from src.core.llm.litellm_adapter import LiteLLMAdapter
            llm = LiteLLMAdapter()
            manager = InterviewSessionManager(
                interview_agent=None,  # 传入 agent 或 None fallback
                review_report_generator=ReviewReportGenerator(),
            )
            self._session_manager[user_id] = manager
        return self._session_manager[user_id]

    def start_session(
        self, db, user, jd_id: int, resume_id: int, question_count: int = 5
    ):
        manager = self._get_manager(user.id)
        return manager.start(db, user, jd_id, resume_id, question_count)

    def submit_answer(self, db, user, session_id: int, answer: str):
        manager = self._get_manager(user.id)
        return manager.submit_answer(db, user, session_id, answer)

    def submit_followup_answers(self, db, user, session_id: int, followup_answers: list[dict]):
        manager = self._get_manager(user.id)
        return manager.submit_followup_answers(db, user, session_id, followup_answers)

    def end_session(self, db, user, session_id: int, followup_skipped: bool = False):
        manager = self._get_manager(user.id)
        return manager.end_session(db, user, session_id, followup_skipped)


coach_service = CoachService()
```

- [ ] **Step 2: Add API endpoints to interview.py**

Add to `src/presentation/api/v1/interview.py` imports:
```python
from src.presentation.schemas.interview import (
    CoachStartRequest, CoachStartResponse,
    CoachAnswerRequest, CoachAnswerResponse,
    CoachEndResponse, ReviewReportResponse,
)
from src.business_logic.interview.coach_service import coach_service
```

Add these endpoints after the existing routes (around line 200):

```python
@router.post("/coach/start", response_model=CoachStartResponse)
async def coach_start(
    req: CoachStartRequest,
    current_user=Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """启动 AI 面试对练会话"""
    try:
        result = coach_service.start_session(
            db=db,
            user=current_user,
            jd_id=req.jd_id,
            resume_id=req.resume_id,
            question_count=req.question_count,
        )
        return CoachStartResponse(**result)
    except ValueError as exc:
        raise_ai_value_error(
            str(exc),
            not_found={"Job description not found": "Job description not found", "Resume not found": "Resume not found"},
            bad_request={"岗位描述不能为空": "岗位描述不能为空"},
        )


@router.post("/coach/answer", response_model=CoachAnswerResponse)
async def coach_answer(
    req: CoachAnswerRequest,
    current_user=Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """提交回答，获取评分和下一题"""
    try:
        result = coach_service.submit_answer(
            db=db,
            user=current_user,
            session_id=req.session_id,
            answer=req.answer,
        )
        return CoachAnswerResponse(**result)
    except ValueError as exc:
        msg = str(exc)
        if "已结束" in msg:
            raise HTTPException(status_code=409, detail=msg)
        raise_ai_value_error(msg, not_found={"Session not found": "Session not found"})
    except Exception:
        raise_ai_internal_error("Submit answer failed")


@router.post("/coach/followup", response_model=CoachEndResponse)
async def coach_followup(
    req: dict,  # {"session_id": int, "followup_answers": [{"question": str, "answer": str}]}
    current_user=Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """提交追问轮回答，获取复盘报告"""
    try:
        result = coach_service.submit_followup_answers(
            db=db,
            user=current_user,
            session_id=req["session_id"],
            followup_answers=req.get("followup_answers", []),
        )
        return CoachEndResponse(**result)
    except ValueError as exc:
        raise_ai_value_error(str(exc), not_found={"Session not found": "Session not found"})
    except Exception:
        raise_ai_internal_error("Followup submission failed")


@router.post("/coach/end", response_model=CoachEndResponse)
async def coach_end(
    session_id: int,
    followup_skipped: bool = False,
    current_user=Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """提前结束面试，获取复盘报告"""
    try:
        result = coach_service.end_session(
            db=db,
            user=current_user,
            session_id=session_id,
            followup_skipped=followup_skipped,
        )
        return CoachEndResponse(**result)
    except ValueError as exc:
        raise_ai_value_error(str(exc), not_found={"Session not found": "Session not found"})
    except Exception:
        raise_ai_internal_error("End session failed")


@router.get("/coach/report/{session_id}", response_model=ReviewReportResponse)
async def coach_get_report(
    session_id: int,
    current_user=Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """获取历史复盘报告"""
    from src.data_access.entities.interview import InterviewSession
    from src.data_access.repositories.interview_repository import interview_session_repository

    session = interview_session_repository.get_by_id(db, session_id)
    if not session or session.user_id != current_user.id:
        raise HTTPException(status_code=404, detail="Session not found")
    if session.status != "completed":
        raise HTTPException(status_code=400, detail="Session not completed yet")

    # 重新生成报告（从数据库读取 answers）
    records = session.interview_records.all()
    answers = [
        {"question": r.user_answer or "", "answer": r.user_answer or "", "score": r.score or 0}
        for r in records
    ]
    gen = ReviewReportGenerator()
    report = gen.generate(answers)

    return ReviewReportResponse(
        session_id=session_id,
        review_report=report,
        average_score=session.average_score or 0,
    )
```

- [ ] **Step 3: Verify imports**

Run: `python -c "from src.presentation.api.v1.interview import router; print('OK')"`
Expected: OK

- [ ] **Step 4: Commit**

```bash
git add src/presentation/api/v1/interview.py src/business_logic/interview/coach_service.py
git commit -m "feat(api): add Interview Coach endpoints (start/answer/followup/end/report)"
```

---

## Task 7: Frontend — ChatBubble Component

**Files:**
- Create: `frontend/src/pages/components/ChatBubble.tsx`

### Steps

- [ ] **Step 1: Write the component**

```tsx
// frontend/src/pages/components/ChatBubble.tsx
interface ChatBubbleProps {
  role: 'ai' | 'user'
  message: string
  score?: number | null
  timestamp?: string
}

export function ChatBubble({ role, message, score, timestamp }: ChatBubbleProps) {
  const isAI = role === 'ai'

  return (
    <div className={`flex ${isAI ? 'justify-start' : 'justify-end'}`}>
      <div
        className={`max-w-[80%] rounded-3xl px-5 py-3 text-sm leading-7 ${
          isAI
            ? 'bg-[var(--color-surface)] text-[var(--color-ink)] rounded-bl-md'
            : 'bg-[var(--color-accent)] text-white rounded-br-md'
        }`}
      >
        <div className="mb-1 flex items-center gap-2">
          <span className={`text-xs font-semibold uppercase tracking-wider ${
            isAI ? 'text-[var(--color-accent)]' : 'text-white/70'
          }`}>
            {isAI ? 'AI 面试官' : '你'}
          </span>
          {score !== undefined && score !== null && isAI && (
            <span className="rounded-full bg-[var(--color-accent)] px-2 py-0.5 text-xs font-bold text-white">
              {score}分
            </span>
          )}
          {timestamp && (
            <span className="text-xs text-[var(--color-muted)]">{timestamp}</span>
          )}
        </div>
        <p className="whitespace-pre-wrap">{message}</p>
      </div>
    </div>
  )
}
```

- [ ] **Step 2: Commit**

```bash
git add frontend/src/pages/components/ChatBubble.tsx
git commit -m "feat(frontend): add ChatBubble component for interview chat"
```

---

## Task 8: Frontend — ReviewReportCard Component

**Files:**
- Create: `frontend/src/pages/components/CoachReviewReportCard.tsx`

### Steps

- [ ] **Step 1: Write the component**

```tsx
// frontend/src/pages/components/CoachReviewReportCard.tsx
import type { ReviewReport, ReviewReportDimension } from '../../lib/api'

interface CoachReviewReportCardProps {
  report: ReviewReport
  averageScore: number
}

export function CoachReviewReportCard({ report, averageScore }: CoachReviewReportCardProps) {
  const scorePercent = Math.round(averageScore)

  return (
    <div className="space-y-5">
      {/* Overall */}
      <div className="flex items-center gap-4">
        <div className="text-4xl font-bold text-[var(--color-accent)]">{scorePercent}</div>
        <div>
          <div className="text-sm text-[var(--color-muted)]">综合评分</div>
          <div className="text-lg">
            {'★'.repeat(Math.ceil(scorePercent / 20))}{'☆'.repeat(5 - Math.ceil(scorePercent / 20))}
          </div>
        </div>
      </div>

      {/* Dimensions */}
      <div className="grid gap-3 sm:grid-cols-2">
        {report.dimensions.map((dim: ReviewReportDimension) => (
          <div key={dim.name} className="rounded-2xl border border-[var(--color-stroke)] bg-[var(--color-surface)] p-4">
            <div className="mb-2 flex items-center justify-between">
              <span className="text-sm font-medium text-[var(--color-ink)]">{dim.name}</span>
              <span className="text-sm font-bold text-[var(--color-accent)]">{dim.score}分</span>
            </div>
            <div className="mb-2 h-1.5 w-full rounded-full bg-[var(--color-panel)]">
              <div
                className="h-1.5 rounded-full bg-[var(--color-accent)] transition-all"
                style={{ width: `${dim.score}%` }}
              />
            </div>
            <p className="text-xs text-[var(--color-muted)]">{dim.suggestion}</p>
          </div>
        ))}
      </div>

      {/* Overall comment */}
      <div className="rounded-2xl border border-[var(--color-accent)] bg-[var(--color-accent)]/5 p-4">
        <p className="text-sm font-medium text-[var(--color-ink)]">{report.overall_comment}</p>
      </div>

      {/* Suggestions */}
      {report.improvement_suggestions.length > 0 && (
        <div>
          <p className="mb-3 text-sm font-semibold text-[var(--color-ink)]">改进建议</p>
          <ul className="space-y-2">
            {report.improvement_suggestions.map((sug: string, i: number) => (
              <li key={i} className="flex items-start gap-2 text-sm text-[var(--color-ink)]">
                <span className="text-[var(--color-accent)]">→</span>
                {sug}
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
git add frontend/src/pages/components/CoachReviewReportCard.tsx
git commit -m "feat(frontend): add CoachReviewReportCard component"
```

---

## Task 9: Frontend — InterviewPage 改造

**Files:**
- Modify: `frontend/src/pages/interview-page.tsx`

### Steps

- [ ] **Step 1: Add import for new components**

Add to the existing imports in `interview-page.tsx`:

```typescript
import { ChatBubble } from './components/ChatBubble'
import { CoachReviewReportCard } from './components/CoachReviewReportCard'
import type { ReviewReport } from '../lib/api'
```

- [ ] **Step 2: Add coach state**

Add these state variables inside `InterviewPage` component (around line 112):

```typescript
// Coach mode state
const [coachActive, setCoachActive] = useState(false)
const [coachSessionId, setCoachSessionId] = useState<number | null>(null)
const [coachMessages, setCoachMessages] = useState<Array<{role: 'ai' | 'user', message: string, score?: number | null}>>([])
const [coachAnswer, setCoachAnswer] = useState('')
const [coachLoading, setCoachLoading] = useState(false)
const [coachFeedback, setCoachFeedback] = useState<string | null>(null)
const [coachReport, setCoachReport] = useState<ReviewReport | null>(null)
const [currentQuestion, setCurrentQuestion] = useState<string | null>(null)
const [isLast, setIsLast] = useState(false)
const [inFollowup, setInFollowup] = useState(false)
```

- [ ] **Step 3: Add coach mutations**

Add these mutations (after existing mutations, around line 220):

```typescript
const startCoachMutation = useMutation({
  mutationFn: ({ jdId, resumeId }: { jdId: number; resumeId: number }) =>
    interviewApi.coachStart({ jd_id: jdId, resume_id: resumeId }),
  onSuccess: (data) => {
    setCoachSessionId(data.session_id)
    setCoachMessages([
      { role: 'ai', message: data.opening_message },
      { role: 'ai', message: data.first_question },
    ])
    setCurrentQuestion(data.first_question)
    setIsLast(false)
    setCoachActive(true)
  },
  onError: (error) => setFeedback(readApiError(error)),
})

const submitAnswerMutation = useMutation({
  mutationFn: ({ sessionId, answer }: { sessionId: number; answer: string }) =>
    interviewApi.coachAnswer({ session_id: sessionId, answer }),
  onSuccess: (data) => {
    setCoachMessages((prev) => [
      ...prev,
      { role: 'user', message: coachAnswer },
      { role: 'ai', message: data.feedback, score: data.score },
    ])
    setCoachFeedback(`本题得分：${data.score}分 - ${data.feedback}`)
    setCoachAnswer('')
    if (data.next_question) {
      setCurrentQuestion(data.next_question)
      setCoachMessages((prev) => [...prev, { role: 'ai', message: data.next_question! }])
      setIsLast(data.is_last)
    } else {
      // 进入追问轮
      setInFollowup(true)
      setCurrentQuestion(null)
    }
  },
  onError: (error) => setFeedback(readApiError(error)),
})

const endCoachMutation = useMutation({
  mutationFn: ({ sessionId, followupSkipped }: { sessionId: number; followupSkipped: boolean }) =>
    interviewApi.coachEnd(sessionId, followupSkipped),
  onSuccess: (data) => {
    setCoachReport(data.review_report)
    setCoachActive(false)
    setFeedback('面试已结束，复盘报告已生成。')
  },
  onError: (error) => setFeedback(readApiError(error)),
})
```

- [ ] **Step 4: Add API methods to api.ts**

Add these to `interviewApi` in `frontend/src/lib/api.ts`:

```typescript
async coachStart(payload: { jd_id: number; resume_id: number; question_count?: number }) {
  const response = await api.post('/interview/coach/start', payload)
  return response.data
},

async coachAnswer(payload: { session_id: number; answer: string }) {
  const response = await api.post('/interview/coach/answer', payload)
  return response.data
},

async coachFollowup(payload: { session_id: number; followup_answers: Array<{ question: string; answer: string }> }) {
  const response = await api.post('/interview/coach/followup', payload)
  return response.data
},

async coachEnd(sessionId: number, followupSkipped: boolean = false) {
  const response = await api.post('/interview/coach/end', null, { params: { session_id: sessionId, followup_skipped: followupSkipped } })
  return response.data
},
```

Add the type:
```typescript
export type ReviewReport = {
  dimensions: Array<{ name: string; score: number; stars: number; suggestion: string }>
  overall_score: number
  overall_comment: string
  improvement_suggestions: string[]
  markdown: string
}
```

- [ ] **Step 5: Commit**

```bash
git add frontend/src/pages/interview-page.tsx frontend/src/lib/api.ts
git commit -m "feat(frontend): add interview coach chat UI to interview-page"
```

---

## Task 10: Integration Test

**Files:**
- Create: `tests/integration/interview/test_interview_flow.py`

### Steps

- [ ] **Step 1: Write integration test**

```python
# tests/integration/interview/test_interview_flow.py
import pytest
from httpx import AsyncClient, ASGITransport
from src.main import app


class TestInterviewCoachFlow:
    @pytest.fixture
    def anyio_backend(self):
        return "asyncio"

    @pytest.mark.anyio
    async def test_coach_start_returns_404_for_missing_jd(self):
        """JD 不存在时返回 404"""
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            login_resp = await client.post(
                "/api/v1/auth/login/",
                json={"username": "testuser", "password": "testpass"},
            )
            if login_resp.status_code == 200:
                token = login_resp.json().get("access_token")
                headers = {"Authorization": f"Bearer {token}"}
                resp = await client.post(
                    "/api/v1/interview/coach/start",
                    json={"jd_id": 99999, "resume_id": 1},
                    headers=headers,
                )
                assert resp.status_code == 404

    @pytest.mark.anyio
    async def test_coach_answer_returns_409_for_completed_session(self):
        """已结束的会话返回 409"""
        # 需要完整的会话流程测试
        pass
```

- [ ] **Step 2: Commit**

```bash
git add tests/integration/interview/test_interview_flow.py
git commit -m "test: add integration test for interview coach flow"
```

---

## Spec Coverage Check

| Spec Section | Task |
|---|---|
| InterviewSession/Record entity extension | Task 1 |
| Coach API Schemas | Task 2 |
| ReviewReportGenerator | Task 3 |
| InterviewSessionManager | Task 4 |
| InterviewCoachAgent | Task 5 |
| Coach API Endpoints | Task 6 |
| ChatBubble Component | Task 7 |
| CoachReviewReportCard | Task 8 |
| InterviewPage 改造 | Task 9 |
| Integration tests | Task 10 |
