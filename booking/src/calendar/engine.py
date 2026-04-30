"""Internal calendar logic — slot generation, conflict checking, work hours."""

from datetime import date, datetime, time, timedelta, timezone
from typing import Optional

from sqlalchemy import select, and_
from sqlalchemy.ext.asyncio import AsyncSession

from src.models import BookingORM, MasterORM, ServiceORM, MasterServiceORM


# Default work hours per day of week (0=Mon, 6=Sun)
DEFAULT_WORK_HOURS: dict[int, tuple[time, time]] = {
    0: (time(9, 0), time(21, 0)),   # Monday
    1: (time(9, 0), time(21, 0)),   # Tuesday
    2: (time(9, 0), time(21, 0)),   # Wednesday
    3: (time(9, 0), time(21, 0)),   # Thursday
    4: (time(9, 0), time(21, 0)),   # Friday
    5: (time(10, 0), time(20, 0)),  # Saturday
    6: (time(10, 0), time(18, 0)),  # Sunday
}

SLOT_STEP_MINUTES = 30  # Slot granularity


def get_work_hours_for_date(target_date: date) -> tuple[time, time]:
    """Get work hours for a specific date."""
    return DEFAULT_WORK_HOURS.get(target_date.weekday(), (time(9, 0), time(21, 0)))


def generate_slots_for_master(
    master_name: str,
    master_id,
    target_date: date,
    service_duration_min: int,
    existing_bookings: list[tuple[datetime, datetime]],
) -> list[dict]:
    """
    Generate available time slots for a master on a given date,
    excluding existing bookings.
    """
    open_time, close_time = get_work_hours_for_date(target_date)
    moscow_tz = timezone(timedelta(hours=3))

    day_start = datetime.combine(target_date, open_time, tzinfo=moscow_tz)
    day_end = datetime.combine(target_date, close_time, tzinfo=moscow_tz)

    slots = []
    current = day_start

    # Build busy intervals — normalize to same timezone
    busy = []
    for b_start, b_end in existing_bookings:
        if b_start.tzinfo is None:
            b_start = b_start.replace(tzinfo=moscow_tz)
        else:
            b_start = b_start.astimezone(moscow_tz)
        if b_end.tzinfo is None:
            b_end = b_end.replace(tzinfo=moscow_tz)
        else:
            b_end = b_end.astimezone(moscow_tz)
        busy.append((b_start, b_end))

    busy.sort()

    while current + timedelta(minutes=service_duration_min) <= day_end:
        slot_end = current + timedelta(minutes=service_duration_min)
        is_free = True

        for b_start, b_end in busy:
            if current < b_end and slot_end > b_start:
                is_free = False
                break

        if is_free:
            slots.append({
                "start": current,
                "end": slot_end,
                "master_id": str(master_id),
                "master_name": master_name,
            })

        current += timedelta(minutes=SLOT_STEP_MINUTES)

    return slots


async def find_available_slots(
    db: AsyncSession,
    tenant_id,
    target_date: date,
    master_id: Optional = None,
    service_id: Optional = None,
) -> list[dict]:
    """
    Find available slots for the given parameters.
    """
    # Determine service duration
    service_duration = 60  # default
    if service_id:
        result = await db.execute(
            select(ServiceORM.duration_min).where(
                ServiceORM.id == service_id,
                ServiceORM.tenant_id == tenant_id,
            )
        )
        row = result.scalar_one_or_none()
        if row:
            service_duration = row

    # Get available masters
    query = select(MasterORM).where(
        MasterORM.tenant_id == tenant_id,
        MasterORM.is_active == True,
    )
    if master_id:
        query = query.where(MasterORM.id == master_id)

    result = await db.execute(query)
    masters = result.scalars().all()

    all_slots = []
    moscow_tz = timezone(timedelta(hours=3))

    for master in masters:
        # Get existing bookings for this master on this date
        day_start = datetime.combine(target_date, time(0, 0), tzinfo=moscow_tz)
        day_end = datetime.combine(target_date, time(23, 59), tzinfo=moscow_tz)

        booking_query = select(BookingORM.start_at, BookingORM.end_at).where(
            BookingORM.master_id == master.id,
            BookingORM.tenant_id == tenant_id,
            BookingORM.start_at >= day_start,
            BookingORM.start_at < day_end,
            BookingORM.status.notin_(["cancelled", "no_show"]),
        )
        booking_result = await db.execute(booking_query)
        existing_bookings = booking_result.all()

        slots = generate_slots_for_master(
            master_name=master.name,
            master_id=master.id,
            target_date=target_date,
            service_duration_min=service_duration,
            existing_bookings=[(b.start_at, b.end_at) for b in existing_bookings],
        )
        all_slots.extend(slots)

    all_slots.sort(key=lambda s: s["start"])
    return all_slots


async def check_slot_conflict(
    db: AsyncSession,
    tenant_id,
    master_id,
    start_at: datetime,
    end_at: datetime,
    exclude_booking_id=None,
) -> bool:
    """
    Check if a slot conflicts with existing bookings.
    Returns True if there IS a conflict.
    """
    query = select(BookingORM).where(
        BookingORM.master_id == master_id,
        BookingORM.tenant_id == tenant_id,
        BookingORM.status.notin_(["cancelled", "no_show"]),
        BookingORM.start_at < end_at,
        BookingORM.end_at > start_at,
    )

    if exclude_booking_id:
        query = query.where(BookingORM.id != exclude_booking_id)

    result = await db.execute(query)
    return result.scalar_one_or_none() is not None
