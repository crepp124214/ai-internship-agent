"""Shared AI route error mapping helpers."""

from fastapi import HTTPException, status


def raise_ai_value_error(
    message: str,
    *,
    not_found: dict[str, str],
    bad_request: set[str] | None = None,
) -> None:
    """Raise a normalized HTTPException for common AI route validation errors."""
    bad_request = bad_request or set()

    if message in not_found:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=not_found[message],
        ) from None

    if message in bad_request:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=message,
        ) from None

    raise HTTPException(
        status_code=status.HTTP_400_BAD_REQUEST,
        detail=message,
    ) from None


def raise_ai_internal_error(detail: str) -> None:
    """Raise a normalized HTTP 500 for AI route failures."""
    raise HTTPException(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        detail=detail,
    ) from None
