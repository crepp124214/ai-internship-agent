"""数据库连接和初始化。"""

from typing import Any

from sqlalchemy import create_engine, text
from sqlalchemy.orm import declarative_base, sessionmaker

from src.utils.config_loader import get_settings

# 获取配置
settings = get_settings()

# 创建数据库引擎
engine = create_engine(
    settings.DATABASE_URL,
    pool_size=20,
    max_overflow=10,
    pool_recycle=3600,
    echo=settings.APP_DEBUG,
)

# OpenTelemetry SQLAlchemy instrumentation (best-effort)
try:
    from opentelemetry.instrumentation.sqlalchemy import SQLAlchemyInstrumentor  # type: ignore
    SQLAlchemyInstrumentor().instrument_engine(engine)
except Exception:
    pass

# 创建SessionLocal类
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# 创建Base类供其他模型继承
Base = declarative_base()


def get_db() -> Any:
    """
    获取数据库会话生成器

    Yields:
        数据库会话
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def create_tables() -> None:
    """
    创建所有数据库表

    Raises:
        Exception: 表创建失败
    """
    try:
        # 导入所有模型以确保它们被注册到Base.metadata中
        from src.data_access.entities import user, resume, job, interview

        Base.metadata.create_all(bind=engine)
    except Exception as e:
        raise Exception(f"创建数据库表失败: {str(e)}") from e


def check_database_connection() -> None:
    """检查当前数据库连接是否可用。"""
    try:
        with engine.connect() as connection:
            connection.execute(text("SELECT 1"))
    except Exception as e:
        raise Exception(f"数据库连接检查失败: {str(e)}") from e


def drop_tables() -> None:
    """
    删除所有数据库表

    Raises:
        Exception: 表删除失败
    """
    try:
        Base.metadata.drop_all(bind=engine)
    except Exception as e:
        raise Exception(f"删除数据库表失败: {str(e)}") from e


def init_db() -> None:
    """
    初始化数据库

    创建所有表，如果表已存在则跳过

    Raises:
        Exception: 数据库初始化失败
    """
    try:
        create_tables()
    except Exception as e:
        raise Exception(f"初始化数据库失败: {str(e)}") from e


def reset_db() -> None:
    """
    重置数据库

    删除所有表并重新创建

    Raises:
        Exception: 数据库重置失败
    """
    try:
        drop_tables()
        create_tables()
    except Exception as e:
        raise Exception(f"重置数据库失败: {str(e)}") from e
