"""
ReadinessGate - 统一就绪门控模块

聚合 DB、Redis、关键配置状态检查，返回统一就绪状态。
"""

from dataclasses import dataclass
from enum import Enum
from typing import Optional

from src.data_access.database import check_database_connection
from src.utils.config_loader import get_settings


class ReadinessState(str, Enum):
    """就绪状态枚举"""
    READY = "ready"
    NOT_READY = "not_ready"


@dataclass
class ReadinessStatus:
    """
    统一就绪状态结构

    Attributes:
        state: 就绪状态 (ready/not_ready)
        reason: 未就绪原因，仅在 not_ready 时填充
        checks: 各检查项详情
    """
    state: ReadinessState
    reason: Optional[str] = None
    checks: Optional[dict] = None

    def to_dict(self) -> dict:
        """转换为字典格式"""
        result = {"status": self.state.value}
        if self.reason:
            result["reason"] = self.reason
        if self.checks:
            result["checks"] = self.checks
        return result

    @property
    def is_ready(self) -> bool:
        """快捷属性：是否就绪"""
        return self.state == ReadinessState.READY


class ReadinessGate:
    """
    就绪门控类

    聚合多种依赖检查：
    - 数据库连接
    - Redis 连接
    - 关键配置
    """

    def __init__(self):
        self._settings = get_settings()

    def check_database(self) -> tuple[bool, Optional[str]]:
        """
        检查数据库连接

        Returns:
            (is_healthy, error_message)
        """
        try:
            check_database_connection()
            return True, None
        except Exception as e:
            return False, f"database: {str(e)}"

    async def check_redis(self) -> tuple[bool, Optional[str]]:
        """
        检查 Redis 连接

        Returns:
            (is_healthy, error_message)
        """
        try:
            import redis.asyncio

            redis_url = getattr(self._settings, "REDIS_URL", "redis://localhost:6379/0")
            if not redis_url:
                return False, "redis: REDIS_URL not configured"

            client = redis.asyncio.from_url(redis_url, decode_responses=True)
            await client.ping()
            await client.aclose()
            return True, None
        except Exception as e:
            return False, f"redis: {str(e)}"

    def check_critical_config(self) -> tuple[bool, Optional[str]]:
        """
        检查关键配置

        Returns:
            (is_valid, error_message)
        """
        try:
            settings = self._settings

            # 检查 SECRET_KEY 是否为不安全默认值（仅在生产环境警告）
            secret_key = getattr(settings, "SECRET_KEY", "")
            insecure_secrets = {
                "your-secret-key-here",
                "change-me-before-production",
                "changeme",
                "secret",
            }
            if secret_key.lower() in insecure_secrets:
                env = getattr(settings, "APP_ENV", "development")
                if env.lower() in {"production", "prod", "staging"}:
                    return False, "SECRET_KEY is insecure for production"

            # 检查 DATABASE_URL
            db_url = getattr(settings, "DATABASE_URL", "")
            if not db_url:
                return False, "DATABASE_URL not configured"

            return True, None
        except Exception as e:
            return False, f"config: {str(e)}"

    async def check_all(self) -> ReadinessStatus:
        """
        执行全部就绪检查

        Returns:
            ReadinessStatus: 统一就绪状态
        """
        checks = {}
        reasons = []

        # 1. 数据库检查
        db_ok, db_err = self.check_database()
        checks["database"] = {"healthy": db_ok, "error": db_err} if db_err else {"healthy": db_ok}
        if not db_ok:
            reasons.append(db_err)

        # 2. Redis 检查
        redis_ok, redis_err = await self.check_redis()
        checks["redis"] = {"healthy": redis_ok, "error": redis_err} if redis_err else {"healthy": redis_ok}
        if not redis_ok:
            reasons.append(redis_err)

        # 3. 关键配置检查
        config_ok, config_err = self.check_critical_config()
        checks["config"] = {"valid": config_ok, "error": config_err} if config_err else {"valid": config_ok}
        if not config_ok:
            reasons.append(config_err)

        # 汇总状态
        all_ok = db_ok and redis_ok and config_ok
        state = ReadinessState.READY if all_ok else ReadinessState.NOT_READY
        reason = "; ".join(reasons) if reasons else None

        return ReadinessStatus(state=state, reason=reason, checks=checks)


# 全局单例
_readiness_gate: Optional[ReadinessGate] = None


def get_readiness_gate() -> ReadinessGate:
    """获取全局 ReadinessGate 单例"""
    global _readiness_gate
    if _readiness_gate is None:
        _readiness_gate = ReadinessGate()
    return _readiness_gate


async def check_readiness() -> ReadinessStatus:
    """
    快捷函数：执行全部就绪检查

    Returns:
        ReadinessStatus: 统一就绪状态
    """
    gate = get_readiness_gate()
    return await gate.check_all()
