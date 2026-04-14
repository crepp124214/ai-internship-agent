"""Resume API integration tests."""

from datetime import datetime
from types import SimpleNamespace
from unittest.mock import AsyncMock, patch

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from src.business_logic.resume import resume_service
from src.data_access.database import Base, get_db
from src.data_access.entities.resume import ResumeOptimization
from src.data_access.repositories.resume_repository import resume_repository
from src.data_access.repositories.user_repository import user_repository
from src.presentation.api.deps import get_current_user
from src.presentation.api.v1.resume import router as resume_router


engine = create_engine(
    "sqlite://",
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

app = FastAPI()
app.include_router(resume_router, prefix="/api/v1/resumes", tags=["resumes"])


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


def _seed_resume(
    db,
    *,
    user_id,
    title="Resume",
    processed_content="Processed resume content",
    resume_text="Raw resume text",
):
    return resume_repository.create(
        db,
        {
            "title": title,
            "user_id": user_id,
            "original_file_path": "/tmp/resume.pdf",
            "file_name": "resume.pdf",
            "file_type": "pdf",
            "processed_content": processed_content,
            "resume_text": resume_text,
            "language": "zh-CN",
        },
    )


def _set_current_user(user_id):
    app.dependency_overrides[get_current_user] = lambda: SimpleNamespace(id=user_id)


def _seed_resume_optimization(
    db,
    *,
    resume_id,
    original_text,
    optimized_text,
    optimization_type,
    keywords,
    score,
    ai_suggestion,
):
    optimization = ResumeOptimization(
        resume_id=resume_id,
        original_text=original_text,
        optimized_text=optimized_text,
        optimization_type=optimization_type,
        keywords=keywords,
        score=score,
        ai_suggestion=ai_suggestion,
        created_at=datetime(2026, 3, 28, 12, 0, 0),
        updated_at=datetime(2026, 3, 28, 12, 0, 0),
    )
    db.add(optimization)
    db.commit()
    db.refresh(optimization)
    return optimization


def test_resume_api_generates_summary_for_current_user(db_session, client):
    user = _seed_user(db_session, "resume_user", "resume_user@example.com")
    resume = _seed_resume(db_session, user_id=user.id)
    _set_current_user(user.id)

    original_method = resume_service.extract_resume_summary
    resume_service.extract_resume_summary = AsyncMock(
        return_value={
            "mode": "summary",
            "resume_text": "Processed resume content",
            "target_role": "backend engineer",
            "content": "Strong backend-focused internship profile.",
            "raw_content": "Summary: Strong backend-focused internship profile.",
            "provider": "mock",
            "model": "mock-model",
            "status": "fallback",
            "fallback_used": True,
        }
    )

    try:
        response = client.post(
            f"/api/v1/resumes/{resume.id}/summary/",
            json={"target_role": "backend engineer"},
        )
    finally:
        resume_service.extract_resume_summary = original_method

    assert response.status_code == 200
    payload = response.json()
    assert payload == {
        "mode": "summary",
        "resume_id": resume.id,
        "target_role": "backend engineer",
        "content": "Strong backend-focused internship profile.",
        "raw_content": "Summary: Strong backend-focused internship profile.",
        "provider": "mock",
        "model": "mock-model",
        "status": "fallback",
        "fallback_used": True,
    }


def test_resume_api_generates_improvements_for_current_user(db_session, client):
    user = _seed_user(db_session, "resume_user_2", "resume_user_2@example.com")
    resume = _seed_resume(db_session, user_id=user.id)
    _set_current_user(user.id)

    original_method = resume_service.suggest_resume_improvements
    resume_service.suggest_resume_improvements = AsyncMock(
        return_value={
            "mode": "resume_improvements",
            "resume_text": "Processed resume content",
            "target_role": None,
            "content": "Add measurable project outcomes and tighten skill grouping.",
            "raw_content": "Summary: Add measurable project outcomes and tighten skill grouping.",
            "provider": "mock",
            "model": "mock-model",
            "status": "fallback",
            "fallback_used": True,
        }
    )

    try:
        response = client.post(f"/api/v1/resumes/{resume.id}/improvements/", json={})
    finally:
        resume_service.suggest_resume_improvements = original_method

    assert response.status_code == 200
    payload = response.json()
    assert payload == {
        "mode": "improvements",
        "resume_id": resume.id,
        "target_role": None,
        "content": "Add measurable project outcomes and tighten skill grouping.",
        "raw_content": "Summary: Add measurable project outcomes and tighten skill grouping.",
        "provider": "mock",
        "model": "mock-model",
        "status": "fallback",
        "fallback_used": True,
    }


def test_resume_api_returns_404_for_non_owned_resume(db_session, client):
    owner = _seed_user(db_session, "owner", "owner@example.com")
    other_user = _seed_user(db_session, "other", "other@example.com")
    resume = _seed_resume(db_session, user_id=owner.id)
    _set_current_user(other_user.id)

    response = client.post(f"/api/v1/resumes/{resume.id}/summary/", json={})

    assert response.status_code == 404
    assert response.json()["detail"] == "Resume not found"


def test_resume_api_returns_400_when_resume_text_is_empty(db_session, client):
    user = _seed_user(db_session, "empty_resume", "empty_resume@example.com")
    resume = _seed_resume(db_session, user_id=user.id, processed_content=" ", resume_text=" ")
    _set_current_user(user.id)

    response = client.post(f"/api/v1/resumes/{resume.id}/summary/", json={})

    assert response.status_code == 400
    assert response.json()["detail"] == "resume text is empty"


def test_resume_api_returns_500_on_agent_failure(db_session, client):
    user = _seed_user(db_session, "failing_resume", "failing_resume@example.com")
    resume = _seed_resume(db_session, user_id=user.id)
    _set_current_user(user.id)

    original_method = resume_service.suggest_resume_improvements
    resume_service.suggest_resume_improvements = AsyncMock(side_effect=RuntimeError("llm exploded"))

    try:
        response = client.post(f"/api/v1/resumes/{resume.id}/improvements/", json={})
    finally:
        resume_service.suggest_resume_improvements = original_method

    assert response.status_code == 500
    assert response.json()["detail"] == "Resume improvements failed"


def test_resume_api_persists_improvements_for_current_user(db_session, client):
    user = _seed_user(db_session, "persist_resume_user", "persist_resume_user@example.com")
    resume = _seed_resume(
        db_session,
        user_id=user.id,
        title="persist_resume_candidate",
        processed_content="Processed resume content for persistence",
        resume_text="Raw resume text for persistence",
    )
    _set_current_user(user.id)

    original_method = resume_service.persist_resume_improvements
    resume_service.persist_resume_improvements = AsyncMock(
        return_value={
            "id": 501,
            "resume_id": resume.id,
            "mode": "resume_improvements",
            "original_text": "Processed resume content for persistence",
            "optimized_text": "Add measurable outcomes to each bullet.",
            "optimization_type": "content",
            "keywords": "metrics, impact",
            "score": 92,
            "ai_suggestion": "Add measurable outcomes to each bullet.",
            "raw_content": "Summary: Add measurable outcomes to each bullet.",
            "provider": "mock",
            "model": "mock-model",
            "status": "fallback",
            "fallback_used": True,
            "created_at": datetime(2026, 3, 28, 12, 0, 0),
            "updated_at": datetime(2026, 3, 28, 12, 0, 0),
        }
    )

    try:
        response = client.post(f"/api/v1/resumes/{resume.id}/improvements/persist/", json={})
    finally:
        resume_service.persist_resume_improvements = original_method

    assert response.status_code == 200
    payload = response.json()
    assert payload["resume_id"] == resume.id
    assert payload["mode"] == "resume_improvements"
    assert payload["original_text"] == "Processed resume content for persistence"
    assert payload["optimized_text"] == "Add measurable outcomes to each bullet."
    assert payload["optimization_type"] == "content"
    assert payload["keywords"] == "metrics, impact"
    assert payload["score"] == 92
    assert payload["ai_suggestion"] == "Add measurable outcomes to each bullet."
    assert payload["raw_content"] == "Summary: Add measurable outcomes to each bullet."
    assert payload["provider"] == "mock"
    assert payload["model"] == "mock-model"
    assert payload["status"] == "fallback"
    assert payload["fallback_used"] is True


def test_resume_api_persists_summary_for_current_user(db_session, client):
    user = _seed_user(db_session, "persist_summary_user", "persist_summary_user@example.com")
    resume = _seed_resume(
        db_session,
        user_id=user.id,
        title="persist_summary_candidate",
        processed_content="Processed resume content for summary persistence",
        resume_text="Raw resume text for summary persistence",
    )
    _set_current_user(user.id)

    original_method = resume_service.persist_resume_summary
    resume_service.persist_resume_summary = AsyncMock(
        return_value={
            "id": 511,
            "resume_id": resume.id,
            "mode": "resume_summary",
            "original_text": "Processed resume content for summary persistence",
            "optimized_text": "Candidate shows strong backend internship readiness.",
            "optimization_type": "summary",
            "keywords": "backend engineer",
            "score": None,
            "ai_suggestion": "Candidate shows strong backend internship readiness.",
            "raw_content": "Summary: Candidate shows strong backend internship readiness.",
            "provider": "mock",
            "model": "mock-model",
            "status": "fallback",
            "fallback_used": True,
            "created_at": datetime(2026, 3, 28, 12, 0, 0),
            "updated_at": datetime(2026, 3, 28, 12, 0, 0),
        }
    )

    try:
        response = client.post(
            f"/api/v1/resumes/{resume.id}/summary/persist/",
            json={"target_role": "backend engineer"},
        )
    finally:
        resume_service.persist_resume_summary = original_method

    assert response.status_code == 200
    payload = response.json()
    assert payload["resume_id"] == resume.id
    assert payload["mode"] == "resume_summary"
    assert payload["optimization_type"] == "summary"
    assert payload["keywords"] == "backend engineer"
    assert payload["provider"] == "mock"
    assert payload["model"] == "mock-model"
    assert payload["status"] == "fallback"
    assert payload["fallback_used"] is True


def test_resume_api_lists_persisted_optimizations_for_current_user(db_session, client):
    user = _seed_user(db_session, "list_resume_user", "list_resume_user@example.com")
    resume = _seed_resume(
        db_session,
        user_id=user.id,
        title="list_resume_candidate",
        processed_content="Processed resume content for listing",
        resume_text="Raw resume text for listing",
    )
    _set_current_user(user.id)

    original_method = resume_service.get_resume_optimizations
    resume_service.get_resume_optimizations = AsyncMock(
        return_value=[
            SimpleNamespace(
                id=601,
                resume_id=resume.id,
                mode="resume_improvements",
                original_text="Processed resume content for listing",
                optimized_text="Tighten bullet phrasing.",
                optimization_type="content",
                keywords="impact, metrics",
                score=90,
                ai_suggestion="Tighten bullet phrasing.",
                raw_content="Summary: Tighten bullet phrasing.",
                provider="mock",
                model="mock-model",
                status="fallback",
                fallback_used=True,
                created_at=datetime(2026, 3, 28, 12, 0, 0),
                updated_at=datetime(2026, 3, 28, 12, 0, 0),
            ),
            SimpleNamespace(
                id=602,
                resume_id=resume.id,
                mode="resume_improvements",
                original_text="Processed resume content for listing",
                optimized_text="Add role-specific keywords.",
                optimization_type="keyword",
                keywords="fastapi, sqlalchemy",
                score=88,
                ai_suggestion="Add role-specific keywords.",
                raw_content="Summary: Add role-specific keywords.",
                provider="mock",
                model="mock-model",
                status="fallback",
                fallback_used=True,
                created_at=datetime(2026, 3, 28, 12, 0, 0),
                updated_at=datetime(2026, 3, 28, 12, 0, 0),
            ),
        ]
    )

    try:
        response = client.get(f"/api/v1/resumes/{resume.id}/optimizations/")
    finally:
        resume_service.get_resume_optimizations = original_method

    assert response.status_code == 200
    payload = response.json()
    assert len(payload) == 2
    assert {item["mode"] for item in payload} == {"resume_improvements"}
    assert {item["optimization_type"] for item in payload} == {"content", "keyword"}
    assert {item["resume_id"] for item in payload} == {resume.id}
    assert {item["raw_content"] for item in payload} == {
        "Summary: Tighten bullet phrasing.",
        "Summary: Add role-specific keywords.",
    }
    assert {item["provider"] for item in payload} == {"mock"}
    assert {item["model"] for item in payload} == {"mock-model"}
    assert {item["status"] for item in payload} == {"fallback"}
    assert {item["fallback_used"] for item in payload} == {True}


def test_resume_api_lists_summary_history_for_current_user(db_session, client):
    user = _seed_user(db_session, "list_summary_user", "list_summary_user@example.com")
    resume = _seed_resume(
        db_session,
        user_id=user.id,
        title="list_summary_candidate",
        processed_content="Processed summary source",
        resume_text="Raw summary source",
    )
    _set_current_user(user.id)

    original_method = resume_service.get_resume_summary_history
    resume_service.get_resume_summary_history = AsyncMock(
        return_value=[
            SimpleNamespace(
                id=701,
                resume_id=resume.id,
                mode="resume_summary",
                original_text="Processed summary source",
                optimized_text="Summary one.",
                optimization_type="summary",
                keywords="backend engineer",
                score=None,
                ai_suggestion="Summary one.",
                raw_content="Summary raw one.",
                provider="mock",
                model="mock-model",
                status="fallback",
                fallback_used=True,
                created_at=datetime(2026, 3, 28, 12, 0, 0),
                updated_at=datetime(2026, 3, 28, 12, 0, 0),
            ),
            SimpleNamespace(
                id=702,
                resume_id=resume.id,
                mode="resume_summary",
                original_text="Processed summary source",
                optimized_text="Summary two.",
                optimization_type="summary",
                keywords="backend engineer",
                score=None,
                ai_suggestion="Summary two.",
                raw_content="Summary raw two.",
                provider="mock",
                model="mock-model",
                status="fallback",
                fallback_used=True,
                created_at=datetime(2026, 3, 28, 12, 0, 0),
                updated_at=datetime(2026, 3, 28, 12, 0, 0),
            ),
        ]
    )

    try:
        response = client.get(f"/api/v1/resumes/{resume.id}/summary/history/")
    finally:
        resume_service.get_resume_summary_history = original_method

    assert response.status_code == 200
    payload = response.json()
    assert len(payload) == 2
    assert {item["mode"] for item in payload} == {"resume_summary"}
    assert {item["mode"] for item in payload} == {"resume_summary"}
    assert {item["resume_id"] for item in payload} == {resume.id}
    assert {item["status"] for item in payload} == {"fallback"}
    assert {item["fallback_used"] for item in payload} == {True}


def test_resume_api_returns_404_for_unowned_resume_persist(db_session, client):
    owner = _seed_user(db_session, "persist_owner", "persist_owner@example.com")
    other_user = _seed_user(db_session, "persist_other", "persist_other@example.com")
    resume = _seed_resume(
        db_session,
        user_id=owner.id,
        title="persist_owner_resume",
        processed_content="Owner processed content",
        resume_text="Owner raw resume text",
    )
    _set_current_user(other_user.id)

    response = client.post(f"/api/v1/resumes/{resume.id}/improvements/persist/", json={})

    assert response.status_code == 404
    assert response.json()["detail"] == "Resume not found"


def test_resume_api_returns_404_for_unowned_resume_summary_persist(db_session, client):
    owner = _seed_user(db_session, "summary_owner", "summary_owner@example.com")
    other_user = _seed_user(db_session, "summary_other", "summary_other@example.com")
    resume = _seed_resume(
        db_session,
        user_id=owner.id,
        title="summary_owner_resume",
        processed_content="Owner processed summary content",
        resume_text="Owner raw summary text",
    )
    _set_current_user(other_user.id)

    response = client.post(f"/api/v1/resumes/{resume.id}/summary/persist/", json={})

    assert response.status_code == 404
    assert response.json()["detail"] == "Resume not found"


def test_resume_api_returns_400_when_resume_text_is_empty_for_persist(db_session, client):
    user = _seed_user(db_session, "persist_empty", "persist_empty@example.com")
    resume = _seed_resume(
        db_session,
        user_id=user.id,
        title="persist_empty_resume",
        processed_content=" ",
        resume_text=" ",
    )
    _set_current_user(user.id)

    response = client.post(f"/api/v1/resumes/{resume.id}/improvements/persist/", json={})

    assert response.status_code == 400
    assert response.json()["detail"] == "resume text is empty"


def test_resume_api_returns_400_when_resume_text_is_empty_for_summary_persist(db_session, client):
    user = _seed_user(db_session, "summary_empty", "summary_empty@example.com")
    resume = _seed_resume(
        db_session,
        user_id=user.id,
        title="summary_empty_resume",
        processed_content=" ",
        resume_text=" ",
    )
    _set_current_user(user.id)

    response = client.post(f"/api/v1/resumes/{resume.id}/summary/persist/", json={})

    assert response.status_code == 400
    assert response.json()["detail"] == "resume text is empty"


def test_resume_api_returns_500_when_provider_fails_during_persist(db_session, client):
    user = _seed_user(db_session, "persist_failure", "persist_failure@example.com")
    resume = _seed_resume(
        db_session,
        user_id=user.id,
        title="persist_failure_resume",
        processed_content="Processed resume content for failure",
        resume_text="Raw resume text for failure",
    )
    _set_current_user(user.id)

    original_method = resume_service.persist_resume_improvements
    resume_service.persist_resume_improvements = AsyncMock(side_effect=RuntimeError("llm exploded"))

    try:
        response = client.post(f"/api/v1/resumes/{resume.id}/improvements/persist/", json={})
    finally:
        resume_service.persist_resume_improvements = original_method

    assert response.status_code == 500
    assert response.json()["detail"] == "Resume persistence failed"


def test_resume_api_returns_500_when_provider_fails_during_summary_persist(db_session, client):
    user = _seed_user(db_session, "summary_failure", "summary_failure@example.com")
    resume = _seed_resume(
        db_session,
        user_id=user.id,
        title="summary_failure_resume",
        processed_content="Processed resume content for summary failure",
        resume_text="Raw resume text for summary failure",
    )
    _set_current_user(user.id)

    original_method = resume_service.persist_resume_summary
    resume_service.persist_resume_summary = AsyncMock(side_effect=RuntimeError("llm exploded"))

    try:
        response = client.post(f"/api/v1/resumes/{resume.id}/summary/persist/", json={})
    finally:
        resume_service.persist_resume_summary = original_method

    assert response.status_code == 500
    assert response.json()["detail"] == "Resume summary persistence failed"
