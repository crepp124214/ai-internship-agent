# tests/unit/business_logic/job/tools/test_analyze_jd.py
import pytest
from unittest.mock import MagicMock, patch

from src.business_logic.job.tools.analyze_jd import AnalyzeJDTool, AnalyzeJDInput


class TestAnalyzeJDTool:
    def setup_method(self):
        self.tool = AnalyzeJDTool()

    def test_analyze_jd_returns_error_when_job_not_found(self):
        """Test that analyze_jd returns error when job doesn't exist."""
        with patch("src.data_access.repositories.job_repository") as mock_repo:
            mock_repo.get_by_id.return_value = None

            result = self.tool._execute_sync(
                {"jd_id": 999},
                context=MagicMock(db=MagicMock())
            )

            assert "error" in result
            assert "Job 999 not found" in result["error"]

    def test_analyze_jd_extracts_title_and_company(self):
        """Test that title and company are extracted correctly."""
        mock_job = MagicMock()
        mock_job.id = 1
        mock_job.title = "Python Developer"
        mock_job.company = "TechCorp"
        mock_job.description = "Looking for a Python developer"

        with patch("src.data_access.repositories.job_repository") as mock_repo:
            mock_repo.get_by_id.return_value = mock_job
            mock_context = MagicMock(db=MagicMock())

            result = self.tool._execute_sync(
                {"jd_id": 1},
                context=mock_context
            )

            assert result["jd_id"] == 1
            assert result["title"] == "Python Developer"
            assert result["company"] == "TechCorp"

    def test_analyze_jd_extracts_python_skill(self):
        """Test that Python skill is extracted."""
        mock_job = MagicMock()
        mock_job.id = 1
        mock_job.title = "Backend Developer"
        mock_job.company = "TechCorp"
        mock_job.description = "We need Python, FastAPI and MySQL experience"

        with patch("src.data_access.repositories.job_repository") as mock_repo:
            mock_repo.get_by_id.return_value = mock_job
            mock_context = MagicMock(db=MagicMock())

            result = self.tool._execute_sync(
                {"jd_id": 1},
                context=mock_context
            )

            assert "required_skills" in result
            assert "Python" in result["required_skills"]
            assert "FastAPI" in result["required_skills"]
            assert "MySQL" in result["required_skills"]

    def test_analyze_jd_extracts_experience_chinese(self):
        """Test that experience requirement is extracted from Chinese JD."""
        mock_job = MagicMock()
        mock_job.id = 1
        mock_job.title = "Senior Developer"
        mock_job.company = "TechCorp"
        mock_job.description = "要求 3 年以上 Python 开发经验"

        with patch("src.data_access.repositories.job_repository") as mock_repo:
            mock_repo.get_by_id.return_value = mock_job
            mock_context = MagicMock(db=MagicMock())

            result = self.tool._execute_sync(
                {"jd_id": 1},
                context=mock_context
            )

            assert "experience_required" in result
            assert "3 年" in result["experience_required"]

    def test_analyze_jd_extracts_experience_english(self):
        """Test that experience requirement is extracted from English JD."""
        mock_job = MagicMock()
        mock_job.id = 1
        mock_job.title = "Senior Developer"
        mock_job.company = "TechCorp"
        mock_job.description = "Requires 5+ years of Python development experience"

        with patch("src.data_access.repositories.job_repository") as mock_repo:
            mock_repo.get_by_id.return_value = mock_job
            mock_context = MagicMock(db=MagicMock())

            result = self.tool._execute_sync(
                {"jd_id": 1},
                context=mock_context
            )

            assert "experience_required" in result
            assert "5 年" in result["experience_required"]

    def test_analyze_jd_extracts_education_bachelor(self):
        """Test that education requirement is extracted."""
        mock_job = MagicMock()
        mock_job.id = 1
        mock_job.title = "Developer"
        mock_job.company = "TechCorp"
        mock_job.description = "本科及以上学历，计算机专业优先"

        with patch("src.data_access.repositories.job_repository") as mock_repo:
            mock_repo.get_by_id.return_value = mock_job
            mock_context = MagicMock(db=MagicMock())

            result = self.tool._execute_sync(
                {"jd_id": 1},
                context=mock_context
            )

            assert "education" in result
            assert result["education"] == "本科"

    def test_analyze_jd_extracts_education_master(self):
        """Test that Master's education is extracted."""
        mock_job = MagicMock()
        mock_job.id = 1
        mock_job.title = "Researcher"
        mock_job.company = "Lab"
        mock_job.description = "Master's degree in Computer Science required"

        with patch("src.data_access.repositories.job_repository") as mock_repo:
            mock_repo.get_by_id.return_value = mock_job
            mock_context = MagicMock(db=MagicMock())

            result = self.tool._execute_sync(
                {"jd_id": 1},
                context=mock_context
            )

            assert "education" in result
            assert result["education"] == "Master"

    def test_analyze_jd_includes_raw_text_length(self):
        """Test that raw text length is included."""
        mock_job = MagicMock()
        mock_job.id = 1
        mock_job.title = "Developer"
        mock_job.company = "TechCorp"
        mock_job.description = "Python developer position"  # 24 characters

        with patch("src.data_access.repositories.job_repository") as mock_repo:
            mock_repo.get_by_id.return_value = mock_job
            mock_context = MagicMock(db=MagicMock())

            result = self.tool._execute_sync(
                {"jd_id": 1},
                context=mock_context
            )

            assert "raw_text_length" in result
            assert result["raw_text_length"] == 25

    def test_analyze_jd_empty_description(self):
        """Test with empty job description."""
        mock_job = MagicMock()
        mock_job.id = 1
        mock_job.title = "Developer"
        mock_job.company = "TechCorp"
        mock_job.description = ""

        with patch("src.data_access.repositories.job_repository") as mock_repo:
            mock_repo.get_by_id.return_value = mock_job
            mock_context = MagicMock(db=MagicMock())

            result = self.tool._execute_sync(
                {"jd_id": 1},
                context=mock_context
            )

            assert result["jd_id"] == 1
            assert "required_skills" not in result
            assert "experience_required" not in result
            assert "education" not in result
            assert result["raw_text_length"] == 0

    def test_analyze_jd_multiple_skills(self):
        """Test that multiple skills are extracted."""
        mock_job = MagicMock()
        mock_job.id = 1
        mock_job.title = "Full Stack Developer"
        mock_job.company = "TechCorp"
        mock_job.description = """
        Requirements:
        - Python, JavaScript, TypeScript
        - React, Django
        - PostgreSQL, Redis
        - AWS, Docker
        - 3+ years experience
        """

        with patch("src.data_access.repositories.job_repository") as mock_repo:
            mock_repo.get_by_id.return_value = mock_job
            mock_context = MagicMock(db=MagicMock())

            result = self.tool._execute_sync(
                {"jd_id": 1},
                context=mock_context
            )

            assert "required_skills" in result
            skills = result["required_skills"]
            assert "Python" in skills
            assert "JavaScript" in skills
            assert "TypeScript" in skills
            assert "React" in skills
            assert "Django" in skills
            assert "PostgreSQL" in skills
            assert "Redis" in skills
            assert "AWS" in skills
            assert "Docker" in skills

    def test_analyze_jd_input_schema(self):
        """Test that AnalyzeJDInput schema is correct."""
        schema = AnalyzeJDInput
        assert hasattr(schema, "model_fields")
        assert "jd_id" in schema.model_fields