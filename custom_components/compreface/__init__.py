"""Custom integration to integrate CompreFace with Home Assistant.

For more details about this integration, please refer to
https://github.com/frnyb/compreface
"""

import asyncio
from datetime import timedelta
import logging
import socket

import voluptuous as vol

from compreface import CompreFace
from compreface.service import RecognitionService
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import Platform
from homeassistant.core import HomeAssistant
from homeassistant.exceptions import ConfigEntryNotReady
from homeassistant.helpers.aiohttp_client import async_get_clientsession
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed

from .const import (
    CONF_DETECT_API_KEY,
    CONF_HOST,
    CONF_PORT,
    CONF_RECOGNIZE_API_KEY,
    CONF_VERIFY_API_KEY,
    DOMAIN,
    STARTUP_MESSAGE,
)

# SCAN_INTERVAL = timedelta(seconds=30)

_LOGGER: logging.Logger = logging.getLogger(__package__)

PLATFORMS = [Platform.SENSOR]


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry):
    """Set up this integration using UI."""
    if hass.data.get(DOMAIN) is None:
        hass.data.setdefault(DOMAIN, {})
        _LOGGER.info(STARTUP_MESSAGE)

    host: str = entry.data.get(CONF_HOST)
    try:
        socket.gethostbyname(host)
    except OSError:
        _LOGGER.error("Invalid host: %s", host)
        return False

    # If host does not start with http:// or https://, add http://
    if not host.startswith("http://") and not host.startswith("https://"):
        host = f"http://{host}"

    port = entry.data.get(CONF_PORT)

    compre_face: CompreFace = CompreFace(host, str(port))

    hass.data[DOMAIN]["compre_face"] = compre_face

    if (
        CONF_RECOGNIZE_API_KEY in entry.data
        and entry.data.get(CONF_RECOGNIZE_API_KEY) is not None
        and entry.data.get(CONF_RECOGNIZE_API_KEY) != ""
    ):
        recognition: RecognitionService = compre_face.init_face_recognition(
            entry.data.get(CONF_RECOGNIZE_API_KEY)
        )

        hass.data[DOMAIN]["recognition"] = recognition

    else:
        hass.data[DOMAIN]["recognition"] = None

    if (
        CONF_VERIFY_API_KEY in entry.data
        and entry.data.get(CONF_VERIFY_API_KEY) is not None
        and entry.data.get(CONF_VERIFY_API_KEY) != ""
    ):
        verification = compre_face.init_face_verification(
            entry.data.get(CONF_VERIFY_API_KEY)
        )

        hass.data[DOMAIN]["verification"] = verification

    else:
        hass.data[DOMAIN]["verification"] = None

    if (
        CONF_DETECT_API_KEY in entry.data
        and entry.data.get(CONF_DETECT_API_KEY) is not None
        and entry.data.get(CONF_DETECT_API_KEY) != ""
    ):
        detection = compre_face.init_face_detection(entry.data.get(CONF_DETECT_API_KEY))

        hass.data[DOMAIN]["detection"] = detection

    else:
        hass.data[DOMAIN]["detection"] = None

    # session = async_get_clientsession(hass)
    # client = CompreFaceApiClient(username, password, session)

    # coordinator = CompreFaceDataUpdateCoordinator(hass, client=client)
    # await coordinator.async_refresh()

    # if not coordinator.last_update_success:
    #     raise ConfigEntryNotReady

    # hass.data[DOMAIN][entry.entry_id] = coordinator

    await _async_setup_platforms(hass, entry)

    entry.add_update_listener(_async_reload_platforms)

    return True


async def _async_setup_platforms(hass: HomeAssistant, entry: ConfigEntry):
    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)


async def _async_unload_platforms(hass: HomeAssistant, entry: ConfigEntry):
    await hass.config_entries.async_unload_platforms(entry, PLATFORMS)


async def _async_reload_platforms(hass: HomeAssistant, entry: ConfigEntry):
    await _async_unload_platforms(hass, entry)
    await _async_setup_platforms(hass, entry)


# class CompreFaceDataUpdateCoordinator(DataUpdateCoordinator):
#     """Class to manage fetching data from the API."""

#     def __init__(
#         self,
#         hass: HomeAssistant,
#         client: CompreFaceApiClient,
#     ) -> None:
#         """Initialize."""
#         self.api = client
#         self.platforms = []

#         super().__init__(hass, _LOGGER, name=DOMAIN, update_interval=SCAN_INTERVAL)

#     async def _async_update_data(self):
#         """Update data via library."""
#         try:
#             return await self.api.async_get_data()
#         except Exception as exception:
#             raise UpdateFailed from exception


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Handle removal of an entry."""
    await _async_unload_platforms(hass, entry)
    # coordinator = hass.data[DOMAIN][entry.entry_id]
    # unloaded = all(
    #     await asyncio.gather(
    #         *[
    #             hass.config_entries.async_forward_entry_unload(entry, platform)
    #             for platform in PLATFORMS
    #             if platform in coordinator.platforms
    #         ]
    #     )
    # )
    # if unloaded:
    hass.data.pop(DOMAIN)

    # return unloaded
    return True


async def async_reload_entry(hass: HomeAssistant, entry: ConfigEntry) -> None:
    """Reload config entry."""

    await async_unload_entry(hass, entry)
    await async_setup_entry(hass, entry)

    # hass.services.async_register(
    #     DOMAIN,
    #     "recognize_from_camera",
    #     recognize_face_service_callback,
    #     # schema={
    #     #     vol.Required("camera_entity_id"): str,
    #     # },
    #     supports_response=SupportsResponse.ONLY,
    # )
