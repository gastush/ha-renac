"""Sensor data of the Renac inverter."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
import logging

from pyrenac import InverterType, PyRenac

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

_LOGGER = logging.getLogger(__name__)


@dataclass(frozen=True, kw_only=True)
class RenacSensorEntityDescription(SensorEntityDescription):
    """Description of a Renac sensor."""

    raw_format: bool
    daily_reset: bool
    internal_key: str


ONGRID_SENSORS: tuple[RenacSensorEntityDescription, ...] = (
    RenacSensorEntityDescription(
        internal_key="SUM_ENERGY",
        key="totalPower",
        translation_key="totalPower",
        raw_format=True,
        device_class=SensorDeviceClass.ENERGY,
        state_class=SensorStateClass.TOTAL_INCREASING,
        native_unit_of_measurement=UnitOfEnergy.KILO_WATT_HOUR,
        daily_reset=False,
    ),
    RenacSensorEntityDescription(
        internal_key="DAY_ENERGY",
        key="todayPower",
        translation_key="todayPower",
        raw_format=True,
        device_class=SensorDeviceClass.ENERGY,
        state_class=SensorStateClass.TOTAL,
        native_unit_of_measurement=UnitOfEnergy.KILO_WATT_HOUR,
        daily_reset=True,
    ),
    RenacSensorEntityDescription(
        internal_key="OUTPUT_POWER",
        key="acPower",
        translation_key="acPower",
        raw_format=True,
        device_class=SensorDeviceClass.POWER,
        state_class=SensorStateClass.MEASUREMENT,
        native_unit_of_measurement=UnitOfPower.WATT,
        daily_reset=False,
    ),
    RenacSensorEntityDescription(
        internal_key="PV1_VOL",
        key="PV1voltage",
        translation_key="PV1voltage",
        raw_format=True,
        device_class=SensorDeviceClass.VOLTAGE,
        state_class=SensorStateClass.MEASUREMENT,
        native_unit_of_measurement=UnitOfElectricPotential.VOLT,
        daily_reset=False,
    ),
    RenacSensorEntityDescription(
        internal_key="PV2_VOL",
        key="PV2voltage",
        translation_key="PV2voltage",
        raw_format=True,
        device_class=SensorDeviceClass.VOLTAGE,
        state_class=SensorStateClass.MEASUREMENT,
        native_unit_of_measurement=UnitOfElectricPotential.VOLT,
        daily_reset=False,
    ),
    RenacSensorEntityDescription(
        internal_key="PV1_CUR",
        key="PV1current",
        translation_key="PV1current",
        raw_format=True,
        device_class=SensorDeviceClass.CURRENT,
        state_class=SensorStateClass.MEASUREMENT,
        native_unit_of_measurement=UnitOfElectricCurrent.AMPERE,
        daily_reset=False,
    ),
    RenacSensorEntityDescription(
        internal_key="PV2_CUR",
        key="PV2current",
        translation_key="PV2current",
        raw_format=True,
        device_class=SensorDeviceClass.CURRENT,
        state_class=SensorStateClass.MEASUREMENT,
        native_unit_of_measurement=UnitOfElectricCurrent.AMPERE,
        daily_reset=False,
    ),
    RenacSensorEntityDescription(
        internal_key="PV1_POWER",
        key="PV1power",
        translation_key="PV1power",
        raw_format=True,
        device_class=SensorDeviceClass.POWER,
        state_class=SensorStateClass.MEASUREMENT,
        native_unit_of_measurement=UnitOfPower.WATT,
        daily_reset=False,
    ),
    RenacSensorEntityDescription(
        internal_key="PV2_POWER",
        key="PV2power",
        translation_key="PV2power",
        raw_format=True,
        device_class=SensorDeviceClass.POWER,
        state_class=SensorStateClass.MEASUREMENT,
        native_unit_of_measurement=UnitOfPower.WATT,
        daily_reset=False,
    ),
    RenacSensorEntityDescription(
        internal_key="R_VOL",
        key="Rvoltage",
        translation_key="Rvoltage",
        raw_format=True,
        device_class=SensorDeviceClass.VOLTAGE,
        state_class=SensorStateClass.MEASUREMENT,
        native_unit_of_measurement=UnitOfElectricPotential.VOLT,
        daily_reset=False,
    ),
    RenacSensorEntityDescription(
        internal_key="S_VOL",
        key="Svoltage",
        translation_key="Svoltage",
        raw_format=True,
        device_class=SensorDeviceClass.VOLTAGE,
        state_class=SensorStateClass.MEASUREMENT,
        native_unit_of_measurement=UnitOfElectricPotential.VOLT,
        daily_reset=False,
    ),
    RenacSensorEntityDescription(
        internal_key="T_VOL",
        key="Tvoltage",
        translation_key="Tvoltage",
        raw_format=True,
        device_class=SensorDeviceClass.VOLTAGE,
        state_class=SensorStateClass.MEASUREMENT,
        native_unit_of_measurement=UnitOfElectricPotential.VOLT,
        daily_reset=False,
    ),
    RenacSensorEntityDescription(
        internal_key="R_CUR",
        key="Rcurrent",
        translation_key="Rcurrent",
        raw_format=True,
        device_class=SensorDeviceClass.CURRENT,
        state_class=SensorStateClass.MEASUREMENT,
        native_unit_of_measurement=UnitOfElectricCurrent.AMPERE,
        daily_reset=False,
    ),
    RenacSensorEntityDescription(
        internal_key="S_CUR",
        key="Scurrent",
        translation_key="Scurrent",
        raw_format=True,
        device_class=SensorDeviceClass.CURRENT,
        state_class=SensorStateClass.MEASUREMENT,
        native_unit_of_measurement=UnitOfElectricCurrent.AMPERE,
        daily_reset=False,
    ),
    RenacSensorEntityDescription(
        internal_key="T_CUR",
        key="Tcurrent",
        translation_key="Tcurrent",
        raw_format=True,
        device_class=SensorDeviceClass.CURRENT,
        state_class=SensorStateClass.MEASUREMENT,
        native_unit_of_measurement=UnitOfElectricCurrent.AMPERE,
        daily_reset=False,
    ),
    RenacSensorEntityDescription(
        internal_key="R_FRE",
        key="Rfrequency",
        translation_key="Rfrequency",
        raw_format=True,
        device_class=SensorDeviceClass.FREQUENCY,
        state_class=SensorStateClass.MEASUREMENT,
        native_unit_of_measurement=UnitOfFrequency.HERTZ,
        daily_reset=False,
    ),
    RenacSensorEntityDescription(
        internal_key="S_FRE",
        key="Sfrequency",
        translation_key="Sfrequency",
        raw_format=True,
        device_class=SensorDeviceClass.FREQUENCY,
        state_class=SensorStateClass.MEASUREMENT,
        native_unit_of_measurement=UnitOfFrequency.HERTZ,
        daily_reset=False,
    ),
    RenacSensorEntityDescription(
        internal_key="T_FRE",
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
        internal_key="ENERGY_TOTAL",
        key="ENERGY_TOTAL",
        translation_key="ENERGY_TOTAL",
        raw_format=True,
        device_class=SensorDeviceClass.ENERGY,
        state_class=SensorStateClass.TOTAL_INCREASING,
        native_unit_of_measurement=UnitOfEnergy.KILO_WATT_HOUR,
        daily_reset=False,
    ),
    RenacSensorEntityDescription(
        internal_key="ENERGY_DAY",
        key="ENERGY_TODAY",
        translation_key="ENERGY_TODAY",
        raw_format=True,
        device_class=SensorDeviceClass.ENERGY,
        state_class=SensorStateClass.TOTAL,
        native_unit_of_measurement=UnitOfEnergy.KILO_WATT_HOUR,
        daily_reset=True,
    ),
    RenacSensorEntityDescription(
        internal_key="POWER_LOAD",
        key="Load",
        translation_key="Load",
        raw_format=True,
        device_class=SensorDeviceClass.POWER,
        state_class=SensorStateClass.MEASUREMENT,
        native_unit_of_measurement=UnitOfPower.WATT,
        daily_reset=False,
    ),
    RenacSensorEntityDescription(
        internal_key="PV_POWER_TOTAL",
        key="PV",
        translation_key="PV",
        raw_format=True,
        device_class=SensorDeviceClass.POWER,
        state_class=SensorStateClass.MEASUREMENT,
        native_unit_of_measurement=UnitOfPower.WATT,
        daily_reset=False,
    ),
    RenacSensorEntityDescription(
        internal_key="BATTERY1_POWER",
        key="BAT",
        translation_key="BAT",
        raw_format=True,
        device_class=SensorDeviceClass.POWER,
        state_class=SensorStateClass.MEASUREMENT,
        native_unit_of_measurement=UnitOfPower.WATT,
        daily_reset=False,
    ),
    RenacSensorEntityDescription(
        internal_key="GRID_POWER",
        key="GRID",
        translation_key="GRID",
        raw_format=True,
        device_class=SensorDeviceClass.POWER,
        state_class=SensorStateClass.MEASUREMENT,
        native_unit_of_measurement=UnitOfPower.WATT,
        daily_reset=False,
    ),
    RenacSensorEntityDescription(
        internal_key="BATTERY1_CAPACITY",
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
        self.internal_key = description.internal_key

    @callback
    def _handle_coordinator_update(self) -> None:
        """Handle updated data from the coordinator."""
        all_data = self.coordinator.data

        if self.daily_reset:
            last_upload = self.api.fetch_field_value(all_data, "UPLOAD_TIME")
            # Only consider the update if it was uploaded on the same day.
            if datetime.fromisoformat(last_upload) >= datetime.now().replace(
                hour=0, minute=0, second=0, microsecond=0
            ):
                value = self.api.fetch_field_value(all_data, self.internal_key)
                self._attr_native_value = value
                self._attr_last_reset = datetime.fromisoformat(last_upload).replace(
                    hour=0, minute=0, second=0, microsecond=0
                )
        else:
            value = self.api.fetch_field_value(all_data, self.internal_key)
            self._attr_native_value = value

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
