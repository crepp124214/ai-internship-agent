"""
岗位Repository - 提供岗位相关的数据访问方法
"""

from src.data_access.entities.job import Job
from src.data_access.repositories.base_repository import create_repository

# 创建岗位Repository实例
job_repository = create_repository(Job)
