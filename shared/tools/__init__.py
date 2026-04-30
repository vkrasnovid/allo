"""
Shared tools library — Pydantic input/output schemas, DB query interfaces.
Used by both booking service and AI engine.
"""

from shared.tools.protocols import (
    BookingServiceInterface,
    ToolDef,
    TOOL_REGISTRY,
)
from shared.tools.services import get_services, GetServicesParams, GetServicesResult, Service
from shared.tools.masters import get_masters, GetMastersParams, GetMastersResult, Master
from shared.tools.calendar import find_slots, FindSlotsParams, FindSlotsResult, TimeSlot
from shared.tools.booking import (
    create_booking,
    CreateBookingParams,
    CreateBookingResult,
    find_booking,
    FindBookingParams,
    FindBookingResult,
    BookingInfo,
    update_booking,
    UpdateBookingParams,
    UpdateBookingResult,
    cancel_booking,
    CancelBookingParams,
    CancelBookingResult,
)
from shared.tools.business import get_business_info, GetBusinessInfoParams, GetBusinessInfoResult, BusinessInfo
from shared.tools.escalation import escalate_to_human, EscalateParams, EscalateResult

__all__ = [
    "BookingServiceInterface",
    "ToolDef",
    "TOOL_REGISTRY",
    "get_services", "GetServicesParams", "GetServicesResult", "Service",
    "get_masters", "GetMastersParams", "GetMastersResult", "Master",
    "find_slots", "FindSlotsParams", "FindSlotsResult", "TimeSlot",
    "create_booking", "CreateBookingParams", "CreateBookingResult",
    "find_booking", "FindBookingParams", "FindBookingResult", "BookingInfo",
    "update_booking", "UpdateBookingParams", "UpdateBookingResult",
    "cancel_booking", "CancelBookingParams", "CancelBookingResult",
    "get_business_info", "GetBusinessInfoParams", "GetBusinessInfoResult", "BusinessInfo",
    "escalate_to_human", "EscalateParams", "EscalateResult",
]
