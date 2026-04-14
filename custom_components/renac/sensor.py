"""Sensor data of the Renac inverter."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
import logging

from homeassistant.components.sensor import (
    SensorDeviceClass,
    SensorEntity,
    SensorEntityDescription,
    SensorStateClass,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import (
    UnitOfElectricCurrent,
    UnitOfElectricPotential,
    UnitOfEnergy,
    UnitOfFrequency,
    UnitOfPower,
)
from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from . import RenacData
from .const import DOMAIN
from .coordinator import RenacCoordinator
from .entity import RenacEntity
from pyrenac import InverterType, PyRenac

_LOGGER = logging.getLogger(__name__)


@dataclass(frozen=True, kw_only=True)
class RenacSensorEntityDescription(SensorEntityDescription):
    """Description of a Renac sensor."""

    raw_format: bool
    daily_reset: bool


ONGRID_SENSORS: tuple[RenacSensorEntityDescription, ...] = (
    RenacSensorEntityDescription(
        key="totalPower",
        translation_key="totalPower",
        raw_format=True,
        device_class=SensorDeviceClass.ENERGY,
        state_class=SensorStateClass.TOTAL_INCREASING,
        native_unit_of_measurement=UnitOfEnergy.KILO_WATT_HOUR,
        daily_reset=False,
    ),
    RenacSensorEntityDescription(
        key="todayPower",
        translation_key="todayPower",
        raw_format=True,
        device_class=SensorDeviceClass.ENERGY,
        state_class=SensorStateClass.TOTAL,
        native_unit_of_measurement=UnitOfEnergy.KILO_WATT_HOUR,
        daily_reset=True,
    ),
    RenacSensorEntityDescription(
        key="acPower",
        translation_key="acPower",
        raw_format=True,
        device_class=SensorDeviceClass.POWER,
        state_class=SensorStateClass.MEASUREMENT,
        native_unit_of_measurement=UnitOfPower.WATT,
        daily_reset=False,
    ),
    RenacSensorEntityDescription(
        key="PV1voltage",
        translation_key="PV1voltage",
        raw_format=True,
        device_class=SensorDeviceClass.VOLTAGE,
        state_class=SensorStateClass.MEASUREMENT,
        native_unit_of_measurement=UnitOfElectricPotential.VOLT,
        daily_reset=False,
    ),
    RenacSensorEntityDescription(
        key="PV2voltage",
        translation_key="PV2voltage",
        raw_format=True,
        device_class=SensorDeviceClass.VOLTAGE,
        state_class=SensorStateClass.MEASUREMENT,
        native_unit_of_measurement=UnitOfElectricPotential.VOLT,
        daily_reset=False,
    ),
    RenacSensorEntityDescription(
        key="PV1current",
        translation_key="PV1current",
        raw_format=True,
        device_class=SensorDeviceClass.CURRENT,
        state_class=SensorStateClass.MEASUREMENT,
        native_unit_of_measurement=UnitOfElectricCurrent.AMPERE,
        daily_reset=False,
    ),
    RenacSensorEntityDescription(
        key="PV2current",
        translation_key="PV2current",
        raw_format=True,
        device_class=SensorDeviceClass.CURRENT,
        state_class=SensorStateClass.MEASUREMENT,
        native_unit_of_measurement=UnitOfElectricCurrent.AMPERE,
        daily_reset=False,
    ),
    RenacSensorEntityDescription(
        key="PV1power",
        translation_key="PV1power",
        raw_format=True,
        device_class=SensorDeviceClass.POWER,
        state_class=SensorStateClass.MEASUREMENT,
        native_unit_of_measurement=UnitOfPower.WATT,
        daily_reset=False,
    ),
    RenacSensorEntityDescription(
        key="PV2power",
        translation_key="PV2power",
        raw_format=True,
        device_class=SensorDeviceClass.POWER,
        state_class=SensorStateClass.MEASUREMENT,
        native_unit_of_measurement=UnitOfPower.WATT,
        daily_reset=False,
    ),
    RenacSensorEntityDescription(
        key="Rvoltage",
        translation_key="Rvoltage",
        raw_format=True,
        device_class=SensorDeviceClass.VOLTAGE,
        state_class=SensorStateClass.MEASUREMENT,
        native_unit_of_measurement=UnitOfElectricPotential.VOLT,
        daily_reset=False,
    ),
    RenacSensorEntityDescription(
        key="Svoltage",
        translation_key="Svoltage",
        raw_format=True,
        device_class=SensorDeviceClass.VOLTAGE,
        state_class=SensorStateClass.MEASUREMENT,
        native_unit_of_measurement=UnitOfElectricPotential.VOLT,
        daily_reset=False,
    ),
    RenacSensorEntityDescription(
        key="Tvoltage",
        translation_key="Tvoltage",
        raw_format=True,
        device_class=SensorDeviceClass.VOLTAGE,
        state_class=SensorStateClass.MEASUREMENT,
        native_unit_of_measurement=UnitOfElectricPotential.VOLT,
        daily_reset=False,
    ),
    RenacSensorEntityDescription(
        key="Rcurrent",
        translation_key="Rcurrent",
        raw_format=True,
        device_class=SensorDeviceClass.CURRENT,
        state_class=SensorStateClass.MEASUREMENT,
        native_unit_of_measurement=UnitOfElectricCurrent.AMPERE,
        daily_reset=False,
    ),
    RenacSensorEntityDescription(
        key="Scurrent",
        translation_key="Scurrent",
        raw_format=True,
        device_class=SensorDeviceClass.CURRENT,
        state_class=SensorStateClass.MEASUREMENT,
        native_unit_of_measurement=UnitOfElectricCurrent.AMPERE,
        daily_reset=False,
    ),
    RenacSensorEntityDescription(
        key="Tcurrent",
        translation_key="Tcurrent",
        raw_format=True,
        device_class=SensorDeviceClass.CURRENT,
        state_class=SensorStateClass.MEASUREMENT,
        native_unit_of_measurement=UnitOfElectricCurrent.AMPERE,
        daily_reset=False,
    ),
    RenacSensorEntityDescription(
        key="Rfrequency",
        translation_key="Rfrequency",
        raw_format=True,
        device_class=SensorDeviceClass.FREQUENCY,
        state_class=SensorStateClass.MEASUREMENT,
        native_unit_of_measurement=UnitOfFrequency.HERTZ,
        daily_reset=False,
    ),
    RenacSensorEntityDescription(
        key="Sfrequency",
        translation_key="Sfrequency",
        raw_format=True,
        device_class=SensorDeviceClass.FREQUENCY,
        state_class=SensorStateClass.MEASUREMENT,
        native_unit_of_measurement=UnitOfFrequency.HERTZ,
        daily_reset=False,
    ),
    RenacSensorEntityDescription(
        key="Tfrequency",
        translation_key="Tfrequency",
        raw_format=True,
        device_class=SensorDeviceClass.FREQUENCY,
        state_class=SensorStateClass.MEASUREMENT,
        native_unit_of_measurement=UnitOfFrequency.HERTZ,
        daily_reset=False,
    ),
)

HYBRID_SENSORS: tuple[RenacSensorEntityDescription, ...] = (
    RenacSensorEntityDescription(
        key="ENERGY_TOTAL",
        translation_key="ENERGY_TOTAL",
        raw_format=True,
        device_class=SensorDeviceClass.ENERGY,
        state_class=SensorStateClass.TOTAL_INCREASING,
        native_unit_of_measurement=UnitOfEnergy.KILO_WATT_HOUR,
        daily_reset=False,
    ),
    RenacSensorEntityDescription(
        key="ENERGY_TODAY",
        translation_key="ENERGY_TODAY",
        raw_format=True,
        device_class=SensorDeviceClass.ENERGY,
        state_class=SensorStateClass.TOTAL,
        native_unit_of_measurement=UnitOfEnergy.KILO_WATT_HOUR,
        daily_reset=True,
    ),
    RenacSensorEntityDescription(
        key="Load",
        translation_key="Load",
        raw_format=True,
        device_class=SensorDeviceClass.POWER,
        state_class=SensorStateClass.MEASUREMENT,
        native_unit_of_measurement=UnitOfPower.WATT,
        daily_reset=False,
    ),
    RenacSensorEntityDescription(
        key="PV",
        translation_key="PV",
        raw_format=True,
        device_class=SensorDeviceClass.POWER,
        state_class=SensorStateClass.MEASUREMENT,
        native_unit_of_measurement=UnitOfPower.WATT,
        daily_reset=False,
    ),
    RenacSensorEntityDescription(
        key="BAT",
        translation_key="BAT",
        raw_format=True,
        device_class=SensorDeviceClass.POWER,
        state_class=SensorStateClass.MEASUREMENT,
        native_unit_of_measurement=UnitOfPower.WATT,
        daily_reset=False,
    ),
    RenacSensorEntityDescription(
        key="GRID",
        translation_key="GRID",
        raw_format=True,
        device_class=SensorDeviceClass.POWER,
        state_class=SensorStateClass.MEASUREMENT,
        native_unit_of_measurement=UnitOfPower.WATT,
        daily_reset=False,
    ),
    RenacSensorEntityDescription(
        key="CAPACITY_CHARGE",
        translation_key="CAPACITY_CHARGE",
        raw_format=True,
        device_class=SensorDeviceClass.BATTERY,
        state_class=SensorStateClass.MEASUREMENT,
        native_unit_of_measurement="%",
        daily_reset=False,
    ),
)


class RenacSensor(RenacEntity, SensorEntity):
    """Get a sensor data from the Renson API and store it in the state of the class."""

    _attr_has_entity_name = True

    def __init__(
        self,
        description: RenacSensorEntityDescription,
        api: PyRenac,
        coordinator: RenacCoordinator,
    ) -> None:
        """Initialize class."""
        super().__init__(description.key, api, coordinator)
        _LOGGER.info("Creating Sensor %s", description.key)
        self.field = description.key
        self.entity_description = description
        self.daily_reset = description.daily_reset
        self.raw_format = description.raw_format

    @callback
    def _handle_coordinator_update(self) -> None:
        """Handle updated data from the coordinator."""
        all_data = self.coordinator.data

        value = self.api.fetch_field_value(all_data, self.field)
        self._attr_native_value = value
        if self.daily_reset:
            self._attr_last_reset = datetime.now().replace(
                hour=0, minute=0, second=0, microsecond=0
            )

        self.async_write_ha_state()


async def async_setup_entry(
    hass: HomeAssistant,
    config_entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up the Renson sensor platform."""

    _LOGGER.info("Setup entries")
    data: RenacData = hass.data[DOMAIN][config_entry.entry_id]

    if data.api.getType(data.coordinator.data) == InverterType.ONGRID:
        _LOGGER.info("On Grid inverter entries")
        entities = [
            RenacSensor(description, data.api, data.coordinator)
            for description in ONGRID_SENSORS
        ]
    else:
        _LOGGER.info("Hybrid inverter entries")
        entities = [
            RenacSensor(description, data.api, data.coordinator)
            for description in HYBRID_SENSORS
        ]

    async_add_entities(entities, update_before_add=True)
