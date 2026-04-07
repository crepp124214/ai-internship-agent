# tests/unit/business_logic/job/tools/test_search_jobs.py
import pytest
from unittest.mock import MagicMock, patch

from src.business_logic.job.tools.search_jobs import SearchJobsTool, SearchJobsInput


class TestSearchJobsTool:
    def setup_method(self):
        self.tool = SearchJobsTool()

    def test_search_jobs_returns_matching_jobs(self):
        """Test that search_jobs returns jobs matching the keyword."""
        mock_job1 = MagicMock()
        mock_job1.id = 1
        mock_job1.title = "Python Developer"
        mock_job1.company = "TechCorp"
        mock_job1.location = "Beijing"
        mock_job1.description = "We are looking for a Python developer"

        mock_job2 = MagicMock()
        mock_job2.id = 2
        mock_job2.title = "Java Engineer"
        mock_job2.company = "JavaCo"
        mock_job2.location = "Shanghai"
        mock_job2.description = "Java position available"

        with patch("src.data_access.repositories.job_repository") as mock_repo:
            mock_repo.get_all.return_value = [mock_job1, mock_job2]
            mock_context = MagicMock(db=MagicMock())

            result = self.tool._execute_sync(
                {"keyword": "Python", "limit": 10},
                context=mock_context
            )

            assert result["keyword"] == "Python"
            assert result["count"] == 1
            assert len(result["jobs"]) == 1
            assert result["jobs"][0]["job_id"] == 1
            assert result["jobs"][0]["title"] == "Python Developer"

    def test_search_jobs_matches_in_description(self):
        """Test that search matches job description."""
        mock_job = MagicMock()
        mock_job.id = 1
        mock_job.title = "Backend Developer"
        mock_job.company = "StartupX"
        mock_job.location = "Remote"
        mock_job.description = "Need Python developer with FastAPI experience"

        with patch("src.data_access.repositories.job_repository") as mock_repo:
            mock_repo.get_all.return_value = [mock_job]
            mock_context = MagicMock(db=MagicMock())

            result = self.tool._execute_sync(
                {"keyword": "FastAPI", "limit": 10},
                context=mock_context
            )

            assert result["count"] == 1
            assert result["jobs"][0]["job_id"] == 1

    def test_search_jobs_matches_in_company_name(self):
        """Test that search matches company name."""
        mock_job = MagicMock()
        mock_job.id = 1
        mock_job.title = "Software Engineer"
        mock_job.company = "Google"
        mock_job.location = "Mountain View"
        mock_job.description = "Software engineering position"

        with patch("src.data_access.repositories.job_repository") as mock_repo:
            mock_repo.get_all.return_value = [mock_job]
            mock_context = MagicMock(db=MagicMock())

            result = self.tool._execute_sync(
                {"keyword": "Google", "limit": 10},
                context=mock_context
            )

            assert result["count"] == 1
            assert result["jobs"][0]["company"] == "Google"

    def test_search_jobs_respects_limit(self):
        """Test that search respects the limit parameter."""
        mock_jobs = []
        for i in range(15):
            mock_job = MagicMock()
            mock_job.id = i + 1
            mock_job.title = f"Python Job {i+1}"
            mock_job.company = f"Company {i+1}"
            mock_job.location = "Location"
            mock_job.description = "Python developer position"
            mock_jobs.append(mock_job)

        with patch("src.data_access.repositories.job_repository") as mock_repo:
            mock_repo.get_all.return_value = mock_jobs
            mock_context = MagicMock(db=MagicMock())

            result = self.tool._execute_sync(
                {"keyword": "Python", "limit": 5},
                context=mock_context
            )

            assert result["count"] == 5
            assert len(result["jobs"]) == 5

    def test_search_jobs_returns_empty_when_no_match(self):
        """Test that search returns empty list when no jobs match."""
        mock_job = MagicMock()
        mock_job.id = 1
        mock_job.title = "Go Developer"
        mock_job.company = "GoCorp"
        mock_job.location = "Beijing"
        mock_job.description = "Go programming position"

        with patch("src.data_access.repositories.job_repository") as mock_repo:
            mock_repo.get_all.return_value = [mock_job]
            mock_context = MagicMock(db=MagicMock())

            result = self.tool._execute_sync(
                {"keyword": "Python", "limit": 10},
                context=mock_context
            )

            assert result["count"] == 0
            assert result["jobs"] == []

    def test_search_jobs_truncates_description(self):
        """Test that description is truncated to 200 characters."""
        mock_job = MagicMock()
        mock_job.id = 1
        mock_job.title = "Developer"
        mock_job.company = "Company"
        mock_job.location = "Location"
        mock_job.description = "A" * 300  # 300 character description

        with patch("src.data_access.repositories.job_repository") as mock_repo:
            mock_repo.get_all.return_value = [mock_job]
            mock_context = MagicMock(db=MagicMock())

            result = self.tool._execute_sync(
                {"keyword": "Developer", "limit": 10},
                context=mock_context
            )

            assert len(result["jobs"][0]["description"]) == 200

    def test_search_jobs_case_insensitive(self):
        """Test that search is case insensitive."""
        mock_job = MagicMock()
        mock_job.id = 1
        mock_job.title = "Python Developer"
        mock_job.company = "TechCorp"
        mock_job.location = "Beijing"
        mock_job.description = "python developer"

        with patch("src.data_access.repositories.job_repository") as mock_repo:
            mock_repo.get_all.return_value = [mock_job]
            mock_context = MagicMock(db=MagicMock())

            result = self.tool._execute_sync(
                {"keyword": "PYTHON", "limit": 10},
                context=mock_context
            )

            assert result["count"] == 1

    def test_search_jobs_input_schema(self):
        """Test that SearchJobsInput schema is correct."""
        schema = SearchJobsInput
        assert hasattr(schema, "model_fields")
        assert "keyword" in schema.model_fields
        assert "limit" in schema.model_fields