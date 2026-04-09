#!/usr/bin/env python3
"""Seed a minimal local demo dataset for the portfolio product flow."""

from __future__ import annotations

import asyncio
import os
import sys
from pathlib import Path
from types import SimpleNamespace

from dotenv import load_dotenv


REPO_ROOT = Path(__file__).resolve().parents[1]
ENV_FILE = REPO_ROOT / ".env"
ENV_EXAMPLE = REPO_ROOT / ".env.example"

if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

if ENV_FILE.exists():
    load_dotenv(ENV_FILE)
elif ENV_EXAMPLE.exists():
    load_dotenv(ENV_EXAMPLE)

os.environ.setdefault("DATABASE_URL", "sqlite:///./data/app.db")
os.environ.setdefault("LLM_PROVIDER", "mock")
os.environ.setdefault("SECRET_KEY", "portfolio-demo-secret")
os.environ.setdefault("APP_DEBUG", "False")

from src.business_logic.interview import interview_service
from src.business_logic.job import job_service
from src.business_logic.resume import resume_service
from src.business_logic.user import user_service
from src.data_access.database import SessionLocal
from src.data_access.entities.interview import InterviewQuestion, InterviewRecord, InterviewSession
from src.data_access.entities.job import Job, JobMatchResult
from src.data_access.entities.resume import Resume, ResumeOptimization
from src.data_access.entities.user import User
from src.presentation.schemas.interview import InterviewQuestionCreate, InterviewRecordCreate, InterviewSessionCreate
from src.presentation.schemas.job import JobCreate
from src.presentation.schemas.resume import ResumeCreate, ResumeUpdate
from src.presentation.schemas.user import UserCreate


def seed_example_data(db: Session):
    """创建示例简历和 JD 数据"""
    from src.data_access.repositories.resume_repository import resume_repository
    from src.data_access.repositories.job_repository import job_repository

    # 示例简历
    resumes = [
        {
            "title": "张三 - Python 开发工程师",
            "original_file_path": "demo/zhangsan_resume.txt",
            "resume_text": """姓名：张三
学历：本科 - 计算机科学 - 清华大学 2016-2020

技能：
- Python、Django、FastAPI
- PostgreSQL、Redis、MongoDB
- Docker、Kubernetes
- AWS 云服务
- Git、JIRA

经历：
百度 - 后端开发工程师 2020-至今
- 负责搜索服务开发，使用 Python + FastAPI
- 优化查询性能，提升 50% 响应速度
- 设计并实现微服务架构""",
            "processed_content": """姓名：张三
学历：本科 - 计算机科学 - 清华大学 2016-2020

技能：Python, Django, FastAPI, PostgreSQL, Redis, MongoDB, Docker, Kubernetes, AWS

经历：百度 - 后端开发工程师 2020-至今
- 负责搜索服务开发，使用 Python + FastAPI
- 优化查询性能，提升 50% 响应速度
- 设计并实现微服务架构""",
        },
        {
            "title": "李四 - 数据分析师",
            "original_file_path": "demo/lisi_resume.txt",
            "resume_text": """姓名：李四
学历：硕士 - 数据科学 - 上海交通大学 2018-2021

技能：
- Python、R、SQL
- Pandas、NumPy、Matplotlib
- TensorFlow、PyTorch
- Tableau、PowerBI
- Spark、Hadoop

经历：字节跳动 - 数据分析师 2021-至今
- 分析用户行为数据，提供业务洞察
- 建立数据管道，处理 TB 级数据
- 使用机器学习预测用户留存""",
            "processed_content": """姓名：李四
学历：硕士 - 数据科学 - 上海交通大学 2018-2021

技能：Python, R, SQL, Pandas, NumPy, TensorFlow, PyTorch, Spark, Hadoop

经历：字节跳动 - 数据分析师 2021-至今
- 分析用户行为数据，提供业务洞察
- 建立数据管道，处理 TB 级数据""",
        },
    ]

    # 示例 JD
    jobs = [
        {
            "title": "Python 后端开发工程师",
            "company": "字节跳动",
            "description": "负责抖音后端服务开发，使用 Python + Go 语言",
            "requirements": "3年以上 Python 开发经验，熟悉 Django 或 FastAPI",
            "location": "北京",
            "salary": "30-50K",
            "source": "demo",
        },
        {
            "title": "AI 算法工程师",
            "company": "商汤科技",
            "description": "负责计算机视觉算法研发，推动 AI 技术落地",
            "requirements": "硕士及以上，熟悉 PyTorch/TensorFlow，有顶会论文优先",
            "location": "上海",
            "salary": "40-60K",
            "source": "demo",
        },
        {
            "title": "前端开发工程师",
            "company": "腾讯",
            "description": "负责微信小程序和 Web 端开发",
            "requirements": "3年以上前端经验，熟悉 React 或 Vue",
            "location": "深圳",
            "salary": "25-45K",
            "source": "demo",
        },
        {
            "title": "数据分析师",
            "company": "美团",
            "description": "挖掘用户数据，提供商业洞察",
            "requirements": "熟练使用 SQL 和 Python，有数据分析经验",
            "location": "北京",
            "salary": "20-35K",
            "source": "demo",
        },
        {
            "title": "DevOps 工程师",
            "company": "阿里云",
            "description": "负责云原生基础设施建设",
            "requirements": "熟悉 Docker、Kubernetes，有大规模运维经验",
            "location": "杭州",
            "salary": "35-55K",
            "source": "demo",
        },
    ]

    # 检查是否已有数据
    existing_resumes = resume_repository.get_all(db)
    if len(existing_resumes) >= 2:
        print(f"简历数据已存在 ({len(existing_resumes)} 条)，跳过示例简历创建")
    else:
        for resume_data in resumes:
            try:
                resume_repository.create(db, {**resume_data, "user_id": 1})
                print(f"  Created resume: {resume_data['title']}")
            except Exception as e:
                print(f"  Failed to create resume {resume_data['title']}: {e}")

    existing_jobs = job_repository.get_all(db)
    if len(existing_jobs) >= 5:
        print(f"JD 数据已存在 ({len(existing_jobs)} 条)，跳过示例 JD 创建")
    else:
        for job_data in jobs:
            try:
                job_repository.create(db, job_data)
                print(f"  Created job: {job_data['title']}")
            except Exception as e:
                print(f"  Failed to create job {job_data['title']}: {e}")

    return len(resumes), len(jobs)


DEMO_USERNAME = "demo"
DEMO_PASSWORD = "demo123"
DEMO_EMAIL = "demo@example.com"
DEMO_NAME = "Portfolio Demo User"

DEMO_RESUME_TITLE = "2026 Internship Master Resume"
DEMO_RESUME_TEXT = """Portfolio Demo User
Backend engineer intern focused on FastAPI, React, SQLAlchemy, and AI workflow tooling.
Built an internship application platform with resume optimization, job matching,
and interview prep flows. Comfortable with Python, TypeScript,
REST APIs, async services, and product-oriented delivery.
"""

DEMO_JOB_TITLE = "Backend Engineer Intern"
DEMO_JOB_COMPANY = "Aster Labs"
DEMO_JOB_LOCATION = "Hong Kong"
DEMO_JOB_DESCRIPTION = """Build FastAPI services, maintain clean architecture boundaries,
and collaborate with product-minded engineers on AI-assisted workflows."""
DEMO_JOB_REQUIREMENTS = """Python, FastAPI, SQLAlchemy, REST API design, async programming,
and comfort working across backend and product integration surfaces."""

DEMO_QUESTION_TEXT = "Tell me how you would design a FastAPI service that supports resumable AI workflows."
DEMO_ANSWER_TEXT = """I would separate the HTTP layer, business services, and persistence layer,
use a provider abstraction for the AI model, store durable job state, and expose status and history
through stable API contracts so the workflow remains traceable and recoverable."""


def ensure_data_dir() -> None:
    (REPO_ROOT / "data").mkdir(parents=True, exist_ok=True)


def ensure_demo_user(db) -> User:
    user = db.query(User).filter(User.username == DEMO_USERNAME).first()
    password_hash = user_service.get_password_hash(DEMO_PASSWORD)

    if user is None:
        payload = UserCreate(
            username=DEMO_USERNAME,
            email=DEMO_EMAIL,
            password=DEMO_PASSWORD,
            name=DEMO_NAME,
            bio="Seeded demo user for the portfolio front-end flow.",
        )
        user = asyncio.run(user_service.create_user(db, payload))
    else:
        user.email = DEMO_EMAIL
        user.name = DEMO_NAME
        user.bio = "Seeded demo user for the portfolio front-end flow."
        user.password_hash = password_hash
        db.commit()
        db.refresh(user)

    return user


def ensure_resume(db, current_user) -> Resume:
    resume = (
        db.query(Resume)
        .filter(Resume.user_id == current_user.id, Resume.title == DEMO_RESUME_TITLE)
        .first()
    )

    if resume is None:
        resume = asyncio.run(
            resume_service.create_resume(
                db,
                current_user,
                ResumeCreate(title=DEMO_RESUME_TITLE, file_path="manual/demo-resume.txt"),
            )
        )

    asyncio.run(
        resume_service.update_resume(
            db,
            current_user,
            resume.id,
            ResumeUpdate(
                title=DEMO_RESUME_TITLE,
                processed_content=DEMO_RESUME_TEXT,
                resume_text=DEMO_RESUME_TEXT,
                language="en-US",
                is_default=True,
            ),
        )
    )
    db.refresh(resume)
    return resume


def ensure_job(db) -> Job:
    job = (
        db.query(Job)
        .filter(Job.title == DEMO_JOB_TITLE, Job.company == DEMO_JOB_COMPANY)
        .first()
    )

    if job is None:
        job = asyncio.run(
            job_service.create_job(
                db,
                JobCreate(
                    title=DEMO_JOB_TITLE,
                    company=DEMO_JOB_COMPANY,
                    location=DEMO_JOB_LOCATION,
                    description=DEMO_JOB_DESCRIPTION,
                    requirements=DEMO_JOB_REQUIREMENTS,
                    salary=None,
                    work_type=None,
                    experience=None,
                    education=None,
                    welfare=None,
                    tags=None,
                    source="manual",
                    source_url=None,
                    source_id=None,
                ),
            )
        )

    return job


def ensure_resume_ai_results(db, current_user, resume: Resume) -> None:
    summary = (
        db.query(ResumeOptimization)
        .filter(ResumeOptimization.resume_id == resume.id, ResumeOptimization.mode == "resume_summary")
        .first()
    )
    if summary is None:
        asyncio.run(
            resume_service.persist_resume_summary(
                db,
                current_user,
                resume.id,
                target_role=DEMO_JOB_TITLE,
            )
        )

    improvements = (
        db.query(ResumeOptimization)
        .filter(ResumeOptimization.resume_id == resume.id, ResumeOptimization.mode == "resume_improvements")
        .first()
    )
    if improvements is None:
        asyncio.run(
            resume_service.persist_resume_improvements(
                db,
                current_user,
                resume.id,
                target_role=DEMO_JOB_TITLE,
            )
        )


def ensure_job_match(db, current_user, resume: Resume, job: Job) -> None:
    match = (
        db.query(JobMatchResult)
        .filter(JobMatchResult.job_id == job.id, JobMatchResult.resume_id == resume.id)
        .first()
    )
    if match is None:
        asyncio.run(job_service.persist_job_match(db, job.id, resume.id, current_user.id))


def ensure_interview_question(db) -> InterviewQuestion:
    question = (
        db.query(InterviewQuestion)
        .filter(InterviewQuestion.question_text == DEMO_QUESTION_TEXT)
        .first()
    )
    if question is None:
        question = asyncio.run(
            interview_service.create_question(
                db,
                InterviewQuestionCreate(
                    question_type="technical",
                    difficulty="medium",
                    question_text=DEMO_QUESTION_TEXT,
                    category="backend",
                    tags="fastapi,architecture,ai",
                ),
            )
        )
    return question


def ensure_interview_session(db, current_user, job: Job) -> InterviewSession:
    session = (
        db.query(InterviewSession)
        .filter(InterviewSession.user_id == current_user.id, InterviewSession.job_id == job.id)
        .first()
    )
    if session is None:
        session = asyncio.run(
            interview_service.create_session(
                db,
                InterviewSessionCreate(
                    job_id=job.id,
                    session_type="technical",
                    total_questions=5,
                    completed=0,
                ),
                current_user.id,
            )
        )
    return session


def ensure_interview_record(db, current_user, job: Job, question: InterviewQuestion) -> InterviewRecord:
    record = (
        db.query(InterviewRecord)
        .filter(
            InterviewRecord.user_id == current_user.id,
            InterviewRecord.job_id == job.id,
            InterviewRecord.question_id == question.id,
        )
        .first()
    )

    if record is None:
        record = asyncio.run(
            interview_service.create_record(
                db,
                InterviewRecordCreate(
                    job_id=job.id,
                    question_id=question.id,
                    user_answer=DEMO_ANSWER_TEXT,
                ),
                current_user.id,
            )
        )
    else:
        record.user_answer = DEMO_ANSWER_TEXT
        db.commit()
        db.refresh(record)

    if not record.ai_evaluation:
        asyncio.run(
            interview_service.persist_interview_record_evaluation(
                db,
                record.id,
                current_user.id,
                job_context=DEMO_JOB_DESCRIPTION,
            )
        )
        db.refresh(record)

    return record


def main() -> None:
    ensure_data_dir()
    db = SessionLocal()

    try:
        user = ensure_demo_user(db)
        current_user = SimpleNamespace(id=user.id)

        resume = ensure_resume(db, current_user)
        job = ensure_job(db)
        ensure_resume_ai_results(db, current_user, resume)
        ensure_job_match(db, current_user, resume, job)
        question = ensure_interview_question(db)
        ensure_interview_session(db, current_user, job)
        record = ensure_interview_record(db, current_user, job, question)

        # 创建示例数据
        print("\nCreating example data...")
        r_count, j_count = seed_example_data(db)
        print(f"Created {r_count} resumes and {j_count} jobs")

        print("Demo seed completed.")
        print(f"User: {DEMO_USERNAME} / {DEMO_PASSWORD}")
        print(f"Resume ID: {resume.id}")
        print(f"Job ID: {job.id}")
        print(f"Question ID: {question.id}")
        print(f"Interview Record ID: {record.id}")
    finally:
        db.close()


if __name__ == "__main__":
    main()
