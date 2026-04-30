"""YClients API adapter — sync services, masters, and bookings with YClients."""

import logging
from typing import Optional

logger = logging.getLogger(__name__)


class YClientsAdapter:
    """
    Adapter for YClients API.
    In MVP mode, this is a stub that will be replaced with real integration.
    """

    def __init__(self, bearer_token: Optional[str] = None):
        self.bearer_token = bearer_token
        self.base_url = "https://api.yclients.com/api/v1"

    async def is_available(self) -> bool:
        """Check if YClients API is available."""
        if not self.bearer_token:
            return False
        # In real implementation: health check request
        return False  # stub

    async def sync_services(self, tenant_id, company_id: int) -> list[dict]:
        """Sync services from YClients."""
        if not self.is_available:
            return []
        # Placeholder for real implementation
        logger.info(f"YClients sync services: tenant={tenant_id}, company={company_id}")
        return []

    async def create_booking(self, tenant_id, booking_data: dict) -> Optional[int]:
        """Create booking in YClients. Returns YClients record ID."""
        if not await self.is_available():
            return None
        # Placeholder
        logger.info(f"YClients create booking: tenant={tenant_id}")
        return None

    async def cancel_booking(self, yclients_id: int) -> bool:
        """Cancel booking in YClients."""
        if not await self.is_available():
            return False
        # Placeholder
        logger.info(f"YClients cancel booking: id={yclients_id}")
        return True
