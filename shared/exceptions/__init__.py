"""Shared exceptions for the Алло project."""

from .errors import (
    AlloError,
    BookingNotFoundError,
    ClientNotFoundError,
    ErrorCategory,
    EscalationFailedError,
    LLMError,
    ServiceUnavailableError,
    SlotTakenError,
    TenantInactiveError,
    TenantNotFoundError,
)

__all__ = [
    "AlloError",
    "ErrorCategory",
    "TenantNotFoundError",
    "TenantInactiveError",
    "BookingNotFoundError",
    "SlotTakenError",
    "ClientNotFoundError",
    "ServiceUnavailableError",
    "EscalationFailedError",
    "LLMError",
]
