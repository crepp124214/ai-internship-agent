import pytest
from unittest.mock import MagicMock, patch

from src.business_logic.jd.tools.format_resume import FormatResumeTool, FormatResumeInput


class TestFormatResumeTool:
    def setup_method(self):
        self.tool = FormatResumeTool()

    def test_format_resume_returns_error_when_not_found(self):
        """Test that format_resume returns error when resume doesn't exist."""
        with patch("src.data_access.repositories.resume_repository") as mock_repo:
            mock_repo.get_by_id.return_value = None

            result = self.tool._execute_sync(
                {"resume_id": 999},
                context=MagicMock(db=MagicMock())
            )

            assert "error" in result
            assert "Resume 999 not found" in result["error"]

    def test_format_resume_parses_markdown_sections(self):
        """Test that format_resume correctly parses markdown sections."""
        mock_resume = MagicMock()
        mock_resume.title = "Software Engineer Resume"
        mock_resume.processed_content = """# 个人信息
- 姓名：张三
- 邮箱：zhang@example.com

# 教育背景
- 北京大学 计算机科学 硕士

# 工作经历
- 公司A 高级工程师
- 公司B 技术总监
"""

        with patch("src.data_access.repositories.resume_repository") as mock_repo:
            mock_repo.get_by_id.return_value = mock_resume
            mock_context = MagicMock(db=MagicMock())

            result = self.tool._execute_sync(
                {"resume_id": 1},
                context=mock_context
            )

            assert result["resume_id"] == 1
            assert result["title"] == "Software Engineer Resume"
            assert result["section_count"] == 3
            assert "个人信息" in result["sections"]
            assert "教育背景" in result["sections"]
            assert "工作经历" in result["sections"]

    def test_format_resume_uses_resume_text_when_no_processed_content(self):
        """Test that format_resume falls back to resume_text when processed_content is empty."""
        mock_resume = MagicMock()
        mock_resume.title = "Resume"
        mock_resume.processed_content = None
        mock_resume.resume_text = """# 技能
- Python
- JavaScript

# 项目
- 项目A
"""

        with patch("src.data_access.repositories.resume_repository") as mock_repo:
            mock_repo.get_by_id.return_value = mock_resume
            mock_context = MagicMock(db=MagicMock())

            result = self.tool._execute_sync(
                {"resume_id": 1},
                context=mock_context
            )

            assert result["section_count"] == 2
            assert "技能" in result["sections"]
            assert "项目" in result["sections"]

    def test_format_resume_handles_empty_content(self):
        """Test that format_resume handles empty resume content."""
        mock_resume = MagicMock()
        mock_resume.title = "Empty Resume"
        mock_resume.processed_content = ""
        mock_resume.resume_text = ""

        with patch("src.data_access.repositories.resume_repository") as mock_repo:
            mock_repo.get_by_id.return_value = mock_resume
            mock_context = MagicMock(db=MagicMock())

            result = self.tool._execute_sync(
                {"resume_id": 1},
                context=mock_context
            )

            assert result["resume_id"] == 1
            assert result["title"] == "Empty Resume"
            assert result["section_count"] == 1
            assert "个人信息" in result["sections"]

    def test_format_resume_deduces_first_section_name(self):
        """Test that format_resume uses default section name for content before first header."""
        mock_resume = MagicMock()
        mock_resume.title = "Resume"
        mock_resume.processed_content = """姓名：李四
邮箱：li@example.com

# 技能
- Python
"""

        with patch("src.data_access.repositories.resume_repository") as mock_repo:
            mock_repo.get_by_id.return_value = mock_resume
            mock_context = MagicMock(db=MagicMock())

            result = self.tool._execute_sync(
                {"resume_id": 1},
                context=mock_context
            )

            assert result["section_count"] == 2
            assert "个人信息" in result["sections"]
            assert "技能" in result["sections"]
