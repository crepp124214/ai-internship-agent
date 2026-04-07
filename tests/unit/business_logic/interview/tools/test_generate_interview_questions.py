# tests/unit/business_logic/interview/tools/test_generate_interview_questions.py
import pytest
from unittest.mock import MagicMock, patch

from src.business_logic.interview.tools.generate_interview_questions import (
    GenerateInterviewQuestionsTool,
    GenerateInterviewQuestionsInput,
)


class TestGenerateInterviewQuestionsTool:
    def setup_method(self):
        self.tool = GenerateInterviewQuestionsTool()

    def test_returns_error_when_job_not_found(self):
        """Test that tool returns error when job doesn't exist."""
        with patch("src.data_access.repositories.job_repository") as mock_job_repo, \
             patch("src.data_access.repositories.resume_repository") as mock_resume_repo:
            mock_job_repo.get_by_id.return_value = None
            mock_resume_repo.get_by_id.return_value = MagicMock()

            result = self.tool._execute_sync(
                {"jd_id": 999, "resume_id": 1},
                context=MagicMock(db=MagicMock())
            )

            assert "error" in result
            assert "Job 999 not found" in result["error"]

    def test_returns_error_when_resume_not_found(self):
        """Test that tool returns error when resume doesn't exist."""
        with patch("src.data_access.repositories.job_repository") as mock_job_repo, \
             patch("src.data_access.repositories.resume_repository") as mock_resume_repo:
            mock_job_repo.get_by_id.return_value = MagicMock()
            mock_resume_repo.get_by_id.return_value = None

            result = self.tool._execute_sync(
                {"jd_id": 1, "resume_id": 999},
                context=MagicMock(db=MagicMock())
            )

            assert "error" in result
            assert "Resume 999 not found" in result["error"]

    def test_generates_python_question_for_python_jd(self):
        """Test that Python question is generated for Python JD."""
        mock_job = MagicMock()
        mock_job.description = "我们需要 Python 开发工程师，熟悉 Django 框架"

        mock_resume = MagicMock()
        mock_resume.processed_content = "熟悉 Python 编程"
        mock_resume.resume_text = ""

        with patch("src.data_access.repositories.job_repository") as mock_job_repo, \
             patch("src.data_access.repositories.resume_repository") as mock_resume_repo:
            mock_job_repo.get_by_id.return_value = mock_job
            mock_resume_repo.get_by_id.return_value = mock_resume

            result = self.tool._execute_sync(
                {"jd_id": 1, "resume_id": 1},
                context=MagicMock(db=MagicMock())
            )

            assert "questions" in result
            python_questions = [q for q in result["questions"] if "Python" in q["question"]]
            assert len(python_questions) > 0

    def test_generates_sql_question_for_database_jd(self):
        """Test that SQL question is generated for JD mentioning database."""
        mock_job = MagicMock()
        mock_job.description = "需要具备数据库设计和 SQL 优化经验"

        mock_resume = MagicMock()
        mock_resume.processed_content = ""
        mock_resume.resume_text = ""

        with patch("src.data_access.repositories.job_repository") as mock_job_repo, \
             patch("src.data_access.repositories.resume_repository") as mock_resume_repo:
            mock_job_repo.get_by_id.return_value = mock_job
            mock_resume_repo.get_by_id.return_value = mock_resume

            result = self.tool._execute_sync(
                {"jd_id": 1, "resume_id": 1},
                context=MagicMock(db=MagicMock())
            )

            assert "questions" in result
            sql_questions = [q for q in result["questions"] if "SQL" in q["question"]]
            assert len(sql_questions) > 0

    def test_generates_javascript_question_for_js_jd(self):
        """Test that JavaScript question is generated for JD mentioning JS."""
        mock_job = MagicMock()
        mock_job.description = "前端开发需要熟悉 JavaScript 和 React"

        mock_resume = MagicMock()
        mock_resume.processed_content = ""
        mock_resume.resume_text = ""

        with patch("src.data_access.repositories.job_repository") as mock_job_repo, \
             patch("src.data_access.repositories.resume_repository") as mock_resume_repo:
            mock_job_repo.get_by_id.return_value = mock_job
            mock_resume_repo.get_by_id.return_value = mock_resume

            result = self.tool._execute_sync(
                {"jd_id": 1, "resume_id": 1},
                context=MagicMock(db=MagicMock())
            )

            assert "questions" in result
            js_questions = [q for q in result["questions"] if "JavaScript" in q["question"]]
            assert len(js_questions) > 0

    def test_includes_behavioral_question(self):
        """Test that behavioral question is always included."""
        mock_job = MagicMock()
        mock_job.description = "后端开发工程师"

        mock_resume = MagicMock()
        mock_resume.processed_content = ""
        mock_resume.resume_text = ""

        with patch("src.data_access.repositories.job_repository") as mock_job_repo, \
             patch("src.data_access.repositories.resume_repository") as mock_resume_repo:
            mock_job_repo.get_by_id.return_value = mock_job
            mock_resume_repo.get_by_id.return_value = mock_resume

            result = self.tool._execute_sync(
                {"jd_id": 1, "resume_id": 1},
                context=MagicMock(db=MagicMock())
            )

            assert "questions" in result
            behavioral_questions = [q for q in result["questions"] if q["category"] == "行为"]
            assert len(behavioral_questions) > 0

    def test_includes_general_question(self):
        """Test that general interest question is always included."""
        mock_job = MagicMock()
        mock_job.description = "后端开发工程师"

        mock_resume = MagicMock()
        mock_resume.processed_content = ""
        mock_resume.resume_text = ""

        with patch("src.data_access.repositories.job_repository") as mock_job_repo, \
             patch("src.data_access.repositories.resume_repository") as mock_resume_repo:
            mock_job_repo.get_by_id.return_value = mock_job
            mock_resume_repo.get_by_id.return_value = mock_resume

            result = self.tool._execute_sync(
                {"jd_id": 1, "resume_id": 1},
                context=MagicMock(db=MagicMock())
            )

            assert "questions" in result
            general_questions = [q for q in result["questions"] if q["category"] == "通用"]
            assert len(general_questions) > 0

    def test_count_parameter_limits_questions(self):
        """Test that count parameter limits the number of questions returned."""
        mock_job = MagicMock()
        mock_job.description = "Python 工程师，熟悉 SQL 和 JavaScript"

        mock_resume = MagicMock()
        mock_resume.processed_content = ""
        mock_resume.resume_text = ""

        with patch("src.data_access.repositories.job_repository") as mock_job_repo, \
             patch("src.data_access.repositories.resume_repository") as mock_resume_repo:
            mock_job_repo.get_by_id.return_value = mock_job
            mock_resume_repo.get_by_id.return_value = mock_resume

            result = self.tool._execute_sync(
                {"jd_id": 1, "resume_id": 1, "count": 2},
                context=MagicMock(db=MagicMock())
            )

            assert len(result["questions"]) <= 2

    def test_input_schema_validation(self):
        """Test that input schema is correctly defined."""
        schema = GenerateInterviewQuestionsInput
        assert schema.model_fields["jd_id"].is_required()
        assert schema.model_fields["resume_id"].is_required()
        assert schema.model_fields["count"].default == 5
