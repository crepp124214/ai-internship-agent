"""Business logic tests configuration - patch user_llm_config_service for all tests."""

import pytest
from unittest.mock import MagicMock


@pytest.fixture(autouse=True)
def mock_user_llm_config_service():
    """Auto-mock user_llm_config_service.get_config_for_agent to return None.

    This prevents tests from hitting the real database/repository when calling
    job_service.match_job_to_resume() or interview_service methods, which now
    call user_llm_config_service.get_config_for_agent() internally.
    """
    from unittest.mock import patch
    with patch(
        "src.business_logic.user_llm_config_service.user_llm_config_service"
    ) as mock_svc:
        mock_svc.get_config_for_agent.return_value = None
        yield mock_svc
