"""
日志配置模块
配置结构化日志输出
"""

import logging
import sys
from typing import Optional

import structlog

from src.utils.config_loader import get_settings


def setup_logger(name: Optional[str] = None) -> structlog.stdlib.BoundLogger:
    """
    配置并获取结构化日志记录器

    Args:
        name: 日志记录器名称

    Returns:
        配置好的日志记录器
    """
    settings = get_settings()

    # 配置标准库日志
    logging.basicConfig(
        format="%(message)s",
        stream=sys.stdout,
        level=getattr(logging, settings.LOG_LEVEL),
    )

    # 配置structlog
    timestamper = structlog.processors.TimeStamper(fmt="iso")

    shared_processors = [
        structlog.stdlib.add_log_level,
        structlog.stdlib.add_logger_name,
        timestamper,
    ]

    if settings.APP_ENV == "production":
        # 生产环境使用JSON格式
        processors = shared_processors + [
            structlog.processors.dict_tracebacks,
            structlog.processors.JSONRenderer(),
        ]
    else:
        # 开发环境使用易读格式
        processors = shared_processors + [
            structlog.dev.ConsoleRenderer(),
        ]

    structlog.configure(
        processors=processors,
        context_class=dict,
        logger_factory=structlog.stdlib.LoggerFactory(),
        wrapper_class=structlog.stdlib.BoundLogger,
        cache_logger_on_first_use=True,
    )

    return structlog.get_logger(name or "app")


def get_logger(name: Optional[str] = None) -> structlog.stdlib.BoundLogger:
    """
    获取日志记录器

    Args:
        name: 日志记录器名称

    Returns:
        日志记录器
    """
    return structlog.get_logger(name or "app")
