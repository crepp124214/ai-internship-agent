"""用户 LLM 配置 CRUD API。"""
from typing import Literal

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from src.business_logic.user_llm_config_service import user_llm_config_service
from src.presentation.api.deps import get_current_user, get_db
from src.presentation.schemas.user_llm_config import UserLlmConfigCreate, UserLlmConfigResponse

router = APIRouter()

@router.get("/", response_model=list[UserLlmConfigResponse])
async def get_llm_configs(current_user=Depends(get_current_user), db: Session = Depends(get_db)):
    configs = user_llm_config_service.get_user_configs(db, current_user.id)
    return configs

@router.post("/", response_model=UserLlmConfigResponse)
async def save_llm_config(data: UserLlmConfigCreate, current_user=Depends(get_current_user), db: Session = Depends(get_db)):
    try:
        config = user_llm_config_service.save_config(db, current_user.id, data)
        return config
    except Exception as exc:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Save config failed")

@router.delete("/{agent}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_llm_config(
    agent: Literal["resume_agent", "job_agent", "interview_agent"],
    current_user=Depends(get_current_user),
    db: Session = Depends(get_db),
):
    deleted = user_llm_config_service.delete_config(db, current_user.id, agent)
    if not deleted:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Config not found")