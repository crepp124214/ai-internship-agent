"""测试 ORM 实体模型基础结构。"""

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

    def test_user_table_name(self):
        """测试用户表名称"""
        assert User.__tablename__ == "users"

    def test_user_has_required_columns(self):
        """测试用户是否有必需的列"""
        assert hasattr(User, "id")
        assert hasattr(User, "username")
        assert hasattr(User, "email")
        assert hasattr(User, "password_hash")
        assert hasattr(User, "name")
        assert hasattr(User, "avatar_url")
        assert hasattr(User, "phone")
        assert hasattr(User, "bio")
        assert hasattr(User, "is_active")
        assert hasattr(User, "is_verified")
        assert hasattr(User, "created_at")
        assert hasattr(User, "updated_at")

    def test_user_relationships(self):
        """测试用户关系映射"""
        assert hasattr(User, "profile")
        assert hasattr(User, "resumes")
        assert hasattr(User, "job_applications")
        assert hasattr(User, "interview_records")
        assert hasattr(User, "interview_sessions")


class TestUserProfileEntity:
    """测试用户资料实体"""

    def test_user_profile_table_name(self):
        """测试用户资料表名称"""
        assert UserProfile.__tablename__ == "user_profiles"

    def test_user_profile_has_required_columns(self):
        """测试用户资料是否有必需的列"""
        assert hasattr(UserProfile, "id")
        assert hasattr(UserProfile, "user_id")
        assert hasattr(UserProfile, "education")
        assert hasattr(UserProfile, "work_experience")
        assert hasattr(UserProfile, "skills")
        assert hasattr(UserProfile, "preferences")
        assert hasattr(UserProfile, "job_target")
        assert hasattr(UserProfile, "created_at")
        assert hasattr(UserProfile, "updated_at")

    def test_user_profile_relationships(self):
        """测试用户资料关系映射"""
        assert hasattr(UserProfile, "user")


class TestResumeEntity:
    """测试简历实体"""

    def test_resume_table_name(self):
        """测试简历表名称"""
        assert Resume.__tablename__ == "resumes"

    def test_resume_has_required_columns(self):
        """测试简历是否有必需的列"""
        assert hasattr(Resume, "id")
        assert hasattr(Resume, "user_id")
        assert hasattr(Resume, "title")
        assert hasattr(Resume, "original_file_path")
        assert hasattr(Resume, "file_type")
        assert hasattr(Resume, "processed_content")
        assert hasattr(Resume, "resume_text")
        assert hasattr(Resume, "language")
        assert hasattr(Resume, "is_default")
        assert hasattr(Resume, "created_at")
        assert hasattr(Resume, "updated_at")

    def test_resume_relationships(self):
        """测试简历关系映射"""
        assert hasattr(Resume, "user")
        assert hasattr(Resume, "resume_optimizations")
        assert hasattr(Resume, "job_applications")


class TestResumeOptimizationEntity:
    """测试简历优化实体"""

    def test_resume_optimization_table_name(self):
        """测试简历优化表名称"""
        assert ResumeOptimization.__tablename__ == "resume_optimizations"

    def test_resume_optimization_has_required_columns(self):
        """测试简历优化是否有必需的列"""
        assert hasattr(ResumeOptimization, "id")
        assert hasattr(ResumeOptimization, "resume_id")
        assert hasattr(ResumeOptimization, "original_text")
        assert hasattr(ResumeOptimization, "optimized_text")
        assert hasattr(ResumeOptimization, "optimization_type")
        assert hasattr(ResumeOptimization, "keywords")
        assert hasattr(ResumeOptimization, "score")
        assert hasattr(ResumeOptimization, "ai_suggestion")
        assert hasattr(ResumeOptimization, "status")
        assert hasattr(ResumeOptimization, "fallback_used")
        assert hasattr(ResumeOptimization, "created_at")
        assert hasattr(ResumeOptimization, "updated_at")

    def test_resume_optimization_relationships(self):
        """测试简历优化关系映射"""
        assert hasattr(ResumeOptimization, "resume")


class TestJobEntity:
    """测试岗位实体"""

    def test_job_table_name(self):
        """测试岗位表名称"""
        assert Job.__tablename__ == "jobs"

    def test_job_has_required_columns(self):
        """测试岗位是否有必需的列"""
        assert hasattr(Job, "id")
        assert hasattr(Job, "title")
        assert hasattr(Job, "company")
        assert hasattr(Job, "company_logo")
        assert hasattr(Job, "location")
        assert hasattr(Job, "salary")
        assert hasattr(Job, "salary_min")
        assert hasattr(Job, "salary_max")
        assert hasattr(Job, "work_type")
        assert hasattr(Job, "experience")
        assert hasattr(Job, "education")
        assert hasattr(Job, "description")
        assert hasattr(Job, "requirements")
        assert hasattr(Job, "welfare")
        assert hasattr(Job, "tags")
        assert hasattr(Job, "source")
        assert hasattr(Job, "source_url")
        assert hasattr(Job, "source_id")
        assert hasattr(Job, "is_active")
        assert hasattr(Job, "publish_date")
        assert hasattr(Job, "deadline")
        assert hasattr(Job, "created_at")
        assert hasattr(Job, "updated_at")
        # JobMatchResult fields (should be on the Job entity relationships)
        assert hasattr(Job, "job_match_results")

    def test_job_relationships(self):
        """测试岗位关系映射"""
        assert hasattr(Job, "job_applications")
        assert hasattr(Job, "interview_records")
        assert hasattr(Job, "interview_sessions")


class TestJobApplicationEntity:
    """测试岗位申请实体"""

    def test_job_application_table_name(self):
        """测试岗位申请表名称"""
        assert JobApplication.__tablename__ == "job_applications"

    def test_job_application_has_required_columns(self):
        """测试岗位申请是否有必需的列"""
        assert hasattr(JobApplication, "id")
        assert hasattr(JobApplication, "user_id")
        assert hasattr(JobApplication, "job_id")
        assert hasattr(JobApplication, "resume_id")
        assert hasattr(JobApplication, "application_date")
        assert hasattr(JobApplication, "status")
        assert hasattr(JobApplication, "status_updated_at")
        assert hasattr(JobApplication, "notes")
        assert hasattr(JobApplication, "created_at")
        assert hasattr(JobApplication, "updated_at")

    def test_job_application_relationships(self):
        """测试岗位申请关系映射"""
        assert hasattr(JobApplication, "user")
        assert hasattr(JobApplication, "job")
        assert hasattr(JobApplication, "resume")


class TestInterviewQuestionEntity:
    """测试面试问题实体"""

    def test_interview_question_table_name(self):
        """测试面试问题表名称"""
        assert InterviewQuestion.__tablename__ == "interview_questions"

    def test_interview_question_has_required_columns(self):
        """测试面试问题是否有必需的列"""
        assert hasattr(InterviewQuestion, "id")
        assert hasattr(InterviewQuestion, "question_type")
        assert hasattr(InterviewQuestion, "difficulty")
        assert hasattr(InterviewQuestion, "question_text")
        assert hasattr(InterviewQuestion, "category")
        assert hasattr(InterviewQuestion, "tags")
        assert hasattr(InterviewQuestion, "sample_answer")
        assert hasattr(InterviewQuestion, "reference_material")
        assert hasattr(InterviewQuestion, "is_active")
        assert hasattr(InterviewQuestion, "created_at")
        assert hasattr(InterviewQuestion, "updated_at")

    def test_interview_question_relationships(self):
        """测试面试问题关系映射"""
        assert hasattr(InterviewQuestion, "interview_records")


class TestInterviewRecordEntity:
    """测试面试记录实体"""

    def test_interview_record_table_name(self):
        """测试面试记录表名称"""
        assert InterviewRecord.__tablename__ == "interview_records"

    def test_interview_record_has_required_columns(self):
        """测试面试记录是否有必需的列"""
        assert hasattr(InterviewRecord, "id")
        assert hasattr(InterviewRecord, "user_id")
        assert hasattr(InterviewRecord, "job_id")
        assert hasattr(InterviewRecord, "question_id")
        assert hasattr(InterviewRecord, "user_answer")
        assert hasattr(InterviewRecord, "ai_evaluation")
        assert hasattr(InterviewRecord, "score")
        assert hasattr(InterviewRecord, "feedback")
        assert hasattr(InterviewRecord, "status")
        assert hasattr(InterviewRecord, "fallback_used")
        assert hasattr(InterviewRecord, "answered_at")
        assert hasattr(InterviewRecord, "created_at")
        assert hasattr(InterviewRecord, "updated_at")

    def test_interview_record_relationships(self):
        """测试面试记录关系映射"""
        assert hasattr(InterviewRecord, "user")
        assert hasattr(InterviewRecord, "job")
        assert hasattr(InterviewRecord, "question")


class TestInterviewSessionEntity:
    """测试面试会话实体"""

    def test_interview_session_table_name(self):
        """测试面试会话表名称"""
        assert InterviewSession.__tablename__ == "interview_sessions"

    def test_interview_session_has_required_columns(self):
        """测试面试会话是否有必需的列"""
        assert hasattr(InterviewSession, "id")
        assert hasattr(InterviewSession, "user_id")
        assert hasattr(InterviewSession, "job_id")
        assert hasattr(InterviewSession, "session_type")
        assert hasattr(InterviewSession, "duration")
        assert hasattr(InterviewSession, "total_questions")
        assert hasattr(InterviewSession, "answered_questions")
        assert hasattr(InterviewSession, "average_score")
        assert hasattr(InterviewSession, "completed")
        assert hasattr(InterviewSession, "started_at")
        assert hasattr(InterviewSession, "completed_at")
        assert hasattr(InterviewSession, "created_at")
        assert hasattr(InterviewSession, "updated_at")

    def test_interview_session_relationships(self):
        """测试面试会话关系映射"""
        assert hasattr(InterviewSession, "user")
        assert hasattr(InterviewSession, "job")


class TestEntityStructure:
    """测试实体结构完整性"""

    def test_all_entities_have_table_names(self):
        """测试所有实体都有表名"""
        assert hasattr(User, "__tablename__")
        assert hasattr(UserProfile, "__tablename__")
        assert hasattr(Resume, "__tablename__")
        assert hasattr(ResumeOptimization, "__tablename__")
        assert hasattr(Job, "__tablename__")
        assert hasattr(JobApplication, "__tablename__")
        assert hasattr(InterviewQuestion, "__tablename__")
        assert hasattr(InterviewRecord, "__tablename__")
        assert hasattr(InterviewSession, "__tablename__")

    def test_all_entities_have_primary_key(self):
        """测试所有实体都有主键"""
        assert hasattr(User, "id")
        assert hasattr(UserProfile, "id")
        assert hasattr(Resume, "id")
        assert hasattr(ResumeOptimization, "id")
        assert hasattr(Job, "id")
        assert hasattr(JobApplication, "id")
        assert hasattr(InterviewQuestion, "id")
        assert hasattr(InterviewRecord, "id")
        assert hasattr(InterviewSession, "id")

    def test_all_entities_have_timestamps(self):
        """测试所有实体都有时间戳"""
        assert hasattr(User, "created_at") and hasattr(User, "updated_at")
        assert hasattr(UserProfile, "created_at") and hasattr(UserProfile, "updated_at")
        assert hasattr(Resume, "created_at") and hasattr(Resume, "updated_at")
        assert hasattr(ResumeOptimization, "created_at") and hasattr(ResumeOptimization, "updated_at")
        assert hasattr(Job, "created_at") and hasattr(Job, "updated_at")
        assert hasattr(JobApplication, "created_at") and hasattr(JobApplication, "updated_at")
        assert hasattr(InterviewQuestion, "created_at") and hasattr(InterviewQuestion, "updated_at")
        assert hasattr(InterviewRecord, "created_at") and hasattr(InterviewRecord, "updated_at")
        assert hasattr(InterviewSession, "created_at") and hasattr(InterviewSession, "updated_at")

    def test_new_status_fields_exist(self):
        """测试新添加的status字段存在"""
        assert hasattr(ResumeOptimization, "status")
        assert hasattr(Job, "job_match_results")  # JobMatchResult关系
        assert hasattr(InterviewRecord, "status")

    def test_new_fallback_fields_exist(self):
        """测试新添加的fallback_used字段存在"""
        assert hasattr(ResumeOptimization, "fallback_used")
        assert hasattr(Job, "job_match_results")  # JobMatchResult关系
        assert hasattr(InterviewRecord, "fallback_used")
