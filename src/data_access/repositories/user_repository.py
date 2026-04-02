"""
用户Repository - 提供用户相关的数据访问方法
"""

from src.data_access.entities.user import User
from src.data_access.repositories.base_repository import create_repository

# 创建用户Repository实例
user_repository = create_repository(User)
