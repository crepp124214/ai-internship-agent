"""
初始数据库架构

创建所有核心表
"""

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = '001_initial_schema'
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    """
    执行升级操作
    """
    # 创建用户表
    op.create_table(
        'users',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('username', sa.String(length=50), nullable=False),
        sa.Column('email', sa.String(length=100), nullable=False),
        sa.Column('password_hash', sa.String(length=255), nullable=False),
        sa.Column('name', sa.String(length=50), nullable=False),
        sa.Column('avatar_url', sa.String(length=255), nullable=True),
        sa.Column('phone', sa.String(length=20), nullable=True),
        sa.Column('bio', sa.Text(), nullable=True),
        sa.Column('is_active', sa.Boolean(), nullable=True),
        sa.Column('is_verified', sa.Boolean(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.Column('updated_at', sa.DateTime(), nullable=True),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('phone')
    )
    op.create_index('idx_user_email_active', 'users', ['email', 'is_active'], unique=False)
    op.create_index('idx_user_username_active', 'users', ['username', 'is_active'], unique=False)
    op.create_index(op.f('ix_users_created_at'), 'users', ['created_at'], unique=False)
    op.create_index(op.f('ix_users_email'), 'users', ['email'], unique=True)
    op.create_index(op.f('ix_users_id'), 'users', ['id'], unique=False)
    op.create_index(op.f('ix_users_is_active'), 'users', ['is_active'], unique=False)
    op.create_index(op.f('ix_users_is_verified'), 'users', ['is_verified'], unique=False)
    op.create_index(op.f('ix_users_phone'), 'users', ['phone'], unique=True)
    op.create_index(op.f('ix_users_username'), 'users', ['username'], unique=True)

    # 创建用户资料表
    op.create_table(
        'user_profiles',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('user_id', sa.Integer(), nullable=False),
        sa.Column('education', sa.Text(), nullable=True),
        sa.Column('work_experience', sa.Text(), nullable=True),
        sa.Column('skills', sa.String(length=500), nullable=True),
        sa.Column('preferences', sa.Text(), nullable=True),
        sa.Column('job_target', sa.String(length=200), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.Column('updated_at', sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('user_id')
    )
    op.create_index(op.f('ix_user_profiles_id'), 'user_profiles', ['id'], unique=False)
    op.create_index(op.f('ix_user_profiles_job_target'), 'user_profiles', ['job_target'], unique=False)
    op.create_index(op.f('ix_user_profiles_skills'), 'user_profiles', ['skills'], unique=False)
    op.create_index(op.f('ix_user_profiles_user_id'), 'user_profiles', ['user_id'], unique=True)

    # 创建简历表
    op.create_table(
        'resumes',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('user_id', sa.Integer(), nullable=False),
        sa.Column('title', sa.String(length=200), nullable=False),
        sa.Column('original_file_path', sa.String(length=500), nullable=False),
        sa.Column('file_name', sa.String(length=255), nullable=False),
        sa.Column('file_type', sa.String(length=20), nullable=False),
        sa.Column('file_size', sa.Integer(), nullable=True),
        sa.Column('processed_content', sa.Text(), nullable=True),
        sa.Column('resume_text', sa.Text(), nullable=True),
        sa.Column('language', sa.String(length=20), nullable=True),
        sa.Column('is_default', sa.Boolean(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.Column('updated_at', sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('idx_resume_user_default', 'resumes', ['user_id', 'is_default'], unique=False)
    op.create_index('idx_resume_user_language', 'resumes', ['user_id', 'language'], unique=False)
    op.create_index(op.f('ix_resumes_created_at'), 'resumes', ['created_at'], unique=False)
    op.create_index(op.f('ix_resumes_file_type'), 'resumes', ['file_type'], unique=False)
    op.create_index(op.f('ix_resumes_id'), 'resumes', ['id'], unique=False)
    op.create_index(op.f('ix_resumes_is_default'), 'resumes', ['is_default'], unique=False)
    op.create_index(op.f('ix_resumes_language'), 'resumes', ['language'], unique=False)
    op.create_index(op.f('ix_resumes_user_id'), 'resumes', ['user_id'], unique=False)

    # 创建简历优化表
    op.create_table(
        'resume_optimizations',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('resume_id', sa.Integer(), nullable=False),
        sa.Column('original_text', sa.Text(), nullable=True),
        sa.Column('optimized_text', sa.Text(), nullable=True),
        sa.Column('optimization_type', sa.String(length=50), nullable=False),
        sa.Column('keywords', sa.String(length=500), nullable=True),
        sa.Column('score', sa.Integer(), nullable=True),
        sa.Column('ai_suggestion', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.Column('updated_at', sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(['resume_id'], ['resumes.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_resume_optimizations_created_at'), 'resume_optimizations', ['created_at'], unique=False)
    op.create_index(op.f('ix_resume_optimizations_id'), 'resume_optimizations', ['id'], unique=False)
    op.create_index(op.f('ix_resume_optimizations_optimization_type'), 'resume_optimizations', ['optimization_type'], unique=False)
    op.create_index(op.f('ix_resume_optimizations_resume_id'), 'resume_optimizations', ['resume_id'], unique=False)
    op.create_index(op.f('ix_resume_optimizations_score'), 'resume_optimizations', ['score'], unique=False)

    # 创建岗位表
    op.create_table(
        'jobs',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('title', sa.String(length=200), nullable=False),
        sa.Column('company', sa.String(length=100), nullable=False),
        sa.Column('company_logo', sa.String(length=500), nullable=True),
        sa.Column('location', sa.String(length=100), nullable=False),
        sa.Column('salary', sa.String(length=100), nullable=True),
        sa.Column('salary_min', sa.Numeric(precision=10, scale=2), nullable=True),
        sa.Column('salary_max', sa.Numeric(precision=10, scale=2), nullable=True),
        sa.Column('work_type', sa.String(length=50), nullable=True),
        sa.Column('experience', sa.String(length=50), nullable=True),
        sa.Column('education', sa.String(length=50), nullable=True),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('requirements', sa.Text(), nullable=True),
        sa.Column('welfare', sa.Text(), nullable=True),
        sa.Column('tags', sa.String(length=500), nullable=True),
        sa.Column('source', sa.String(length=50), nullable=False),
        sa.Column('source_url', sa.String(length=500), nullable=True),
        sa.Column('source_id', sa.String(length=100), nullable=True),
        sa.Column('is_active', sa.Boolean(), nullable=True),
        sa.Column('publish_date', sa.DateTime(), nullable=True),
        sa.Column('deadline', sa.DateTime(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.Column('updated_at', sa.DateTime(), nullable=True),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('idx_job_company_location', 'jobs', ['company', 'location'], unique=False)
    op.create_index('idx_job_publish_active', 'jobs', ['publish_date', 'is_active'], unique=False)
    op.create_index('idx_job_source_active', 'jobs', ['source', 'is_active'], unique=False)
    op.create_index('idx_job_work_type_experience', 'jobs', ['work_type', 'experience'], unique=False)
    op.create_index(op.f('ix_jobs_company'), 'jobs', ['company'], unique=False)
    op.create_index(op.f('ix_jobs_created_at'), 'jobs', ['created_at'], unique=False)
    op.create_index(op.f('ix_jobs_deadline'), 'jobs', ['deadline'], unique=False)
    op.create_index(op.f('ix_jobs_education'), 'jobs', ['education'], unique=False)
    op.create_index(op.f('ix_jobs_experience'), 'jobs', ['experience'], unique=False)
    op.create_index(op.f('ix_jobs_id'), 'jobs', ['id'], unique=False)
    op.create_index(op.f('ix_jobs_is_active'), 'jobs', ['is_active'], unique=False)
    op.create_index(op.f('ix_jobs_location'), 'jobs', ['location'], unique=False)
    op.create_index(op.f('ix_jobs_publish_date'), 'jobs', ['publish_date'], unique=False)
    op.create_index(op.f('ix_jobs_source'), 'jobs', ['source'], unique=False)
    op.create_index(op.f('ix_jobs_title'), 'jobs', ['title'], unique=False)
    op.create_index(op.f('ix_jobs_work_type'), 'jobs', ['work_type'], unique=False)

    # 创建面试问题表
    op.create_table(
        'interview_questions',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('question_type', sa.String(length=50), nullable=False),
        sa.Column('difficulty', sa.String(length=20), nullable=True),
        sa.Column('question_text', sa.Text(), nullable=False),
        sa.Column('category', sa.String(length=100), nullable=True),
        sa.Column('tags', sa.String(length=500), nullable=True),
        sa.Column('sample_answer', sa.Text(), nullable=True),
        sa.Column('reference_material', sa.String(length=500), nullable=True),
        sa.Column('is_active', sa.Boolean(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.Column('updated_at', sa.DateTime(), nullable=True),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('idx_question_category_type', 'interview_questions', ['category', 'question_type'], unique=False)
    op.create_index('idx_question_type_difficulty', 'interview_questions', ['question_type', 'difficulty'], unique=False)
    op.create_index(op.f('ix_interview_questions_category'), 'interview_questions', ['category'], unique=False)
    op.create_index(op.f('ix_interview_questions_created_at'), 'interview_questions', ['created_at'], unique=False)
    op.create_index(op.f('ix_interview_questions_difficulty'), 'interview_questions', ['difficulty'], unique=False)
    op.create_index(op.f('ix_interview_questions_id'), 'interview_questions', ['id'], unique=False)
    op.create_index(op.f('ix_interview_questions_is_active'), 'interview_questions', ['is_active'], unique=False)
    op.create_index(op.f('ix_interview_questions_question_type'), 'interview_questions', ['question_type'], unique=False)

    # 创建面试记录表
    op.create_table(
        'interview_records',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('user_id', sa.Integer(), nullable=False),
        sa.Column('job_id', sa.Integer(), nullable=True),
        sa.Column('question_id', sa.Integer(), nullable=True),
        sa.Column('user_answer', sa.Text(), nullable=True),
        sa.Column('ai_evaluation', sa.Text(), nullable=True),
        sa.Column('score', sa.Integer(), nullable=True),
        sa.Column('feedback', sa.Text(), nullable=True),
        sa.Column('answered_at', sa.DateTime(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.Column('updated_at', sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(['job_id'], ['jobs.id'], ondelete='SET NULL'),
        sa.ForeignKeyConstraint(['question_id'], ['interview_questions.id'], ondelete='SET NULL'),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('idx_record_job_score', 'interview_records', ['job_id', 'score'], unique=False)
    op.create_index('idx_record_user_question', 'interview_records', ['user_id', 'question_id'], unique=False)
    op.create_index('idx_record_user_score', 'interview_records', ['user_id', 'score'], unique=False)
    op.create_index(op.f('ix_interview_records_answered_at'), 'interview_records', ['answered_at'], unique=False)
    op.create_index(op.f('ix_interview_records_id'), 'interview_records', ['id'], unique=False)
    op.create_index(op.f('ix_interview_records_job_id'), 'interview_records', ['job_id'], unique=False)
    op.create_index(op.f('ix_interview_records_question_id'), 'interview_records', ['question_id'], unique=False)
    op.create_index(op.f('ix_interview_records_score'), 'interview_records', ['score'], unique=False)
    op.create_index(op.f('ix_interview_records_user_id'), 'interview_records', ['user_id'], unique=False)

    # 创建面试会话表
    op.create_table(
        'interview_sessions',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('user_id', sa.Integer(), nullable=False),
        sa.Column('job_id', sa.Integer(), nullable=True),
        sa.Column('session_type', sa.String(length=50), nullable=True),
        sa.Column('duration', sa.Integer(), nullable=True),
        sa.Column('total_questions', sa.Integer(), nullable=True),
        sa.Column('answered_questions', sa.Integer(), nullable=True),
        sa.Column('average_score', sa.Float(), nullable=True),
        sa.Column('completed', sa.Boolean(), nullable=True),
        sa.Column('started_at', sa.DateTime(), nullable=True),
        sa.Column('completed_at', sa.DateTime(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.Column('updated_at', sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(['job_id'], ['jobs.id'], ondelete='SET NULL'),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('idx_session_job_completed', 'interview_sessions', ['job_id', 'completed'], unique=False)
    op.create_index('idx_session_user_completed', 'interview_sessions', ['user_id', 'completed'], unique=False)
    op.create_index('idx_session_user_type', 'interview_sessions', ['user_id', 'session_type'], unique=False)
    op.create_index(op.f('ix_interview_sessions_average_score'), 'interview_sessions', ['average_score'], unique=False)
    op.create_index(op.f('ix_interview_sessions_completed'), 'interview_sessions', ['completed'], unique=False)
    op.create_index(op.f('ix_interview_sessions_created_at'), 'interview_sessions', ['created_at'], unique=False)
    op.create_index(op.f('ix_interview_sessions_id'), 'interview_sessions', ['id'], unique=False)
    op.create_index(op.f('ix_interview_sessions_job_id'), 'interview_sessions', ['job_id'], unique=False)
    op.create_index(op.f('ix_interview_sessions_session_type'), 'interview_sessions', ['session_type'], unique=False)
    op.create_index(op.f('ix_interview_sessions_started_at'), 'interview_sessions', ['started_at'], unique=False)
    op.create_index(op.f('ix_interview_sessions_user_id'), 'interview_sessions', ['user_id'], unique=False)

    # 创建岗位申请表
    op.create_table(
        'job_applications',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('user_id', sa.Integer(), nullable=False),
        sa.Column('job_id', sa.Integer(), nullable=False),
        sa.Column('resume_id', sa.Integer(), nullable=False),
        sa.Column('application_date', sa.DateTime(), nullable=True),
        sa.Column('status', sa.String(length=50), nullable=True),
        sa.Column('status_updated_at', sa.DateTime(), nullable=True),
        sa.Column('notes', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.Column('updated_at', sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(['job_id'], ['jobs.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['resume_id'], ['resumes.id'], ondelete='SET NULL'),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('idx_application_date_status', 'job_applications', ['application_date', 'status'], unique=False)
    op.create_index('idx_application_job_status', 'job_applications', ['job_id', 'status'], unique=False)
    op.create_index('idx_application_user_status', 'job_applications', ['user_id', 'status'], unique=False)
    op.create_index(op.f('ix_job_applications_application_date'), 'job_applications', ['application_date'], unique=False)
    op.create_index(op.f('ix_job_applications_id'), 'job_applications', ['id'], unique=False)
    op.create_index(op.f('ix_job_applications_job_id'), 'job_applications', ['job_id'], unique=False)
    op.create_index(op.f('ix_job_applications_resume_id'), 'job_applications', ['resume_id'], unique=False)
    op.create_index(op.f('ix_job_applications_status'), 'job_applications', ['status'], unique=False)
    op.create_index(op.f('ix_job_applications_user_id'), 'job_applications', ['user_id'], unique=False)


def downgrade() -> None:
    """
    执行降级操作
    """
    # 删除表（按相反顺序以避免外键约束）
    op.drop_index(op.f('ix_job_applications_user_id'), table_name='job_applications')
    op.drop_index(op.f('ix_job_applications_status'), table_name='job_applications')
    op.drop_index(op.f('ix_job_applications_resume_id'), table_name='job_applications')
    op.drop_index(op.f('ix_job_applications_job_id'), table_name='job_applications')
    op.drop_index(op.f('ix_job_applications_id'), table_name='job_applications')
    op.drop_index(op.f('ix_job_applications_application_date'), table_name='job_applications')
    op.drop_index('idx_application_user_status', table_name='job_applications')
    op.drop_index('idx_application_job_status', table_name='job_applications')
    op.drop_index('idx_application_date_status', table_name='job_applications')
    op.drop_table('job_applications')

    op.drop_index(op.f('ix_interview_sessions_user_id'), table_name='interview_sessions')
    op.drop_index(op.f('ix_interview_sessions_started_at'), table_name='interview_sessions')
    op.drop_index(op.f('ix_interview_sessions_session_type'), table_name='interview_sessions')
    op.drop_index(op.f('ix_interview_sessions_job_id'), table_name='interview_sessions')
    op.drop_index(op.f('ix_interview_sessions_id'), table_name='interview_sessions')
    op.drop_index(op.f('ix_interview_sessions_created_at'), table_name='interview_sessions')
    op.drop_index(op.f('ix_interview_sessions_completed'), table_name='interview_sessions')
    op.drop_index(op.f('ix_interview_sessions_average_score'), table_name='interview_sessions')
    op.drop_index('idx_session_user_type', table_name='interview_sessions')
    op.drop_index('idx_session_user_completed', table_name='interview_sessions')
    op.drop_index('idx_session_job_completed', table_name='interview_sessions')
    op.drop_table('interview_sessions')

    op.drop_index(op.f('ix_interview_records_user_id'), table_name='interview_records')
    op.drop_index(op.f('ix_interview_records_score'), table_name='interview_records')
    op.drop_index(op.f('ix_interview_records_question_id'), table_name='interview_records')
    op.drop_index(op.f('ix_interview_records_job_id'), table_name='interview_records')
    op.drop_index(op.f('ix_interview_records_id'), table_name='interview_records')
    op.drop_index(op.f('ix_interview_records_answered_at'), table_name='interview_records')
    op.drop_index('idx_record_user_score', table_name='interview_records')
    op.drop_index('idx_record_user_question', table_name='interview_records')
    op.drop_index('idx_record_job_score', table_name='interview_records')
    op.drop_table('interview_records')

    op.drop_index(op.f('ix_interview_questions_question_type'), table_name='interview_questions')
    op.drop_index(op.f('ix_interview_questions_is_active'), table_name='interview_questions')
    op.drop_index(op.f('ix_interview_questions_id'), table_name='interview_questions')
    op.drop_index(op.f('ix_interview_questions_difficulty'), table_name='interview_questions')
    op.drop_index(op.f('ix_interview_questions_created_at'), table_name='interview_questions')
    op.drop_index(op.f('ix_interview_questions_category'), table_name='interview_questions')
    op.drop_index('idx_question_type_difficulty', table_name='interview_questions')
    op.drop_index('idx_question_category_type', table_name='interview_questions')
    op.drop_table('interview_questions')

    op.drop_index(op.f('ix_jobs_work_type'), table_name='jobs')
    op.drop_index(op.f('ix_jobs_title'), table_name='jobs')
    op.drop_index(op.f('ix_jobs_source'), table_name='jobs')
    op.drop_index(op.f('ix_jobs_publish_date'), table_name='jobs')
    op.drop_index(op.f('ix_jobs_location'), table_name='jobs')
    op.drop_index(op.f('ix_jobs_is_active'), table_name='jobs')
    op.drop_index(op.f('ix_jobs_id'), table_name='jobs')
    op.drop_index(op.f('ix_jobs_experience'), table_name='jobs')
    op.drop_index(op.f('ix_jobs_education'), table_name='jobs')
    op.drop_index(op.f('ix_jobs_deadline'), table_name='jobs')
    op.drop_index(op.f('ix_jobs_created_at'), table_name='jobs')
    op.drop_index(op.f('ix_jobs_company'), table_name='jobs')
    op.drop_index('idx_job_work_type_experience', table_name='jobs')
    op.drop_index('idx_job_source_active', table_name='jobs')
    op.drop_index('idx_job_publish_active', table_name='jobs')
    op.drop_index('idx_job_company_location', table_name='jobs')
    op.drop_table('jobs')

    op.drop_index(op.f('ix_resume_optimizations_score'), table_name='resume_optimizations')
    op.drop_index(op.f('ix_resume_optimizations_resume_id'), table_name='resume_optimizations')
    op.drop_index(op.f('ix_resume_optimizations_optimization_type'), table_name='resume_optimizations')
    op.drop_index(op.f('ix_resume_optimizations_id'), table_name='resume_optimizations')
    op.drop_index(op.f('ix_resume_optimizations_created_at'), table_name='resume_optimizations')
    op.drop_table('resume_optimizations')

    op.drop_index(op.f('ix_resumes_user_id'), table_name='resumes')
    op.drop_index(op.f('ix_resumes_language'), table_name='resumes')
    op.drop_index(op.f('ix_resumes_is_default'), table_name='resumes')
    op.drop_index(op.f('ix_resumes_id'), table_name='resumes')
    op.drop_index(op.f('ix_resumes_file_type'), table_name='resumes')
    op.drop_index(op.f('ix_resumes_created_at'), table_name='resumes')
    op.drop_index('idx_resume_user_language', table_name='resumes')
    op.drop_index('idx_resume_user_default', table_name='resumes')
    op.drop_table('resumes')

    op.drop_index(op.f('ix_user_profiles_user_id'), table_name='user_profiles')
    op.drop_index(op.f('ix_user_profiles_skills'), table_name='user_profiles')
    op.drop_index(op.f('ix_user_profiles_job_target'), table_name='user_profiles')
    op.drop_index(op.f('ix_user_profiles_id'), table_name='user_profiles')
    op.drop_table('user_profiles')

    op.drop_index(op.f('ix_users_username'), table_name='users')
    op.drop_index(op.f('ix_users_phone'), table_name='users')
    op.drop_index(op.f('ix_users_is_verified'), table_name='users')
    op.drop_index(op.f('ix_users_is_active'), table_name='users')
    op.drop_index(op.f('ix_users_id'), table_name='users')
    op.drop_index(op.f('ix_users_email'), table_name='users')
    op.drop_index(op.f('ix_users_created_at'), table_name='users')
    op.drop_index('idx_user_username_active', table_name='users')
    op.drop_index('idx_user_email_active', table_name='users')
    op.drop_table('users')