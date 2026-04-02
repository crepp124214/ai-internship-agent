"""
基础Repository - 提供通用的数据访问方法
"""

from typing import Any, Dict, Generic, List, Optional, Type, TypeVar

from sqlalchemy import and_, or_
from sqlalchemy.orm import Session

from src.data_access.database import Base

# 类型变量
T = TypeVar("T", bound=Base)


class PaginationResult:
    """分页结果类"""

    def __init__(
        self,
        items: List[T],
        total: int,
        page: int,
        page_size: int,
        total_pages: int
    ):
        self.items = items
        self.total = total
        self.page = page
        self.page_size = page_size
        self.total_pages = total_pages

    def to_dict(self) -> Dict[str, Any]:
        """转换为字典格式"""
        return {
            "items": self.items,
            "total": self.total,
            "page": self.page,
            "page_size": self.page_size,
            "total_pages": self.total_pages
        }


class BaseRepository(Generic[T]):
    """基础Repository类"""

    def __init__(self, model: Type[T]):
        """
        初始化方法

        Args:
            model: 对应的ORM模型类
        """
        self.model = model

    def get_by_id(self, db: Session, id: int) -> Optional[T]:
        """
        根据ID获取记录

        Args:
            db: 数据库会话
            id: 记录ID

        Returns:
            记录对象或None
        """
        return db.query(self.model).filter(self.model.id == id).first()

    def get_all(self, db: Session, order_by: Optional[str] = None) -> List[T]:
        """
        获取所有记录

        Args:
            db: 数据库会话
            order_by: 排序字段名，默认None

        Returns:
            记录列表
        """
        query = db.query(self.model)
        if order_by and hasattr(self.model, order_by):
            query = query.order_by(getattr(self.model, order_by))
        return query.all()

    def get_by_field(
        self, db: Session, field: str, value: Any, limit: Optional[int] = None
    ) -> List[T]:
        """
        根据字段值获取记录

        Args:
            db: 数据库会话
            field: 字段名
            value: 字段值
            limit: 返回数量限制

        Returns:
            记录列表
        """
        query = db.query(self.model).filter(getattr(self.model, field) == value)
        if limit:
            query = query.limit(limit)
        return query.all()

    def get_by_fields(
        self, db: Session, filters: Dict[str, Any], limit: Optional[int] = None
    ) -> List[T]:
        """
        根据多个字段值获取记录（AND条件）

        Args:
            db: 数据库会话
            filters: 字段名到值的映射字典
            limit: 返回数量限制

        Returns:
            记录列表
        """
        query = db.query(self.model)
        conditions = []
        for field, value in filters.items():
            if hasattr(self.model, field):
                conditions.append(getattr(self.model, field) == value)
        if conditions:
            query = query.filter(and_(*conditions))
        if limit:
            query = query.limit(limit)
        return query.all()

    def paginate(
        self,
        db: Session,
        page: int = 1,
        page_size: int = 20,
        filters: Optional[Dict[str, Any]] = None,
        order_by: Optional[str] = None,
        desc: bool = False
    ) -> PaginationResult:
        """
        分页查询

        Args:
            db: 数据库会话
            page: 页码，从1开始
            page_size: 每页数量
            filters: 筛选条件字典
            order_by: 排序字段
            desc: 是否降序

        Returns:
            分页结果
        """
        query = db.query(self.model)

        # 应用筛选条件
        if filters:
            conditions = []
            for field, value in filters.items():
                if hasattr(self.model, field):
                    conditions.append(getattr(self.model, field) == value)
            if conditions:
                query = query.filter(and_(*conditions))

        # 计算总数
        total = query.count()

        # 应用排序
        if order_by and hasattr(self.model, order_by):
            order_column = getattr(self.model, order_by)
            query = query.order_by(order_column.desc() if desc else order_column)

        # 应用分页
        offset = (page - 1) * page_size
        items = query.offset(offset).limit(page_size).all()

        # 计算总页数
        total_pages = (total + page_size - 1) // page_size if total > 0 else 0

        return PaginationResult(
            items=items,
            total=total,
            page=page,
            page_size=page_size,
            total_pages=total_pages
        )

    def create(self, db: Session, data: dict) -> T:
        """
        创建新记录

        Args:
            db: 数据库会话
            data: 记录数据

        Returns:
            创建的记录对象
        """
        instance = self.model(**data)
        db.add(instance)
        db.commit()
        db.refresh(instance)
        return instance

    def bulk_create(self, db: Session, data_list: List[dict]) -> List[T]:
        """
        批量创建记录

        Args:
            db: 数据库会话
            data_list: 记录数据列表

        Returns:
            创建的记录对象列表
        """
        instances = [self.model(**data) for data in data_list]
        db.bulk_save_objects(instances, return_defaults=True)
        db.commit()
        return instances

    def update(self, db: Session, id: int, data: dict) -> Optional[T]:
        """
        更新记录

        Args:
            db: 数据库会话
            id: 记录ID
            data: 更新数据

        Returns:
            更新后的记录对象或None
        """
        instance = self.get_by_id(db, id)
        if not instance:
            return None

        for key, value in data.items():
            if hasattr(instance, key):
                setattr(instance, key, value)

        db.commit()
        db.refresh(instance)
        return instance

    def bulk_update(self, db: Session, ids: List[int], data: dict) -> int:
        """
        批量更新记录

        Args:
            db: 数据库会话
            ids: 记录ID列表
            data: 更新数据

        Returns:
            更新的记录数量
        """
        query = db.query(self.model).filter(self.model.id.in_(ids))
        updated_count = query.update(data, synchronize_session=False)
        db.commit()
        return updated_count

    def delete(self, db: Session, id: int) -> bool:
        """
        删除记录

        Args:
            db: 数据库会话
            id: 记录ID

        Returns:
            是否删除成功
        """
        instance = self.get_by_id(db, id)
        if not instance:
            return False

        db.delete(instance)
        db.commit()
        return True

    def bulk_delete(self, db: Session, ids: List[int]) -> int:
        """
        批量删除记录

        Args:
            db: 数据库会话
            ids: 记录ID列表

        Returns:
            删除的记录数量
        """
        deleted_count = db.query(self.model).filter(self.model.id.in_(ids)).delete(
            synchronize_session=False
        )
        db.commit()
        return deleted_count

    def delete_by_field(self, db: Session, field: str, value: Any) -> int:
        """
        根据字段值删除记录

        Args:
            db: 数据库会话
            field: 字段名
            value: 字段值

        Returns:
            删除的记录数量
        """
        deleted_count = db.query(self.model).filter(
            getattr(self.model, field) == value
        ).delete(synchronize_session=False)
        db.commit()
        return deleted_count

    def count(self, db: Session, condition: Any = None) -> int:
        """
        统计记录数量

        Args:
            db: 数据库会话
            condition: 查询条件

        Returns:
            记录数量
        """
        query = db.query(self.model)
        if condition is not None:
            query = query.filter(condition)
        return query.count()

    def count_by_field(self, db: Session, field: str, value: Any) -> int:
        """
        统计特定字段值的记录数量

        Args:
            db: 数据库会话
            field: 字段名
            value: 字段值

        Returns:
            记录数量
        """
        return db.query(self.model).filter(
            getattr(self.model, field) == value
        ).count()

    def exists(self, db: Session, id: int) -> bool:
        """
        检查记录是否存在

        Args:
            db: 数据库会话
            id: 记录ID

        Returns:
            是否存在
        """
        return db.query(self.model.id).filter(self.model.id == id).first() is not None

    def exists_by_field(self, db: Session, field: str, value: Any) -> bool:
        """
        检查特定字段值的记录是否存在

        Args:
            db: 数据库会话
            field: 字段名
            value: 字段值

        Returns:
            是否存在
        """
        return db.query(self.model.id).filter(
            getattr(self.model, field) == value
        ).first() is not None


def create_repository(model: Type[T]) -> BaseRepository[T]:
    """
    创建Repository实例

    Args:
        model: ORM模型类

    Returns:
        Repository实例
    """
    class Repository(BaseRepository[T]):
        pass

    return Repository(model)
