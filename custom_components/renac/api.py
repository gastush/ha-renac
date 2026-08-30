"""Library providing access to the Renac SEC APIs.

Vendored and corrected copy of the logic previously provided by the external
`pyrenac` package (https://pypi.org/project/pyrenac/, version 0.1.2). That
package's login flow, response parsing and hybrid-inverter field name no
longer match the RENAC Cloud API as of 2026 (the API now requires a signed
Token/timestamp/sign header on every authenticated request, and the login
endpoint/payload/response shape changed). Rather than depending on an
external, single-maintainer package for logic this integration relies on
completely, the corrected client now lives directly in this repository.

Endpoints, field names and the signature algorithm below were verified
against live traffic from an N3-HV-10.0 hybrid inverter (see the
accompanying pull request description for details).
"""

import asyncio
from collections.abc import Coroutine
from concurrent.futures import ThreadPoolExecutor
from dataclasses import dataclass
from enum import Enum
import hashlib
import logging
import threading
import time
from typing import Any, TypeVar

import aiohttp
import requests

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


API_ROOT = "https://europe.renacpower.com:8084/api/"
RENAC_API_ROOT = "https://europe.renacpower.com:8084/renac/"
BG_API_ROOT = "https://europe.renacpower.com:8084/bg/"

# Hardcoded in the RENAC web app's own JavaScript bundle (not a server
# secret) - required to compute the `sign` header on every authenticated
# request.
SIGN_SECRET = "9P@3kF7sD2&zX5cV8bNm1qR4tY6uI0o"

_LOGGER = logging.getLogger(__name__)

InverterType = Enum("InverterType", ["ONGRID", "HYBRID"])


class Inverter:
    """The base class that represent the Inverter."""

    def __init__(self, api_client) -> None:
        """Initialize the Inverter."""
        self.api_client = api_client
        self._manufacturer = None
        self._model = None
        self._version = None
        self._type = None

    def _get_base_data(self):
        pass

    @property
    def type(self) -> Any:
        """The Inverter type."""
        return self._type


class OnGridInverter(Inverter):
    """An On-Grid ivnerter."""

    def __init__(self, api_client) -> None:
        """Initialize the Inverter."""
        super().__init__(api_client)
        self._type = InverterType.ONGRID


class HybridInverter(Inverter):
    """An hybrid inverter."""

    def __init__(self, api_client) -> None:
        """Initialize the Inverter."""
        super().__init__(api_client)
        self._type = InverterType.HYBRID


@dataclass
class RenacInverterData:
    """Renac inverter data class."""

    name: str
    version: str
    fwversion: str
    registration_time: str
    equipment_serial: str
    model: str


class PyRenac:
    """The API wrapper."""

    def __init__(self, username, password) -> None:
        """Initialize the librqry."""
        _LOGGER.info("New PyRenac instance %s", username)
        self.username = username
        self.password = password
        # Historically named `emailSn`, even though the RENAC API never
        # actually returns an email here - it's the numeric `user_id` from
        # the login response, required as-is on several other endpoints.
        self.userId = None
        self.equipSn = None
        self.token = None
        self.station_id = None
        self.inverterData = None
        inverterData = run_coroutine_sync(self.async_get_inverter_data())
        self.equipSn = inverterData.equipment_serial
        self.inverterData = inverterData

    def getSerial(self):
        """Get the serial number of the inverter."""
        return self.equipSn

    def getUniqueId(self, field):
        """Get a unique id for q given field name."""
        return "renac_" + field + "_" + self.equipSn

    def _login_request(self):
        return {"login_name": self.username, "pwd": self.password}

    def _fetch_request(self):
        return {"sn": self.equipSn, "email": self.userId}

    def _parse_login_response(self, login_response) -> None:
        if login_response.get("code") != 1 or "user" not in login_response:
            raise ValueError(f"Renac login failed: {login_response}")
        self.userId = login_response.get("data")
        self.token = login_response["user"]["token"]

    async def async_login(self) -> None:
        """Login to the Renac SEC API backend."""
        _LOGGER.info("Requesting authorization")
        req_json = self._login_request()
        async with (
            aiohttp.ClientSession() as session,
            session.post(API_ROOT + "user/login", json=req_json) as resp,
        ):
            _LOGGER.debug(resp.status)
            loginResponse = await resp.json(content_type=None)
            self._parse_login_response(loginResponse)
            _LOGGER.debug("Login successful, user_id=%s", self.userId)

    def login(self) -> None:
        """Login to the Renac SEC API backend."""
        _LOGGER.info("Requesting authorization")
        req_json = self._login_request()
        resp = requests.post(API_ROOT + "user/login", json=req_json, timeout=60)
        if resp.status_code == 200:
            loginResponse = resp.json()
            self._parse_login_response(loginResponse)

    def fetch_field_value(self, data, field, context=None):
        """Fetch the given field from the data."""
        _LOGGER.debug("Fetch field value %s", field)
        if context is None:
            context = "im"
        if data is not None:
            if data.get(context) is not None:
                return data[context].get(field)
            else:
                return data.get(field)
        return None

    async def async_fetch(self, field, context=None):
        """Fetch the data identified by the field."""
        if context is None:
            context = "im"
        data = await self.async_fetch_all()
        if data is not None:
            return data[context].get(field)
        return None

    def fetch(self, field, context=None):
        """Fetch the data identified by the field."""
        if context is None:
            context = "im"
        data = self.fetch_all()
        if data is not None:
            return data[context].get(field)
        return None

    def build_header(self):
        """Build the header for the requests."""
        token = self.token
        timestamp = str(int(time.time()))

        # Concatenate the token, timestamp, and hardcoded value
        data_to_sign = f"{token}{timestamp}{SIGN_SECRET}"

        # Calculate the MD5 digest
        sign = hashlib.md5(data_to_sign.encode()).hexdigest()

        return {
            "Content-Type": "application/json;charset=UTF-8",
            "Token": token,
            "timestamp": timestamp,
            "sign": sign,
        }

    async def async_ensure_login(self):
        """Ensure that we have a valid Token to be used."""
        if self.token is None:
            _LOGGER.info("Token is null, new fresh login sequence required")
            await self.async_login()

    def ensure_login(self):
        """Ensure that we have a valid Token to be used."""
        if self.token is None:
            _LOGGER.info("Token is null, new fresh login sequence required")
            self.login()

    async def async_fetch_all(self, context=None):
        """Fetch all the data.

        A login will be done if needed to retrieve the right token.
        """
        _LOGGER.debug("Fetching all data")
        data = None
        await self.async_ensure_login()
        current_date = time.strftime("%Y-%m-%d")
        req_json = {
            "equ_sn": self.equipSn,
            "offset": 0,
            "rows": 10,
            "time": current_date,
        }
        headers = self.build_header()
        timeout = aiohttp.ClientTimeout(total=30)
        async with (
            aiohttp.ClientSession() as session,
            session.post(
                BG_API_ROOT + "inv/detail",
                json=req_json,
                headers=headers,
                timeout=timeout,
            ) as resp,
        ):
            if resp.status == 200:
                response = await resp.json(content_type=None)
                _LOGGER.debug("Got %s", response)
                if "data" in response and response["data"] is not None:
                    data = {}
                    if "inv" in response.get("data"):
                        data["inv"] = response.get("data").get("inv")
                    if "im" in response.get("data"):
                        data["im"] = response.get("data").get("im")
                    if "invInfo" in response.get("data"):
                        data["invInfo"] = response.get("data").get("invInfo")
                else:
                    _LOGGER.info("Null results. assuming a new Token is required")
                    self.token = None
            else:
                _LOGGER.error("Failed to read sensor %s", resp.status)
                raise RuntimeError("Failed to read sensor " + str(resp.status))
        if context is not None:
            return data.get(context)
        return data

    def fetch_all(self, context=None):
        """Fetch all the data.

        A login will be done if needed to retrieve the right token.
        """
        _LOGGER.debug("Fetching all data")
        data = None
        self.ensure_login()
        current_date = time.strftime("%Y-%m-%d")
        req_json = {
            "equ_sn": self.equipSn,
            "offset": 0,
            "rows": 10,
            "time": current_date,
        }
        headers = self.build_header()
        resp = requests.post(
            BG_API_ROOT + "inv/detail", headers=headers, json=req_json, timeout=60
        )
        if resp.status_code == 200:
            response = resp.json()
            if "data" in response:
                data = {}
                if "inv" in response.get("data"):
                    data["inv"] = response.get("data").get("inv")
                if "im" in response.get("data"):
                    data["im"] = response.get("data").get("im")
                if "invInfo" in response.get("data"):
                    data["invInfo"] = response.get("data").get("invInfo")
            else:
                _LOGGER.info("Null results. assuming a new Token is required")
                self.token = None
        else:
            _LOGGER.error("Failed to read sensor %s", resp.status_code)
            raise RuntimeError("Failed to read sensor " + str(resp.status_code))

        if context is not None:
            return data.get(context)
        return data

    def getType(self, data) -> "InverterType":
        """Get the Inverter Type from the availqble fields."""
        inverterType = None
        try:
            value = self.fetch_field_value(
                data, "BATTERY1_CAPACITY"
            )  # HYBRID inverter have a battery.
            if value is None:
                inverterType = InverterType.ONGRID
            else:
                inverterType = InverterType.HYBRID
        except KeyError:
            inverterType = InverterType.ONGRID  # Assume this is an On-Grid inverter.
        return inverterType

    def _station_list_request(self):
        return {
            "user_id": self.userId,
            "station_name": "",
            "status": None,
            "station_type": None,
            "offset": 0,
            "rows": 10,
        }

    async def async_get_station_id(self):
        """Get the station id."""
        if self.station_id is None:
            await self.async_ensure_login()
            req_json = self._station_list_request()
            headers = self.build_header()
            timeout = aiohttp.ClientTimeout(total=30)
            async with (
                aiohttp.ClientSession() as session,
                session.post(
                    API_ROOT + "station/list",
                    json=req_json,
                    headers=headers,
                    timeout=timeout,
                ) as resp,
            ):
                if resp.status == 200:
                    response = await resp.json(content_type=None)
                    if "data" in response and response["data"] is not None:
                        self.station_id = response["data"]["list"][0]["station_id"]
                    else:
                        _LOGGER.info("Null results. assuming a new Token is required")
                        self.token = None
                else:
                    raise RuntimeError("Failed to read sensor " + str(resp.status))
            _LOGGER.debug("Got station_id %s", self.station_id)
        return self.station_id

    def get_station_id(self):
        """Get the station id."""
        if self.station_id is None:
            self.ensure_login()
            req_json = self._station_list_request()
            headers = self.build_header()
            resp = requests.post(
                API_ROOT + "station/list", headers=headers, json=req_json, timeout=60
            )
            if resp.status_code == 200:
                response = resp.json()
                if "data" in response and response["data"] is not None:
                    self.station_id = response["data"]["list"][0]["station_id"]
                else:
                    _LOGGER.info("Null results. assuming a new Token is required")
                    self.token = None
            else:
                raise RuntimeError("Failed to read sensor " + str(resp.status_code))
            _LOGGER.debug("Got station_id %s", self.station_id)
        return self.station_id

    async def async_get_historical_data(self, date):
        """Get Historical production data for the given date time range."""
        data = None
        await self.async_ensure_login()
        station_id = await self.async_get_station_id()
        req_json = {"station_id": station_id, "time": str(date), "time_type": 1}
        headers = self.build_header()
        timeout = aiohttp.ClientTimeout(total=30)
        async with (
            aiohttp.ClientSession() as session,
            session.post(
                RENAC_API_ROOT + "station/energy",
                json=req_json,
                headers=headers,
                timeout=timeout,
            ) as resp,
        ):
            if resp.status == 200:
                response = await resp.json(content_type=None)
                if "data" in response:
                    data = response["data"]
                else:
                    _LOGGER.info("Null results. assuming a new Token is required")
                    self.token = None
            else:
                raise RuntimeError("Failed to read sensor " + str(resp.status))
        return data

    def get_inverter_data(self) -> RenacInverterData:
        """Get details about the inverter itslef."""
        if self.inverterData is None:
            self.inverterData = RenacInverterData(
                version=self.async_fetch("version", "inv"),
                fwversion=self.async_fetch("hmi_version", "inv"),
                name=self.async_fetch("equ_POSITION", "invInfo"),
                registration_time=self.async_fetch("reg_TIME", "inv"),
                equipment_serial=self.async_fetch("inv_SN", "inv"),
                model=self.async_fetch("equ_MODEL_NAME", "inv"),
            )
        return self.inverterData

    async def async_get_serial_numbers(self) -> list[str]:
        """Get the serial number of the inverter."""
        await self.async_ensure_login()
        station_id = await self.async_get_station_id()
        req_json = {
            "user_id": self.userId,
            "station_id": station_id,
            "status": 0,
            "offset": 0,
            "rows": 10,
            "equ_sn": "",
        }
        headers = self.build_header()
        timeout = aiohttp.ClientTimeout(total=30)
        async with (
            aiohttp.ClientSession() as session,
            session.post(
                BG_API_ROOT + "equList",
                json=req_json,
                headers=headers,
                timeout=timeout,
            ) as resp,
        ):
            if resp.status == 200:
                response = await resp.json(content_type=None)
                if "data" in response and response["data"] is not None:
                    data = response["data"]["list"]
                    return [item["INV_SN"] for item in data]
            else:
                raise RuntimeError("Failed to read sensor " + str(resp.status))

    async def async_get_inverter_data(self) -> RenacInverterData:
        """Get details about the inverter itslef."""
        if self.inverterData is None:
            await self.async_ensure_login()
            station_id = await self.async_get_station_id()
            req_json = {
                "station_id": station_id,
                "user_id": self.userId,
                "status": 0,
                "offset": 0,
                "rows": 1,
            }
            headers = self.build_header()
            timeout = aiohttp.ClientTimeout(total=30)
            async with (
                aiohttp.ClientSession() as session,
                session.post(
                    BG_API_ROOT + "equList",
                    json=req_json,
                    headers=headers,
                    timeout=timeout,
                ) as resp,
            ):
                if resp.status == 200:
                    response = await resp.json(content_type=None)
                    if "data" in response and response["data"] is not None:
                        data = response["data"]["list"]
                        if len(data) > 0:
                            self.inverterData = RenacInverterData(
                                version=data[0].get("FIRMWARE_VER"),
                                fwversion=data[0].get("FIRMWARE_VER"),
                                name=data[0].get("EQU_POSITION"),
                                registration_time=data[0].get("REG_TIME"),
                                equipment_serial=data[0].get("INV_SN"),
                                model=data[0].get("MODEL_NAME"),
                            )
                    else:
                        _LOGGER.info("Null results. assuming a new Token is required")
                        self.token = None
                else:
                    raise RuntimeError("Failed to read sensor " + str(resp.status))
        return self.inverterData


class InverterFactory:
    """The inverter factory."""

    def getInverter(self, api_client: PyRenac) -> Inverter:
        """Get the inverter based on his type."""
        inverterType = api_client.getType()
        if inverterType is InverterType.ONGRID:
            return OnGridInverter(api_client)
        if inverterType is InverterType.HYBRID:
            return HybridInverter(api_client)
        raise ValueError("Unsupported Inverter type")
