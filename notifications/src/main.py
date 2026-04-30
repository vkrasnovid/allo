"""Notifications service — FastAPI application."""

import logging
import os

from fastapi import FastAPI
from pydantic import BaseModel

from src.sms.provider import sms_provider

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)

logger = logging.getLogger(__name__)

app = FastAPI(
    title="Алло — Notification Service",
    description="SMS & Telegram notifications for voice AI secretary",
    version="0.1.0",
)


class SmsSendRequest(BaseModel):
    phone: str
    text: str


class SmsReminderRequest(BaseModel):
    phone: str
    client_name: str
    service: str
    master: str
    time: str
    reminder_type: str = "day_before"  # day_before | hour_before


@app.on_event("shutdown")
async def shutdown():
    await sms_provider.close()


@app.post("/api/notifications/sms/send")
async def send_sms(body: SmsSendRequest):
    """Send an SMS message."""
    result = await sms_provider.send_sms(body.phone, body.text)
    return result


@app.post("/api/notifications/sms/reminder")
async def send_reminder(body: SmsReminderRequest):
    """Send a structured reminder SMS."""
    if body.reminder_type == "day_before":
        result = await sms_provider.send_reminder_day_before(
            body.phone, body.client_name, body.service, body.master, body.time
        )
    else:
        result = await sms_provider.send_reminder_hour_before(
            body.phone, body.client_name, body.service, body.master, body.time
        )
    return result


@app.get("/health")
async def health():
    return {"status": "ok", "service": "notifications"}
