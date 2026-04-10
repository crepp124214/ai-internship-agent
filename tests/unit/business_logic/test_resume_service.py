import unittest
from types import SimpleNamespace
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from src.business_logic.resume.service import ResumeService
from src.presentation.schemas.resume import ResumeCreate, ResumeUpdate


class TestResumeService(unittest.IsolatedAsyncioTestCase):
    def setUp(self):
        self.resume_agent = MagicMock()
        self.resume_agent.extract_resume_summary = AsyncMock()
        self.resume_agent.suggest_resume_improvements = AsyncMock()
        self.service = ResumeService(resume_agent=self.resume_agent)
        self.db = MagicMock()
        self.current_user = SimpleNamespace(id=42)

    @pytest.mark.asyncio
    async def test_create_resume_populates_file_metadata_and_user_id(self):
        resume_data = ResumeCreate(
            title="My Resume",
            file_path="/uploads/candidate/Profile.V2.PDF",
        )

        with patch("src.business_logic.resume.service.resume_repository") as mock_repo:
            mock_resume = MagicMock()
            mock_resume.id = 7
            mock_resume.title = "My Resume"
            mock_repo.create.return_value = mock_resume

            result = await self.service.create_resume(
                self.db,
                self.current_user,
                resume_data,
            )

            assert result.id == 7
            mock_repo.create.assert_called_once()
            payload = mock_repo.create.call_args.args[1]
            assert payload["user_id"] == 42
            assert payload["title"] == "My Resume"
            assert payload["original_file_path"] == "/uploads/candidate/Profile.V2.PDF"
            assert payload["file_name"] == "Profile.V2.PDF"
            assert payload["file_type"] == "pdf"
            assert payload["processed_content"] == ""
            assert payload["resume_text"] == ""

    @pytest.mark.asyncio
    async def test_get_resume_is_scoped_to_current_user(self):
        with patch("src.business_logic.resume.service.resume_repository") as mock_repo:
            mock_repo.get_by_id_and_user_id.return_value = None

            result = await self.service.get_resume(self.db, self.current_user, 99)

            assert result is None
            mock_repo.get_by_id_and_user_id.assert_called_once_with(self.db, 99, 42)

    @pytest.mark.asyncio
    async def test_update_resume_uses_partial_payload_and_current_user_scope(self):
        resume_data = ResumeUpdate(
            title="Updated Resume",
            processed_content="processed",
        )

        with patch("src.business_logic.resume.service.resume_repository") as mock_repo:
            mock_resume = MagicMock()
            mock_resume.id = 99
            mock_resume.title = "Updated Resume"
            mock_repo.update_by_id_and_user_id.return_value = mock_resume

            result = await self.service.update_resume(
                self.db,
                self.current_user,
                99,
                resume_data,
            )

            assert result.id == 99
            mock_repo.update_by_id_and_user_id.assert_called_once_with(
                self.db,
                99,
                42,
                {
                    "title": "Updated Resume",
                    "processed_content": "processed",
                },
            )

    @pytest.mark.asyncio
    async def test_delete_resume_is_scoped_to_current_user(self):
        with patch("src.business_logic.resume.service.resume_repository") as mock_repo:
            mock_repo.delete_by_id_and_user_id.return_value = False

            result = await self.service.delete_resume(self.db, self.current_user, 99)

            assert result is False
            mock_repo.delete_by_id_and_user_id.assert_called_once_with(self.db, 99, 42)

    @pytest.mark.asyncio
    async def test_list_resumes_is_scoped_to_current_user(self):
        with patch("src.business_logic.resume.service.resume_repository") as mock_repo:
            mock_repo.get_all_by_user_id.return_value = []

            result = await self.service.get_resumes(self.db, self.current_user)

            assert result == []
            mock_repo.get_all_by_user_id.assert_called_once_with(self.db, 42)

    @pytest.mark.asyncio
    async def test_extract_resume_summary_prefers_processed_content(self):
        resume = SimpleNamespace(
            id=99,
            processed_content="Processed summary text",
            resume_text="Raw resume text",
        )

        with patch("src.business_logic.resume.service.resume_repository") as mock_repo:
            mock_repo.get_by_id_and_user_id.return_value = resume

            with patch("src.business_logic.resume.service.ResumeAgent") as MockResumeAgent:
                mock_agent = MagicMock()
                mock_agent.extract_resume_summary = AsyncMock(return_value={
                    "mode": "summary",
                    "content": "mock summary",
                    "provider": "zhipu",
                    "model": "glm-4",
                    "status": "success",
                    "fallback_used": False,
                })
                MockResumeAgent.return_value = mock_agent

                with patch("src.business_logic.user_llm_config_service.user_llm_config_service") as mock_ullcs:
                    mock_ullcs.get_config_for_agent.return_value = {
                        "provider": "zhipu",
                        "model": "glm-4",
                    }

                    result = await self.service.extract_resume_summary(
                        self.db,
                        self.current_user,
                        99,
                    )

                    assert result["mode"] == "summary"
                    mock_agent.extract_resume_summary.assert_awaited_once_with(
                        "Processed summary text",
                        target_role=None,
                    )

    @pytest.mark.asyncio
    async def test_generate_resume_summary_preview_delegates_to_existing_summary_flow(self):
        with patch.object(
            self.service,
            "extract_resume_summary",
            new=AsyncMock(return_value={"mode": "summary", "content": "preview"}),
        ) as mock_extract:
            result = await self.service.generate_resume_summary_preview(
                self.db,
                self.current_user,
                99,
                target_role="backend engineer",
            )

        assert result["content"] == "preview"
        mock_extract.assert_awaited_once_with(
            self.db,
            self.current_user,
            99,
            target_role="backend engineer",
        )

    @pytest.mark.asyncio
    async def test_suggest_resume_improvements_falls_back_to_resume_text(self):
        resume = SimpleNamespace(
            id=100,
            processed_content="",
            resume_text="Raw resume text",
        )

        with patch("src.business_logic.resume.service.resume_repository") as mock_repo:
            mock_repo.get_by_id_and_user_id.return_value = resume

            with patch("src.business_logic.resume.service.ResumeAgent") as MockResumeAgent:
                mock_agent = MagicMock()
                mock_agent.suggest_resume_improvements = AsyncMock(return_value={
                    "mode": "improvements",
                    "content": "mock improvements",
                    "provider": "zhipu",
                    "model": "glm-4",
                    "status": "success",
                    "fallback_used": False,
                })
                MockResumeAgent.return_value = mock_agent

                with patch("src.business_logic.user_llm_config_service.user_llm_config_service") as mock_ullcs:
                    mock_ullcs.get_config_for_agent.return_value = {
                        "provider": "zhipu",
                        "model": "glm-4",
                    }

                    result = await self.service.suggest_resume_improvements(
                        self.db,
                        self.current_user,
                        100,
                        target_role="backend engineer",
                    )

                    assert result["mode"] == "improvements"
                    mock_agent.suggest_resume_improvements.assert_awaited_once_with(
                        "Raw resume text",
                        target_role="backend engineer",
                    )

    @pytest.mark.asyncio
    async def test_generate_resume_improvements_preview_delegates_to_existing_improvement_flow(self):
        with patch.object(
            self.service,
            "suggest_resume_improvements",
            new=AsyncMock(return_value={"mode": "improvements", "content": "preview"}),
        ) as mock_suggest:
            result = await self.service.generate_resume_improvements_preview(
                self.db,
                self.current_user,
                100,
                target_role="backend engineer",
            )

        assert result["content"] == "preview"
        mock_suggest.assert_awaited_once_with(
            self.db,
            self.current_user,
            100,
            target_role="backend engineer",
        )

    @pytest.mark.asyncio
    async def test_extract_resume_summary_raises_when_both_text_sources_are_empty(self):
        resume = SimpleNamespace(
            id=101,
            processed_content=" ",
            resume_text=" ",
        )

        with patch("src.business_logic.resume.service.resume_repository") as mock_repo:
            mock_repo.get_by_id_and_user_id.return_value = resume

            with pytest.raises(ValueError, match="resume text is empty"):
                await self.service.extract_resume_summary(
                    self.db,
                    self.current_user,
                    101,
                )

    @pytest.mark.asyncio
    async def test_persist_resume_improvements_creates_resume_optimization_record(self):
        resume = SimpleNamespace(
            id=102,
            processed_content="Processed resume text",
            resume_text="Raw resume text",
        )
        optimization_result = {
            "mode": "improvements",
            "original_text": "Processed resume text",
            "optimized_text": "Add measurable impact to each bullet.",
            "optimization_type": "content",
            "keywords": "metrics, impact",
            "score": 92,
            "ai_suggestion": "Add measurable impact to each bullet.",
            "raw_content": "Summary: Add measurable impact to each bullet.",
            "provider": "mock",
            "model": "mock-model",
            "content": "Add measurable impact to each bullet.",
            "status": "success",
            "fallback_used": False,
        }
        persisted_optimization = SimpleNamespace(
            id=301,
            resume_id=102,
            mode="resume_improvements",
            original_text="Processed resume text",
            optimized_text="Add measurable impact to each bullet.",
            optimization_type="content",
            keywords="metrics, impact",
            score=92,
            ai_suggestion="Add measurable impact to each bullet.",
            raw_content="Summary: Add measurable impact to each bullet.",
            provider="mock",
            model="mock-model",
            status="success",
            fallback_used=False,
        )

        with patch("src.business_logic.resume.service.resume_repository") as mock_resume_repo, patch(
            "src.business_logic.resume.service.resume_optimization_repository",
            create=True,
        ) as mock_optimization_repo:
            mock_resume_repo.get_by_id_and_user_id.return_value = resume
            mock_optimization_repo.create.return_value = persisted_optimization

            with patch("src.business_logic.resume.service.ResumeAgent") as MockResumeAgent:
                mock_agent = MagicMock()
                mock_agent.suggest_resume_improvements = AsyncMock(return_value=optimization_result)
                MockResumeAgent.return_value = mock_agent

                with patch("src.business_logic.user_llm_config_service.user_llm_config_service") as mock_ullcs:
                    mock_ullcs.get_config_for_agent.return_value = {
                        "provider": "zhipu",
                        "model": "glm-4",
                    }

                    result = await self.service.persist_resume_improvements(
                        self.db,
                        self.current_user,
                        102,
                        target_role="backend engineer",
                    )

                    assert result is persisted_optimization
                    mock_agent.suggest_resume_improvements.assert_awaited_once_with(
                        "Processed resume text",
                        target_role="backend engineer",
                    )
                    mock_optimization_repo.create.assert_called_once()
                    payload = mock_optimization_repo.create.call_args.args[1]
                    assert payload == {
                        "resume_id": 102,
                        "mode": "resume_improvements",
                        "original_text": "Processed resume text",
                        "optimized_text": "Add measurable impact to each bullet.",
                        "optimization_type": "content",
                        "keywords": "metrics, impact",
                        "score": 92,
                        "ai_suggestion": "Add measurable impact to each bullet.",
                        "raw_content": "Summary: Add measurable impact to each bullet.",
                        "provider": "mock",
                        "model": "mock-model",
                        "status": "success",
                        "fallback_used": False,
                    }

    @pytest.mark.asyncio
    async def test_persist_resume_summary_creates_resume_summary_record(self):
        resume = SimpleNamespace(
            id=104,
            processed_content="Processed resume text",
            resume_text="Raw resume text",
        )
        summary_result = {
            "mode": "summary",
            "target_role": "backend engineer",
            "content": "Candidate has strong backend project experience.",
            "raw_content": "Summary: Candidate has strong backend project experience.",
            "provider": "mock",
            "model": "mock-model",
            "status": "success",
            "fallback_used": False,
        }
        persisted_summary = SimpleNamespace(
            id=302,
            resume_id=104,
            mode="resume_summary",
            original_text="Processed resume text",
            optimized_text="Candidate has strong backend project experience.",
            optimization_type="summary",
            keywords="backend engineer",
            score=None,
            ai_suggestion="Candidate has strong backend project experience.",
            raw_content="Summary: Candidate has strong backend project experience.",
            provider="mock",
            model="mock-model",
            status="success",
            fallback_used=False,
        )

        with patch("src.business_logic.resume.service.resume_repository") as mock_resume_repo, patch(
            "src.business_logic.resume.service.resume_optimization_repository",
            create=True,
        ) as mock_optimization_repo:
            mock_resume_repo.get_by_id_and_user_id.return_value = resume
            mock_optimization_repo.create.return_value = persisted_summary

            with patch("src.business_logic.resume.service.ResumeAgent") as MockResumeAgent:
                mock_agent = MagicMock()
                mock_agent.extract_resume_summary = AsyncMock(return_value=summary_result)
                MockResumeAgent.return_value = mock_agent

                with patch("src.business_logic.user_llm_config_service.user_llm_config_service") as mock_ullcs:
                    mock_ullcs.get_config_for_agent.return_value = {
                        "provider": "zhipu",
                        "model": "glm-4",
                    }

                    result = await self.service.persist_resume_summary(
                        self.db,
                        self.current_user,
                        104,
                        target_role="backend engineer",
                    )

                    assert result is persisted_summary
                    mock_agent.extract_resume_summary.assert_awaited_once_with(
                        "Processed resume text",
                        target_role="backend engineer",
                    )
                    payload = mock_optimization_repo.create.call_args.args[1]
                    assert payload == {
                        "resume_id": 104,
                        "original_text": "Processed resume text",
                        "optimized_text": "Candidate has strong backend project experience.",
                        "optimization_type": "summary",
                        "keywords": "backend engineer",
                        "score": None,
                        "ai_suggestion": "Candidate has strong backend project experience.",
                        "mode": "resume_summary",
                        "raw_content": "Summary: Candidate has strong backend project experience.",
                        "provider": "mock",
                        "model": "mock-model",
                        "status": "success",
                        "fallback_used": False,
                    }

    @pytest.mark.asyncio
    async def test_get_resume_optimizations_lists_records_for_current_user(self):
        resume = SimpleNamespace(
            id=103,
            processed_content="Processed resume text",
            resume_text="Raw resume text",
        )
        optimizations = [
            SimpleNamespace(
                id=401,
                resume_id=103,
                mode="resume_improvements",
                original_text="Processed resume text",
                optimized_text="Strengthen impact statements.",
                optimization_type="content",
                keywords="impact, verbs",
                score=91,
                ai_suggestion="Strengthen impact statements.",
                raw_content="Summary: Strengthen impact statements.",
                provider="mock",
                model="mock-model",
            ),
            SimpleNamespace(
                id=402,
                resume_id=103,
                mode="resume_improvements",
                original_text="Processed resume text",
                optimized_text="Improve keyword alignment.",
                optimization_type="keyword",
                keywords="python, fastapi",
                score=88,
                ai_suggestion="Improve keyword alignment.",
                raw_content="Summary: Improve keyword alignment.",
                provider="mock",
                model="mock-model",
            ),
        ]

        with patch("src.business_logic.resume.service.resume_repository") as mock_resume_repo, patch(
            "src.business_logic.resume.service.resume_optimization_repository",
            create=True,
        ) as mock_optimization_repo:
            mock_resume_repo.get_by_id_and_user_id.return_value = resume
            mock_optimization_repo.get_all_by_resume_id_and_mode.return_value = optimizations

            result = await self.service.get_resume_optimizations(self.db, self.current_user, 103)

            assert result == optimizations
            mock_resume_repo.get_by_id_and_user_id.assert_called_once_with(self.db, 103, 42)
            mock_optimization_repo.get_all_by_resume_id_and_mode.assert_called_once_with(
                self.db,
                103,
                "resume_improvements",
                42,
            )
            assert [item.mode for item in result] == ["resume_improvements", "resume_improvements"]
            assert [item.raw_content for item in result] == [
                "Summary: Strengthen impact statements.",
                "Summary: Improve keyword alignment.",
            ]
            assert [item.provider for item in result] == ["mock", "mock"]
            assert [item.model for item in result] == ["mock-model", "mock-model"]

    @pytest.mark.asyncio
    async def test_get_resume_optimization_history_delegates_to_existing_history_flow(self):
        optimizations = [SimpleNamespace(id=1), SimpleNamespace(id=2)]
        with patch.object(
            self.service,
            "get_resume_optimizations",
            new=AsyncMock(return_value=optimizations),
        ) as mock_history:
            result = await self.service.get_resume_optimization_history(
                self.db,
                self.current_user,
                103,
            )

        assert result == optimizations
        mock_history.assert_awaited_once_with(self.db, self.current_user, 103)

    @pytest.mark.asyncio
    async def test_get_resume_summaries_lists_only_summary_records_for_current_user(self):
        resume = SimpleNamespace(
            id=105,
            processed_content="Processed resume text",
            resume_text="Raw resume text",
        )
        summaries = [
            SimpleNamespace(
                id=501,
                resume_id=105,
                mode="resume_summary",
                original_text="Processed resume text",
                optimized_text="Summary one.",
                optimization_type="summary",
                keywords="backend engineer",
                score=None,
                ai_suggestion="Summary one.",
                raw_content="Summary raw one.",
                provider="mock",
                model="mock-model",
            ),
            SimpleNamespace(
                id=502,
                resume_id=105,
                mode="resume_summary",
                original_text="Processed resume text",
                optimized_text="Summary two.",
                optimization_type="summary",
                keywords="backend engineer",
                score=None,
                ai_suggestion="Summary two.",
                raw_content="Summary raw two.",
                provider="mock",
                model="mock-model",
            ),
        ]

        with patch("src.business_logic.resume.service.resume_repository") as mock_resume_repo, patch(
            "src.business_logic.resume.service.resume_optimization_repository",
            create=True,
        ) as mock_optimization_repo:
            mock_resume_repo.get_by_id_and_user_id.return_value = resume
            mock_optimization_repo.get_all_by_resume_id_and_mode.return_value = summaries

            result = await self.service.get_resume_summaries(self.db, self.current_user, 105)

            assert result == summaries
            mock_optimization_repo.get_all_by_resume_id_and_mode.assert_called_once_with(
                self.db,
                105,
                "resume_summary",
                42,
            )

    @pytest.mark.asyncio
    async def test_get_resume_summary_history_delegates_to_summary_history_flow(self):
        summaries = [SimpleNamespace(id=1), SimpleNamespace(id=2)]
        with patch.object(
            self.service,
            "get_resume_summaries",
            new=AsyncMock(return_value=summaries),
        ) as mock_history:
            result = await self.service.get_resume_summary_history(
                self.db,
                self.current_user,
                105,
            )

        assert result == summaries
        mock_history.assert_awaited_once_with(self.db, self.current_user, 105)

    def test_service_can_build_default_agent_from_config(self):
        with patch("src.business_logic.resume.service.ResumeAgent") as mock_agent_cls:
            mock_instance = MagicMock()
            mock_agent_cls.return_value = mock_instance

            service = ResumeService(
                resume_agent=None,
                resume_agent_config={"provider": "mock", "model": "mock-model"},
            )

        assert service.resume_agent is mock_instance
        mock_agent_cls.assert_called_once_with(
            config={"provider": "mock", "model": "mock-model"},
            allow_mock_fallback=True,
        )

    @pytest.mark.asyncio
    async def test_extract_resume_summary_uses_user_llm_config_when_available(self):
        """用户配置了 LLM 时，extract_resume_summary 应使用用户配置而非默认 mock。"""
        resume = SimpleNamespace(
            id=99,
            processed_content="Processed summary text",
            resume_text="Raw resume text",
        )
        user_id = 42

        mock_user_config = {
            "provider": "zhipu",
            "model": "glm-4.7",
            "api_key": "user-key",
            "base_url": None,
            "temperature": 0.7,
        }

        with patch("src.business_logic.resume.service.resume_repository") as mock_repo:
            mock_repo.get_by_id_and_user_id.return_value = resume

            with patch("src.business_logic.resume.service.ResumeAgent") as MockResumeAgent:
                mock_agent = MagicMock()
                mock_agent.config = mock_user_config
                mock_agent.extract_resume_summary = AsyncMock(return_value={
                    "mode": "summary",
                    "content": "mock summary",
                    "provider": "zhipu",
                    "model": "glm-4.7",
                    "status": "success",
                    "fallback_used": False,
                })
                MockResumeAgent.return_value = mock_agent

                with patch("src.business_logic.user_llm_config_service.user_llm_config_service") as mock_ullcs:
                    mock_ullcs.get_config_for_agent.return_value = mock_user_config

                    result = await self.service.extract_resume_summary(
                        self.db,
                        self.current_user,
                        99,
                    )

                    # 验证 ResumeAgent 被创建时传入了 user_id 和 user_llm_config
                    MockResumeAgent.assert_called_once_with(
                        user_id=user_id,
                        user_llm_config=mock_user_config,
                        allow_mock_fallback=True,
                    )
                    # 验证返回的 provider 和 model 来自用户配置
                    assert result["provider"] == "zhipu"
                    assert result["model"] == "glm-4.7"

    @pytest.mark.asyncio
    async def test_suggest_resume_improvements_uses_user_llm_config_when_available(self):
        """用户配置了 LLM 时，suggest_resume_improvements 应使用用户配置而非默认 mock。"""
        resume = SimpleNamespace(
            id=100,
            processed_content="Processed resume text",
            resume_text="Raw resume text",
        )
        user_id = 42

        mock_user_config = {
            "provider": "zhipu",
            "model": "glm-4.7",
            "api_key": "user-key",
            "base_url": None,
            "temperature": 0.7,
        }

        with patch("src.business_logic.resume.service.resume_repository") as mock_repo:
            mock_repo.get_by_id_and_user_id.return_value = resume

            with patch("src.business_logic.resume.service.ResumeAgent") as MockResumeAgent:
                mock_agent = MagicMock()
                mock_agent.config = mock_user_config
                mock_agent.suggest_resume_improvements = AsyncMock(return_value={
                    "mode": "improvements",
                    "content": "mock improvements",
                    "provider": "zhipu",
                    "model": "glm-4.7",
                    "status": "success",
                    "fallback_used": False,
                })
                MockResumeAgent.return_value = mock_agent

                with patch("src.business_logic.user_llm_config_service.user_llm_config_service") as mock_ullcs:
                    mock_ullcs.get_config_for_agent.return_value = mock_user_config

                    result = await self.service.suggest_resume_improvements(
                        self.db,
                        self.current_user,
                        100,
                        target_role="backend engineer",
                    )

                    MockResumeAgent.assert_called_once_with(
                        user_id=user_id,
                        user_llm_config=mock_user_config,
                        allow_mock_fallback=True,
                    )
                    assert result["provider"] == "zhipu"
                    assert result["model"] == "glm-4.7"

    @pytest.mark.asyncio
    async def test_extract_resume_summary_fallback_returns_mock_content_on_api_failure(self):
        """当 LLM API 调用失败且 allow_mock_fallback=True 时，应返回 mock 内容而非抛出异常。"""
        resume = SimpleNamespace(
            id=99,
            processed_content="Processed summary text",
            resume_text="Raw resume text",
        )

        with patch("src.business_logic.resume.service.resume_repository") as mock_repo:
            mock_repo.get_by_id_and_user_id.return_value = resume

            with patch("src.business_logic.resume.service.ResumeAgent") as MockResumeAgent:
                mock_agent = MagicMock()
                # 模拟 fallback 场景：agent 返回 mock 内容
                mock_agent.extract_resume_summary = AsyncMock(return_value={
                    "mode": "summary",
                    "content": "mock-summary-content",
                    "provider": "mock",
                    "model": "mock-model",
                    "status": "fallback",
                    "fallback_used": True,
                })
                mock_agent.config = {"provider": "zhipu", "model": "glm-4"}

                MockResumeAgent.return_value = mock_agent

                with patch("src.business_logic.user_llm_config_service.user_llm_config_service") as mock_ullcs:
                    mock_ullcs.get_config_for_agent.return_value = {
                        "provider": "zhipu",
                        "model": "glm-4",
                    }

                    result = await self.service.extract_resume_summary(
                        self.db,
                        self.current_user,
                        99,
                    )

                    # 验证返回了 fallback 的 mock 结果
                    assert result["provider"] == "mock"
                    assert result["fallback_used"] is True
                    assert result["status"] == "fallback"

    @pytest.mark.asyncio
    async def test_persist_resume_improvements_uses_fallback_provider_from_agent_result(self):
        """当 extract_resume_summary fallback 返回 mock 内容时，persist_resume_improvements 应使用 agent 结果中的 provider。"""
        resume = SimpleNamespace(
            id=102,
            processed_content="Processed resume text",
            resume_text="Raw resume text",
        )

        with patch("src.business_logic.resume.service.resume_repository") as mock_repo, patch(
            "src.business_logic.resume.service.resume_optimization_repository",
            create=True,
        ) as mock_optimization_repo:
            mock_repo.get_by_id_and_user_id.return_value = resume
            persisted_optimization = SimpleNamespace(
                id=301,
                resume_id=102,
                provider="mock",
                model="mock-model",
                status="fallback",
                fallback_used=True,
            )
            mock_optimization_repo.create.return_value = persisted_optimization

            with patch("src.business_logic.resume.service.ResumeAgent") as MockResumeAgent:
                mock_agent = MagicMock()
                mock_agent.suggest_resume_improvements = AsyncMock(return_value={
                    "mode": "improvements",
                    "content": "mock improvements",
                    "raw_content": "mock-raw-content",
                    "provider": "mock",
                    "model": "mock-model",
                    "status": "fallback",
                    "fallback_used": True,
                })
                mock_agent.config = {"provider": "zhipu", "model": "glm-4"}
                MockResumeAgent.return_value = mock_agent

                with patch("src.business_logic.user_llm_config_service.user_llm_config_service") as mock_ullcs:
                    mock_ullcs.get_config_for_agent.return_value = {
                        "provider": "zhipu",
                        "model": "glm-4",
                    }

                    result = await self.service.persist_resume_improvements(
                        self.db,
                        self.current_user,
                        102,
                        target_role="backend engineer",
                    )

                    mock_optimization_repo.create.assert_called_once()
                    payload = mock_optimization_repo.create.call_args.args[1]
                    # provider 必须来自 agent 结果（fallback 时为 "mock"）
                    assert payload["provider"] == "mock"
                    assert payload["model"] == "mock-model"
                    assert payload["status"] == "fallback"
                    assert payload["fallback_used"] is True
