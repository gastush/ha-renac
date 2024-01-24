"""Platform for sensor integration."""
from __future__ import annotations

from homeassistant.components.sensor import (
    SensorEntity,
    SensorStateClass,
    SensorDeviceClass,
)
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.typing import ConfigType, DiscoveryInfoType
import time
import requests
import logging

_LOGGER = logging.getLogger(__name__)

DOMAIN = "renac"

CONF_USERNAME = "username"
CONF_PASSWORD = "password"
CONF_EQUIPSN = "equipment_serial"

API_ROOT = "https://sec.bg.renacpower.cn:8084/api/"

class Updater():
    def __init__(self, emailSn, equipSn):
        self.emailSn = emailSn
        self.equipSn = equipSn
        self.data = {}
        self.lastUpdate = 0

    def fetch(self, field):
        if self.lastUpdate + 10 < time.time():
            req_json = {
                "sn": self.equipSn,
                "email": self.emailSn
            }
            r = requests.post(API_ROOT+'equipDetail', json=req_json)
            if r.status_code == 200:
                self.lastUpdate = time.time()
                self.data = r.json()['results']
            else:
                raise("Failed to update sensor " + str(r.status_code))

        return self.data[field]

def setup_platform(
    hass: HomeAssistant,
    config: ConfigType,
    add_entities: AddEntitiesCallback,
    discovery_info: DiscoveryInfoType | None = None
) -> None:
    """Set up the sensor platform."""
    _LOGGER.info("Init...")
    conf = hass.data[DOMAIN]
    emailSn = login(conf.get(CONF_USERNAME), conf.get(CONF_PASSWORD))
    updater = Updater(emailSn, conf.get(CONF_EQUIPSN))
    add_entities([
        EnergySensor(updater, 'acPower', 'Generated'),
        PowerSensor(updater, 'todayPower', "Today's"),
        PowerSensor(updater, 'totalPower', "Total"),
        VoltageSensor(updater, 'PV1voltage', 'PV1'),
        VoltageSensor(updater, 'PV2voltage', 'PV2'),
        CurrentSensor(updater, 'PV1current', 'PV1'),
        CurrentSensor(updater, 'PV2current', 'PV2'),
        EnergySensor(updater, 'PV1power', 'PV1'),
        EnergySensor(updater, 'PV2power', 'PV2'),
        VoltageSensor(updater, 'Rvoltage', 'R'),
        VoltageSensor(updater, 'Svoltage', 'S'),
        VoltageSensor(updater, 'Tvoltage', 'T'),
        CurrentSensor(updater, 'Rcurrent', 'R'),
        CurrentSensor(updater, 'Scurrent', 'S'),
        CurrentSensor(updater, 'Tcurrent', 'T')
        ])

def login(username, password):
    _LOGGER.info("Requesting authorization...")
    req_json = {
        "loginName": username, 
        "password": password
    }
    r = requests.post(API_ROOT+'login', json=req_json)
    if r.status_code == 200:
        _LOGGER.info("Got email id :" + str(r.json()['email']))
        return r.json()['email']
    else:
        _LOGGER.error("Failed to login to renac : " + str(r.json()))
        raise("Failed to login")

class EnergySensor(SensorEntity):
    def __init__(self, updater, field, name):
        self.updater = updater
        self.field = field
        self.display_name = name
        self._attr_name = name + "_Power"
        self._attr_native_unit_of_measurement = "W" 
        self._attr_state_class = SensorStateClass.MEASUREMENT
        self._attr_device_class = SensorDeviceClass.POWER
    
    @property
    def name(self):
        return "Renac " + self.display_name + " Power"
    
    def update(self) -> None:
        self._attr_native_value = self.updater.fetch(self.field)

class PowerSensor(SensorEntity):
    def __init__(self, updater, field, name):
        self.updater = updater
        self.field = field
        self.display_name = name
        self._attr_name = name + " Power"
        self._attr_native_unit_of_measurement = "kWh" 
        self._attr_state_class = SensorStateClass.MEASUREMENT
    
    @property
    def name(self):
        return "Renac " + self.display_name + " Generated Power"
    
    def update(self) -> None:
        self._attr_native_value = self.updater.fetch(self.field)


class VoltageSensor(SensorEntity):
    def __init__(self, updater, field, name):
        self.updater = updater
        self.field = field
        self.display_name = name
        self._attr_name = name + " Voltage" 
        self._attr_native_unit_of_measurement = "V" 
        self._attr_state_class = SensorStateClass.MEASUREMENT

    @property
    def name(self):
        return "Renac " + self.display_name + " Voltage"

    def update(self) -> None:
        self._attr_native_value = self.updater.fetch(self.field)

class CurrentSensor(SensorEntity):
    def __init__(self, updater, field, name):
        self.updater = updater
        self.field = field
        self.display_name = name
        self._attr_name =  name + " Current" 
        self._attr_native_unit_of_measurement = "A" 
        self._attr_state_class = SensorStateClass.MEASUREMENT

    @property
    def name(self):
        return "Renac " + self.display_name + " Current"

    def update(self) -> None:
        self._attr_native_value = self.updater.fetch(self.field)
