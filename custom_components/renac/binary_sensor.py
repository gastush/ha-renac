"""Binary sensor data of the Renac inverter (hybrid inverters only)."""

from __future__ import annotations

from dataclasses import dataclass
import logging

from homeassistant.components.binary_sensor import (
    BinarySensorDeviceClass,
    BinarySensorEntity,
    BinarySensorEntityDescription,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import EntityCategory
from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from . import RenacData
from .api import InverterType, PyRenac
from .const import DOMAIN
from .coordinator import RenacCoordinator
from .entity import RenacEntity

_LOGGER = logging.getLogger(__name__)


@dataclass(frozen=True, kw_only=True)
class RenacBinarySensorEntityDescription(BinarySensorEntityDescription):
    """Description of a Renac binary sensor."""

    internal_key: str


HYBRID_BINARY_SENSORS: tuple[RenacBinarySensorEntityDescription, ...] = (
    RenacBinarySensorEntityDescription(
        internal_key="Meter_Connect_State",
        key="MeterConnected",
        translation_key="MeterConnected",
        device_class=BinarySensorDeviceClass.CONNECTIVITY,
        entity_category=EntityCategory.DIAGNOSTIC,
    ),
    RenacBinarySensorEntityDescription(
        internal_key="BMS_Connect_State",
        key="BMSConnected",
        translation_key="BMSConnected",
        device_class=BinarySensorDeviceClass.CONNECTIVITY,
        entity_category=EntityCategory.DIAGNOSTIC,
    ),
    RenacBinarySensorEntityDescription(
        internal_key="Forbid_Charge_Flag",
        key="ChargeForbidden",
        translation_key="ChargeForbidden",
        entity_category=EntityCategory.DIAGNOSTIC,
    ),
    RenacBinarySensorEntityDescription(
        internal_key="Forbid_Discharge_Flag",
        key="DischargeForbidden",
        translation_key="DischargeForbidden",
        entity_category=EntityCategory.DIAGNOSTIC,
    ),
)


class RenacBinarySensor(RenacEntity, BinarySensorEntity):
    """Get a binary sensor value from the Renac API and store it in the entity."""

    _attr_has_entity_name = True

    def __init__(
        self,
        description: RenacBinarySensorEntityDescription,
        api: PyRenac,
        coordinator: RenacCoordinator,
    ) -> None:
        """Initialize class."""
        super().__init__(description.key, api, coordinator)
        _LOGGER.info("Creating Binary Sensor %s", description.key)
        self.entity_description = description
        self.internal_key = description.internal_key

    @callback
    def _handle_coordinator_update(self) -> None:
        """Handle updated data from the coordinator."""
        all_data = self.coordinator.data
        value = self.api.fetch_field_value(all_data, self.internal_key)
        self._attr_is_on = bool(value) if value is not None else None
        self.async_write_ha_state()


async def async_setup_entry(
    hass: HomeAssistant,
    config_entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up the Renac binary sensor platform (hybrid inverters only)."""
    data: RenacData = hass.data[DOMAIN][config_entry.entry_id]

    if data.api.getType(data.coordinator.data) != InverterType.HYBRID:
        return

    entities = [
        RenacBinarySensor(description, data.api, data.coordinator)
        for description in HYBRID_BINARY_SENSORS
    ]
    async_add_entities(entities, update_before_add=True)
