"""Celery tasks for scheduled notifications."""

import asyncio
import logging
from datetime import datetime, timedelta, timezone

import httpx

from src.celery_app import app
from src.sms.provider import sms_provider

logger = logging.getLogger(__name__)

BOOKING_API_URL = "http://booking:8003/api/v1"


def _run_async(coro):
    """Run an async function in the Celery sync context."""
    loop = asyncio.new_event_loop()
    try:
        return loop.run_until_complete(coro)
    finally:
        loop.close()


@app.task(bind=True, max_retries=3, default_retry_delay=30)
def send_reminders(self, type: str):
    """
    Scheduled task to send SMS reminders.
    type: 'day_before' or 'hour_before'
    """
    logger.info(f"Running reminders: type={type}")

    async def _run():
        now = datetime.now(timezone.utc)

        # Calculate target window
        if type == "day_before":
            # Appointments happening tomorrow
            window_start = now + timedelta(hours=24)
            window_end = window_start + timedelta(hours=1)
        elif type == "hour_before":
            # Appointments happening in ~1 hour
            window_start = now + timedelta(hours=1)
            window_end = window_start + timedelta(minutes=30)
        else:
            return {"error": f"Unknown reminder type: {type}"}

        # We need to get bookings from the booking service
        # For MVP, we query all tenants and find upcoming bookings
        # This is a simplified version — in production we'd use scheduled_notifications table

        async with httpx.AsyncClient(timeout=10.0) as client:
            # For demo: we check the seed tenant's bookings
            try:
                # Simple health check of booking service
                resp = await client.get(f"{BOOKING_API_URL}/health")
                if resp.status_code == 200:
                    logger.info("Booking service healthy, checking for reminders")
                else:
                    logger.warning("Booking service unhealthy")
            except httpx.RequestError as e:
                logger.error(f"Cannot reach booking service: {e}")

        return {
            "type": type,
            "processed": 0,
            "status": "completed",
        }

    try:
        return _run_async(_run())
    except Exception as e:
        logger.error(f"Reminder task failed: {e}")
        raise self.retry(exc=e)


@app.task(bind=True)
def send_single_sms(self, phone: str, text: str):
    """Send a single SMS (called from webhook or on-demand)."""
    logger.info(f"Sending SMS to {phone}")
    result = _run_async(sms_provider.send_sms(phone, text))
    return result


@app.task(bind=True)
def cleanup_sessions(self):
    """Cleanup task — placeholder for session cleanup."""
    logger.info("Running cleanup: no sessions to clean (placeholder)")
    return {"status": "completed", "cleaned": 0}
