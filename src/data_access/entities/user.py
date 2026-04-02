"""
用户模型
"""

from datetime import datetime
from typing import Optional

from sqlalchemy import Column, DateTime, Integer, String, ForeignKey, Index, Boolean, Text
from sqlalchemy.orm import relationship

from src.data_access.database import Base


class User(Base):
    """
    用户实体模型

    存储用户的基本信息，包括登录凭证和个人资料。

    Attributes:
        id: 用户主键ID
        username: 用户名（唯一）
        email: 邮箱地址（唯一）
        password_hash: 密码哈希值
        name: 真实姓名
        avatar_url: 头像URL
        phone: 电话号码
        bio: 个人简介
        is_active: 账户是否激活
        is_verified: 邮箱是否验证
        created_at: 创建时间
        updated_at: 更新时间
    """

    __tablename__ = "users"

    # 主键和基本字段
    id = Column(Integer, primary_key=True, index=True, comment="用户主键ID")
    username = Column(String(50), unique=True, index=True, nullable=False, comment="用户名")
    email = Column(String(100), unique=True, index=True, nullable=False, comment="邮箱地址")
    password_hash = Column(String(255), nullable=False, comment="密码哈希值")
    # Refresh token hash for validating refresh tokens without storing plaintext
    refresh_token_hash = Column(String(255), nullable=True, comment="刷新令牌哈希值")

    # 个人信息字段
    name = Column(String(50), nullable=False, comment="真实姓名")
    avatar_url = Column(String(255), comment="头像URL")
    phone = Column(String(20), unique=True, index=True, comment="电话号码")
    bio = Column(Text, comment="个人简介")

    # 账户状态字段
    is_active = Column(Boolean, default=True, index=True, comment="账户是否激活")
    is_verified = Column(Boolean, default=False, index=True, comment="邮箱是否验证")

    # 时间戳字段
    created_at = Column(DateTime, default=datetime.now, index=True, comment="创建时间")
    updated_at = Column(DateTime, default=datetime.now, onupdate=datetime.now, comment="更新时间")

    # 关系映射
    profile = relationship("UserProfile", back_populates="user", uselist=False, lazy="joined")
    resumes = relationship("Resume", back_populates="user", cascade="all, delete-orphan", lazy="dynamic")
    job_applications = relationship("JobApplication", back_populates="user", cascade="all, delete-orphan", lazy="dynamic")
    interview_records = relationship("InterviewRecord", back_populates="user", cascade="all, delete-orphan", lazy="dynamic")
    interview_sessions = relationship("InterviewSession", back_populates="user", cascade="all, delete-orphan", lazy="dynamic")

    # 复合索引
    __table_args__ = (
        Index('idx_user_email_active', 'email', 'is_active'),
        Index('idx_user_username_active', 'username', 'is_active'),
    )

    def __repr__(self) -> str:
        """用户对象的字符串表示"""
        return f"<User(id={self.id}, username='{self.username}', email='{self.email}')>"

    def is_admin(self) -> bool:
        """
        检查用户是否为管理员

        Returns:
            bool: 是否为管理员
        """
        return False

    def get_full_name(self) -> str:
        """
        获取用户全名

        Returns:
            str: 用户姓名
        """
        return self.name


class UserProfile(Base):
    """
    用户详细资料

    存储用户的扩展信息，包括教育背景、工作经历、技能等。

    Attributes:
        id: 资料主键ID
        user_id: 关联的用户ID（外键）
        education: 教育背景
        work_experience: 工作经历
        skills: 技能列表
        preferences: JSON格式的偏好设置
        job_target: 求职目标
        created_at: 创建时间
        updated_at: 更新时间
    """

    __tablename__ = "user_profiles"

    # 主键和外键
    id = Column(Integer, primary_key=True, index=True, comment="资料主键ID")
    user_id = Column(
        Integer,
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        unique=True,
        index=True,
        comment="关联的用户ID"
    )

    # 详细信息字段
    education = Column(Text, comment="教育背景")
    work_experience = Column(Text, comment="工作经历")
    skills = Column(String(500), index=True, comment="技能列表")
    preferences = Column(Text, comment="JSON格式的偏好设置")
    job_target = Column(String(200), index=True, comment="求职目标")

    # 时间戳字段
    created_at = Column(DateTime, default=datetime.now, comment="创建时间")
    updated_at = Column(DateTime, default=datetime.now, onupdate=datetime.now, comment="更新时间")

    # 关系映射
    user = relationship("User", back_populates="profile")

    def __repr__(self) -> str:
        """用户资料对象的字符串表示"""
        return f"<UserProfile(id={self.id}, user_id={self.user_id})>"
