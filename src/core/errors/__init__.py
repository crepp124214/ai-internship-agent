"""
Core Errors - 统一错误处理模块

提供错误码定义和 ApiErrorTranslator，将各类异常映射为统一错误结构。
"""

from src.core.errors.api_error_translator import (
    ApiErrorResponse,
    ApiErrorTranslator,
    api_exception_handler,
    http_exception_handler,
    get_api_error_translator,
)
from src.core.errors.error_codes import (
    ERROR_CODE_INFO,
    ErrorCode,
    ErrorCodeInfo,
    get_error_code_info,
)


__all__ = [
    # 错误码
    "ErrorCode",
    "ErrorCodeInfo",
    "ERROR_CODE_INFO",
    "get_error_code_info",
    # 错误响应
    "ApiErrorResponse",
    # 翻译器
    "ApiErrorTranslator",
    "get_api_error_translator",
    # 全局异常处理器
    "api_exception_handler",
    "http_exception_handler",
]
