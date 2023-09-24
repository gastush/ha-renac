# Renac Inverter
import logging
from homeassistant.const import EVENT_HOMEASSISTANT_START, EVENT_HOMEASSISTANT_STOP
from homeassistant.helpers import discovery
import homeassistant.helpers.config_validation as cv
import voluptuous as vol
import threading
import requests

_LOGGER = logging.getLogger(__name__)

DOMAIN = "renac"

CONF_USERNAME = "username"
CONF_PASSWORD = "password"
CONF_EQUIPSN = "equipment_serial"

REQ_LOCK = threading.Lock()
CONFIG_SCHEMA = vol.Schema(
	{
		DOMAIN: vol.Schema({
			vol.Required(CONF_USERNAME): cv.string,
			vol.Required(CONF_PASSWORD): cv.string,
			vol.Required(CONF_EQUIPSN): cv.string
			})
	},
	extra=vol.ALLOW_EXTRA,
)

async def async_setup(hass, config):
	conf = config[DOMAIN]
	hass.data[DOMAIN] = conf
	# Load components
	hass.async_create_task(
		discovery.async_load_platform(hass, "sensor", DOMAIN, {}, config)
	)
	return True


