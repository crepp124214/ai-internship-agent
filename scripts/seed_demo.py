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
from src.business_logic.tracker import tracker_service
from src.business_logic.user import user_service
from src.data_access.database import SessionLocal
from src.data_access.entities.interview import InterviewQuestion, InterviewRecord, InterviewSession
from src.data_access.entities.job import Job, JobApplication, JobMatchResult
from src.data_access.entities.resume import Resume, ResumeOptimization
from src.data_access.entities.tracker import TrackerAdvice
from src.data_access.entities.user import User
from src.presentation.schemas.interview import InterviewQuestionCreate, InterviewRecordCreate, InterviewSessionCreate
from src.presentation.schemas.job import JobCreate
from src.presentation.schemas.resume import ResumeCreate, ResumeUpdate
from src.presentation.schemas.tracker import ApplicationTrackerCreate
from src.presentation.schemas.user import UserCreate


DEMO_USERNAME = "demo"
DEMO_PASSWORD = "demo123"
DEMO_EMAIL = "demo@example.com"
DEMO_NAME = "Portfolio Demo User"

DEMO_RESUME_TITLE = "2026 Internship Master Resume"
DEMO_RESUME_TEXT = """Portfolio Demo User
Backend engineer intern focused on FastAPI, React, SQLAlchemy, and AI workflow tooling.
Built an internship application platform with resume optimization, job matching,
interview prep, and tracker advice flows. Comfortable with Python, TypeScript,
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

DEMO_APPLICATION_NOTES = "Applied after tailoring resume and persisting job match."


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


def ensure_application(db, current_user, job: Job, resume: Resume) -> JobApplication:
    application = (
        db.query(JobApplication)
        .filter(
            JobApplication.user_id == current_user.id,
            JobApplication.job_id == job.id,
            JobApplication.resume_id == resume.id,
        )
        .first()
    )
    if application is None:
        application = asyncio.run(
            tracker_service.create_application(
                db,
                ApplicationTrackerCreate(
                    job_id=job.id,
                    resume_id=resume.id,
                    status="applied",
                    notes=DEMO_APPLICATION_NOTES,
                ),
                current_user.id,
            )
        )
    return application


def ensure_tracker_advice(db, current_user, application: JobApplication) -> TrackerAdvice:
    advice = (
        db.query(TrackerAdvice)
        .filter(TrackerAdvice.application_id == application.id)
        .first()
    )
    if advice is None:
        advice = asyncio.run(
            tracker_service.persist_application_advice(
                db,
                application.id,
                current_user.id,
            )
        )
    return advice


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
        application = ensure_application(db, current_user, job, resume)
        advice = ensure_tracker_advice(db, current_user, application)

        print("Demo seed completed.")
        print(f"User: {DEMO_USERNAME} / {DEMO_PASSWORD}")
        print(f"Resume ID: {resume.id}")
        print(f"Job ID: {job.id}")
        print(f"Question ID: {question.id}")
        print(f"Interview Record ID: {record.id}")
        print(f"Application ID: {application.id}")
        print(f"Tracker Advice ID: {advice.id}")
    finally:
        db.close()


if __name__ == "__main__":
    main()
