"""
Job service unit tests.
"""

import pytest
from types import SimpleNamespace
from unittest.mock import AsyncMock, MagicMock, patch

from src.business_logic.job.service import JobService
from src.presentation.schemas.job import JobUpdate


class TestJobService:
    def setup_method(self):
        self.service = JobService()
        self.mock_db = MagicMock()

    @pytest.mark.asyncio
    async def test_search_jobs_filters_by_keyword_and_location(self):
        job_beijing = MagicMock()
        job_beijing.title = "Python Developer Intern"
        job_beijing.company = "Alpha Tech"
        job_beijing.location = "Beijing"
        job_beijing.description = "Build backend APIs with FastAPI"
        job_beijing.requirements = "Python, SQL"
        job_beijing.tags = "python,backend"

        job_keyword_only = MagicMock()
        job_keyword_only.title = "Python Data Intern"
        job_keyword_only.company = "Beta Labs"
        job_keyword_only.location = "Shanghai"
        job_keyword_only.description = "Data pipelines"
        job_keyword_only.requirements = "Python, pandas"
        job_keyword_only.tags = "data"

        job_location_only = MagicMock()
        job_location_only.title = "Java Intern"
        job_location_only.company = "Gamma Studio"
        job_location_only.location = "Beijing"
        job_location_only.description = "Android development"
        job_location_only.requirements = "Java"
        job_location_only.tags = "mobile"

        with patch("src.business_logic.job.service.job_repository") as mock_repo:
            mock_repo.get_all.return_value = [
                job_beijing,
                job_keyword_only,
                job_location_only,
            ]

            result = await self.service.search_jobs(
                self.mock_db,
                keyword="python",
                location="beijing",
            )

            assert result == [job_beijing]
            mock_repo.get_all.assert_called_once_with(self.mock_db)

    @pytest.mark.asyncio
    async def test_update_job_accepts_partial_payload(self):
        job_id = 1
        update_data = JobUpdate(is_active=False)

        updated_job = MagicMock()
        updated_job.id = job_id
        updated_job.is_active = False

        with patch("src.business_logic.job.service.job_repository") as mock_repo:
            mock_repo.update.return_value = updated_job

            result = await self.service.update_job(self.mock_db, job_id, update_data)

            assert result is not None
            assert result.is_active is False
            mock_repo.update.assert_called_once_with(
                self.mock_db,
                job_id,
                {"is_active": False},
            )

    @pytest.mark.asyncio
    async def test_match_job_to_resume_returns_structured_result(self):
        job = SimpleNamespace(id=11, title="Backend Intern", company="Test Co")
        resume = SimpleNamespace(id=7, user_id=55, processed_content="Built APIs", resume_text="")
        service = self.service

        with patch("src.business_logic.job.service.job_repository", create=True) as mock_job_repo:
            with patch("src.business_logic.job.service.resume_repository", create=True) as mock_resume_repo:
                with patch("src.business_logic.job.service.JobAgent") as MockJobAgent:
                    mock_job_repo.get_by_id.return_value = job
                    mock_resume_repo.get_by_id_and_user_id.return_value = resume

                    mock_agent = MagicMock()
                    mock_agent.match_job_to_resume = AsyncMock(return_value={
                        "mode": "job_match",
                        "score": 85,
                        "feedback": "Good fit",
                        "raw_content": "Score: 85",
                    })
                    mock_agent.config = {"provider": "mock", "model": "mock-model"}
                    MockJobAgent.return_value = mock_agent

                    result = await service.match_job_to_resume(
                        self.mock_db,
                        job_id=11,
                        resume_id=7,
                        current_user_id=55,
                    )

        assert result["mode"] == "job_match"
        assert result["job_id"] == 11
        assert result["resume_id"] == 7
        assert "score" in result
        assert "feedback" in result

    @pytest.mark.asyncio
    async def test_generate_job_match_preview_delegates_to_existing_match_flow(self):
        with patch.object(
            self.service,
            "match_job_to_resume",
            new=AsyncMock(return_value={"mode": "job_match", "score": 90, "feedback": "fit"}),
        ) as mock_match:
            result = await self.service.generate_job_match_preview(
                self.mock_db,
                job_id=11,
                resume_id=7,
                current_user_id=55,
            )

        assert result["score"] == 90
        mock_match.assert_awaited_once_with(
            self.mock_db,
            job_id=11,
            resume_id=7,
            current_user_id=55,
        )

    @pytest.mark.asyncio
    async def test_match_job_to_resume_returns_404_for_missing_job(self):
        service = self.service

        with patch("src.business_logic.job.service.job_repository", create=True) as mock_job_repo:
            with patch("src.business_logic.job.service.resume_repository", create=True) as mock_resume_repo:
                mock_job_repo.get_by_id.return_value = None
                mock_resume_repo.get_by_id_and_user_id.return_value = SimpleNamespace(
                    id=7,
                    user_id=55,
                    processed_content="Built APIs",
                    resume_text="",
                )

                with pytest.raises(ValueError, match="job not found"):
                    await service.match_job_to_resume(
                        self.mock_db,
                        job_id=11,
                        resume_id=7,
                        current_user_id=55,
                    )

    @pytest.mark.asyncio
    async def test_match_job_to_resume_returns_404_for_unowned_resume(self):
        service = self.service

        with patch("src.business_logic.job.service.job_repository", create=True) as mock_job_repo:
            with patch("src.business_logic.job.service.resume_repository", create=True) as mock_resume_repo:
                mock_job_repo.get_by_id.return_value = SimpleNamespace(id=11, title="Backend Intern")
                mock_resume_repo.get_by_id_and_user_id.return_value = None

                with pytest.raises(ValueError, match="resume not found"):
                    await service.match_job_to_resume(
                        self.mock_db,
                        job_id=11,
                        resume_id=7,
                        current_user_id=55,
                    )

    @pytest.mark.asyncio
    async def test_match_job_to_resume_returns_400_for_empty_resume_text(self):
        service = self.service

        with patch("src.business_logic.job.service.job_repository", create=True) as mock_job_repo:
            with patch("src.business_logic.job.service.resume_repository", create=True) as mock_resume_repo:
                with patch("src.business_logic.job.service.JobAgent") as MockJobAgent:
                    mock_job_repo.get_by_id.return_value = SimpleNamespace(id=11, title="Backend Intern")
                    mock_resume_repo.get_by_id_and_user_id.return_value = SimpleNamespace(
                        id=7,
                        user_id=55,
                        processed_content="",
                        resume_text="",
                    )

                    with pytest.raises(ValueError, match="resume text is empty"):
                        await service.match_job_to_resume(
                            self.mock_db,
                            job_id=11,
                            resume_id=7,
                            current_user_id=55,
                        )

    @pytest.mark.asyncio
    async def test_match_job_to_resume_wraps_provider_failure_without_fallback(self):
        """当 JobAgent 不使用 fallback 时，LLM 失败异常应向上传播。"""
        service = self.service
        with patch("src.business_logic.job.service.job_repository", create=True) as mock_job_repo:
            with patch("src.business_logic.job.service.resume_repository", create=True) as mock_resume_repo:
                mock_job_repo.get_by_id.return_value = SimpleNamespace(id=11, title="Backend Intern")
                mock_resume_repo.get_by_id_and_user_id.return_value = SimpleNamespace(
                    id=7,
                    user_id=55,
                    processed_content="Built APIs",
                    resume_text="",
                )

                # Mock JobAgent whose match_job_to_resume raises error directly
                # (bypassing agent's internal fallback logic)
                mock_agent = MagicMock()
                mock_agent.match_job_to_resume = AsyncMock(side_effect=RuntimeError("boom"))
                mock_agent.config = {"provider": "zhipu", "model": "glm-4"}
                with patch("src.business_logic.job.service.JobAgent") as MockJobAgent:
                    MockJobAgent.return_value = mock_agent

                    with pytest.raises(RuntimeError, match="boom"):
                        await service.match_job_to_resume(
                            self.mock_db,
                            job_id=11,
                            resume_id=7,
                            current_user_id=55,
                        )

    @pytest.mark.asyncio
    async def test_match_job_to_resume_fallback_returns_mock_content_on_api_failure(self):
        """当 LLM API 调用失败且 allow_mock_fallback=True 时，应返回 mock 内容而非抛出异常。"""
        service = self.service
        job = SimpleNamespace(id=11, title="Backend Intern", company="Test Co")
        resume = SimpleNamespace(id=7, user_id=55, processed_content="Built APIs", resume_text="")

        with patch("src.business_logic.job.service.job_repository", create=True) as mock_job_repo:
            with patch("src.business_logic.job.service.resume_repository", create=True) as mock_resume_repo:
                mock_job_repo.get_by_id.return_value = job
                mock_resume_repo.get_by_id_and_user_id.return_value = resume

                # Mock agent whose LLM failed and fallback returned mock content
                mock_agent = MagicMock()
                mock_agent.match_job_to_resume = AsyncMock(return_value={
                    "mode": "job_match",
                    "score": 0,
                    "feedback": "mock feedback",
                    "raw_content": "mock-generate:...",
                    "provider": "mock",
                    "model": "mock-model",
                    "fallback_used": True,
                })
                mock_agent.config = {"provider": "zhipu", "model": "glm-4"}
                with patch("src.business_logic.job.service.JobAgent") as MockJobAgent:
                    MockJobAgent.return_value = mock_agent

                    result = await service.match_job_to_resume(
                        self.mock_db,
                        job_id=11,
                        resume_id=7,
                        current_user_id=55,
                    )

        # 验证返回了 fallback 的 mock 结果
        assert result["score"] == 0
        assert result["provider"] == "mock"
        assert result["fallback_used"] is True

    @pytest.mark.asyncio
    async def test_persist_job_match_creates_result_record(self):
        persisted_result = SimpleNamespace(id=501, job_id=11, resume_id=7)
        service = self.service

        with patch.object(
            service,
            "match_job_to_resume",
            new=AsyncMock(
                return_value={
                    "mode": "job_match",
                    "job_id": 11,
                    "resume_id": 7,
                    "score": 86,
                    "feedback": "Strong fit",
                    "raw_content": "Score: 86\nFeedback: Strong fit.",
                    "provider": "mock",
                    "model": "mock-model",
                }
            ),
        ) as mock_match, patch(
            "src.business_logic.job.service.job_match_result_repository",
            create=True,
        ) as mock_repo:
            mock_repo.create.return_value = persisted_result

            result = await service.persist_job_match(self.mock_db, 11, 7, 55)

        assert result is persisted_result
        mock_match.assert_awaited_once_with(
            self.mock_db,
            job_id=11,
            resume_id=7,
            current_user_id=55,
        )
        payload = mock_repo.create.call_args.args[1]
        assert payload == {
            "job_id": 11,
            "resume_id": 7,
            "mode": "job_match",
            "score": 86,
            "feedback": "Strong fit",
            "raw_content": "Score: 86\nFeedback: Strong fit.",
            "provider": "mock",
            "model": "mock-model",
            "status": "success",
            "fallback_used": False,
        }

    @pytest.mark.asyncio
    async def test_persist_job_match_propagates_match_failure(self):
        service = self.service

        with patch.object(
            service,
            "match_job_to_resume",
            new=AsyncMock(side_effect=RuntimeError("boom")),
        ):
            with pytest.raises(RuntimeError, match="boom"):
                await service.persist_job_match(self.mock_db, 11, 7, 55)

    @pytest.mark.asyncio
    async def test_persist_job_match_uses_fallback_provider_from_agent_result(self):
        """当 match_job_to_resume fallback 返回 mock 内容时，persist_job_match 应使用 agent 结果中的 provider。"""
        persisted_result = SimpleNamespace(id=501, job_id=11, resume_id=7)
        service = self.service

        with patch.object(
            service,
            "match_job_to_resume",
            new=AsyncMock(
                return_value={
                    "mode": "job_match",
                    "job_id": 11,
                    "resume_id": 7,
                    "score": 0,
                    "feedback": "mock feedback",
                    "raw_content": "mock-generate:...",
                    "provider": "mock",
                    "model": "mock-model",
                    "fallback_used": True,
                }
            ),
        ) as mock_match, patch(
            "src.business_logic.job.service.job_match_result_repository",
            create=True,
        ) as mock_repo:
            mock_repo.create.return_value = persisted_result

            result = await service.persist_job_match(self.mock_db, 11, 7, 55)

        assert result is persisted_result
        payload = mock_repo.create.call_args.args[1]
        # provider 必须来自 agent 结果（fallback 时为 "mock"），而不是 self.job_agent
        assert payload["provider"] == "mock"
        assert payload["model"] == "mock-model"
        assert payload["raw_content"] == "mock-generate:..."

    @pytest.mark.asyncio
    async def test_persist_job_match_uses_real_provider_when_no_fallback(self):
        """当 match_job_to_resume 使用真实 provider 时，persist_job_match 应使用 agent 结果中的真实 provider。"""
        persisted_result = SimpleNamespace(id=501, job_id=11, resume_id=7)
        service = self.service

        with patch.object(
            service,
            "match_job_to_resume",
            new=AsyncMock(
                return_value={
                    "mode": "job_match",
                    "job_id": 11,
                    "resume_id": 7,
                    "score": 86,
                    "feedback": "Good fit",
                    "raw_content": "Score: 86\nFeedback: Good fit.",
                    "provider": "zhipu",
                    "model": "glm-4.7",
                }
            ),
        ) as mock_match, patch(
            "src.business_logic.job.service.job_match_result_repository",
            create=True,
        ) as mock_repo:
            mock_repo.create.return_value = persisted_result

            result = await service.persist_job_match(self.mock_db, 11, 7, 55)

        assert result is persisted_result
        payload = mock_repo.create.call_args.args[1]
        # provider 必须来自 agent 结果（真实 provider），不是 self.job_agent
        assert payload["provider"] == "zhipu"
        assert payload["model"] == "glm-4.7"
        assert "mock" not in payload["raw_content"]

    @pytest.mark.asyncio
    async def test_get_job_match_history_lists_records_for_current_user(self):
        history = [
            SimpleNamespace(id=401, job_id=11, resume_id=7),
            SimpleNamespace(id=402, job_id=11, resume_id=8),
        ]

        with patch("src.business_logic.job.service.job_repository") as mock_job_repo:
            with patch("src.business_logic.job.service.job_match_result_repository", create=True) as mock_repo:
                mock_job_repo.get_by_id.return_value = SimpleNamespace(id=11, title="Backend Intern")
                mock_repo.get_all_by_job_id_and_user_id.return_value = history

                result = await self.service.get_job_match_history(self.mock_db, 11, 55)

        assert result == history
        mock_job_repo.get_by_id.assert_called_once_with(self.mock_db, 11)
        mock_repo.get_all_by_job_id_and_user_id.assert_called_once_with(
            self.mock_db,
            11,
            55,
        )

    @pytest.mark.asyncio
    async def test_get_job_match_history_raises_for_missing_job(self):
        with patch("src.business_logic.job.service.job_repository") as mock_job_repo:
            mock_job_repo.get_by_id.return_value = None

            with pytest.raises(ValueError, match="job not found"):
                await self.service.get_job_match_history(self.mock_db, 11, 55)

    @pytest.mark.asyncio
    async def test_match_job_to_resume_uses_user_llm_config_when_available(self):
        """用户配置了 LLM 时，match_job_to_resume 应使用用户配置而非默认 mock。"""
        job = SimpleNamespace(id=11, title="Backend Intern", company="Test Co")
        resume = SimpleNamespace(id=7, user_id=55, processed_content="Built APIs", resume_text="")
        user_id = 55

        mock_user_config = {
            "provider": "zhipu",
            "model": "glm-4.7",
            "api_key": "user-key",
            "base_url": None,
            "temperature": 0.7,
        }

        with patch("src.business_logic.job.service.job_repository", create=True) as mock_job_repo:
            with patch("src.business_logic.job.service.resume_repository", create=True) as mock_resume_repo:
                with patch("src.business_logic.job.service.JobAgent") as MockJobAgent:
                    with patch("src.business_logic.user_llm_config_service.user_llm_config_service") as mock_ullcs:
                        # Mock agent whose config matches user config
                        mock_agent = MagicMock()
                        mock_agent.config = mock_user_config
                        mock_agent.match_job_to_resume = AsyncMock(return_value={
                            "mode": "job_match",
                            "score": 85,
                            "feedback": "Good fit",
                            "raw_content": "Score: 85",
                            "provider": "zhipu",
                            "model": "glm-4.7",
                        })
                        MockJobAgent.return_value = mock_agent

                        # Override autouse fixture to return actual user config
                        mock_ullcs.get_config_for_agent.return_value = mock_user_config
                        mock_job_repo.get_by_id.return_value = SimpleNamespace(id=11, title="Backend Intern")
                        mock_resume_repo.get_by_id_and_user_id.return_value = SimpleNamespace(
                            id=7, user_id=55, processed_content="Built APIs", resume_text=""
                        )

                        result = await self.service.match_job_to_resume(
                            self.mock_db,
                            job_id=11,
                            resume_id=7,
                            current_user_id=user_id,
                        )

        # 验证 JobAgent 被创建时传入了 user_id 和 user_llm_config
        MockJobAgent.assert_called_once_with(
            user_id=user_id,
            user_llm_config=mock_user_config,
            allow_mock_fallback=True,
        )
        # 验证返回的 provider 和 model 来自用户配置
        assert result["provider"] == "zhipu"
        assert result["model"] == "glm-4.7"
        assert result["score"] == 85

    @pytest.mark.asyncio
    async def test_get_recommended_jobs_uses_goal_summary_for_ranking_and_normalizes_tags(self):
        backend_job = SimpleNamespace(
            id=1,
            title="Backend Intern",
            company="Alpha Tech",
            location="Beijing",
            description="Build APIs with FastAPI",
            requirements="Python",
            work_type="internship",
            tags="python,fastapi",
            source_url="https://alpha.example/jobs/1",
        )
        frontend_job = SimpleNamespace(
            id=2,
            title="Frontend Intern",
            company="Beta Labs",
            location="Shanghai",
            description="Build React interfaces",
            requirements="TypeScript",
            work_type="internship",
            tags="react,typescript",
            source_url="https://beta.example/jobs/2",
        )

        with patch("src.business_logic.job.service.job_repository") as mock_repo:
            mock_repo.get_all.return_value = [frontend_job, backend_job]

            result = await self.service.get_recommended_jobs(
                self.mock_db,
                goal_summary="backend fastapi beijing",
                limit=5,
            )

        assert [job.id for job in result] == [1, 2]
        assert result[0].tags == ["python", "fastapi"]
