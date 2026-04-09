"""
配置加载器
从环境变量或配置文件加载配置
"""

import os
from typing import List, Literal, Optional

from dotenv import load_dotenv
from pydantic_settings import BaseSettings

# 加载环境变量
load_dotenv()

_DEFAULT_SECRET_PLACEHOLDERS = {
    "your-secret-key-here",
    "change-me-before-production",
    "changeme",
    "secret",
}


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

    # LLM 配置 — 支持多厂商模型接入
    # 通过 LLM_PROVIDER 指定默认提供商：openai / anthropic / minimax / deepseek / zhipu / dashscope / moonshot / siliconflow
    LLM_PROVIDER: str = "openai"

    # OpenAI
    OPENAI_API_KEY: Optional[str] = None
    OPENAI_BASE_URL: Optional[str] = None  # 兼容第三方代理（如 one-api、new-api）
    OPENAI_MODEL: Optional[str] = None

    # Anthropic (Claude)
    ANTHROPIC_API_KEY: Optional[str] = None
    ANTHROPIC_BASE_URL: Optional[str] = None
    ANTHROPIC_MODEL: Optional[str] = None

    # MiniMax
    MINIMAX_API_KEY: Optional[str] = None
    MINIMAX_BASE_URL: Optional[str] = None
    MINIMAX_MODEL: Optional[str] = None

    # DeepSeek
    DEEPSEEK_API_KEY: Optional[str] = None
    DEEPSEEK_BASE_URL: Optional[str] = None
    DEEPSEEK_MODEL: Optional[str] = None

    # 智谱 AI (ChatGLM / CogView)
    ZHIPU_API_KEY: Optional[str] = None
    ZHIPU_BASE_URL: Optional[str] = None
    ZHIPU_MODEL: Optional[str] = None

    # 阿里云 DashScope（通义千问 Qwen）
    DASHSCOPE_API_KEY: Optional[str] = None
    DASHSCOPE_BASE_URL: Optional[str] = None
    DASHSCOPE_MODEL: Optional[str] = None

    # Moonshot AI（Kimi）
    MOONSHOT_API_KEY: Optional[str] = None
    MOONSHOT_BASE_URL: Optional[str] = None
    MOONSHOT_MODEL: Optional[str] = None

    # SiliconFlow（模型聚合平台）
    SILICONFLOW_API_KEY: Optional[str] = None
    SILICONFLOW_BASE_URL: Optional[str] = None
    SILICONFLOW_MODEL: Optional[str] = None

    # 全局 LLM 开关
    ENABLE_REAL_LLM: bool = False

    # 向量数据库配置
    CHROMA_DB_PATH: str = "./data/vectors/chroma"

    # 日志配置
    LOG_LEVEL: str = "INFO"
    LOG_FILE: Optional[str] = None

    # 安全配置
    SECRET_KEY: str = "your-secret-key-here"

    # JWT 配置
    JWT_ISSUER: str = "ai-internship-agent"
    JWT_AUDIENCE: str = "ai-internship-agent-client"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60
    REFRESH_TOKEN_EXPIRE_DAYS: int = 7

    # Cookie 配置
    AUTH_REFRESH_COOKIE_NAME: str = "aiia_refresh_token"
    AUTH_REFRESH_COOKIE_PATH: str = "/api/v1/auth"
    AUTH_REFRESH_COOKIE_SECURE: bool = False
    AUTH_REFRESH_COOKIE_SAMESITE: Literal["lax", "strict", "none"] = "lax"
    AUTH_REFRESH_COOKIE_DOMAIN: Optional[str] = None

    # Security headers / CSP
    CSP_POLICY: str = (
        "default-src 'self'; "
        "script-src 'self'; "
        "style-src 'self' 'unsafe-inline'; "
        "img-src 'self' data: https:; "
        "font-src 'self' data:; "
        "connect-src 'self' http://localhost:8000 http://127.0.0.1:8000; "
        "frame-ancestors 'none'; "
        "base-uri 'self'; "
        "form-action 'self'"
    )

    # CORS配置
    CORS_ORIGINS: List[str] = [
        "http://localhost:3000",
        "http://localhost:4173",
        "http://localhost:4174",
        "http://localhost:5173",
        "http://localhost:5174",
        "http://localhost:5175",
        "http://localhost:5176",
        "http://localhost:5177",
        "http://localhost:5178",
        "http://localhost:5179",
        "http://127.0.0.1:3000",
        "http://127.0.0.1:4173",
        "http://127.0.0.1:4174",
        "http://127.0.0.1:5173",
        "http://127.0.0.1:5174",
        "http://127.0.0.1:5175",
        "http://127.0.0.1:5176",
        "http://127.0.0.1:5177",
        "http://127.0.0.1:5178",
        "http://127.0.0.1:5179",
    ]

    model_config = {
        "env_file": ".env",
        "case_sensitive": True,
        "extra": "ignore",
    }


# Security / rate limiting simple MVP configuration (loaded from env or defaults)
def _load_rate_limit_settings() -> tuple[int, int, Literal["auto", "memory", "redis"]]:
    try:
        rate_requests = int(os.getenv("RATE_LIMIT_REQUESTS", "100"))
        window_seconds = int(os.getenv("RATE_LIMIT_WINDOW_SECONDS", "60"))

        backend_raw = os.getenv("RATE_LIMIT_BACKEND", "auto").strip().lower()
        if backend_raw not in {"auto", "memory", "redis"}:
            backend = "auto"
        else:
            backend = backend_raw

        return rate_requests, window_seconds, backend  # type: ignore[return-value]
    except ValueError:
        # Fallback to sane defaults on bad env values
        return 100, 60, "auto"


RATE_LIMIT_REQUESTS, RATE_LIMIT_WINDOW_SECONDS, RATE_LIMIT_BACKEND = _load_rate_limit_settings()


# 全局配置实例
_settings: Optional[Settings] = None


def _is_production_env(env: str) -> bool:
    return env.strip().lower() in {"production", "prod", "staging"}


def _is_insecure_secret(secret_key: str) -> bool:
    normalized = secret_key.strip().lower()
    return len(normalized) < 16 or normalized in _DEFAULT_SECRET_PLACEHOLDERS


def _validate_runtime_security(settings: Settings) -> None:
    if _is_production_env(settings.APP_ENV) and _is_insecure_secret(settings.SECRET_KEY):
        raise ValueError(
            "Insecure SECRET_KEY for non-development environment. "
            "Please set a strong SECRET_KEY before startup."
        )

    if settings.AUTH_REFRESH_COOKIE_SAMESITE == "none" and not settings.AUTH_REFRESH_COOKIE_SECURE:
        raise ValueError("AUTH_REFRESH_COOKIE_SECURE must be true when AUTH_REFRESH_COOKIE_SAMESITE is 'none'")


def get_settings() -> Settings:
    """获取全局配置单例"""
    global _settings
    if _settings is None:
        loaded = Settings()
        _validate_runtime_security(loaded)
        _settings = loaded
    return _settings
