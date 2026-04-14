"""Import API integration tests."""

from io import BytesIO
from types import SimpleNamespace
from unittest.mock import patch, MagicMock, PropertyMock

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from src.data_access.database import Base, get_db
from src.data_access.repositories.resume_repository import resume_repository
from src.data_access.repositories.job_repository import job_repository
from src.data_access.repositories.user_repository import user_repository
from src.presentation.api.deps import get_current_user
import importlib
import_router = importlib.import_module("src.presentation.api.v1.import").router


engine = create_engine(
    "sqlite://",
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

app = FastAPI()
app.include_router(import_router, prefix="/api/v1/import", tags=["import"])


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


def _set_current_user(user_id):
    app.dependency_overrides[get_current_user] = lambda: SimpleNamespace(id=user_id)


def _create_mock_parse_result(name, education, skills, experience, raw_text):
    """Create a mock parse result with proper attribute access."""
    mock = MagicMock()
    mock.name = name
    mock.education = education
    mock.skills = skills
    mock.experience = experience
    mock.raw_text = raw_text
    return mock


class TestImportResumeAPI:
    """Tests for POST /api/v1/import/resume"""

    def test_import_resume_pdf_success(self, db_session, client):
        """Test successful PDF resume import."""
        user = _seed_user(db_session, "resume_user", "resume_user@example.com")
        _set_current_user(user.id)

        # Mock the parser since PDF parsing requires PyPDF2 which needs real PDF content
        with patch("src.presentation.api.v1.import.ResumeParser") as mock_parser_class:
            mock_parser = MagicMock()
            mock_parser.parse.return_value = _create_mock_parse_result(
                name="Zhang San",
                education="Bachelor",
                skills=["Python", "FastAPI"],
                experience="3 years",
                raw_text="Zhang San\nBachelor\nPython, FastAPI\n3 years experience",
            )
            mock_parser_class.return_value = mock_parser

            response = client.post(
                "/api/v1/import/resume",
                files={"file": ("resume.pdf", BytesIO(b"%PDF-1.4 test content"), "application/pdf")},
            )

        assert response.status_code == 200
        payload = response.json()
        assert payload["success"] is True
        assert "resume_id" in payload
        assert payload["parsed"]["name"] == "Zhang San"

    def test_import_resume_docx_success(self, db_session, client):
        """Test successful DOCX resume import."""
        user = _seed_user(db_session, "docx_user", "docx_user@example.com")
        _set_current_user(user.id)

        # Mock the parser for DOCX
        with patch("src.presentation.api.v1.import.ResumeParser") as mock_parser_class:
            mock_parser = MagicMock()
            mock_parser.parse.return_value = _create_mock_parse_result(
                name="Li Si",
                education="Master",
                skills=["Python", "FastAPI"],
                experience="3 years",
                raw_text="Li Si\nMaster\nPython, FastAPI\n3 years experience",
            )
            mock_parser_class.return_value = mock_parser

            response = client.post(
                "/api/v1/import/resume",
                files={"file": ("resume.docx", BytesIO(b"PK\x03\x04"), "application/vnd.openxmlformats-officedocument.wordprocessingml.document")},
            )

        assert response.status_code == 200
        payload = response.json()
        assert payload["success"] is True
        assert payload["parsed"]["name"] == "Li Si"
        assert payload["parsed"]["education"] == "Master"
        assert "Python" in payload["parsed"]["skills"]

    def test_import_resume_unsupported_format(self, db_session, client):
        """Test import fails for unsupported file format."""
        user = _seed_user(db_session, "bad_format_user", "bad_format_user@example.com")
        _set_current_user(user.id)

        with patch("src.presentation.api.v1.import.ResumeParser") as mock_parser_class:
            mock_parser = MagicMock()
            mock_parser.parse.side_effect = ValueError("Unsupported file format: txt")
            mock_parser_class.return_value = mock_parser

            response = client.post(
                "/api/v1/import/resume",
                files={"file": ("resume.txt", BytesIO(b"plain text content"), "text/plain")},
            )

        assert response.status_code == 400
        assert "Unsupported file format" in response.json()["detail"]

    def test_import_resume_requires_authentication(self, client):
        """Test import fails without authentication."""
        if get_current_user in app.dependency_overrides:
            del app.dependency_overrides[get_current_user]

        response = client.post(
            "/api/v1/import/resume",
            files={"file": ("resume.pdf", BytesIO(b"dummy"), "application/pdf")},
        )

        assert response.status_code == 401


class TestImportJDsAPI:
    """Tests for POST /api/v1/import/jds"""

    def test_import_jds_csv_success(self, db_session, client):
        """Test successful CSV JD import."""
        user = _seed_user(db_session, "jd_csv_user", "jd_csv_user@example.com")
        _set_current_user(user.id)

        def create_mock_jd(title, company, description, requirements, location, salary):
            mock = MagicMock()
            mock.title = title
            mock.company = company
            mock.description = description
            mock.requirements = requirements
            mock.location = location
            mock.salary = salary
            return mock

        with patch("src.presentation.api.v1.import.JDParser") as mock_parser_class:
            mock_parser = MagicMock()
            mock_parser.parse_file.return_value = [
                create_mock_jd(
                    title="Backend Engineer",
                    company="ByteDance",
                    description="Backend service development",
                    requirements="Python",
                    location="Beijing",
                    salary="30k-50k",
                ),
                create_mock_jd(
                    title="Frontend Engineer",
                    company="Tencent",
                    description="Frontend development",
                    requirements="React",
                    location="Shenzhen",
                    salary="25k-45k",
                ),
            ]
            mock_parser_class.return_value = mock_parser

            response = client.post(
                "/api/v1/import/jds",
                files={"file": ("jobs.csv", BytesIO(b"csv content"), "text/csv")},
            )

        assert response.status_code == 200
        payload = response.json()
        assert payload["success"] is True
        assert payload["total"] == 2
        assert payload["imported"] == 2
        assert payload["failed"] == 0
        assert "job_ids" in payload
        assert len(payload["job_ids"]) == 2
        assert all(isinstance(jid, int) for jid in payload["job_ids"])

    def test_import_jds_excel_success(self, db_session, client):
        """Test successful Excel JD import."""
        user = _seed_user(db_session, "jd_xlsx_user", "jd_xlsx_user@example.com")
        _set_current_user(user.id)

        def create_mock_jd(title, company, description, requirements, location, salary):
            mock = MagicMock()
            mock.title = title
            mock.company = company
            mock.description = description
            mock.requirements = requirements
            mock.location = location
            mock.salary = salary
            return mock

        with patch("src.presentation.api.v1.import.JDParser") as mock_parser_class:
            mock_parser = MagicMock()
            mock_parser.parse_file.return_value = [
                create_mock_jd(
                    title="Product Manager",
                    company="Alibaba",
                    description="Product planning",
                    requirements="PRD",
                    location="Hangzhou",
                    salary="35k-60k",
                ),
            ]
            mock_parser_class.return_value = mock_parser

            response = client.post(
                "/api/v1/import/jds",
                files={"file": ("jobs.xlsx", BytesIO(b"PK\x03\x04"), "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")},
            )

        assert response.status_code == 200
        payload = response.json()
        assert payload["success"] is True
        assert payload["total"] == 1
        assert payload["imported"] == 1
        assert "job_ids" in payload
        assert len(payload["job_ids"]) == 1

    def test_import_jds_partial_failure(self, db_session, client):
        """Test partial failure during JD import."""
        user = _seed_user(db_session, "jd_partial_user", "jd_partial_user@example.com")
        _set_current_user(user.id)

        def create_mock_jd(title, company, description, requirements, location, salary):
            mock = MagicMock()
            mock.title = title
            mock.company = company
            mock.description = description
            mock.requirements = requirements
            mock.location = location
            mock.salary = salary
            return mock

        with patch("src.presentation.api.v1.import.JDParser") as mock_parser_class:
            mock_parser = MagicMock()
            mock_parser.parse_file.return_value = [
                create_mock_jd(
                    title="Valid Job",
                    company="Company A",
                    description="Description",
                    requirements="Requirements",
                    location="Beijing",
                    salary="20k",
                ),
                create_mock_jd(
                    title="Invalid Job",
                    company="Company B",
                    description="Description",
                    requirements="Requirements",
                    location="Shanghai",
                    salary="25k",
                ),
            ]
            mock_parser_class.return_value = mock_parser

            # Mock job_repository.create to raise error for second JD
            original_create = job_repository.create
            call_count = [0]

            def mock_create(db, data):
                call_count[0] += 1
                if call_count[0] == 2:
                    raise ValueError("Database error")
                return original_create(db, data)

            with patch.object(job_repository, "create", side_effect=mock_create):
                response = client.post(
                    "/api/v1/import/jds",
                    files={"file": ("jobs.csv", BytesIO(b"csv"), "text/csv")},
                )

        assert response.status_code == 200
        payload = response.json()
        assert payload["success"] is True
        assert payload["total"] == 2
        assert payload["imported"] == 1
        assert payload["failed"] == 1
        assert "job_ids" in payload
        assert len(payload["job_ids"]) == 1
        assert len(payload["errors"]) == 1
        assert "Invalid Job" in payload["errors"][0]
        assert payload["failed"] == 1
        assert len(payload["errors"]) == 1

    def test_import_jds_unsupported_format(self, db_session, client):
        """Test import fails for unsupported file format."""
        user = _seed_user(db_session, "jd_bad_format_user", "jd_bad_format_user@example.com")
        _set_current_user(user.id)

        with patch("src.presentation.api.v1.import.JDParser") as mock_parser_class:
            mock_parser = MagicMock()
            mock_parser.parse_file.side_effect = ValueError("Unsupported file format: txt")
            mock_parser_class.return_value = mock_parser

            response = client.post(
                "/api/v1/import/jds",
                files={"file": ("jobs.txt", BytesIO(b"plain text"), "text/plain")},
            )

        assert response.status_code == 400
        assert "Unsupported file format" in response.json()["detail"]

    def test_import_jds_requires_authentication(self, client):
        """Test import fails without authentication."""
        if get_current_user in app.dependency_overrides:
            del app.dependency_overrides[get_current_user]

        response = client.post(
            "/api/v1/import/jds",
            files={"file": ("jobs.csv", BytesIO(b"csv"), "text/csv")},
        )

        assert response.status_code == 401
