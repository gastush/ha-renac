"""Entity class for Renac inverter."""

from __future__ import annotations

import asyncio

from homeassistant.core import HomeAssistant
from homeassistant.helpers.device_registry import DeviceInfo
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import DOMAIN
from .coordinator import RenacCoordinator
from .pyrenac import PyRenac, RenacInverterData

import threading
from concurrent.futures import ThreadPoolExecutor
from typing import Any, Coroutine, TypeVar

__all__ = [
    "run_coroutine_sync",
]

T = TypeVar("T")


def run_coroutine_sync(coroutine: Coroutine[Any, Any, T], timeout: float = 30) -> T:
    def run_in_new_loop():
        new_loop = asyncio.new_event_loop()
        asyncio.set_event_loop(new_loop)
        try:
            return new_loop.run_until_complete(coroutine)
        finally:
            new_loop.close()

    try:
        loop = asyncio.get_running_loop()
    except RuntimeError:
        return asyncio.run(coroutine)

    if threading.current_thread() is threading.main_thread():
        if not loop.is_running():
            return loop.run_until_complete(coroutine)
        else:
            with ThreadPoolExecutor() as pool:
                future = pool.submit(run_in_new_loop)
                return future.result(timeout=timeout)
    else:
        return asyncio.run_coroutine_threadsafe(coroutine, loop).result()


class RenacEntity(CoordinatorEntity[RenacCoordinator]):
    """Renac entity."""

    def __init__(self, name: str, api: PyRenac, coordinator: RenacCoordinator) -> None:
        """Initialize the Renac entity."""
        super().__init__(coordinator)
        data: RenacInverterData

        data = run_coroutine_sync(api.async_get_inverter_data())

        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, api.getSerial())},
            manufacturer="Renac",
            model=api.fetch_field_value(coordinator.data, "model"),
            name=data.name,
            hw_version=data.fwversion,
            serial_number=api.getSerial(),
        )

        self.api = api

        self._attr_unique_id = api.getSerial() + f"{name}"
