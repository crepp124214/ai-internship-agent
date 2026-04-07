import pytest
from unittest.mock import MagicMock, patch

from src.business_logic.job.tools.calculate_job_match import CalculateJobMatchTool, CalculateJobMatchInput


class TestCalculateJobMatchTool:
    def setup_method(self):
        self.tool = CalculateJobMatchTool()

    def test_calculate_job_match_returns_error_when_resume_not_found(self):
        """Test that calculate_job_match returns error when resume doesn't exist."""
        with patch("src.data_access.repositories.resume_repository") as mock_resume_repo:
            with patch("src.data_access.repositories.job_repository") as mock_job_repo:
                mock_resume_repo.get_by_id.return_value = None
                mock_job_repo.get_by_id.return_value = MagicMock()

                result = self.tool._execute_sync(
                    {"resume_id": 999, "jd_id": 1},
                    context=MagicMock(db=MagicMock())
                )

                assert "error" in result
                assert "Resume 999 not found" in result["error"]

    def test_calculate_job_match_returns_error_when_job_not_found(self):
        """Test that calculate_job_match returns error when job doesn't exist."""
        mock_resume = MagicMock()

        with patch("src.data_access.repositories.resume_repository") as mock_resume_repo:
            with patch("src.data_access.repositories.job_repository") as mock_job_repo:
                mock_resume_repo.get_by_id.return_value = mock_resume
                mock_job_repo.get_by_id.return_value = None

                result = self.tool._execute_sync(
                    {"resume_id": 1, "jd_id": 999},
                    context=MagicMock(db=MagicMock())
                )

                assert "error" in result
                assert "Job 999 not found" in result["error"]

    def test_calculate_job_match_computes_match_score(self):
        """Test that calculate_job_match correctly computes match score."""
        mock_resume = MagicMock()
        mock_resume.processed_content = "Python JavaScript React MySQL"
        mock_resume.resume_text = ""

        mock_job = MagicMock()
        mock_job.description = "Need Python and React developer"

        mock_report = MagicMock()
        mock_report.match_score = 75.5
        mock_report.keyword_coverage = 0.8
        mock_report.gaps = ["TypeScript", "Docker"]
        mock_report.suggestions = ["Add TypeScript experience", "Add Docker knowledge"]

        with patch("src.data_access.repositories.resume_repository") as mock_resume_repo:
            with patch("src.data_access.repositories.job_repository") as mock_job_repo:
                with patch("src.business_logic.jd.jd_parser_service.JdParserService") as mock_parser_class:
                    with patch("src.business_logic.jd.resume_match_service.ResumeMatchService") as mock_matcher_class:
                        mock_resume_repo.get_by_id.return_value = mock_resume
                        mock_job_repo.get_by_id.return_value = mock_job

                        mock_parser = MagicMock()
                        mock_parser.parse.return_value = MagicMock()
                        mock_parser_class.return_value = mock_parser

                        mock_matcher = MagicMock()
                        mock_matcher.compute_match.return_value = mock_report
                        mock_matcher_class.return_value = mock_matcher

                        result = self.tool._execute_sync(
                            {"resume_id": 1, "jd_id": 2},
                            context=MagicMock(db=MagicMock())
                        )

                        assert result["resume_id"] == 1
                        assert result["jd_id"] == 2
                        assert result["match_score"] == 75.5
                        assert result["keyword_coverage"] == 0.8
                        assert result["gaps"] == ["TypeScript", "Docker"]
                        assert result["suggestions"] == ["Add TypeScript experience", "Add Docker knowledge"]

    def test_calculate_job_match_uses_resume_text_fallback(self):
        """Test that calculate_job_match uses resume_text when processed_content is empty."""
        mock_resume = MagicMock()
        mock_resume.processed_content = None
        mock_resume.resume_text = "Python Django Flask PostgreSQL"

        mock_job = MagicMock()
        mock_job.description = "Backend developer with Python"

        mock_report = MagicMock()
        mock_report.match_score = 60.0
        mock_report.keyword_coverage = 0.6
        mock_report.gaps = ["Microservices"]
        mock_report.suggestions = ["Add microservices experience"]

        with patch("src.data_access.repositories.resume_repository") as mock_resume_repo:
            with patch("src.data_access.repositories.job_repository") as mock_job_repo:
                with patch("src.business_logic.jd.jd_parser_service.JdParserService") as mock_parser_class:
                    with patch("src.business_logic.jd.resume_match_service.ResumeMatchService") as mock_matcher_class:
                        mock_resume_repo.get_by_id.return_value = mock_resume
                        mock_job_repo.get_by_id.return_value = mock_job

                        mock_parser = MagicMock()
                        mock_parser.parse.return_value = MagicMock()
                        mock_parser_class.return_value = mock_parser

                        mock_matcher = MagicMock()
                        mock_matcher.compute_match.return_value = mock_report
                        mock_matcher_class.return_value = mock_matcher

                        result = self.tool._execute_sync(
                            {"resume_id": 1, "jd_id": 2},
                            context=MagicMock(db=MagicMock())
                        )

                        assert result["match_score"] == 60.0
                        mock_parser.parse.assert_called_once()
                        mock_matcher.compute_match.assert_called_once()

    def test_calculate_job_match_passes_correct_texts_to_services(self):
        """Test that calculate_job_match passes correct resume and job texts to services."""
        mock_resume = MagicMock()
        mock_resume.processed_content = "Resume content here"
        mock_resume.resume_text = ""

        mock_job = MagicMock()
        mock_job.description = "Job description here"

        mock_report = MagicMock()
        mock_report.match_score = 50.0
        mock_report.keyword_coverage = 0.5
        mock_report.gaps = []
        mock_report.suggestions = []

        with patch("src.data_access.repositories.resume_repository") as mock_resume_repo:
            with patch("src.data_access.repositories.job_repository") as mock_job_repo:
                with patch("src.business_logic.jd.jd_parser_service.JdParserService") as mock_parser_class:
                    with patch("src.business_logic.jd.resume_match_service.ResumeMatchService") as mock_matcher_class:
                        mock_resume_repo.get_by_id.return_value = mock_resume
                        mock_job_repo.get_by_id.return_value = mock_job

                        mock_parser = MagicMock()
                        mock_parsed_jd = MagicMock()
                        mock_parser.parse.return_value = mock_parsed_jd
                        mock_parser_class.return_value = mock_parser

                        mock_matcher = MagicMock()
                        mock_matcher.compute_match.return_value = mock_report
                        mock_matcher_class.return_value = mock_matcher

                        self.tool._execute_sync(
                            {"resume_id": 1, "jd_id": 2},
                            context=MagicMock(db=MagicMock())
                        )

                        mock_parser.parse.assert_called_once_with("Job description here")
                        mock_matcher.compute_match.assert_called_once_with("Resume content here", mock_parsed_jd)
