"""DataUpdateCoordinator for the renac integration."""

from __future__ import annotations

import asyncio
from datetime import timedelta
import logging
from typing import Any

from homeassistant.core import HomeAssistant
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator

from .api import PyRenac

_LOGGER = logging.getLogger(__name__)


class RenacCoordinator(DataUpdateCoordinator[dict[str, Any]]):
    """Data update coordinator for Renac."""

    def __init__(
        self,
        name: str,
        hass: HomeAssistant,
        api: PyRenac,
        # The RENAC Cloud API's rate limits are undocumented; 5-10 minute
        # polling intervals are known to be safe from manual testing, while
        # rapid repeated requests have been observed to trigger an
        # undocumented error response. 30s was too aggressive.
        update_interval=timedelta(minutes=5),
    ) -> None:
        """Initialize my coordinator."""
        super().__init__(
            hass,
            _LOGGER,
            # Name of the data. For logging purposes.
            name=name,
            # Polling interval. Will only be polled if there are subscribers.
            update_interval=update_interval,
        )
        self.api = api

    async def _async_update_data(self) -> dict[str, Any]:
        """Fetch data from API endpoint."""
        async with asyncio.timeout(60):
            return await self.api.async_fetch_all("im")
