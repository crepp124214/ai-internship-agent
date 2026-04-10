"""
ApiErrorTranslator 单元测试
"""

import pytest
from fastapi import HTTPException
from fastapi.testclient import TestClient

from src.core.errors import (
    ApiErrorResponse,
    ApiErrorTranslator,
    ErrorCode,
    get_error_code_info,
)


class TestErrorCode:
    """测试错误码定义"""

    def test_error_code_values(self):
        """验证错误码枚举值"""
        assert ErrorCode.SERVICE_NOT_READY.value == "SERVICE_NOT_READY"
        assert ErrorCode.AUTH_REQUIRED.value == "AUTH_REQUIRED"
        assert ErrorCode.BAD_REQUEST.value == "BAD_REQUEST"
        assert ErrorCode.INVALID_INPUT.value == "INVALID_INPUT"
        assert ErrorCode.RESOURCE_NOT_FOUND.value == "RESOURCE_NOT_FOUND"
        assert ErrorCode.STATE_CONFLICT.value == "STATE_CONFLICT"
        assert ErrorCode.INTERNAL_ERROR.value == "INTERNAL_ERROR"

    def test_error_code_info(self):
        """验证错误码详情映射"""
        info = get_error_code_info(ErrorCode.SERVICE_NOT_READY)
        assert info.http_status == 503
        assert info.retryable is True

        info = get_error_code_info(ErrorCode.AUTH_REQUIRED)
        assert info.http_status == 401
        assert info.retryable is False

        info = get_error_code_info(ErrorCode.BAD_REQUEST)
        assert info.http_status == 400
        assert info.retryable is False

        info = get_error_code_info(ErrorCode.INVALID_INPUT)
        assert info.http_status == 422
        assert info.retryable is False

        info = get_error_code_info(ErrorCode.RESOURCE_NOT_FOUND)
        assert info.http_status == 404
        assert info.retryable is False

        info = get_error_code_info(ErrorCode.STATE_CONFLICT)
        assert info.http_status == 409
        assert info.retryable is False

        info = get_error_code_info(ErrorCode.INTERNAL_ERROR)
        assert info.http_status == 500
        assert info.retryable is True


class TestApiErrorResponse:
    """测试统一错误响应结构"""

    def test_to_dict_basic(self):
        """测试基本字典转换"""
        response = ApiErrorResponse(
            code="TEST_ERROR",
            message="Test message",
            retryable=True,
        )
        result = response.to_dict()
        assert result["code"] == "TEST_ERROR"
        assert result["message"] == "Test message"
        assert result["retryable"] is True
        assert "request_id" not in result

    def test_to_dict_with_request_id(self):
        """测试带 request_id 的字典转换"""
        response = ApiErrorResponse(
            code="TEST_ERROR",
            message="Test message",
            retryable=False,
            request_id="abc-123",
        )
        result = response.to_dict()
        assert result["request_id"] == "abc-123"


class TestApiErrorTranslator:
    """测试 ApiErrorTranslator 异常翻译功能"""

    def setup_method(self):
        """每个测试方法前的 setup"""
        self.translator = ApiErrorTranslator()

    def test_translate_http_exception_401(self):
        """测试 HTTP 401 未认证异常"""
        exc = HTTPException(status_code=401, detail="Not authenticated")
        code, info, message = self.translator.translate_exception(exc)
        assert code == ErrorCode.AUTH_REQUIRED
        assert info.http_status == 401
        assert info.retryable is False

    def test_translate_http_exception_404(self):
        """测试 HTTP 404 资源不存在异常"""
        exc = HTTPException(status_code=404, detail="Resource not found")
        code, info, message = self.translator.translate_exception(exc)
        assert code == ErrorCode.RESOURCE_NOT_FOUND
        assert info.http_status == 404
        assert info.retryable is False

    def test_translate_http_exception_409(self):
        """测试 HTTP 409 状态冲突异常"""
        exc = HTTPException(status_code=409, detail="State conflict")
        code, info, message = self.translator.translate_exception(exc)
        assert code == ErrorCode.STATE_CONFLICT
        assert info.http_status == 409
        assert info.retryable is False

    def test_translate_http_exception_422(self):
        """测试 HTTP 422 参数无效异常"""
        exc = HTTPException(status_code=422, detail="Validation error")
        code, info, message = self.translator.translate_exception(exc)
        assert code == ErrorCode.INVALID_INPUT
        assert info.http_status == 422
        assert info.retryable is False

    def test_translate_http_exception_503(self):
        """测试 HTTP 503 服务不可用异常"""
        exc = HTTPException(status_code=503, detail="Service unavailable")
        code, info, message = self.translator.translate_exception(exc)
        assert code == ErrorCode.SERVICE_NOT_READY
        assert info.http_status == 503
        assert info.retryable is True

    def test_translate_http_exception_403(self):
        """测试 HTTP 403 禁止访问异常"""
        exc = HTTPException(status_code=403, detail="Access forbidden")
        code, info, message = self.translator.translate_exception(exc)
        assert code == ErrorCode.FORBIDDEN
        assert info.http_status == 403
        assert info.retryable is False

    def test_translate_resource_not_found_error(self):
        """测试业务层 ResourceNotFoundError"""
        from src.utils.exceptions import ResourceNotFoundError

        exc = ResourceNotFoundError("User not found")
        code, info, message = self.translator.translate_exception(exc)
        assert code == ErrorCode.RESOURCE_NOT_FOUND
        assert info.http_status == 404
        assert info.retryable is False

    def test_translate_validation_error(self):
        """测试业务层 ValidationError"""
        from src.utils.exceptions import ValidationError

        exc = ValidationError("Invalid input")
        code, info, message = self.translator.translate_exception(exc)
        assert code == ErrorCode.INVALID_INPUT
        assert info.http_status == 422
        assert info.retryable is False

    def test_translate_value_error_not_found(self):
        """测试 ValueError with 'not found' 映射到资源不存在"""
        exc = ValueError("job not found")
        code, info, message = self.translator.translate_exception(exc)
        assert code == ErrorCode.RESOURCE_NOT_FOUND
        assert info.http_status == 404

    def test_translate_value_error_invalid_input(self):
        """测试普通 ValueError 映射到参数无效"""
        exc = ValueError("invalid parameter")
        code, info, message = self.translator.translate_exception(exc)
        assert code == ErrorCode.INVALID_INPUT
        assert info.http_status == 422

    def test_translate_unknown_exception(self):
        """测试未知异常映射到内部错误"""
        exc = RuntimeError("Something went wrong")
        code, info, message = self.translator.translate_exception(exc)
        assert code == ErrorCode.INTERNAL_ERROR
        assert info.http_status == 500
        assert info.retryable is True

    def test_translate_with_override_message(self):
        """测试使用覆盖消息"""
        exc = ValueError("original message")
        code, info, message = self.translator.translate_exception(
            exc,
            override_message="custom message",
        )
        assert message == "custom message"

    def test_translate_with_request_id(self):
        """测试翻译时保留 request_id"""
        exc = RuntimeError("error")
        code, info, message = self.translator.translate_exception(
            exc,
            request_id="test-123",
        )
        # request_id 在 to_json_response 中使用
        assert code == ErrorCode.INTERNAL_ERROR

    def test_to_json_response_401(self):
        """测试转换为 JSONResponse (401)"""
        exc = HTTPException(status_code=401, detail="Not authenticated")
        response = self.translator.to_json_response(exc, request_id="req-123")
        assert response.status_code == 401
        import json

        body = json.loads(response.body)
        assert body["code"] == "AUTH_REQUIRED"
        assert body["message"] == "Not authenticated"
        assert body["retryable"] is False
        assert body["request_id"] == "req-123"

    def test_to_json_response_500(self):
        """测试转换为 JSONResponse (500) - 未知异常隐藏内部细节"""
        exc = RuntimeError("Database connection failed")
        response = self.translator.to_json_response(exc, request_id="req-456")
        assert response.status_code == 500
        import json

        body = json.loads(response.body)
        assert body["code"] == "INTERNAL_ERROR"
        # 设计要求：未知异常隐藏内部细节，使用默认错误消息
        assert "内部错误" in body["message"] or body["message"] == "内部错误"
        assert body["retryable"] is True
        assert body["request_id"] == "req-456"

    def test_to_json_response_503_db_error(self):
        """测试数据库错误转换为 503"""
        # Create a subclass that mimics SQLAlchemy OperationalError
        class OperationalError(Exception):
            """Simulates SQLAlchemy OperationalError"""
            pass

        exc = OperationalError("Could not connect to database")

        code, info, message = self.translator.translate_exception(exc)
        # Since OperationalError is caught by name in the translator,
        # it maps to SERVICE_NOT_READY
        assert code == ErrorCode.SERVICE_NOT_READY
        assert info.http_status == 503
        assert info.retryable is True

    def test_to_json_response_403(self):
        """测试转换为 JSONResponse (403 Forbidden)"""
        exc = HTTPException(status_code=403, detail="Access forbidden")
        response = self.translator.to_json_response(exc, request_id="req-789")
        assert response.status_code == 403
        import json

        body = json.loads(response.body)
        assert body["code"] == "FORBIDDEN"
        assert body["message"] == "Access forbidden"
        assert body["retryable"] is False
        assert body["request_id"] == "req-789"
