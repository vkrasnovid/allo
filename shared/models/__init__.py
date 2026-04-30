# shared/models/__init__.py
from shared.models.tenants import (
    TenantInfo,
    WorkHours,
    BusinessInfo,
    SipSettings,
    NotificationSettings,
)
from shared.models.services import Service, ServiceCreate, ServiceUpdate
from shared.models.masters import Master, MasterCreate, MasterUpdate, MasterServiceLink
from shared.models.clients import Client, ClientCreate, ClientUpdate, ClientInfo
from shared.models.bookings import (
    Booking,
    BookingCreate,
    BookingUpdate,
    BookingInfo,
    BookingStatus,
    BookingSource,
    BookingHistoryEntry,
)
from shared.models.calls import (
    Call,
    CallCreate,
    CallStatus,
    CallResult,
    CallTranscript,
    CallBookingLink,
)
from shared.models.prompts import (
    PromptProfile,
    PromptProfileCreate,
    PromptBlock,
    PromptBlockCreate,
    ComposedPrompt,
)

__all__ = [
    "TenantInfo",
    "WorkHours",
    "BusinessInfo",
    "SipSettings",
    "NotificationSettings",
    "Service",
    "ServiceCreate",
    "ServiceUpdate",
    "Master",
    "MasterCreate",
    "MasterUpdate",
    "MasterServiceLink",
    "Client",
    "ClientCreate",
    "ClientUpdate",
    "ClientInfo",
    "Booking",
    "BookingCreate",
    "BookingUpdate",
    "BookingInfo",
    "BookingStatus",
    "BookingSource",
    "BookingHistoryEntry",
    "Call",
    "CallCreate",
    "CallStatus",
    "CallResult",
    "CallTranscript",
    "CallBookingLink",
    "PromptProfile",
    "PromptProfileCreate",
    "PromptBlock",
    "PromptBlockCreate",
    "ComposedPrompt",
]
