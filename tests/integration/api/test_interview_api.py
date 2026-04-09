"""Interview API integration tests."""

from types import SimpleNamespace
from unittest.mock import AsyncMock

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from src.data_access.database import Base, get_db
from src.data_access.repositories.resume_repository import resume_repository
from src.data_access.repositories.interview_repository import interview_question_repository
from src.data_access.repositories.user_repository import user_repository
from src.business_logic.interview import interview_service
from src.presentation.api.deps import get_current_user
from src.presentation.api.v1.interview import router as interview_router


engine = create_engine(
    "sqlite://",
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

app = FastAPI()
app.include_router(interview_router, prefix="/api/v1/interview", tags=["interview"])


@pytest.fixture(scope="module", autouse=True)
def setup_database():
    Base.metadata.create_all(bind=engine)
    yield
    Base.metadata.drop_all(bind=engine)


@pytest.fixture
def db_session():
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()


@pytest.fixture
def client(db_session):
    def override_get_db():
        try:
            yield db_session
        finally:
            pass

    app.dependency_overrides[get_db] = override_get_db
    with TestClient(app) as test_client:
        yield test_client
    app.dependency_overrides.clear()


def _seed_user(db, username, email):
    return user_repository.create(
        db,
        {
            "username": username,
            "email": email,
            "password_hash": "hashed-password",
            "name": username,
        },
    )


def _seed_question(db, question_text):
    return interview_question_repository.create(
        db,
        {
            "question_type": "technical",
            "difficulty": "easy",
            "question_text": question_text,
            "category": "backend",
            "tags": "python,api",
            "sample_answer": "sample",
            "reference_material": "docs",
        },
    )


def _set_current_user(user_id):
    app.dependency_overrides[get_current_user] = lambda: SimpleNamespace(id=user_id)


def _seed_resume(db, user_id, title="Resume", resume_text="Built APIs with FastAPI"):
    return resume_repository.create(
        db,
        {
            "title": title,
            "user_id": user_id,
            "original_file_path": "/tmp/resume.pdf",
            "file_name": "resume.pdf",
            "file_type": "pdf",
            "processed_content": "",
            "resume_text": resume_text,
            "language": "zh-CN",
        },
    )


def test_interview_api_creates_and_lists_user_scoped_sessions_and_records(db_session, client):
    user_1 = _seed_user(db_session, "user1", "user1@example.com")
    user_2 = _seed_user(db_session, "user2", "user2@example.com")
    question = _seed_question(db_session, "Explain dependency injection.")

    _set_current_user(user_1.id)
    response = client.post(
        "/api/v1/interview/sessions/",
        json={
            "duration": 30,
            "total_questions": 5,
        },
    )
    assert response.status_code == 200
    session_user_1 = response.json()
    assert session_user_1["user_id"] == user_1.id

    response = client.post(
        "/api/v1/interview/records/",
        json={
            "question_id": question.id,
            "user_answer": "It wires dependencies together.",
            "score": 95,
            "feedback": "Strong answer.",
        },
    )
    assert response.status_code == 200
    record_user_1 = response.json()
    assert record_user_1["user_id"] == user_1.id

    _set_current_user(user_2.id)
    response = client.post(
        "/api/v1/interview/sessions/",
        json={
            "duration": 45,
            "total_questions": 6,
            "session_type": "behavioral",
        },
    )
    assert response.status_code == 200
    session_user_2 = response.json()
    assert session_user_2["user_id"] == user_2.id

    response = client.post(
        "/api/v1/interview/records/",
        json={
            "question_id": question.id,
            "user_answer": "It separates concerns.",
            "score": 88,
            "feedback": "Good.",
        },
    )
    assert response.status_code == 200
    record_user_2 = response.json()
    assert record_user_2["user_id"] == user_2.id

    _set_current_user(user_1.id)
    response = client.get("/api/v1/interview/sessions/")
    assert response.status_code == 200
    sessions = response.json()
    assert len(sessions) == 1
    assert sessions[0]["id"] == session_user_1["id"]
    assert sessions[0]["user_id"] == user_1.id

    response = client.get("/api/v1/interview/records/")
    assert response.status_code == 200
    records = response.json()
    assert len(records) == 1
    assert records[0]["id"] == record_user_1["id"]
    assert records[0]["user_id"] == user_1.id


def test_interview_api_generates_questions(client):
    _set_current_user(1)
    original_method = interview_service.generate_interview_questions_preview
    interview_service.generate_interview_questions_preview = AsyncMock(
        return_value={
            "mode": "question_generation",
            "job_context": "Backend intern role",
            "resume_context": "Built APIs with FastAPI",
            "count": 2,
            "questions": [
                {
                    "question_number": 1,
                    "question_text": "Explain dependency injection.",
                    "question_type": "technical",
                    "difficulty": "medium",
                    "category": "generated",
                },
                {
                    "question_number": 2,
                    "question_text": "How do you test FastAPI routes?",
                    "question_type": "technical",
                    "difficulty": "medium",
                    "category": "generated",
                },
            ],
            "raw_content": "mock output",
            "provider": "mock",
            "model": "mock-model",
        }
    )

    try:
        response = client.post(
            "/api/v1/interview/questions/generate/",
            json={
                "job_context": "Backend intern role",
                "resume_id": 3,
                "count": 2,
            },
        )
    finally:
        interview_service.generate_interview_questions_preview = original_method

    assert response.status_code == 200
    payload = response.json()
    assert payload["mode"] == "question_generation"
    assert len(payload["questions"]) == 2
    assert payload["raw_content"] == "mock output"
    assert payload["provider"] == "mock"
    assert payload["model"] == "mock-model"


def test_interview_api_evaluates_answer(client):
    _set_current_user(1)
    original_method = interview_service.evaluate_interview_answer_preview
    interview_service.evaluate_interview_answer_preview = AsyncMock(
        return_value={
            "mode": "answer_evaluation",
            "question_text": "Explain dependency injection",
            "user_answer": "It wires dependencies into handlers.",
            "job_context": "Backend intern role",
            "score": 90,
            "feedback": "Clear explanation.",
            "raw_content": "Score: 90\\nFeedback: Clear explanation.",
            "provider": "mock",
            "model": "mock-model",
        }
    )

    try:
        response = client.post(
            "/api/v1/interview/answers/evaluate/",
            json={
                "question_text": "Explain dependency injection",
                "user_answer": "It wires dependencies into handlers.",
                "job_context": "Backend intern role",
            },
        )
    finally:
        interview_service.evaluate_interview_answer_preview = original_method

    assert response.status_code == 200
    payload = response.json()
    assert payload["mode"] == "answer_evaluation"
    assert payload["score"] == 90
    assert payload["raw_content"] == "Score: 90\\nFeedback: Clear explanation."
    assert payload["provider"] == "mock"
    assert payload["model"] == "mock-model"


def test_interview_api_generate_questions_returns_404_for_unowned_resume(db_session, client):
    user_1 = _seed_user(db_session, "owner-a", "owner-a@example.com")
    user_2 = _seed_user(db_session, "owner-b", "owner-b@example.com")
    resume = _seed_resume(db_session, user_2.id)

    _set_current_user(user_1.id)
    response = client.post(
        "/api/v1/interview/questions/generate/",
        json={
            "job_context": "Backend intern role",
            "resume_id": resume.id,
            "count": 2,
        },
    )

    assert response.status_code == 404
    assert response.json()["detail"] == "resume not found"


def test_interview_api_persists_record_evaluation(client):
    _set_current_user(1)
    original_method = interview_service.persist_interview_record_evaluation
    interview_service.persist_interview_record_evaluation = AsyncMock(
        return_value={
            "mode": "answer_evaluation",
            "record_id": 7,
            "score": 92,
            "feedback": "Strong answer.",
            "ai_evaluation": "Score: 92\\nFeedback: Strong answer.",
            "raw_content": "Score: 92\\nFeedback: Strong answer.",
            "answered_at": "2026-03-28T15:05:00",
            "provider": "mock",
            "model": "mock-model",
        }
    )

    try:
        response = client.post("/api/v1/interview/records/7/evaluate/", json={})
    finally:
        interview_service.persist_interview_record_evaluation = original_method

    assert response.status_code == 200
    payload = response.json()
    assert payload["record_id"] == 7
    assert payload["score"] == 92
    assert payload["mode"] == "answer_evaluation"
    assert payload["raw_content"] == "Score: 92\\nFeedback: Strong answer."
    assert payload["provider"] == "mock"
    assert payload["model"] == "mock-model"


def test_interview_api_persists_record_evaluation_exposes_provider_model(client):
    _set_current_user(1)
    original_method = interview_service.persist_interview_record_evaluation
    interview_service.persist_interview_record_evaluation = AsyncMock(
        return_value={
            "mode": "answer_evaluation",
            "record_id": 8,
            "score": 88,
            "feedback": "Good answer.",
            "ai_evaluation": "Score: 88\\nFeedback: Good answer.",
            "raw_content": "Score: 88\\nFeedback: Good answer.",
            "answered_at": "2026-03-28T15:10:00",
            "provider": "mock",
            "model": "mock-model",
        }
    )

    try:
        response = client.post("/api/v1/interview/records/8/evaluate/", json={})
    finally:
        interview_service.persist_interview_record_evaluation = original_method

    assert response.status_code == 200
    payload = response.json()
    assert payload["record_id"] == 8
    assert payload["mode"] == "answer_evaluation"
    assert payload["raw_content"] == "Score: 88\\nFeedback: Good answer."
    assert payload["provider"] == "mock"
    assert payload["model"] == "mock-model"


def test_interview_api_record_evaluation_returns_404_for_unowned_record(client):
    _set_current_user(1)
    original_method = interview_service.persist_interview_record_evaluation
    interview_service.persist_interview_record_evaluation = AsyncMock(side_effect=ValueError("interview record not found"))

    try:
        response = client.post("/api/v1/interview/records/7/evaluate/", json={})
    finally:
        interview_service.persist_interview_record_evaluation = original_method

    assert response.status_code == 404
    assert response.json()["detail"] == "interview record not found"


def test_interview_api_record_evaluation_returns_400_for_missing_input(client):
    _set_current_user(1)
    original_method = interview_service.persist_interview_record_evaluation
    interview_service.persist_interview_record_evaluation = AsyncMock(
        side_effect=ValueError("interview record is missing required evaluation input")
    )

    try:
        response = client.post("/api/v1/interview/records/7/evaluate/", json={})
    finally:
        interview_service.persist_interview_record_evaluation = original_method

    assert response.status_code == 400
    assert response.json()["detail"] == "interview record is missing required evaluation input"


def test_interview_api_coach_start_success(client):
    """Test POST /api/v1/interview/coach/start - success case"""
    _set_current_user(1)
    import src.presentation.api.v1.interview as interview_module

    def mock_start(db, user, jd_id, resume_id, question_count):
        return {
            "session_id": 1,
            "opening_message": "Welcome to your interview practice session.",
            "first_question": "Tell me about yourself.",
            "total_questions": 5,
        }

    original_start = interview_module.coach_service.start_session
    interview_module.coach_service.start_session = mock_start

    try:
        response = client.post(
            "/api/v1/interview/coach/start",
            json={
                "jd_id": 1,
                "resume_id": 1,
                "question_count": 5,
            },
        )
        assert response.status_code == 200
        payload = response.json()
        assert payload["session_id"] == 1
        assert "opening_message" in payload
    finally:
        interview_module.coach_service.start_session = original_start


def test_interview_api_coach_start_not_found(client):
    """Test POST /api/v1/interview/coach/start - resource not found"""
    _set_current_user(1)
    import src.presentation.api.v1.interview as interview_module

    def mock_start(db, user, jd_id, resume_id, question_count):
        raise ValueError("jd_id not found")

    original_start = interview_module.coach_service.start_session
    interview_module.coach_service.start_session = mock_start

    try:
        response = client.post(
            "/api/v1/interview/coach/start",
            json={
                "jd_id": 999,
                "resume_id": 1,
                "question_count": 5,
            },
        )
        assert response.status_code == 404
    finally:
        interview_module.coach_service.start_session = original_start


def test_interview_api_coach_answer_success(client):
    """Test POST /api/v1/interview/coach/answer - success case"""
    _set_current_user(1)
    import src.presentation.api.v1.interview as interview_module

    def mock_answer(db, user, session_id, answer):
        return {
            "score": 85,
            "feedback": "Good answer!",
            "next_question": "What is your greatest strength?",
            "is_followup": False,
            "is_last": False,
            "timeout_followup_skipped": False,
        }

    original_answer = interview_module.coach_service.submit_answer
    interview_module.coach_service.submit_answer = mock_answer

    try:
        response = client.post(
            "/api/v1/interview/coach/answer",
            json={
                "session_id": 1,
                "answer": "I have strong problem-solving skills.",
            },
        )
        assert response.status_code == 200
        payload = response.json()
        assert payload["score"] == 85
    finally:
        interview_module.coach_service.submit_answer = original_answer


def test_interview_api_coach_answer_session_ended(client):
    """Test POST /api/v1/interview/coach/answer - session already ended"""
    _set_current_user(1)
    import src.presentation.api.v1.interview as interview_module

    def mock_answer(db, user, session_id, answer):
        raise ValueError("面试已结束")

    original_answer = interview_module.coach_service.submit_answer
    interview_module.coach_service.submit_answer = mock_answer

    try:
        response = client.post(
            "/api/v1/interview/coach/answer",
            json={
                "session_id": 1,
                "answer": "Late answer attempt.",
            },
        )
        assert response.status_code == 409
    finally:
        interview_module.coach_service.submit_answer = original_answer


def test_interview_api_coach_followup_success(client):
    """Test POST /api/v1/interview/coach/followup - success case"""
    _set_current_user(1)
    import src.presentation.api.v1.interview as interview_module

    def mock_followup(db, user, session_id, followup_answers):
        return {
            "session_id": session_id,
            "review_report": {
                "dimensions": [],
                "overall_score": 88,
                "overall_comment": "Great practice session!",
                "improvement_suggestions": [],
                "markdown": "# Practice Report",
            },
            "average_score": 88.0,
        }

    original_followup = interview_module.coach_service.submit_followup_answers
    interview_module.coach_service.submit_followup_answers = mock_followup

    try:
        response = client.post(
            "/api/v1/interview/coach/followup",
            json={
                "session_id": 1,
                "followup_answers": [{"question": "Why this company?", "answer": "I like the culture."}],
            },
        )
        assert response.status_code == 200
        payload = response.json()
        assert payload["session_id"] == 1
    finally:
        interview_module.coach_service.submit_followup_answers = original_followup


def test_interview_api_coach_end_success(client):
    """Test POST /api/v1/interview/coach/end - success case"""
    _set_current_user(1)
    import src.presentation.api.v1.interview as interview_module

    def mock_end(db, user, session_id, followup_skipped):
        return {
            "session_id": session_id,
            "review_report": {
                "dimensions": [],
                "overall_score": 85,
                "overall_comment": "Practice session complete.",
                "improvement_suggestions": [],
                "markdown": "# Practice Report",
            },
            "average_score": 85.0,
        }

    original_end = interview_module.coach_service.end_session
    interview_module.coach_service.end_session = mock_end

    try:
        response = client.post(
            "/api/v1/interview/coach/end?session_id=1&followup_skipped=true",
        )
        assert response.status_code == 200
        payload = response.json()
        assert payload["session_id"] == 1
    finally:
        interview_module.coach_service.end_session = original_end


def test_interview_api_coach_end_not_found(client):
    """Test POST /api/v1/interview/coach/end - session not found"""
    _set_current_user(1)
    import src.presentation.api.v1.interview as interview_module

    def mock_end(db, user, session_id, followup_skipped):
        raise ValueError("Session or unauthorized")

    original_end = interview_module.coach_service.end_session
    interview_module.coach_service.end_session = mock_end

    try:
        response = client.post(
            "/api/v1/interview/coach/end?session_id=999",
        )
        assert response.status_code == 404
    finally:
        interview_module.coach_service.end_session = original_end


def test_interview_api_get_question_not_found(client):
    """Test GET /api/v1/interview/questions/{question_id} - not found"""
    _set_current_user(1)
    response = client.get("/api/v1/interview/questions/99999")
    assert response.status_code == 404
    assert response.json()["detail"] == "Interview question not found"


def test_interview_api_update_question_not_found(db_session, client):
    """Test PUT /api/v1/interview/questions/{question_id} - not found"""
    _set_current_user(1)
    question = _seed_question(db_session, "Test question")

    original_update = interview_service.update_question
    interview_service.update_question = AsyncMock(return_value=None)

    try:
        response = client.put(
            f"/api/v1/interview/questions/{question.id}",
            json={
                "question_text": "Updated question text",
                "question_type": "technical",
                "difficulty": "medium",
            },
        )
        assert response.status_code == 404
    finally:
        interview_service.update_question = original_update
