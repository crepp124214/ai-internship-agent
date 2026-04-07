# tests/unit/business_logic/jd/tools/test_update_resume.py
import pytest
from unittest.mock import MagicMock, patch

from src.business_logic.jd.tools.update_resume import UpdateResumeTool, UpdateResumeInput


class TestUpdateResumeTool:
    def setup_method(self):
        self.tool = UpdateResumeTool()

    def test_update_resume_returns_error_when_not_found(self):
        """Test that update_resume returns error when resume doesn't exist."""
        with patch("src.data_access.repositories.resume_repository") as mock_repo:
            mock_repo.get_by_id.return_value = None

            result = self.tool._execute_sync(
                {"resume_id": 999},
                context=MagicMock(db=MagicMock())
            )

            assert "error" in result
            assert "Resume 999 not found" in result["error"]

    def test_update_resume_partial_update(self):
        """Test partial update of resume fields."""
        mock_resume = MagicMock()
        mock_resume.title = "Old Title"
        mock_resume.resume_text = "Old text"
        mock_resume.processed_content = None

        with patch("src.data_access.repositories.resume_repository") as mock_repo:
            mock_repo.get_by_id.return_value = mock_resume
            mock_db = MagicMock()
            mock_context = MagicMock(db=mock_db)

            result = self.tool._execute_sync(
                {"resume_id": 1, "title": "New Title"},
                context=mock_context
            )

            assert result["resume_id"] == 1
            assert result["updated"] is True
            assert result["title"] == "New Title"
            assert mock_resume.title == "New Title"
            mock_db.commit.assert_called_once()
            mock_db.refresh.assert_called_once()

    def test_update_resume_updates_all_fields(self):
        """Test updating all fields of resume."""
        mock_resume = MagicMock()
        mock_resume.title = "Old"
        mock_resume.resume_text = "Old text"
        mock_resume.processed_content = None

        with patch("src.data_access.repositories.resume_repository") as mock_repo:
            mock_repo.get_by_id.return_value = mock_resume
            mock_db = MagicMock()
            mock_context = MagicMock(db=mock_db)

            result = self.tool._execute_sync(
                {
                    "resume_id": 1,
                    "title": "New Title",
                    "resume_text": "New resume text",
                    "processed_content": "Processed content"
                },
                context=mock_context
            )

            assert result["updated"] is True
            assert mock_resume.title == "New Title"
            assert mock_resume.resume_text == "New resume text"
            assert mock_resume.processed_content == "Processed content"

    def test_update_resume_only_title(self):
        """Test updating only the title, leaving other fields unchanged."""
        mock_resume = MagicMock()
        mock_resume.title = "Original"
        mock_resume.resume_text = "Original text"
        mock_resume.processed_content = "Original processed"

        with patch("src.data_access.repositories.resume_repository") as mock_repo:
            mock_repo.get_by_id.return_value = mock_resume
            mock_db = MagicMock()
            mock_context = MagicMock(db=mock_db)

            result = self.tool._execute_sync(
                {"resume_id": 1, "title": "Updated Title"},
                context=mock_context
            )

            assert mock_resume.title == "Updated Title"
            assert mock_resume.resume_text == "Original text"
            assert mock_resume.processed_content == "Original processed"
