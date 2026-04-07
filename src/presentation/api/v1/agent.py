"""Agent 流式对话端点"""
import json
from typing import AsyncIterator

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from sqlalchemy.orm import Session

from src.business_logic.agent.agent_chat_service import AgentChatService
from src.core.llm.litellm_adapter import LiteLLMAdapter
from src.presentation.api.deps import get_current_user, get_db

router = APIRouter()

# 全局单例
_agent_service = AgentChatService()
_llm = LiteLLMAdapter()


class AgentChatRequest(BaseModel):
    task: str
    context: dict | None = None


def _build_sse_event(event_type: str, data: dict) -> str:
    return f"data: {json.dumps({'type': event_type, **data})}\n\n"


async def _generate_stream(
    task: str,
    context: dict,
) -> AsyncIterator[str]:
    """
    生成 SSE 流。
    """
    # 路由任务
    task_type = _agent_service.route_task(task)
    system_prompt = _agent_service.get_system_prompt(task_type)

    # 发送 planning 步骤
    yield _build_sse_event("step", {
        "step": "planning",
        "content": f"任务类型：{task_type}，正在分析..."
    })

    # 构建消息
    messages = [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": task},
    ]

    # 流式调用 LLM
    try:
        async for chunk in _llm.stream_chat(messages=messages):
            if chunk:
                yield _build_sse_event("step", {
                    "step": "final",
                    "content": chunk,
                })
    except Exception as e:
        yield _build_sse_event("error", {"content": str(e)})

    yield _build_sse_event("done", {})


@router.post("/chat")
async def agent_chat(
    req: AgentChatRequest,
    current_user=Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    SSE 流式 Agent 对话端点。
    """
    if not req.task or not req.task.strip():
        raise HTTPException(status_code=400, detail="task is required")

    return StreamingResponse(
        _generate_stream(req.task.strip(), req.context or {}),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
        },
    )