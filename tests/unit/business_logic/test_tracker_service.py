"""Tracker service tests."""

from types import SimpleNamespace
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

import src.business_logic.tracker.service as tracker_service_module
from src.business_logic.tracker.service import TrackerService
from src.presentation.schemas.tracker import ApplicationTrackerCreate, ApplicationTrackerUpdate


class TestTrackerService:
    def setup_method(self):
        self.service = TrackerService()
        self.db = MagicMock()

    @pytest.mark.asyncio
    async def test_create_application_uses_current_user_id(self):
        application_data = ApplicationTrackerCreate(
            job_id=11,
            resume_id=22,
            status="applied",
            notes="first application",
        )
        mock_application = SimpleNamespace(id=1, user_id=7, job_id=11, resume_id=22, status="applied")

        with patch("src.business_logic.tracker.service.tracker_repository") as mock_repo:
            mock_repo.create.return_value = mock_application

            result = await self.service.create_application(self.db, application_data, 7)

            assert result == mock_application
            payload = mock_repo.create.call_args.args[1]
            assert payload["user_id"] == 7
            assert payload["job_id"] == 11
            assert payload["resume_id"] == 22
            assert payload["status"] == "applied"
            assert "status_updated_at" in payload

    @pytest.mark.asyncio
    async def test_get_applications_by_status_uses_repository_query(self):
        with patch("src.business_logic.tracker.service.tracker_repository") as mock_repo:
            mock_repo.get_by_user_id_and_status.return_value = []

            result = await self.service.get_applications_by_status(self.db, 7, "applied")

            assert result == []
            mock_repo.get_by_user_id_and_status.assert_called_once_with(self.db, 7, "applied")

    @pytest.mark.asyncio
    async def test_update_application_refreshes_status_timestamp_when_status_changes(self):
        existing_application = SimpleNamespace(id=1, user_id=7, status="applied")
        updated_application = SimpleNamespace(id=1, user_id=7, status="interviewing")
        application_data = ApplicationTrackerUpdate(status="interviewing", notes="updated")

        with patch("src.business_logic.tracker.service.tracker_repository") as mock_repo:
            mock_repo.get_by_id_and_user_id.return_value = existing_application
            mock_repo.update_by_id_and_user_id.return_value = updated_application

            result = await self.service.update_application(self.db, 1, application_data, 7)

            assert result == updated_application
            payload = mock_repo.update_by_id_and_user_id.call_args.args[3]
            assert payload["status"] == "interviewing"
            assert payload["notes"] == "updated"
            assert "status_updated_at" in payload

    @pytest.mark.asyncio
    async def test_update_application_keeps_status_timestamp_when_status_stays_same(self):
        existing_application = SimpleNamespace(id=1, user_id=7, status="applied")
        updated_application = SimpleNamespace(id=1, user_id=7, status="applied")
        application_data = ApplicationTrackerUpdate(notes="updated note")

        with patch("src.business_logic.tracker.service.tracker_repository") as mock_repo:
            mock_repo.get_by_id_and_user_id.return_value = existing_application
            mock_repo.update_by_id_and_user_id.return_value = updated_application

            result = await self.service.update_application(self.db, 1, application_data, 7)

            assert result == updated_application
            payload = mock_repo.update_by_id_and_user_id.call_args.args[3]
            assert payload["notes"] == "updated note"
            assert "status_updated_at" not in payload

    @pytest.mark.asyncio
    async def test_generate_application_advice_returns_structured_result(self, monkeypatch):
        application = SimpleNamespace(
            id=31,
            user_id=7,
            job_id=11,
            resume_id=22,
            status="applied",
            notes="Applied yesterday",
        )
        job = SimpleNamespace(
            id=11,
            title="Backend Intern",
            company="Test Co",
            location="Remote",
            description="Build APIs",
            requirements="Python, FastAPI",
        )
        resume = SimpleNamespace(id=22, processed_content="Built APIs with FastAPI.", resume_text="")
        tracker_agent = MagicMock()
        tracker_agent.config = {"provider": "mock", "model": "mock-model"}
        tracker_agent.advise_next_steps = AsyncMock(
            return_value={
                "mode": "tracker_advice",
                "summary": "Strong fit with some follow-up risk.",
                "next_steps": ["Follow up with the recruiter.", "Prepare evidence of impact."],
                "risks": ["No recent status update."],
                "raw_content": "Summary: Strong fit with some follow-up risk.",
            }
        )

        monkeypatch.setattr(tracker_service_module, "tracker_repository", MagicMock(), raising=False)
        monkeypatch.setattr(tracker_service_module, "job_repository", MagicMock(), raising=False)
        monkeypatch.setattr(tracker_service_module, "resume_repository", MagicMock(), raising=False)

        tracker_service_module.tracker_repository.get_by_id_and_user_id.return_value = application
        tracker_service_module.job_repository.get_by_id.return_value = job
        tracker_service_module.resume_repository.get_by_id_and_user_id.return_value = resume

        service = TrackerService(tracker_agent=tracker_agent)
        result = await service.generate_application_advice(self.db, 31, 7)

        assert result["mode"] == "tracker_advice"
        assert result["application_id"] == 31
        assert result["summary"] == "Strong fit with some follow-up risk."
        assert result["next_steps"] == [
            "Follow up with the recruiter.",
            "Prepare evidence of impact.",
        ]
        assert result["risks"] == ["No recent status update."]
        assert result["provider"] == "mock"
        assert result["model"] == "mock-model"
        tracker_agent.advise_next_steps.assert_awaited_once()

    @pytest.mark.asyncio
    async def test_generate_tracker_advice_preview_delegates_to_existing_advice_flow(self):
        with patch.object(
            self.service,
            "generate_application_advice",
            new=AsyncMock(return_value={"summary": "Do next step"}),
        ) as mock_generate:
            result = await self.service.generate_tracker_advice_preview(self.db, 31, 7)

        assert result == {"summary": "Do next step"}
        mock_generate.assert_awaited_once_with(self.db, 31, 7)

    @pytest.mark.asyncio
    async def test_generate_application_advice_raises_when_application_missing(self, monkeypatch):
        monkeypatch.setattr(tracker_service_module, "tracker_repository", MagicMock(), raising=False)
        tracker_service_module.tracker_repository.get_by_id_and_user_id.return_value = None

        service = TrackerService()

        with pytest.raises(ValueError, match="application not found"):
            await service.generate_application_advice(self.db, 31, 7)

    @pytest.mark.asyncio
    async def test_generate_application_advice_raises_when_required_context_missing(self, monkeypatch):
        application = SimpleNamespace(
            id=31,
            user_id=7,
            job_id=11,
            resume_id=22,
            status="applied",
            notes="Applied yesterday",
        )

        monkeypatch.setattr(tracker_service_module, "tracker_repository", MagicMock(), raising=False)
        monkeypatch.setattr(tracker_service_module, "job_repository", MagicMock(), raising=False)
        monkeypatch.setattr(tracker_service_module, "resume_repository", MagicMock(), raising=False)
        tracker_service_module.tracker_repository.get_by_id_and_user_id.return_value = application
        tracker_service_module.job_repository.get_by_id.return_value = None
        tracker_service_module.resume_repository.get_by_id_and_user_id.return_value = None

        service = TrackerService()

        with pytest.raises(ValueError, match="required context is missing"):
            await service.generate_application_advice(self.db, 31, 7)

    @pytest.mark.asyncio
    async def test_persist_application_advice_creates_record(self, monkeypatch):
        application = SimpleNamespace(id=31, user_id=7, job_id=11, resume_id=22)
        advice_record = SimpleNamespace(id=501, application_id=31)
        tracker_agent = MagicMock()
        tracker_agent.config = {"provider": "mock", "model": "mock-model"}
        tracker_agent.advise_next_steps = AsyncMock(
            return_value={
                "mode": "tracker_advice",
                "summary": "Follow up soon.",
                "next_steps": ["Send recruiter follow-up"],
                "risks": ["No response yet"],
                "raw_content": "Summary: Follow up soon.",
            }
        )

        monkeypatch.setattr(tracker_service_module, "tracker_repository", MagicMock(), raising=False)
        monkeypatch.setattr(tracker_service_module, "job_repository", MagicMock(), raising=False)
        monkeypatch.setattr(tracker_service_module, "resume_repository", MagicMock(), raising=False)
        monkeypatch.setattr(tracker_service_module, "tracker_advice_repository", MagicMock(), raising=False)
        tracker_service_module.tracker_repository.get_by_id_and_user_id.return_value = application
        tracker_service_module.job_repository.get_by_id.return_value = SimpleNamespace(
            id=11,
            title="Backend Intern",
            company="Test Co",
            location="Remote",
            description="Build APIs",
            requirements="Python, FastAPI",
        )
        tracker_service_module.resume_repository.get_by_id_and_user_id.return_value = SimpleNamespace(
            id=22,
            processed_content="Built APIs with FastAPI.",
            resume_text="",
        )
        tracker_service_module.tracker_advice_repository.create.return_value = advice_record

        service = TrackerService(tracker_agent=tracker_agent)
        result = await service.persist_application_advice(self.db, 31, 7)

        assert result is advice_record
        payload = tracker_service_module.tracker_advice_repository.create.call_args.args[1]
        assert payload["application_id"] == 31
        assert payload["mode"] == "tracker_advice"
        assert payload["summary"] == "Follow up soon."
        assert payload["next_steps"] == ["Send recruiter follow-up"]
        assert payload["risks"] == ["No response yet"]
        assert payload["provider"] == "mock"
        assert payload["model"] == "mock-model"

    @pytest.mark.asyncio
    async def test_persist_application_advice_raises_for_unowned_application(self):
        service = TrackerService()
        with patch("src.business_logic.tracker.service.tracker_repository") as mock_repo:
            mock_repo.get_by_id_and_user_id.return_value = None
            with pytest.raises(ValueError, match="application not found"):
                await service.persist_application_advice(self.db, 99, 7)

    @pytest.mark.asyncio
    async def test_get_application_advice_history_returns_scoped_records(self):
        service = TrackerService()
        history = [SimpleNamespace(id=1), SimpleNamespace(id=2)]
        with patch("src.business_logic.tracker.service.tracker_repository") as mock_tracker_repo, patch(
            "src.business_logic.tracker.service.tracker_advice_repository"
        ) as mock_advice_repo:
            mock_tracker_repo.get_by_id_and_user_id.return_value = SimpleNamespace(id=31)
            mock_advice_repo.get_all_by_application_id_and_user_id.return_value = history

            result = await service.get_application_advice_history(self.db, 31, 7)

            assert result == history
            mock_advice_repo.get_all_by_application_id_and_user_id.assert_called_once_with(
                self.db,
                31,
                7,
            )

    @pytest.mark.asyncio
    async def test_get_tracker_advice_history_delegates_to_existing_history_flow(self):
        history = [SimpleNamespace(id=1), SimpleNamespace(id=2)]
        with patch.object(
            self.service,
            "get_application_advice_history",
            new=AsyncMock(return_value=history),
        ) as mock_history:
            result = await self.service.get_tracker_advice_history(self.db, 31, 7)

        assert result == history
        mock_history.assert_awaited_once_with(self.db, 31, 7)
