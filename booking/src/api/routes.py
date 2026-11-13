"""Booking service REST API routes."""

import logging
from datetime import datetime, timedelta, timezone
from decimal import Decimal
from typing import Optional
from uuid import UUID, uuid4

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select, func, delete, and_
from sqlalchemy.ext.asyncio import AsyncSession

from src.database import get_db
from src.models import (
    TenantORM,
    ServiceORM,
    MasterORM,
    MasterServiceORM,
    ClientORM,
    BookingORM,
    BookingHistoryORM,
    CallORM,
    NotificationSettingsORM,
    SipSettingsORM,
    PromptProfileORM,
    PromptBlockORM,
)
from src.calendar.engine import find_available_slots, check_slot_conflict
from src.schemas import (
    SlotRequest,
    SlotResponse,
    SlotsListResponse,
    BookingCreateRequest,
    BookingUpdateRequest,
    BookingResponse,
    BookingListResponse,
    CancelResponse,
    ClientByPhoneResponse,
    BusinessInfoResponse,
    EscalateRequest,
    EscalateResponse,
    ErrorResponse,
)

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1")


def _moscow_now():
    return datetime.now(timezone.utc).astimezone()


# ===== Tenant helpers =====

async def _get_tenant(db: AsyncSession, tenant_id: UUID) -> TenantORM:
    result = await db.execute(select(TenantORM).where(TenantORM.id == tenant_id))
    tenant = result.scalar_one_or_none()
    if not tenant:
        raise HTTPException(status_code=404, detail={"error": "TENANT_NOT_FOUND", "message": "Салон не найден"})
    if tenant.status != "active":
        raise HTTPException(status_code=403, detail={"error": "TENANT_INACTIVE", "message": "Салон деактивирован"})
    return tenant


async def _get_or_create_client(
    db: AsyncSession,
    tenant_id: UUID,
    phone: str,
    name: Optional[str] = None,
) -> ClientORM:
    result = await db.execute(
        select(ClientORM).where(
            ClientORM.tenant_id == tenant_id,
            ClientORM.phone == phone,
        )
    )
    client = result.scalar_one_or_none()
    if not client:
        client = ClientORM(
            tenant_id=tenant_id,
            phone=phone,
            name=name,
        )
        db.add(client)
        await db.flush()
    elif name and not client.name:
        client.name = name
    return client


# ===== Services =====

@router.get("/tenants/{tenant_id}/services")
async def list_services(
    tenant_id: UUID,
    category: Optional[str] = None,
    is_active: Optional[bool] = None,
    db: AsyncSession = Depends(get_db),
):
    await _get_tenant(db, tenant_id)
    query = select(ServiceORM).where(ServiceORM.tenant_id == tenant_id)
    if category:
        query = query.where(ServiceORM.category == category)
    if is_active is not None:
        query = query.where(ServiceORM.is_active == is_active)
    query = query.order_by(ServiceORM.category, ServiceORM.name)

    result = await db.execute(query)
    services = result.scalars().all()
    return {
        "services": [
            {
                "id": str(s.id),
                "name": s.name,
                "description": s.description,
                "duration_min": s.duration_min,
                "price_rub": float(s.price_rub),
                "category": s.category,
                "is_active": s.is_active,
            }
            for s in services
        ]
    }


# ===== Masters =====

@router.get("/tenants/{tenant_id}/masters")
async def list_masters(
    tenant_id: UUID,
    service_id: Optional[UUID] = None,
    is_active: Optional[bool] = None,
    db: AsyncSession = Depends(get_db),
):
    await _get_tenant(db, tenant_id)
    query = select(MasterORM).where(MasterORM.tenant_id == tenant_id)
    if is_active is not None:
        query = query.where(MasterORM.is_active == is_active)
    if service_id:
        subq = select(MasterServiceORM.master_id).where(
            MasterServiceORM.service_id == service_id
        )
        query = query.where(MasterORM.id.in_(subq))
    query = query.order_by(MasterORM.name)

    result = await db.execute(query)
    masters = result.scalars().all()
    return {
        "masters": [
            {
                "id": str(m.id),
                "name": m.name,
                "phone": m.phone,
                "specialization": m.specialization,
                "is_active": m.is_active,
            }
            for m in masters
        ]
    }


# ===== Slots =====

@router.get("/tenants/{tenant_id}/slots", response_model=SlotsListResponse)
async def get_slots(
    tenant_id: UUID,
    master_id: Optional[UUID] = None,
    service_id: Optional[UUID] = None,
    date: Optional[str] = None,
    days: int = 1,
    db: AsyncSession = Depends(get_db),
):
    await _get_tenant(db, tenant_id)

    if not date:
        target_date = _moscow_now().date()
    else:
        target_date = datetime.strptime(date, "%Y-%m-%d").date()

    all_slots = []
    for day_offset in range(min(days, 14)):
        d = target_date + timedelta(days=day_offset)
        slots = await find_available_slots(
            db=db,
            tenant_id=tenant_id,
            target_date=d,
            master_id=master_id,
            service_id=service_id,
        )
        all_slots.extend(slots)

    return SlotsListResponse(
        slots=[SlotResponse(**s) for s in all_slots]
    )


# ===== Bookings =====

@router.post("/tenants/{tenant_id}/bookings", status_code=201)
async def create_booking(
    tenant_id: UUID,
    body: BookingCreateRequest,
    db: AsyncSession = Depends(get_db),
):
    await _get_tenant(db, tenant_id)

    # Resolve client
    client = await _get_or_create_client(db, tenant_id, body.client_phone, body.client_name)

    # Verify master exists
    master_result = await db.execute(
        select(MasterORM).where(
            MasterORM.id == body.master_id,
            MasterORM.tenant_id == tenant_id,
        )
    )
    master = master_result.scalar_one_or_none()
    if not master:
        raise HTTPException(status_code=404, detail={
            "error": "MASTER_NOT_FOUND", "message": "Мастер не найден"
        })

    # Verify service exists
    service_result = await db.execute(
        select(ServiceORM).where(
            ServiceORM.id == body.service_id,
            ServiceORM.tenant_id == tenant_id,
        )
    )
    service = service_result.scalar_one_or_none()
    if not service:
        raise HTTPException(status_code=404, detail={
            "error": "SERVICE_NOT_FOUND", "message": "Услуга не найдена"
        })
    if not service.is_active:
        raise HTTPException(status_code=422, detail={
            "error": "SERVICE_UNAVAILABLE", "message": "Услуга временно недоступна"
        })

    # Calculate end time
    start_at = body.start_at
    if start_at.tzinfo is None:
        start_at = start_at.replace(tzinfo=timezone.utc)
    end_at = start_at.replace(tzinfo=timezone.utc) + timedelta(minutes=service.duration_min)
    start_at_utc = start_at.astimezone(timezone.utc)
    end_at_utc = end_at.astimezone(timezone.utc)

    # Check conflict
    has_conflict = await check_slot_conflict(
        db, tenant_id, body.master_id, start_at_utc, end_at_utc
    )
    if has_conflict:
        raise HTTPException(status_code=409, detail={
            "error": "SLOT_TAKEN", "message": "Это время уже занято"
        })

    # Create booking
    booking = BookingORM(
        tenant_id=tenant_id,
        client_id=client.id,
        master_id=body.master_id,
        service_id=body.service_id,
        status="confirmed",
        start_at=start_at_utc,
        end_at=end_at_utc,
        price_rub=service.price_rub,
        comment=body.comment,
        source=body.source,
    )
    db.add(booking)
    await db.flush()

    # Record history
    history = BookingHistoryORM(
        booking_id=booking.id,
        from_status=None,
        to_status="confirmed",
        changed_by="ai",
        reason="Создана через голосового ассистента",
    )
    db.add(history)

    # Update client stats
    client.total_visits += 1
    client.last_visit_at = start_at_utc

    await db.flush()

    return BookingResponse(
        booking_id=booking.id,
        status=booking.status,
        summary=f"{service.name} у {master.name}, {start_at.strftime('%d.%m.%Y в %H:%M')}, {float(service.price_rub):.0f} ₽",
        yclients_id=booking.yclients_id,
        client={"id": str(client.id), "name": client.name, "phone": client.phone},
        master={"name": master.name, "id": str(master.id)},
        service={"name": service.name, "price_rub": float(service.price_rub)},
        start_at=start_at_utc,
        end_at=end_at_utc,
    )


@router.get("/tenants/{tenant_id}/bookings")
async def list_bookings(
    tenant_id: UUID,
    client_phone: Optional[str] = None,
    status: Optional[str] = None,
    limit: int = 5,
    db: AsyncSession = Depends(get_db),
):
    await _get_tenant(db, tenant_id)
    query = (
        select(
            BookingORM,
            ClientORM.name.label("client_name"),
            ClientORM.phone.label("client_phone"),
            ServiceORM.name.label("service_name"),
            MasterORM.name.label("master_name"),
        )
        .join(ClientORM, BookingORM.client_id == ClientORM.id)
        .join(ServiceORM, BookingORM.service_id == ServiceORM.id)
        .join(MasterORM, BookingORM.master_id == MasterORM.id)
        .where(BookingORM.tenant_id == tenant_id)
    )

    if client_phone:
        query = query.where(ClientORM.phone == client_phone)
    if status:
        query = query.where(BookingORM.status == status)

    query = query.order_by(BookingORM.start_at.desc()).limit(limit)
    result = await db.execute(query)
    rows = result.all()

    return BookingListResponse(
        bookings=[
            {
                "booking_id": str(row.BookingORM.id),
                "service_name": row.service_name,
                "master_name": row.master_name,
                "client_name": row.client_name,
                "client_phone": row.client_phone,
                "start_at": row.BookingORM.start_at.isoformat(),
                "end_at": row.BookingORM.end_at.isoformat(),
                "status": row.BookingORM.status,
                "price_rub": float(row.BookingORM.price_rub),
            }
            for row in rows
        ]
    )


@router.get("/tenants/{tenant_id}/bookings/{booking_id}")
async def get_booking(
    tenant_id: UUID,
    booking_id: UUID,
    db: AsyncSession = Depends(get_db),
):
    await _get_tenant(db, tenant_id)
    result = await db.execute(
        select(
            BookingORM,
            ClientORM.name.label("client_name"),
            ClientORM.phone.label("client_phone"),
            ServiceORM.name.label("service_name"),
            MasterORM.name.label("master_name"),
            ServiceORM.price_rub,
        )
        .join(ClientORM, BookingORM.client_id == ClientORM.id)
        .join(ServiceORM, BookingORM.service_id == ServiceORM.id)
        .join(MasterORM, BookingORM.master_id == MasterORM.id)
        .where(BookingORM.id == booking_id, BookingORM.tenant_id == tenant_id)
    )
    row = result.one_or_none()
    if not row:
        raise HTTPException(status_code=404, detail={
            "error": "BOOKING_NOT_FOUND", "message": "Запись не найдена"
        })

    return BookingResponse(
        booking_id=row.BookingORM.id,
        status=row.BookingORM.status,
        summary=f"{row.service_name} у {row.master_name}",
        client={"id": str(row.BookingORM.client_id), "name": row.client_name, "phone": row.client_phone},
        master={"name": row.master_name, "id": str(row.BookingORM.master_id)},
        service={"name": row.service_name, "price_rub": float(row.price_rub)},
        start_at=row.BookingORM.start_at,
        end_at=row.BookingORM.end_at,
    )


@router.patch("/tenants/{tenant_id}/bookings/{booking_id}")
async def update_booking(
    tenant_id: UUID,
    booking_id: UUID,
    body: BookingUpdateRequest,
    db: AsyncSession = Depends(get_db),
):
    await _get_tenant(db, tenant_id)
    result = await db.execute(
        select(BookingORM).where(
            BookingORM.id == booking_id,
            BookingORM.tenant_id == tenant_id,
        )
    )
    booking = result.scalar_one_or_none()
    if not booking:
        raise HTTPException(status_code=404, detail={
            "error": "BOOKING_NOT_FOUND", "message": "Запись не найдена"
        })

    old_status = booking.status
    old_start = booking.start_at
    old_master = booking.master_id
    changes = {}

    if body.action == "reschedule":
        if not body.start_at:
            raise HTTPException(status_code=422, detail={
                "error": "INVALID_TIME", "message": "Укажите новое время"
            })
        new_start = body.start_at
        if new_start.tzinfo is None:
            new_start = new_start.replace(tzinfo=timezone.utc)

        # Get service duration
        svc_result = await db.execute(
            select(ServiceORM.duration_min).where(ServiceORM.id == booking.service_id)
        )
        duration = svc_result.scalar_one_or_none() or 60
        new_end = new_start + timedelta(minutes=duration)

        has_conflict = await check_slot_conflict(
            db, tenant_id, body.master_id or booking.master_id,
            new_start, new_end, exclude_booking_id=booking.id,
        )
        if has_conflict:
            raise HTTPException(status_code=409, detail={
                "error": "SLOT_TAKEN", "message": "Новое время уже занято"
            })

        booking.start_at = new_start
        booking.end_at = new_end
        changes["old_start"] = old_start.isoformat()
        changes["new_start"] = new_start.isoformat()

    if body.action == "update_master" and body.master_id:
        booking.master_id = body.master_id
        changes["old_master"] = str(old_master)
        changes["new_master"] = str(body.master_id)

    if body.action == "update_service" and body.service_id:
        changes["old_service"] = str(booking.service_id)
        booking.service_id = body.service_id
        changes["new_service"] = str(body.service_id)

    if body.action == "cancel":
        booking.status = "cancelled"
        changes["status"] = "cancelled"

    # Record history
    history = BookingHistoryORM(
        booking_id=booking.id,
        from_status=old_status,
        to_status=booking.status,
        changed_by="ai",
        reason=body.reason or f"Действие: {body.action}",
    )
    db.add(history)
    await db.flush()

    return {
        "booking_id": str(booking.id),
        "status": booking.status,
        "summary": "Запись обновлена",
        "changes": changes,
    }


@router.delete("/tenants/{tenant_id}/bookings/{booking_id}")
async def cancel_booking(
    tenant_id: UUID,
    booking_id: UUID,
    reason: str = "client_cancel",
    db: AsyncSession = Depends(get_db),
):
    await _get_tenant(db, tenant_id)
    result = await db.execute(
        select(BookingORM).where(
            BookingORM.id == booking_id,
            BookingORM.tenant_id == tenant_id,
        )
    )
    booking = result.scalar_one_or_none()
    if not booking:
        raise HTTPException(status_code=404, detail={
            "error": "BOOKING_NOT_FOUND", "message": "Запись не найдена"
        })

    old_status = booking.status
    booking.status = "cancelled"

    history = BookingHistoryORM(
        booking_id=booking.id,
        from_status=old_status,
        to_status="cancelled",
        changed_by="ai",
        reason=reason,
    )
    db.add(history)

    now = _moscow_now()

    # Check cancellation penalty (less than 2 hours before)
    penalty_info = None
    time_diff = booking.start_at - now
    if time_diff.total_seconds() < 7200 and time_diff.total_seconds() > 0:
        penalty_info = "Отмена менее чем за 2 часа до начала"

    await db.flush()

    return CancelResponse(
        booking_id=booking.id,
        status="cancelled",
        cancelled_at=now,
        penalty_info=penalty_info,
    )


# ===== Clients =====

@router.get("/tenants/{tenant_id}/clients/by-phone/{phone}")
async def get_client_by_phone(
    tenant_id: UUID,
    phone: str,
    db: AsyncSession = Depends(get_db),
):
    await _get_tenant(db, tenant_id)
    result = await db.execute(
        select(
            ClientORM,
            ServiceORM.name.label("last_service"),
            MasterORM.name.label("last_master"),
            BookingORM.start_at.label("last_date"),
        )
        .outerjoin(BookingORM, and_(
            BookingORM.client_id == ClientORM.id,
            BookingORM.status == "completed",
        ))
        .outerjoin(ServiceORM, BookingORM.service_id == ServiceORM.id)
        .outerjoin(MasterORM, BookingORM.master_id == MasterORM.id)
        .where(ClientORM.tenant_id == tenant_id, ClientORM.phone == phone)
        .order_by(BookingORM.start_at.desc())
        .limit(1)
    )
    row = result.one_or_none()
    if not row:
        return ClientByPhoneResponse(error="CLIENT_NOT_FOUND")

    client = row.ClientORM
    return ClientByPhoneResponse(
        client={
            "id": str(client.id),
            "name": client.name,
            "phone": client.phone,
            "total_visits": client.total_visits,
            "last_visit_at": client.last_visit_at.isoformat() if client.last_visit_at else None,
            "preferences": client.preferences or {},
        },
        last_booking={
            "service": row.last_service,
            "master": row.last_master,
            "date": row.last_date.isoformat() if row.last_date else None,
        } if row.last_date else None,
    )


# ===== Business Info =====

@router.get("/tenants/{tenant_id}/info")
async def get_business_info(
    tenant_id: UUID,
    db: AsyncSession = Depends(get_db),
):
    tenant = await _get_tenant(db, tenant_id)
    return BusinessInfoResponse(
        tenant_name=tenant.name,
        address=tenant.address,
        phone=tenant.phone,
        # TODO: график зашит одинаковый для всех салонов — вынести в tenant
        work_hours={
            "mon-fri": "09:00-21:00",
            "sat": "10:00-20:00",
            "sun": "10:00-18:00",
        },
        description=tenant.description,
    )


# ===== Escalation =====

@router.post("/tenants/{tenant_id}/escalate")
async def escalate(
    tenant_id: UUID,
    body: EscalateRequest,
    db: AsyncSession = Depends(get_db),
):
    tenant = await _get_tenant(db, tenant_id)

    # Look up forward number from SIP settings
    sip_result = await db.execute(
        select(SipSettingsORM).where(
            SipSettingsORM.tenant_id == tenant_id,
            SipSettingsORM.is_active == True,
        )
    )
    sip = sip_result.scalar_one_or_none()
    forward_to = sip.forward_number if sip else tenant.phone

    # Update call status if we have a call_id
    try:
        call_id = UUID(body.call_id)
        call_result = await db.execute(
            select(CallORM).where(CallORM.id == call_id)
        )
        call = call_result.scalar_one_or_none()
        if call:
            call.status = "escalated"
            call.error_reason = f"Эскалация: {body.reason}"
    except (ValueError, AttributeError):
        pass

    return EscalateResponse(
        forward_to=forward_to,
        action="transfer",
    )


# ===== Health =====

@router.get("/health")
async def health():
    return {"status": "ok", "service": "booking"}
