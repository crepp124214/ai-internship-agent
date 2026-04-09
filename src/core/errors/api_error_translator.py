"""
ApiErrorTranslator - 统一异常翻译器

将各类异常（数据库错误、Redis错误、验证错误、业务逻辑错误等）
映射到统一的错误码和 HTTP 语义，生成标准错误响应结构。

统一错误响应结构：
{
    "code": "SERVICE_NOT_READY",  # 错误码
    "message": "依赖服务未就绪",     # 人类可读消息
    "retryable": True,            # 是否可重试
    "request_id": "abc-123-def"  # 请求追踪ID（可选）
}
"""

import logging
import traceback
from dataclasses import dataclass, field
from typing import Any, Optional

from fastapi import HTTPException, Request
from fastapi.responses import JSONResponse

from src.core.errors.error_codes import (
    ERROR_CODE_INFO,
    ErrorCode,
    ErrorCodeInfo,
    get_error_code_info,
)


logger = logging.getLogger(__name__)


@dataclass
class ApiErrorResponse:
    """
    统一错误响应结构

    Attributes:
        code: 错误码
        message: 人类可读的错误消息
        retryable: 是否可以重试
        request_id: 请求追踪ID（可选）
    """

    code: str
    message: str
    retryable: bool
    request_id: Optional[str] = None

    def to_dict(self) -> dict[str, Any]:
        """转换为字典格式"""
        result = {
            "code": self.code,
            "message": self.message,
            "retryable": self.retryable,
        }
        if self.request_id:
            result["request_id"] = self.request_id
        return result


@dataclass
class ApiErrorTranslator:
    """
    统一异常翻译器

    将各类底层异常映射为统一的错误码和 HTTP 语义。

    关键映射规则：
    - 依赖不可用（DB/Redis）-> SERVICE_NOT_READY (503)
    - 参数校验失败 -> INVALID_INPUT (422)
    - 资源不存在 -> RESOURCE_NOT_FOUND (404)
    - 状态冲突 -> STATE_CONFLICT (409)
    - 未认证 -> AUTH_REQUIRED (401)
    - 未知错误 -> INTERNAL_ERROR (500)
    """

    def translate_exception(
        self,
        exc: Exception,
        *,
        request_id: Optional[str] = None,
        override_message: Optional[str] = None,
    ) -> tuple[ErrorCode, ErrorCodeInfo, str]:
        """
        将异常翻译为错误码、错误详情和人类可读消息

        Args:
            exc: 待翻译的异常
            request_id: 请求追踪ID
            override_message: 可选的覆盖消息

        Returns:
            (错误码, 错误码详情, 错误消息)
        """
        # 1. 如果是 HTTPException，直接提取错误码和信息
        if isinstance(exc, HTTPException):
            return self._translate_http_exception(exc, override_message)

        # 2. 业务逻辑层自定义异常
        code, info = self._map_business_exception(exc)
        if code is not None:
            message = override_message or str(exc) or info.default_message
            return code, info, message

        # 3. 数据访问层异常（数据库、Redis 等）
        code, info = self._map_data_access_exception(exc)
        if code is not None:
            message = override_message or info.default_message
            return code, info, message

        # 4. 验证异常
        code, info = self._map_validation_exception(exc)
        if code is not None:
            message = override_message or str(exc) or info.default_message
            return code, info, message

        # 5. LLM 相关异常
        code, info = self._map_llm_exception(exc)
        if code is not None:
            message = override_message or info.default_message
            return code, info, message

        # 6. 未知异常 -> INTERNAL_ERROR
        logger.warning(
            "Unhandled exception translated to INTERNAL_ERROR: %s\n%s",
            exc,
            "".join(traceback.format_exception(type(exc), exc, exc.__traceback__)),
        )
        info = get_error_code_info(ErrorCode.INTERNAL_ERROR)
        message = override_message or info.default_message
        return ErrorCode.INTERNAL_ERROR, info, message

    def _translate_http_exception(
        self,
        exc: HTTPException,
        override_message: Optional[str],
    ) -> tuple[ErrorCode, ErrorCodeInfo, str]:
        """翻译 FastAPI HTTPException"""
        status_code = exc.status_code
        detail = override_message or exc.detail

        if status_code == 400:
            return (
                ErrorCode.BAD_REQUEST,
                get_error_code_info(ErrorCode.BAD_REQUEST),
                detail,
            )
        if status_code == 401:
            return (
                ErrorCode.AUTH_REQUIRED,
                get_error_code_info(ErrorCode.AUTH_REQUIRED),
                detail,
            )
        if status_code == 404:
            return (
                ErrorCode.RESOURCE_NOT_FOUND,
                get_error_code_info(ErrorCode.RESOURCE_NOT_FOUND),
                detail,
            )
        if status_code == 409:
            return (
                ErrorCode.STATE_CONFLICT,
                get_error_code_info(ErrorCode.STATE_CONFLICT),
                detail,
            )
        if status_code == 422:
            return (
                ErrorCode.INVALID_INPUT,
                get_error_code_info(ErrorCode.INVALID_INPUT),
                detail,
            )
        if status_code == 503:
            return (
                ErrorCode.SERVICE_NOT_READY,
                get_error_code_info(ErrorCode.SERVICE_NOT_READY),
                detail,
            )
        # 其他 4xx 错误映射到 BAD_REQUEST
        if 400 <= status_code < 500:
            return (
                ErrorCode.BAD_REQUEST,
                get_error_code_info(ErrorCode.BAD_REQUEST),
                detail,
            )
        # 5xx 错误映射到 INTERNAL_ERROR
        return (
            ErrorCode.INTERNAL_ERROR,
            get_error_code_info(ErrorCode.INTERNAL_ERROR),
            detail,
        )

    def _map_business_exception(
        self,
        exc: Exception,
    ) -> tuple[Optional[ErrorCode], Optional[ErrorCodeInfo]]:
        """映射业务逻辑层异常"""
        exc_type_name = type(exc).__name__
        exc_message = str(exc).lower()

        # ResourceNotFoundError -> 404
        if exc_type_name == "ResourceNotFoundError":
            return (
                ErrorCode.RESOURCE_NOT_FOUND,
                get_error_code_info(ErrorCode.RESOURCE_NOT_FOUND),
            )

        # ValidationError -> 422
        if exc_type_name == "ValidationError":
            return (
                ErrorCode.INVALID_INPUT,
                get_error_code_info(ErrorCode.INVALID_INPUT),
            )

        # AgentSystemException 或其子类
        if exc_type_name in (
            "AgentSystemException",
            "AgentInitializationError",
            "AgentExecutionError",
            "ConfigurationError",
        ):
            # 如果消息包含 "not found" 或 "不存在"
            if "not found" in exc_message or "不存在" in exc_message:
                return (
                    ErrorCode.RESOURCE_NOT_FOUND,
                    get_error_code_info(ErrorCode.RESOURCE_NOT_FOUND),
                )
            # 默认识别为内部错误
            return (
                ErrorCode.INTERNAL_ERROR,
                get_error_code_info(ErrorCode.INTERNAL_ERROR),
            )

        # ValueError 通常是参数无效
        if exc_type_name == "ValueError":
            if "not found" in exc_message or "不存在" in exc_message:
                return (
                    ErrorCode.RESOURCE_NOT_FOUND,
                    get_error_code_info(ErrorCode.RESOURCE_NOT_FOUND),
                )
            if "conflict" in exc_message or "冲突" in exc_message:
                return (
                    ErrorCode.STATE_CONFLICT,
                    get_error_code_info(ErrorCode.STATE_CONFLICT),
                )
            return (
                ErrorCode.INVALID_INPUT,
                get_error_code_info(ErrorCode.INVALID_INPUT),
            )

        return None, None

    def _map_data_access_exception(
        self,
        exc: Exception,
    ) -> tuple[Optional[ErrorCode], Optional[ErrorCodeInfo]]:
        """映射数据访问层异常（数据库、Redis 等）"""
        exc_type_name = type(exc).__name__
        exc_message = str(exc).lower()

        # SQLAlchemy 异常
        if "sqlalchemy" in exc_type_name.lower():
            # 连接问题 -> 503
            if any(keyword in exc_message for keyword in ["connect", "connection", "timeout", "pool"]):
                return (
                    ErrorCode.SERVICE_NOT_READY,
                    get_error_code_info(ErrorCode.SERVICE_NOT_READY),
                )
            # 操作问题 -> 500
            return (
                ErrorCode.INTERNAL_ERROR,
                get_error_code_info(ErrorCode.INTERNAL_ERROR),
            )

        # Redis 异常
        if "redis" in exc_type_name.lower() or "redis" in exc_message:
            return (
                ErrorCode.SERVICE_NOT_READY,
                get_error_code_info(ErrorCode.SERVICE_NOT_READY),
            )

        # OperationalError (数据库操作错误)
        if exc_type_name == "OperationalError":
            return (
                ErrorCode.SERVICE_NOT_READY,
                get_error_code_info(ErrorCode.SERVICE_NOT_READY),
            )

        # IntegrityError (数据完整性错误，如外键冲突)
        if exc_type_name == "IntegrityError":
            return (
                ErrorCode.STATE_CONFLICT,
                get_error_code_info(ErrorCode.STATE_CONFLICT),
            )

        return None, None

    def _map_validation_exception(
        self,
        exc: Exception,
    ) -> tuple[Optional[ErrorCode], Optional[ErrorCodeInfo]]:
        """映射验证异常"""
        exc_type_name = type(exc).__name__

        # Pydantic 验证错误
        if "ValidationError" in exc_type_name and "pydantic" in str(exc).lower():
            return (
                ErrorCode.INVALID_INPUT,
                get_error_code_info(ErrorCode.INVALID_INPUT),
            )

        return None, None

    def _map_llm_exception(
        self,
        exc: Exception,
    ) -> tuple[Optional[ErrorCode], Optional[ErrorCodeInfo]]:
        """映射 LLM 相关异常"""
        exc_type_name = type(exc).__name__
        exc_message = str(exc).lower()

        # LLMRetryableError -> SERVICE_NOT_READY (可重试)
        if exc_type_name == "LLMRetryableError":
            return (
                ErrorCode.SERVICE_NOT_READY,
                get_error_code_info(ErrorCode.SERVICE_NOT_READY),
            )

        # CircuitBreakerOpenError -> SERVICE_NOT_READY
        if exc_type_name == "CircuitBreakerOpenError":
            return (
                ErrorCode.SERVICE_NOT_READY,
                get_error_code_info(ErrorCode.SERVICE_NOT_READY),
            )

        # LLMRequestError -> SERVICE_NOT_READY (LLM 服务不可用)
        if exc_type_name == "LLMRequestError":
            return (
                ErrorCode.SERVICE_NOT_READY,
                get_error_code_info(ErrorCode.SERVICE_NOT_READY),
            )

        # LLMConfigurationError -> INVALID_INPUT (配置问题)
        if exc_type_name == "LLMConfigurationError":
            return (
                ErrorCode.INVALID_INPUT,
                get_error_code_info(ErrorCode.INVALID_INPUT),
            )

        return None, None

    def to_json_response(
        self,
        exc: Exception,
        *,
        request_id: Optional[str] = None,
        override_message: Optional[str] = None,
    ) -> JSONResponse:
        """
        将异常转换为 FastAPI JSONResponse

        Args:
            exc: 待翻译的异常
            request_id: 请求追踪ID
            override_message: 可选的覆盖消息

        Returns:
            JSONResponse with proper status code and error body
        """
        code, info, message = self.translate_exception(
            exc,
            request_id=request_id,
            override_message=override_message,
        )

        response = ApiErrorResponse(
            code=code.value,
            message=message,
            retryable=info.retryable,
            request_id=request_id,
        )

        json_response = JSONResponse(
            status_code=info.http_status,
            content=response.to_dict(),
        )

        # Add X-Request-ID header if request_id is available
        if request_id:
            json_response.headers["X-Request-ID"] = request_id

        return json_response


# 全局单例
_api_error_translator: Optional[ApiErrorTranslator] = None


def get_api_error_translator() -> ApiErrorTranslator:
    """获取全局 ApiErrorTranslator 单例"""
    global _api_error_translator
    if _api_error_translator is None:
        _api_error_translator = ApiErrorTranslator()
    return _api_error_translator


async def api_exception_handler(
    request: Request,
    exc: Exception,
) -> JSONResponse:
    """
    FastAPI 全局异常处理器

    注册到 FastAPI 应用后，拦截所有未处理的异常，
    转换为统一的错误响应结构。

    Args:
        request: FastAPI 请求对象
        exc: 未处理的异常

    Returns:
        JSONResponse with unified error structure
    """
    # 尝试从请求上下文获取 request_id
    request_id = None
    if hasattr(request.state, "request_id"):
        request_id = request.state.request_id
    elif request.headers.get("X-Request-ID"):
        request_id = request.headers.get("X-Request-ID")

    translator = get_api_error_translator()
    return translator.to_json_response(
        exc,
        request_id=request_id,
    )


async def http_exception_handler(
    request: Request,
    exc: HTTPException,
) -> JSONResponse:
    """
    FastAPI HTTPException 专用异常处理器

    注意：HTTPException 需要单独的处理器，因为 FastAPI 的默认 HTTPException
    处理器优先级高于通用的 Exception 处理器。

    Args:
        request: FastAPI 请求对象
        exc: HTTPException

    Returns:
        JSONResponse with unified error structure
    """
    # 尝试从请求上下文获取 request_id
    request_id = None
    if hasattr(request.state, "request_id"):
        request_id = request.state.request_id
    elif request.headers.get("X-Request-ID"):
        request_id = request.headers.get("X-Request-ID")

    translator = get_api_error_translator()
    # 使用 detail 作为 override_message 保留原始错误信息
    return translator.to_json_response(
        exc,
        request_id=request_id,
        override_message=exc.detail,
    )
