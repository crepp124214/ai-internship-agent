"""
配置加载器
从环境变量或配置文件加载配置
"""

import os
from typing import List, Optional

from dotenv import load_dotenv
from pydantic_settings import BaseSettings

# 加载环境变量
load_dotenv()


class Settings(BaseSettings):
    """应用配置类"""

    # 应用基本配置
    APP_NAME: str = "AI Internship Agent"
    APP_ENV: str = "development"
    APP_DEBUG: bool = True
    APP_HOST: str = "0.0.0.0"
    APP_PORT: int = 8000

    # 数据库配置
    DATABASE_URL: str = "postgresql://user:password@localhost:5432/internship_agent"
    REDIS_URL: str = "redis://localhost:6379/0"

    # LLM配置
    OPENAI_API_KEY: Optional[str] = None
    ANTHROPIC_API_KEY: Optional[str] = None
    LLM_PROVIDER: str = "openai"

    # 向量数据库配置
    CHROMA_DB_PATH: str = "./data/vectors/chroma"

    # 日志配置
    LOG_LEVEL: str = "INFO"
    LOG_FILE: Optional[str] = None

    # 安全配置
    SECRET_KEY: str = "your-secret-key-here"

    # CORS配置
    CORS_ORIGINS: List[str] = [
        "http://localhost:3000",
        "http://localhost:4173",
        "http://localhost:4174",
        "http://localhost:5173",
        "http://127.0.0.1:3000",
        "http://127.0.0.1:4173",
        "http://127.0.0.1:4174",
        "http://127.0.0.1:5173",
    ]

    model_config = {
        "env_file": ".env",
        "case_sensitive": True,
    }

# Security / rate limiting simple MVP configuration (loaded from env or defaults)
def _load_rate_limit_settings():
    try:
        rate_requests = int(os.getenv("RATE_LIMIT_REQUESTS", "100"))
        window_seconds = int(os.getenv("RATE_LIMIT_WINDOW_SECONDS", "60"))
        return rate_requests, window_seconds
    except ValueError:
        # Fallback to sane defaults on bad env values
        return 100, 60

RATE_LIMIT_REQUESTS, RATE_LIMIT_WINDOW_SECONDS = _load_rate_limit_settings()


# 全局配置实例
_settings: Optional[Settings] = None


def get_settings() -> Settings:
    """获取全局配置单例"""
    global _settings
    if _settings is None:
        _settings = Settings()
    return _settings
