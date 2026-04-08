from typing import Optional
from pydantic import BaseModel, ConfigDict


class AssistantChatRequest(BaseModel):
    """助手面板对话请求"""
    message: str
    context: "AssistantContextSchema"


class AssistantContextSchema(BaseModel):
    """助手上下文"""
    page: str  # "resume" | "job"
    resource_id: Optional[int] = None
    resource_ids: list[int] = []
    history: list[dict] = []

    model_config = ConfigDict(from_attributes=True)
