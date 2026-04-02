"""
测试ORM实体模型
"""

import pytest
from datetime import datetime
from sqlalchemy import inspect

from src.data_access.database import Base, engine
from src.data_access.entities import (
    User,
    UserProfile,
    Resume,
    ResumeOptimization,
    Job,
    JobApplication,
    InterviewQuestion,
    InterviewRecord,
    InterviewSession,
)


class TestUserEntity:
    """测试用户实体"""

    def test_user_table_exists(self):
        """测试用户表是否存在"""
        inspector = inspect(engine)
        assert "users" in inspector.get_table_names()

    def test_user_columns(self):
        """测试用户表列结构"""
        inspector = inspect(engine)
        columns = [col["name"] for col in inspector.get_columns("users")]

        required_columns = [
            "id",
            "username",
            "email",
            "password_hash",
            "name",
            "avatar_url",
            "phone",
            "bio",
            "is_active",
            "is_verified",
            "created_at",
            "updated_at",
        ]

        for col in required_columns:
            assert col in columns, f"用户表缺少列: {col}"

    def test_user_relationships(self):
        """测试用户关系映射"""
        # 检查关系是否存在
        assert hasattr(User, "profile"), "User缺少profile关系"
        assert hasattr(User, "resumes"), "User缺少resumes关系"
        assert hasattr(User, "job_applications"), "User缺少job_applications关系"
        assert hasattr(User, "interview_records"), "User缺少interview_records关系"
        assert hasattr(User, "interview_sessions"), "User缺少interview_sessions关系"


class TestUserProfileEntity:
    """测试用户资料实体"""

    def test_user_profile_table_exists(self):
        """测试用户资料表是否存在"""
        inspector = inspect(engine)
        assert "user_profiles" in inspector.get_table_names()

    def test_user_profile_columns(self):
        """测试用户资料表列结构"""
        inspector = inspect(engine)
        columns = [col["name"] for col in inspector.get_columns("user_profiles")]

        required_columns = [
            "id",
            "user_id",
            "education",
            "work_experience",
            "skills",
            "preferences",
            "job_target",
            "created_at",
            "updated_at",
        ]

        for col in required_columns:
            assert col in columns, f"用户资料表缺少列: {col}"

    def test_user_profile_relationships(self):
        """测试用户资料关系映射"""
        assert hasattr(UserProfile, "user"), "UserProfile缺少user关系"


class TestResumeEntity:
    """测试简历实体"""

    def test_resume_table_exists(self):
        """测试简历表是否存在"""
        inspector = inspect(engine)
        assert "resumes" in inspector.get_table_names()

    def test_resume_columns(self):
        """测试简历表列结构"""
        inspector = inspect(engine)
        columns = [col["name"] for col in inspector.get_columns("resumes")]

        required_columns = [
            "id",
            "user_id",
            "title",
            "original_file_path",
            "file_name",
            "file_type",
            "file_size",
            "processed_content",
            "resume_text",
            "language",
            "is_default",
            "created_at",
            "updated_at",
        ]

        for col in required_columns:
            assert col in columns, f"简历表缺少列: {col}"

    def test_resume_relationships(self):
        """测试简历关系映射"""
        assert hasattr(Resume, "user"), "Resume缺少user关系"
        assert hasattr(Resume, "resume_optimizations"), "Resume缺少resume_optimizations关系"
        assert hasattr(Resume, "job_applications"), "Resume缺少job_applications关系"


class TestResumeOptimizationEntity:
    """测试简历优化实体"""

    def test_resume_optimization_table_exists(self):
        """测试简历优化表是否存在"""
        inspector = inspect(engine)
        assert "resume_optimizations" in inspector.get_table_names()

    def test_resume_optimization_columns(self):
        """测试简历优化表列结构"""
        inspector = inspect(engine)
        columns = [col["name"] for col in inspector.get_columns("resume_optimizations")]

        required_columns = [
            "id",
            "resume_id",
            "original_text",
            "optimized_text",
            "optimization_type",
            "keywords",
            "score",
            "ai_suggestion",
            "created_at",
            "updated_at",
        ]

        for col in required_columns:
            assert col in columns, f"简历优化表缺少列: {col}"

    def test_resume_optimization_relationships(self):
        """测试简历优化关系映射"""
        assert hasattr(ResumeOptimization, "resume"), "ResumeOptimization缺少resume关系"


class TestJobEntity:
    """测试岗位实体"""

    def test_job_table_exists(self):
        """测试岗位表是否存在"""
        inspector = inspect(engine)
        assert "jobs" in inspector.get_table_names()

    def test_job_columns(self):
        """测试岗位表列结构"""
        inspector = inspect(engine)
        columns = [col["name"] for col in inspector.get_columns("jobs")]

        required_columns = [
            "id",
            "title",
            "company",
            "company_logo",
            "location",
            "salary",
            "salary_min",
            "salary_max",
            "work_type",
            "experience",
            "education",
            "description",
            "requirements",
            "welfare",
            "tags",
            "source",
            "source_url",
            "source_id",
            "is_active",
            "publish_date",
            "deadline",
            "created_at",
            "updated_at",
        ]

        for col in required_columns:
            assert col in columns, f"岗位表缺少列: {col}"

    def test_job_relationships(self):
        """测试岗位关系映射"""
        assert hasattr(Job, "job_applications"), "Job缺少job_applications关系"
        assert hasattr(Job, "interview_records"), "Job缺少interview_records关系"
        assert hasattr(Job, "interview_sessions"), "Job缺少interview_sessions关系"


class TestJobApplicationEntity:
    """测试岗位申请实体"""

    def test_job_application_table_exists(self):
        """测试岗位申请表是否存在"""
        inspector = inspect(engine)
        assert "job_applications" in inspector.get_table_names()

    def test_job_application_columns(self):
        """测试岗位申请表列结构"""
        inspector = inspect(engine)
        columns = [col["name"] for col in inspector.get_columns("job_applications")]

        required_columns = [
            "id",
            "user_id",
            "job_id",
            "resume_id",
            "application_date",
            "status",
            "status_updated_at",
            "notes",
            "created_at",
            "updated_at",
        ]

        for col in required_columns:
            assert col in columns, f"岗位申请表缺少列: {col}"

    def test_job_application_relationships(self):
        """测试岗位申请关系映射"""
        assert hasattr(JobApplication, "user"), "JobApplication缺少user关系"
        assert hasattr(JobApplication, "job"), "JobApplication缺少job关系"
        assert hasattr(JobApplication, "resume"), "JobApplication缺少resume关系"


class TestInterviewQuestionEntity:
    """测试面试问题实体"""

    def test_interview_question_table_exists(self):
        """测试面试问题表是否存在"""
        inspector = inspect(engine)
        assert "interview_questions" in inspector.get_table_names()

    def test_interview_question_columns(self):
        """测试面试问题表列结构"""
        inspector = inspect(engine)
        columns = [col["name"] for col in inspector.get_columns("interview_questions")]

        required_columns = [
            "id",
            "question_type",
            "difficulty",
            "question_text",
            "category",
            "tags",
            "sample_answer",
            "reference_material",
            "is_active",
            "created_at",
            "updated_at",
        ]

        for col in required_columns:
            assert col in columns, f"面试问题表缺少列: {col}"

    def test_interview_question_relationships(self):
        """测试面试问题关系映射"""
        assert hasattr(InterviewQuestion, "interview_records"), "InterviewQuestion缺少interview_records关系"


class TestInterviewRecordEntity:
    """测试面试记录实体"""

    def test_interview_record_table_exists(self):
        """测试面试记录表是否存在"""
        inspector = inspect(engine)
        assert "interview_records" in inspector.get_table_names()

    def test_interview_record_columns(self):
        """测试面试记录表列结构"""
        inspector = inspect(engine)
        columns = [col["name"] for col in inspector.get_columns("interview_records")]

        required_columns = [
            "id",
            "user_id",
            "job_id",
            "question_id",
            "user_answer",
            "ai_evaluation",
            "score",
            "feedback",
            "answered_at",
            "created_at",
            "updated_at",
        ]

        for col in required_columns:
            assert col in columns, f"面试记录表缺少列: {col}"

    def test_interview_record_relationships(self):
        """测试面试记录关系映射"""
        assert hasattr(InterviewRecord, "user"), "InterviewRecord缺少user关系"
        assert hasattr(InterviewRecord, "job"), "InterviewRecord缺少job关系"
        assert hasattr(InterviewRecord, "question"), "InterviewRecord缺少question关系"


class TestInterviewSessionEntity:
    """测试面试会话实体"""

    def test_interview_session_table_exists(self):
        """测试面试会话表是否存在"""
        inspector = inspect(engine)
        assert "interview_sessions" in inspector.get_table_names()

    def test_interview_session_columns(self):
        """测试面试会话表列结构"""
        inspector = inspect(engine)
        columns = [col["name"] for col in inspector.get_columns("interview_sessions")]

        required_columns = [
            "id",
            "user_id",
            "job_id",
            "session_type",
            "duration",
            "total_questions",
            "answered_questions",
            "average_score",
            "completed",
            "started_at",
            "completed_at",
            "created_at",
            "updated_at",
        ]

        for col in required_columns:
            assert col in columns, f"面试会话表缺少列: {col}"

    def test_interview_session_relationships(self):
        """测试面试会话关系映射"""
        assert hasattr(InterviewSession, "user"), "InterviewSession缺少user关系"
        assert hasattr(InterviewSession, "job"), "InterviewSession缺少job关系"


class TestEntityRelationships:
    """测试实体间关系完整性"""

    def test_foreign_key_constraints(self):
        """测试外键约束"""
        inspector = inspect(engine)

        # 测试 UserProfile 的外键
        user_profile_fks = inspector.get_foreign_keys("user_profiles")
        assert any(fk["constrained_columns"] == ["user_id"] for fk in user_profile_fks)

        # 测试 Resume 的外键
        resume_fks = inspector.get_foreign_keys("resumes")
        assert any(fk["constrained_columns"] == ["user_id"] for fk in resume_fks)

        # 测试 ResumeOptimization 的外键
        resume_opt_fks = inspector.get_foreign_keys("resume_optimizations")
        assert any(fk["constrained_columns"] == ["resume_id"] for fk in resume_opt_fks)

        # 测试 JobApplication 的外键
        job_app_fks = inspector.get_foreign_keys("job_applications")
        assert any(fk["constrained_columns"] == ["user_id"] for fk in job_app_fks)
        assert any(fk["constrained_columns"] == ["job_id"] for fk in job_app_fks)
        assert any(fk["constrained_columns"] == ["resume_id"] for fk in job_app_fks)

        # 测试 InterviewRecord 的外键
        interview_record_fks = inspector.get_foreign_keys("interview_records")
        assert any(fk["constrained_columns"] == ["user_id"] for fk in interview_record_fks)
        assert any(fk["constrained_columns"] == ["job_id"] for fk in interview_record_fks)
        assert any(fk["constrained_columns"] == ["question_id"] for fk in interview_record_fks)

        # 测试 InterviewSession 的外键
        interview_session_fks = inspector.get_foreign_keys("interview_sessions")
        assert any(fk["constrained_columns"] == ["user_id"] for fk in interview_session_fks)
        assert any(fk["constrained_columns"] == ["job_id"] for fk in interview_session_fks)


@pytest.fixture(scope="module", autouse=True)
def setup_database():
    """设置测试数据库"""
    # 创建所有表
    Base.metadata.create_all(bind=engine)

    yield

    # 清理数据库
    Base.metadata.drop_all(bind=engine)
