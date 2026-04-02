"""
自定义异常类
定义系统中使用的各种异常
"""


class AgentSystemException(Exception):
    """系统基础异常类"""

    def __init__(self, message: str, code: int = 500):
        self.message = message
        self.code = code
        super().__init__(self.message)


class AgentInitializationError(AgentSystemException):
    """Agent初始化异常"""

    def __init__(self, message: str = "Agent初始化失败"):
        super().__init__(message, code=500)


class AgentExecutionError(AgentSystemException):
    """Agent执行异常"""

    def __init__(self, message: str = "Agent执行失败"):
        super().__init__(message, code=500)


class LLMError(AgentSystemException):
    """LLM调用异常"""

    def __init__(self, message: str = "LLM调用失败"):
        super().__init__(message, code=502)


class ValidationError(AgentSystemException):
    """数据验证异常"""

    def __init__(self, message: str = "数据验证失败"):
        super().__init__(message, code=400)


class ResourceNotFoundError(AgentSystemException):
    """资源未找到异常"""

    def __init__(self, message: str = "资源未找到"):
        super().__init__(message, code=404)


class ConfigurationError(AgentSystemException):
    """配置异常"""

    def __init__(self, message: str = "配置错误"):
        super().__init__(message, code=500)
