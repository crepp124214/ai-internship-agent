# tests/unit/business_logic/jd/tools/test_analyze_resume_skills.py
import pytest
from unittest.mock import MagicMock, patch

from src.business_logic.jd.tools.analyze_resume_skills import AnalyzeResumeSkillsTool


class TestAnalyzeResumeSkillsTool:
    def setup_method(self):
        self.tool = AnalyzeResumeSkillsTool()

    def test_analyze_resume_returns_error_when_not_found(self):
        """Test that analyze_resume_skills returns error when resume doesn't exist."""
        with patch("src.data_access.repositories.resume_repository") as mock_repo:
            mock_repo.get_by_id.return_value = None

            result = self.tool._execute_sync(
                {"resume_id": 999},
                context=MagicMock(db=MagicMock())
            )

            assert "error" in result
            assert "Resume 999 not found" in result["error"]

    def test_analyze_resume_extracts_skills(self):
        """Test that skills are correctly extracted from resume text."""
        mock_resume = MagicMock()
        mock_resume.processed_content = "熟练使用 Python 和 JavaScript，熟悉 React 和 MySQL"
        mock_resume.resume_text = ""

        with patch("src.data_access.repositories.resume_repository") as mock_repo:
            mock_repo.get_by_id.return_value = mock_resume
            mock_context = MagicMock(db=MagicMock())

            result = self.tool._execute_sync(
                {"resume_id": 1},
                context=mock_context
            )

            assert result["resume_id"] == 1
            assert "skills" in result
            assert "编程语言" in result["skills"]
            assert "Python" in result["skills"]["编程语言"]
            assert "JavaScript" in result["skills"]["编程语言"]
            assert "框架" in result["skills"]
            assert "React" in result["skills"]["框架"]
            assert "数据库" in result["skills"]
            assert "MySQL" in result["skills"]["数据库"]

    def test_analyze_resume_falls_back_to_resume_text(self):
        """Test that resume_text is used when processed_content is empty."""
        mock_resume = MagicMock()
        mock_resume.processed_content = ""
        mock_resume.resume_text = "熟悉使用 Django 和 PostgreSQL，有 Docker 使用经验"

        with patch("src.data_access.repositories.resume_repository") as mock_repo:
            mock_repo.get_by_id.return_value = mock_resume
            mock_context = MagicMock(db=MagicMock())

            result = self.tool._execute_sync(
                {"resume_id": 1},
                context=mock_context
            )

            assert "框架" in result["skills"]
            assert "Django" in result["skills"]["框架"]
            assert "数据库" in result["skills"]
            assert "PostgreSQL" in result["skills"]["数据库"]
            assert "云服务" in result["skills"]
            assert "Docker" in result["skills"]["云服务"]

    def test_analyze_resume_counts_total_skills(self):
        """Test that total_count is correctly calculated."""
        mock_resume = MagicMock()
        mock_resume.processed_content = "Python, Java, React, MySQL, Docker"
        mock_resume.resume_text = ""

        with patch("src.data_access.repositories.resume_repository") as mock_repo:
            mock_repo.get_by_id.return_value = mock_resume
            mock_context = MagicMock(db=MagicMock())

            result = self.tool._execute_sync(
                {"resume_id": 1},
                context=mock_context
            )

            assert result["total_count"] == 5

    def test_analyze_resume_empty_skills(self):
        """Test with resume that has no matching skills."""
        mock_resume = MagicMock()
        mock_resume.processed_content = "这是一个没有任何技术技能的简历"
        mock_resume.resume_text = ""

        with patch("src.data_access.repositories.resume_repository") as mock_repo:
            mock_repo.get_by_id.return_value = mock_resume
            mock_context = MagicMock(db=MagicMock())

            result = self.tool._execute_sync(
                {"resume_id": 1},
                context=mock_context
            )

            assert result["skills"] == {}
            assert result["total_count"] == 0
