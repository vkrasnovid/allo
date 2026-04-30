"""SMS provider — Sipuni SMS API integration (with stub fallback)."""

import logging
import os
from typing import Optional

import httpx

logger = logging.getLogger(__name__)

SIPUNI_API_KEY = os.getenv("SIPUNI_API_KEY", "")
SIPUNI_ACCOUNT = os.getenv("SIPUNI_ACCOUNT", "")


class SmsProvider:
    """
    SMS sending provider.
    Uses Sipuni SMS API in production, logs messages in dev/stub mode.
    """

    def __init__(self):
        self.api_key = SIPUNI_API_KEY
        self.api_account = SIPUNI_ACCOUNT
        self.client = httpx.AsyncClient(timeout=10.0)

    async def close(self):
        await self.client.aclose()

    async def send_sms(self, phone: str, text: str) -> dict:
        """
        Send an SMS message.
        Falls back to logging if API is not configured.
        """
        if not self.api_key:
            logger.info(f"[SMS STUB] To: {phone} | Text: {text}")
            return {"status": "stub", "message_id": None, "phone": phone}

        try:
            response = await self.client.post(
                "https://sipuni.com/api/sms/send",
                json={
                    "api_key": self.api_key,
                    "account": self.api_account,
                    "phone": phone,
                    "text": text,
                },
            )
            result = response.json()
            logger.info(f"SMS sent to {phone}: {result}")
            return {"status": "sent", "message_id": result.get("message_id"), "phone": phone}

        except httpx.RequestError as e:
            logger.error(f"SMS send failed to {phone}: {e}")
            return {"status": "failed", "error": str(e), "phone": phone}

        except Exception as e:
            logger.error(f"SMS unexpected error: {e}")
            return {"status": "failed", "error": str(e), "phone": phone}

    async def send_reminder_day_before(self, phone: str, client_name: str, service: str, master: str, time: str):
        """Send reminder 24 hours before appointment."""
        text = (
            f"Здравствуйте, {client_name}!\n"
            f"Напоминаем, что завтра в {time} у вас запись на {service} к мастеру {master}.\n"
            f"Ждём вас в салоне!"
        )
        return await self.send_sms(phone, text)

    async def send_reminder_hour_before(self, phone: str, client_name: str, service: str, master: str, time: str):
        """Send reminder 1 hour before appointment."""
        text = (
            f"Напоминаем, через час в {time} у вас {service} у {master}.\n"
            f"Если нужно отменить или перенести — позвоните нам!"
        )
        return await self.send_sms(phone, text)


# Global SMS provider instance
sms_provider = SmsProvider()
