from copy import deepcopy
import logging
from typing import Any, Dict, Optional

from homeassistant import config_entries, core
from homeassistant.const import CONF_ACCESS_TOKEN, CONF_NAME, CONF_PATH, CONF_URL
from homeassistant.core import callback
from homeassistant.helpers.aiohttp_client import async_get_clientsession
import homeassistant.helpers.config_validation as cv
from homeassistant.helpers.entity_registry import (
    async_entries_for_config_entry,
    async_get_registry,
)
import voluptuous as vol

from .const import CONF_USERNAME, CONF_PASSWORD, CONF_EQUIPSN, DOMAIN, API_ROOT

_LOGGER = logging.getLogger(__name__)

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

async def validate_auth(username: str, password: str, hass: core.HomeAssistant) -> None:
    """Validates Renac Credentials

    Raises a ValueError if the credentials are invalid.
    """
    _LOGGER.info("Requesting authorization...")
    req_json = {
        "loginName": username, 
        "password": password
    }
    r = requests.post(API_ROOT+'login', json=req_json)
    if r.status_code == 200:
        _LOGGER.info("Got email id :" + str(r.json()['email']))
        return
    else:
        _LOGGER.error("Failed to login to renac : " + str(r.json()))
        raise ValueError


class RenacCustomConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Renac Custom config flow."""

    data: Optional[Dict[str, Any]]

    async def async_step_user(self, user_input: Optional[Dict[str, Any]] = None):
        """Invoked when a user initiates a flow via the user interface."""
        errors: Dict[str, str] = {}
        if user_input is not None:
            try:
                await validate_auth(user_input[CONF_USERNAME], user_input[CONF_PASSWORD], self.hass)
            except ValueError:
                errors["base"] = "auth"
            if not errors:
                # Input is valid, set data.
                self.data = user_input

                return self.async_create_entry(title="Renac", data=self.data)

        return self.async_show_form(
            step_id="user", data_schema=CONFIG_SCHEMA, errors=errors
        )

 