"""
core/exceptions.py

Centralised exception handler — every error response goes through here,
guaranteeing a consistent JSON shape across the entire API:

    {
        "error": "Human-readable summary",
        "details": { ... }   # optional field-level breakdown
    }
"""

from rest_framework.views import exception_handler
from rest_framework.response import Response
from rest_framework import status


def custom_exception_handler(exc, context):
    """
    Wraps DRF's default handler so every error response has the same envelope.
    Falls through to Django's 500 handler for truly unexpected exceptions.
    """
    # Let DRF handle what it knows (validation errors, auth errors, etc.)
    response = exception_handler(exc, context)

    if response is not None:
        error_payload = {
            "error": _summarise(response.data),
        }

        # If DRF returned field-level details (e.g. serializer errors), keep them
        if isinstance(response.data, dict) and len(response.data) > 1:
            error_payload["details"] = response.data
        elif isinstance(response.data, list):
            error_payload["details"] = response.data

        response.data = error_payload

    return response


def _summarise(data) -> str:
    """
    Extract a single readable string from whatever DRF put in response.data.
    Covers: {"detail": "..."}, {"field": ["msg"]}, ["msg1", "msg2"]
    """
    if isinstance(data, dict):
        if "detail" in data:
            return str(data["detail"])
        # First field error
        for key, val in data.items():
            if isinstance(val, list) and val:
                return f"{key}: {val[0]}"
            if isinstance(val, str):
                return f"{key}: {val}"
    if isinstance(data, list) and data:
        return str(data[0])
    return str(data)
