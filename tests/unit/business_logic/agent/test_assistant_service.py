import pytest
from src.business_logic.agent.assistant_service import AssistantService

def test_build_system_prompt_for_resume_page():
    service = AssistantService()
    prompt = service.build_system_prompt(page="resume", resource_id=123)
    assert "简历" in prompt
    assert "123" in prompt

def test_build_system_prompt_for_job_page():
    service = AssistantService()
    prompt = service.build_system_prompt(page="job", resource_id=456)
    assert "岗位" in prompt
    assert "456" in prompt

def test_build_context_creates_valid_context():
    service = AssistantService()
    ctx = service.build_context(
        page="resume",
        resource_id=1,
        resource_ids=[1, 2],
        history=[{"role": "user", "content": "hello"}]
    )
    assert ctx["page"] == "resume"
    assert ctx["resource_id"] == 1
    assert len(ctx["history"]) == 1