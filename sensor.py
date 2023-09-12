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
import requests
import logging

_LOGGER = logging.getLogger(__name__)

DOMAIN = "renac"

CONF_USERNAME = "username"
CONF_PASSWORD = "password"
CONF_EQUIPSN = "equipment_serial"

API_ROOT = "http://153.le-pv.com:8082/api/"

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
    add_entities([PowerSensor(emailSn, conf.get(CONF_EQUIPSN)),
        TodayPowerSensor(emailSn, conf.get(CONF_EQUIPSN))])

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

class PowerSensor(SensorEntity):
    def __init__(self, emailSn, equipSn):
        self.emailSn = emailSn
        self.equipSn = equipSn
        self._attr_name = "Power"
        self._attr_native_unit_of_measurement = "W" 
        self._attr_state_class = SensorStateClass.MEASUREMENT
        self._attr_device_class = SensorDeviceClass.POWER
    
    @property
    def name(self):
        return "Renac Generated Power"
    
    def update(self) -> None:
        """Fetch new state data for the sensor.
        This is the only method that should fetch new data for Home Assistant.
        """
        req_json = {
            "sn": self.equipSn,
            "email": self.emailSn
        }
        r = requests.post(API_ROOT+'equipDetail', json=req_json)
        if r.status_code == 200:
            self._attr_native_value = r.json()['results']['acPower']
        else:
            raise("Failed to update sensor " + str(r.status_code))

class TodayPowerSensor(SensorEntity):
    def __init__(self, emailSn, equipSn):
        self.emailSn = emailSn
        self.equipSn = equipSn
        self._attr_name = "Today's Power"
        self._attr_native_unit_of_measurement = "kWh" 
        self._attr_state_class = SensorStateClass.MEASUREMENT
    
    @property
    def name(self):
        return "Renac Today's Generated Power"
    
    def update(self) -> None:
        """Fetch new state data for the sensor.
        This is the only method that should fetch new data for Home Assistant.
        """
        req_json = {
            "sn": self.equipSn,
            "email": self.emailSn
        }
        r = requests.post(API_ROOT+'equipDetail', json=req_json)
        if r.status_code == 200:
            self._attr_native_value = r.json()['results']['todayPower']
        else:
            raise("Failed to update sensor " + str(r.status_code))
