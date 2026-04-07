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

    async def submit_answer(
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
        score_feedback = await self._score_answer(
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

    async def submit_followup_answers(
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
            score_feedback = await self._score_answer(
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
        from src.data_access.entities.interview import InterviewSession
        session = db.query(InterviewSession).filter_by(id=session_id).first()
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

    async def _score_answer(
        self, question: str, answer: str, jd_text: str
    ) -> dict:
        """调用 agent 评分。"""
        if self._agent:
            try:
                return await self._agent.evaluate_single_answer(
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