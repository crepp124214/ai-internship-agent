"""
AI实习求职Agent系统 - 主入口文件
"""

import uvicorn
from fastapi import FastAPI, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware

# 全局异常处理器
from src.core.errors import api_exception_handler, http_exception_handler
from src.presentation.api.middleware.rate_limit import (
    RateLimitMiddleware,
    get_rate_limit_runtime_config,
)
from src.presentation.api.middleware.security_headers import SecurityHeadersMiddleware
from src.presentation.api.middleware.request_id import RequestIDMiddleware
from src.presentation.api.metrics import MetricsMiddleware, metrics

from src.business_logic.readiness import check_readiness
from src.data_access.database import check_database_connection
from src.utils.config_loader import get_settings
from src.utils.logger import setup_logger

# 初始化日志
logger = setup_logger()

# 加载配置
settings = get_settings()

# OpenTelemetry 分布式追踪初始化（在app创建后执行）
_tracer_provider = None
try:
    from src.core.tracing import setup_tracing
    _tracer_provider = setup_tracing()
    logger.info("OpenTelemetry tracing initialized")
except Exception as exc:
    logger.warning(f"OpenTelemetry tracing initialization skipped: {exc}")

# 创建FastAPI应用
app = FastAPI(
    title=settings.APP_NAME,
    description="AI实习求职Agent系统 - 基于大语言模型的智能求职助手",
    version="0.1.0",
    docs_url="/docs",
    redoc_url="/redoc",
)

# 配置CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Request ID middleware - must be first to ensure request_id is available to all subsequent middlewares
app.add_middleware(RequestIDMiddleware)
# Rate limiting and security headers middlewares
app.add_middleware(RateLimitMiddleware)
app.add_middleware(SecurityHeadersMiddleware)
# Observability: Prometheus metrics middleware
app.add_middleware(MetricsMiddleware)

# Startup runtime config logs
_rate_limit_runtime = get_rate_limit_runtime_config()
logger.info(
    "Rate limit configured: mode=%s selected_backend=%s requests=%s window_seconds=%s",
    _rate_limit_runtime["mode"],
    _rate_limit_runtime["selected_backend"],
    _rate_limit_runtime["requests"],
    _rate_limit_runtime["window_seconds"],
)

# OpenTelemetry FastAPI instrumentation（在所有中间件注册完成后执行）
if _tracer_provider is not None:
    try:
        from opentelemetry.instrumentation.fastapi import FastAPIInstrumentor  # type: ignore
        FastAPIInstrumentor.instrument_app(app)
        logger.info("OpenTelemetry FastAPI instrumentation applied")
    except Exception as exc:
        logger.warning(f"FastAPI instrumentation skipped: {exc}")

# 注册全局异常处理器（拦截所有未处理的异常，转换为统一错误结构）
app.add_exception_handler(Exception, api_exception_handler)
# 注册 HTTPException 专用处理器（HTTPException 需要单独处理，因为 FastAPI 默认处理器优先级更高）
app.add_exception_handler(HTTPException, http_exception_handler)

# 注册路由
from src.presentation.api.v1 import auth, resume, jobs, interview, users, agent, assistant, user_llm_configs
app.include_router(auth.router, prefix="/api/v1/auth", tags=["认证"])
app.include_router(resume.router, prefix="/api/v1/resumes", tags=["简历管理"])
app.include_router(jobs.router, prefix="/api/v1/jobs", tags=["岗位管理"])
app.include_router(interview.router, prefix="/api/v1/interview", tags=["面试管理"])
app.include_router(users.router, prefix="/api/v1/users", tags=["用户管理"])
app.include_router(agent.router, prefix="/api/v1/agent", tags=["Agent"])
app.include_router(assistant.router, prefix="/api/v1/agent", tags=["Agent"])
app.include_router(user_llm_configs.router, prefix="/api/v1/users/llm-configs", tags=["用户LLM配置"])

# Metrics endpoint (Prometheus)
app.add_api_route("/metrics", metrics, methods=["GET"])


@app.get("/")
async def root():
    """根路径"""
    return {
        "message": "AI实习求职Agent系统",
        "version": "0.1.0",
        "docs": "/docs",
        "health": "/health",
        "ready": "/ready",
    }


@app.get("/health")
async def health_check():
    """健康检查"""
    return {"status": "healthy"}


@app.get("/ready")
async def readiness_check():
    """就绪检查。"""
    readiness_status = await check_readiness()
    if not readiness_status.is_ready:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=readiness_status.to_dict(),
        ) from None
    return readiness_status.to_dict()


if __name__ == "__main__":
    logger.info(f"启动 {settings.APP_NAME} 服务...")
    uvicorn.run(
        "src.main:app",
        host=settings.APP_HOST,
        port=settings.APP_PORT,
        reload=settings.APP_DEBUG,
    )
