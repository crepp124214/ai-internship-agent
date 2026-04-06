"""
Interview repositories.

This module exports the standard CRUD-style repositories used by the
interview domain.
"""

from src.data_access.entities.interview import (
    InterviewQuestion,
    InterviewRecord,
    InterviewSession,
)
from src.data_access.repositories.base_repository import create_repository


interview_question_repository = create_repository(InterviewQuestion)
interview_record_repository = create_repository(InterviewRecord)
interview_session_repository = create_repository(InterviewSession)

# Backward-compatible alias for older imports.
interview_repository = interview_question_repository
