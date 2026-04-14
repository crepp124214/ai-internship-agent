from unittest.mock import AsyncMock, patch

import pytest

import src.business_logic.agents.job_agent as job_agent_module
from src.core.llm import LLMProviderError, MockLLMAdapter


class TestJobAgent:
    def setup_method(self):
        self.llm = AsyncMock()
        self.llm.generate = AsyncMock(return_value="Score: 86\nFeedback: Strong fit.")
        self.llm.chat = AsyncMock(return_value={"role": "assistant", "content": "mock chat"})
        self.llm.get_embedding = AsyncMock(return_value=[0.1, 0.2, 0.3])

    @pytest.mark.asyncio
    async def test_match_job_to_resume_returns_structured_result(self):
        agent = job_agent_module.JobAgent(llm=self.llm)

        result = await agent.match_job_to_resume(
            job_context="Backend intern role",
            resume_context="Built FastAPI APIs and tests",
        )

        assert result["mode"] == "job_match"
        assert result["job_context"] == "Backend intern role"
        assert result["resume_context"] == "Built FastAPI APIs and tests"
        assert result["score"] == 86
        assert "Strong fit" in result["feedback"]

    @pytest.mark.asyncio
    async def test_match_job_to_resume_rejects_empty_resume_text(self):
        agent = job_agent_module.JobAgent(llm=self.llm)

        with pytest.raises(job_agent_module.EmptyJobResumeTextError, match="resume text is empty"):
            await agent.match_job_to_resume(
                job_context="Backend intern role",
                resume_context="",
            )

    @pytest.mark.asyncio
    async def test_match_job_to_resume_wraps_llm_errors_without_fallback(self):
        """当 allow_mock_fallback=False 时，LLM 调用失败应抛出异常。"""
        self.llm.generate = AsyncMock(side_effect=RuntimeError("boom"))
        agent = job_agent_module.JobAgent(llm=self.llm, allow_mock_fallback=False)

        with pytest.raises(job_agent_module.JobMatchLLMError, match="failed to match job and resume"):
            await agent.match_job_to_resume(
                job_context="Backend intern role",
                resume_context="Built FastAPI APIs and tests",
            )

    @pytest.mark.asyncio
    async def test_match_job_to_resume_falls_back_to_mock_on_api_failure(self):
        """当 allow_mock_fallback=True 且 LLM API 调用失败时，应 fallback 到 mock 并返回有效响应。"""
        # 模拟真实场景：第一次调用失败，fallback 创建 fresh mock adapter 后成功
        failing_llm = AsyncMock()
        failing_llm.generate = AsyncMock(side_effect=RuntimeError("API error"))
        # 让 JobAgent.__init__ 中的 _build_llm 失败（触发 fallback 路径）
        # 注意：这里用 config 触发 _build_llm 失败，而不是注入 llm
        agent = job_agent_module.JobAgent(
            config={"provider": "openai", "api_key": ""},
            allow_mock_fallback=True,
        )
        # 手动替换 llm 为会失败的 mock（模拟 real adapter API call 失败）
        agent.llm = failing_llm

        result = await agent.match_job_to_resume(
            job_context="Backend intern role",
            resume_context="Built FastAPI APIs and tests",
        )

        assert result["mode"] == "job_match"
        assert result["score"] >= 0
        assert "raw_content" in result
        assert result["fallback_used"] is True
        # fallback 后 _active_provider 必须是 "mock"
        assert result["provider"] == "mock"

    def test_job_agent_uses_openai_provider_from_explicit_config(self):
        agent = job_agent_module.JobAgent(config={"provider": "openai", "api_key": "test-key"})

        assert agent.llm is not None

    @patch.dict(
        "os.environ",
        {"OPENAI_API_KEY": "", "OPENAI_BASE_URL": "", "LLM_PROVIDER": ""},
        clear=True,
    )
    def test_job_agent_rejects_openai_without_api_key(self):
        with pytest.raises(LLMProviderError, match="OpenAI API key is required"):
            job_agent_module.JobAgent(config={"provider": "openai"})

    def test_job_agent_active_provider_reflects_zhipu_not_mock(self):
        """_active_provider 应保留用户配置的 provider，不被 fallback 篡改。"""
        agent = job_agent_module.JobAgent(
            config={"provider": "zhipu", "model": "glm-4.7", "api_key": "test-key"},
            allow_mock_fallback=True,
        )

        # _active_provider 必须是 zhipu，不是 mock
        assert agent._active_provider == "zhipu"
        assert agent._active_provider != "mock"

    def test_job_agent_fallback_does_not_corrupt_config_provider(self):
        """
        fallback 发生时，config['provider'] 不应被篡改为 'mock'。
        这是对原始配置的保护。
        _active_provider 在 fallback 时会被更新为 'mock'（见下一测试）。
        """
        agent = job_agent_module.JobAgent(
            config={"provider": "invalid_provider_xyz", "model": "test"},
            allow_mock_fallback=True,
        )

        # 关键是验证 config["provider"] 没有被改成 mock
        assert agent.config.get("provider") != "mock", (
            "config['provider'] 不应被 fallback 篡改为 'mock'"
        )
        # 注意：_active_provider 在 fallback 时会被更新为 'mock'（这是正确的修复）


class TestJobAgentLLMIntegration:
    """验证 JobAgent 与真实 LLM Factory 的集成。"""

    def test_job_agent_openai_adapter_disables_http_client_retries(self):
        """
        OpenAIAdapter 必须将 HTTP 客户端的 max_retries 设为 0，
        避免两层重试（HTTPX retry + retry_async）叠加导致 40s+ 的长时间挂起。
        所有重试统一由 retry_async(decorator 处理，提供确定性 backoff。
        """
        agent = job_agent_module.JobAgent(
            config={
                "provider": "openai",
                "model": "gpt-4o-mini",
                "api_key": "test-key",
                "base_url": "https://api.openai.com/v1",
            },
            allow_mock_fallback=True,
        )

        # 验证 HTTP 客户端的 max_retries 已禁用
        http_client = agent.llm.client
        assert http_client.max_retries == 0, (
            f"HTTP 客户端 max_retries 应为 0，实际为 {http_client.max_retries}。"
            "这会导致 HTTPX 内置重试与 retry_async 叠加，引发 40s+ 长时间挂起。"
        )
        """
        用户配置 zhipu 时，JobAgent 应使用 OpenAIAdapter（zhipu 是 OpenAI 兼容接口），
        而非 MockLLMAdapter。
        """
        agent = job_agent_module.JobAgent(
            config={
                "provider": "zhipu",
                "model": "glm-4.7",
                "api_key": "test-key",
                "base_url": "https://open.bigmodel.cn/api/paas/v4",
            },
            allow_mock_fallback=True,
        )

        # 不应是 mock
        assert not isinstance(agent.llm, MockLLMAdapter)
        # _active_provider 必须反映用户配置的 zhipu
        assert agent._active_provider == "zhipu"

    @pytest.mark.asyncio
    async def test_job_agent_match_response_reports_zhipu_provider(self):
        """match_job_to_resume 响应的 provider 字段必须是 zhipu（不是 mock）。"""
        agent = job_agent_module.JobAgent(
            config={
                "provider": "zhipu",
                "model": "glm-4.7",
                "api_key": "test-key",
                "base_url": "https://open.bigmodel.cn/api/paas/v4",
            },
        )
        # 用 mock LLM 避免真实 API 调用
        mock_llm = AsyncMock()
        mock_llm.generate = AsyncMock(return_value="Score: 88\nFeedback: Good fit.")
        agent.llm = mock_llm

        result = await agent.match_job_to_resume(
            job_context="Backend intern role",
            resume_context="Built FastAPI APIs",
        )

        # 关键断言：provider 必须是 zhipu，不是 mock
        assert result["provider"] == "zhipu", (
            f"响应 provider 应为 'zhipu'，实际为 '{result['provider']}'。"
            "这说明用户配置的 provider 被 fallback 篡改了。"
        )
        assert result["raw_content"]
        assert result["model"] == "glm-4.7"

    def test_job_agent_fallback_to_mock_updates_active_provider(self):
        """
        当 openai 因缺少 API key 触发 fallback 时，_active_provider 必须更新为 'mock'。
        这确保响应 provider 字段准确反映实际使用的 provider。
        """
        # openai 无 key 时 LLMFactory.create 抛出异常，fallback 到 mock
        agent = job_agent_module.JobAgent(
            config={"provider": "openai", "api_key": ""},
            allow_mock_fallback=True,
        )

        # _active_provider 必须反映实际使用的 mock，不是 openai
        assert agent._active_provider == "mock", (
            f"_active_provider 应为 'mock'，实际为 '{agent._active_provider}'。"
            "这说明 fallback 时没有更新 _active_provider。"
        )
        # 不应是 mock 实例
        from src.core.llm import MockLLMAdapter

        assert isinstance(agent.llm, MockLLMAdapter)

    @pytest.mark.asyncio
    async def test_job_agent_fallback_response_has_mock_provider_not_original(self):
        """
        fallback 发生后，响应的 provider 字段必须是 'mock'，不是原始配置值。
        raw_content 应为可消费的 mock 内容。
        """
        agent = job_agent_module.JobAgent(
            config={"provider": "openai", "api_key": ""},
            allow_mock_fallback=True,
        )

        result = await agent.match_job_to_resume(
            job_context="Backend intern role",
            resume_context="Built FastAPI APIs",
        )

        assert result["provider"] == "mock", (
            f"响应 provider 应为 'mock'，实际为 '{result['provider']}'。"
            "fallback 发生后，响应必须报告实际使用的 mock provider。"
        )
        assert result["raw_content"]
        assert result["status"] == "fallback"
        assert result["fallback_used"] is True
