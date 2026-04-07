import pytest
from unittest.mock import MagicMock, patch

from src.business_logic.jd.tools.compare_resumes import CompareResumesTool, CompareResumesInput


class TestCompareResumesTool:
    def setup_method(self):
        self.tool = CompareResumesTool()

    def test_compare_resumes_returns_error_when_first_not_found(self):
        """Test that compare_resumes returns error when first resume doesn't exist."""
        with patch("src.data_access.repositories.resume_repository") as mock_repo:
            mock_repo.get_by_id.return_value = None

            result = self.tool._execute_sync(
                {"resume_id_1": 999, "resume_id_2": 1},
                context=MagicMock(db=MagicMock())
            )

            assert "error" in result
            assert "Resume 999 not found" in result["error"]

    def test_compare_resumes_returns_error_when_second_not_found(self):
        """Test that compare_resumes returns error when second resume doesn't exist."""
        mock_resume1 = MagicMock()
        mock_resume1.processed_content = "Resume 1 content"

        with patch("src.data_access.repositories.resume_repository") as mock_repo:
            mock_repo.get_by_id.side_effect = [mock_resume1, None]

            result = self.tool._execute_sync(
                {"resume_id_1": 1, "resume_id_2": 999},
                context=MagicMock(db=MagicMock())
            )

            assert "error" in result
            assert "Resume 999 not found" in result["error"]

    def test_compare_resumes_identifies_added_lines(self):
        """Test that compare_resumes correctly identifies added lines."""
        mock_resume1 = MagicMock()
        mock_resume1.processed_content = "Line A\nLine B\nLine C"
        mock_resume1.resume_text = ""

        mock_resume2 = MagicMock()
        mock_resume2.processed_content = "Line A\nLine B\nLine C\nLine D\nLine E"
        mock_resume2.resume_text = ""

        with patch("src.data_access.repositories.resume_repository") as mock_repo:
            mock_repo.get_by_id.side_effect = [mock_resume1, mock_resume2]
            mock_context = MagicMock(db=MagicMock())

            result = self.tool._execute_sync(
                {"resume_id_1": 1, "resume_id_2": 2},
                context=mock_context
            )

            assert result["resume_id_1"] == 1
            assert result["resume_id_2"] == 2
            assert result["added_count"] == 2
            assert result["removed_count"] == 0
            assert result["common_count"] == 3
            assert "Line D" in result["added_lines"]
            assert "Line E" in result["added_lines"]

    def test_compare_resumes_identifies_removed_lines(self):
        """Test that compare_resumes correctly identifies removed lines."""
        mock_resume1 = MagicMock()
        mock_resume1.processed_content = "Line A\nLine B\nLine C\nLine D"
        mock_resume1.resume_text = ""

        mock_resume2 = MagicMock()
        mock_resume2.processed_content = "Line A\nLine B"
        mock_resume2.resume_text = ""

        with patch("src.data_access.repositories.resume_repository") as mock_repo:
            mock_repo.get_by_id.side_effect = [mock_resume1, mock_resume2]
            mock_context = MagicMock(db=MagicMock())

            result = self.tool._execute_sync(
                {"resume_id_1": 1, "resume_id_2": 2},
                context=mock_context
            )

            assert result["added_count"] == 0
            assert result["removed_count"] == 2
            assert result["common_count"] == 2
            assert "Line C" in result["removed_lines"]
            assert "Line D" in result["removed_lines"]

    def test_compare_resumes_identifies_common_lines(self):
        """Test that compare_resumes correctly identifies common lines."""
        mock_resume1 = MagicMock()
        mock_resume1.processed_content = "Line A\nLine B\nLine C"
        mock_resume1.resume_text = ""

        mock_resume2 = MagicMock()
        mock_resume2.processed_content = "Line A\nLine B\nLine D"
        mock_resume2.resume_text = ""

        with patch("src.data_access.repositories.resume_repository") as mock_repo:
            mock_repo.get_by_id.side_effect = [mock_resume1, mock_resume2]
            mock_context = MagicMock(db=MagicMock())

            result = self.tool._execute_sync(
                {"resume_id_1": 1, "resume_id_2": 2},
                context=mock_context
            )

            assert result["added_count"] == 1
            assert result["removed_count"] == 1
            assert result["common_count"] == 2

    def test_compare_resumes_handles_empty_content(self):
        """Test that compare_resumes handles empty resume content."""
        mock_resume1 = MagicMock()
        mock_resume1.processed_content = None
        mock_resume1.resume_text = ""

        mock_resume2 = MagicMock()
        mock_resume2.processed_content = None
        mock_resume2.resume_text = ""

        with patch("src.data_access.repositories.resume_repository") as mock_repo:
            mock_repo.get_by_id.side_effect = [mock_resume1, mock_resume2]
            mock_context = MagicMock(db=MagicMock())

            result = self.tool._execute_sync(
                {"resume_id_1": 1, "resume_id_2": 2},
                context=mock_context
            )

            # Empty string "" splits to [""] (one empty string element)
            # So common_count is 1 (both have one empty string line)
            assert result["added_count"] == 0
            assert result["removed_count"] == 0
            assert result["common_count"] == 1

    def test_compare_resumes_limits_output_lines(self):
        """Test that compare_resumes limits added_lines and removed_lines to 10 items."""
        lines = ["Line {}".format(i) for i in range(20)]
        mock_resume1 = MagicMock()
        mock_resume1.processed_content = "\n".join(lines[:10])
        mock_resume1.resume_text = ""

        mock_resume2 = MagicMock()
        mock_resume2.processed_content = "\n".join(lines[10:])
        mock_resume2.resume_text = ""

        with patch("src.data_access.repositories.resume_repository") as mock_repo:
            mock_repo.get_by_id.side_effect = [mock_resume1, mock_resume2]
            mock_context = MagicMock(db=MagicMock())

            result = self.tool._execute_sync(
                {"resume_id_1": 1, "resume_id_2": 2},
                context=mock_context
            )

            assert len(result["added_lines"]) == 10
            assert len(result["removed_lines"]) == 10
