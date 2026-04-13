"""The Renac Inverter integration."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timedelta
import logging

import voluptuous as vol

from homeassistant.components.recorder.models import StatisticData, StatisticMetaData
from homeassistant.components.recorder.statistics import async_import_statistics
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import CONF_PASSWORD, CONF_USERNAME, Platform, UnitOfEnergy
from homeassistant.core import HomeAssistant, ServiceCall, valid_entity_id
from homeassistant.helpers import config_validation as cv

from .const import CONF_EQUIPSN, DOMAIN
from .coordinator import RenacCoordinator
from .pyrenac import PyRenac

PLATFORMS = [
    Platform.SENSOR,
]

_LOGGER = logging.getLogger(__name__)


@dataclass
class RenacData:
    """Renac data class."""

    api: PyRenac
    coordinator: RenacCoordinator


SYNC_RECORDER_SERVICE_NAME = "sync_recorder"
SYNC_RECORDER_SCHEMA = vol.Schema(
    {
        vol.Required("start"): cv.date,
        vol.Required("end"): cv.date,
    }
)


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Set up Renac Inverter from a config entry."""

    api = PyRenac(entry.data[CONF_USERNAME], entry.data[CONF_PASSWORD])
    coordinator = RenacCoordinator("Renac", hass, api)

    # if not await api.login():
    #    raise ConfigEntryNotReady("Cannot connect to Renac SEC")

    await coordinator.async_config_entry_first_refresh()

    hass.data.setdefault(DOMAIN, {})[entry.entry_id] = RenacData(
        api,
        coordinator,
    )
    _LOGGER.info("Forwarding entry setups")
    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)

    async def sync_recorder(call: ServiceCall) -> None:
        """Search in the date range and return the matching items."""

        _LOGGER.info(
            "Sync Recorder %s from : %s to : %s",
            api.getSerial(),
            str(call.data["start"]),
            str(call.data["end"]),
        )

        def daterange(start_date, end_date):
            for n in range(int((end_date - start_date).days + 1)):
                yield start_date + timedelta(n)

        stats = []
        metadata = StatisticMetaData(
            has_mean=False,
            has_sum=True,
            name=None,
            source="recorder",
            statistic_id="sensor.inverter_today_s_generated_power",
            unit_of_measurement=UnitOfEnergy.KILO_WATT_HOUR,
        )
        date_format = "%Y-%m-%d %H:%M:%S"

        stat = None
        current_sum = float(0)
        last_state = float(0)
        for single_date in daterange(call.data["start"], call.data["end"]):
            historical_data = await api.get_historical_data(single_date)
            if historical_data is not None:
                _LOGGER.info(
                    "Got %d historical data for day %s",
                    len(historical_data),
                    single_date,
                )

            # The Long-term stats are only allowed per hour
            for data in historical_data:
                aware_datetime = datetime.strptime(data["TIME"], date_format).replace(
                    tzinfo=datetime.now().astimezone().tzinfo
                )
                if stat is not None:
                    if aware_datetime.hour != stat["start"].hour:
                        stats.append(stat)
                    if aware_datetime.day != stat["start"].day:
                        current_sum += last_state
                last_state = float(data["ENERGY"])
                stat = StatisticData(
                    start=aware_datetime.replace(minute=0, second=0, microsecond=0),
                    last_reset=aware_datetime.replace(
                        hour=0, minute=0, second=0, microsecond=0
                    ),
                    sum=current_sum + float(data["ENERGY"]),
                    state=float(data["ENERGY"]),
                )
            stats.append(stat)  # add the last one
        if valid_entity_id("sensor.inverter_today_s_generated_power"):
            _LOGGER.info("Importing %d stats", len(stats))
            async_import_statistics(hass, metadata, stats)

    hass.services.async_register(
        DOMAIN,
        SYNC_RECORDER_SERVICE_NAME,
        sync_recorder,
        schema=SYNC_RECORDER_SCHEMA,
    )

    return True


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Unload a config entry."""
    if unload_ok := await hass.config_entries.async_unload_platforms(entry, PLATFORMS):
        hass.data[DOMAIN].pop(entry.entry_id)

    return unload_ok
