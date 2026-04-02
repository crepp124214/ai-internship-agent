"""Presentation-layer AI error mapping tests."""

import pytest
from fastapi import HTTPException

from src.presentation.api.ai_errors import raise_ai_internal_error, raise_ai_value_error


def test_raise_ai_value_error_maps_not_found_to_404():
    with pytest.raises(HTTPException) as exc_info:
        raise_ai_value_error(
            "resume not found",
            not_found={"resume not found": "Resume not found"},
        )

    assert exc_info.value.status_code == 404
    assert exc_info.value.detail == "Resume not found"


def test_raise_ai_value_error_maps_known_validation_errors_to_400():
    with pytest.raises(HTTPException) as exc_info:
        raise_ai_value_error(
            "resume text is empty",
            not_found={},
            bad_request={"resume text is empty"},
        )

    assert exc_info.value.status_code == 400
    assert exc_info.value.detail == "resume text is empty"


def test_raise_ai_value_error_defaults_unknown_messages_to_400():
    with pytest.raises(HTTPException) as exc_info:
        raise_ai_value_error(
            "some domain validation error",
            not_found={},
        )

    assert exc_info.value.status_code == 400
    assert exc_info.value.detail == "some domain validation error"


def test_raise_ai_internal_error_maps_to_500():
    with pytest.raises(HTTPException) as exc_info:
        raise_ai_internal_error("Resume summary failed")

    assert exc_info.value.status_code == 500
    assert exc_info.value.detail == "Resume summary failed"
