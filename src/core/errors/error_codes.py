"""
错误码定义

定义系统中使用的错误码枚举，包含 HTTP 状态码、错误消息和可重试性标志。
"""

from enum import Enum
from typing import NamedTuple


class ErrorCode(str, Enum):
    """系统错误码枚举"""

    # 服务不可用 - 依赖未就绪（数据库、Redis 等）
    # HTTP: 503, retryable: true
    SERVICE_NOT_READY = "SERVICE_NOT_READY"

    # 未认证 - 缺少认证凭据或凭据无效
    # HTTP: 401, retryable: false
    AUTH_REQUIRED = "AUTH_REQUIRED"

    # 请求无效 - 请求格式错误或业务逻辑校验失败
    # HTTP: 400, retryable: false
    BAD_REQUEST = "BAD_REQUEST"

    # 参数无效 - 请求参数校验失败（Pydantic 验证）
    # HTTP: 422, retryable: false
    INVALID_INPUT = "INVALID_INPUT"

    # 资源不存在 - 请求的资源未找到
    # HTTP: 404, retryable: false
    RESOURCE_NOT_FOUND = "RESOURCE_NOT_FOUND"

    # 状态冲突 - 当前状态不允许该操作
    # HTTP: 409, retryable: false
    STATE_CONFLICT = "STATE_CONFLICT"

    # 禁止访问 - 用户无权访问该资源
    # HTTP: 403, retryable: false
    FORBIDDEN = "FORBIDDEN"

    # 内部错误 - 未预期的服务器错误
    # HTTP: 500, retryable: true
    INTERNAL_ERROR = "INTERNAL_ERROR"


class ErrorCodeInfo(NamedTuple):
    """错误码详情"""

    http_status: int
    default_message: str
    retryable: bool


# 错误码到 HTTP 状态码、默认消息和可重试性的映射
ERROR_CODE_INFO: dict[ErrorCode, ErrorCodeInfo] = {
    ErrorCode.SERVICE_NOT_READY: ErrorCodeInfo(
        http_status=503,
        default_message="依赖服务未就绪",
        retryable=True,
    ),
    ErrorCode.AUTH_REQUIRED: ErrorCodeInfo(
        http_status=401,
        default_message="未认证",
        retryable=False,
    ),
    ErrorCode.BAD_REQUEST: ErrorCodeInfo(
        http_status=400,
        default_message="请求无效",
        retryable=False,
    ),
    ErrorCode.INVALID_INPUT: ErrorCodeInfo(
        http_status=422,
        default_message="参数无效",
        retryable=False,
    ),
    ErrorCode.RESOURCE_NOT_FOUND: ErrorCodeInfo(
        http_status=404,
        default_message="资源不存在",
        retryable=False,
    ),
    ErrorCode.STATE_CONFLICT: ErrorCodeInfo(
        http_status=409,
        default_message="状态冲突",
        retryable=False,
    ),
    ErrorCode.FORBIDDEN: ErrorCodeInfo(
        http_status=403,
        default_message="禁止访问",
        retryable=False,
    ),
    ErrorCode.INTERNAL_ERROR: ErrorCodeInfo(
        http_status=500,
        default_message="内部错误",
        retryable=True,
    ),
}


def get_error_code_info(code: ErrorCode) -> ErrorCodeInfo:
    """获取错误码详情"""
    return ERROR_CODE_INFO.get(code, ERROR_CODE_INFO[ErrorCode.INTERNAL_ERROR])
