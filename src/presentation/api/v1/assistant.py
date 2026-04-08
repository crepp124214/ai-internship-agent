"""Agent 助手面板 API"""
import json
from typing import AsyncIterator

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from sqlalchemy.orm import Session

from src.business_logic.agent.assistant_service import AssistantService, AssistantContext
from src.presentation.api.deps import get_current_user, get_db
from src.presentation.schemas.assistant import AssistantChatRequest

router = APIRouter()
_assistant_service = AssistantService()


def _build_sse_event(event_type: str, data: dict) -> str:
    return f"data: {json.dumps({'type': event_type, **data})}\n\n"


async def _generate_stream(
    message: str,
    page: str,
    resource_id: int | None,
    resource_ids: list[int],
) -> AsyncIterator[str]:
    ctx = AssistantContext(
        page=page,
        resource_id=resource_id,
        resource_ids=resource_ids,
    )
    try:
        async for event in _assistant_service.chat(message, ctx):
            yield _build_sse_event(event["type"], {"content": event["content"]})
    except Exception as exc:
        yield _build_sse_event("error", {"content": str(exc)})


class ToolInfo(BaseModel):
    name: str
    description: str
    category: str


@router.post("/assistant/chat")
async def assistant_chat(
    req: AssistantChatRequest,
    current_user=Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Agent 助手面板的 SSE 流式对话端点。"""
    if not req.message or not req.message.strip():
        raise HTTPException(status_code=400, detail="message is required")

    return StreamingResponse(
        _generate_stream(
            message=req.message.strip(),
            page=req.context.page,
            resource_id=req.context.resource_id,
            resource_ids=req.context.resource_ids,
        ),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
        },
    )