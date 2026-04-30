"""Tests for the calendar engine."""

import pytest
from datetime import date, datetime, timedelta, timezone

from src.calendar.engine import generate_slots_for_master, get_work_hours_for_date


def test_get_work_hours_weekday():
    """Monday = 09:00-21:00"""
    open_t, close_t = get_work_hours_for_date(date(2026, 4, 27))  # Monday
    assert open_t.hour == 9
    assert close_t.hour == 21


def test_get_work_hours_saturday():
    """Saturday = 10:00-20:00"""
    open_t, close_t = get_work_hours_for_date(date(2026, 5, 2))  # Saturday
    assert open_t.hour == 10
    assert close_t.hour == 20


def test_get_work_hours_sunday():
    """Sunday = 10:00-18:00"""
    open_t, close_t = get_work_hours_for_date(date(2026, 5, 3))  # Sunday
    assert open_t.hour == 10
    assert close_t.hour == 18


def test_generate_slots_no_bookings():
    """Generate slots for a full day without any bookings."""
    slots = generate_slots_for_master(
        master_name="Анна",
        master_id="test-id",
        target_date=date(2026, 5, 1),
        service_duration_min=60,
        existing_bookings=[],
    )
    # 12 hours (09-21) with 30min step and 60min service
    # Starts at 09:00, 09:30, ..., 20:00 = 23 slots (20:30→21:30 past close)
    assert len(slots) == 23
    # First slot starts at 09:00
    assert slots[0]["start"].hour == 9
    assert slots[0]["start"].minute == 0
    # Last slot starts at 20:00 and ends at 21:00
    assert slots[-1]["start"].hour == 20
    assert slots[-1]["end"].hour == 21


def test_generate_slots_with_bookings():
    """Generate slots avoiding existing bookings."""
    msk = timezone(timedelta(hours=3))
    dt = datetime(2026, 5, 1, 14, 0, tzinfo=msk)
    existing = [(dt, datetime(2026, 5, 1, 15, 0, tzinfo=msk))]
    slots = generate_slots_for_master(
        master_name="Анна",
        master_id="test-id",
        target_date=date(2026, 5, 1),
        service_duration_min=60,
        existing_bookings=existing,
    )
    # 23 total - 3 blocked (13:30, 14:00, 14:30) = 20
    # 13:30→14:30 overlaps (14:30 > 14:00), 14:00→15:00, 14:30→15:30 overlaps (14:30 < 15:00)
    assert len(slots) == 20
    # Slot 13:00-14:00 should exist
    assert any(s["start"].hour == 13 and s["start"].minute == 0 for s in slots)
    # No slot should start at 13:30, 14:00, or 14:30
    assert not any(s["start"].hour == 14 and s["start"].minute == 0 for s in slots)
    assert not any(s["start"].hour == 14 and s["start"].minute == 30 for s in slots)


def test_generate_slots_service_30min():
    """30-minute service generates more slots."""
    slots = generate_slots_for_master(
        master_name="Анна",
        master_id="test-id",
        target_date=date(2026, 5, 1),
        service_duration_min=30,
        existing_bookings=[],
    )
    # 12 hours × 2 = 24 half-hour blocks, all fit since 20:30→21:00 is within bounds
    assert len(slots) == 24


def test_generate_slots_service_120min():
    """120-minute service — many overlapping 30-min step slots."""
    slots = generate_slots_for_master(
        master_name="Анна",
        master_id="test-id",
        target_date=date(2026, 5, 1),
        service_duration_min=120,
        existing_bookings=[],
    )
    # 12 hours, 30min step, 120min service
    # Available start times: 09:00, 09:30, ..., 19:00 = 21 slots (19:30→21:30 past close)
    assert len(slots) == 21


def test_slots_are_sorted():
    """Slots should be sorted by start time."""
    slots = generate_slots_for_master(
        master_name="Анна",
        master_id="test-id",
        target_date=date(2026, 5, 1),
        service_duration_min=60,
        existing_bookings=[],
    )
    for i in range(len(slots) - 1):
        assert slots[i]["start"] <= slots[i + 1]["start"]


def test_slot_master_info():
    """Slots contain correct master information."""
    slots = generate_slots_for_master(
        master_name="Анна Петрова",
        master_id="master-123",
        target_date=date(2026, 5, 1),
        service_duration_min=60,
        existing_bookings=[],
    )
    assert slots[0]["master_name"] == "Анна Петрова"
    assert slots[0]["master_id"] == "master-123"
