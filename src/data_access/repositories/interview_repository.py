"""
闈㈣瘯Repository - 鎻愪緵闈㈣瘯鐩稿叧鐨勬暟鎹闂柟娉?
"""

from src.data_access.entities.interview import InterviewQuestion, InterviewRecord, InterviewSession
from src.data_access.repositories.base_repository import create_repository

# 闈㈣瘯闂 / 璁板綍 / 浼氳瘽 Repository 宸ュ巶瀹炰緥
interview_question_repository = create_repository(InterviewQuestion)
interview_record_repository = create_repository(InterviewRecord)
interview_session_repository = create_repository(InterviewSession)

# 鏃у鍏煎鍒版棫鍚嶇О
interview_repository = interview_question_repository
