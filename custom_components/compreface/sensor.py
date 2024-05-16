"""Sensor platform for CompreFace."""

import asyncio
from datetime import datetime
import os
from time import sleep

from compreface import CompreFace
from compreface.service import RecognitionService
from homeassistant.components.sensor import (
    SensorDeviceClass,
    SensorEntity,
    SensorStateClass,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import (
    HomeAssistant,
    ServiceCall,
    ServiceRegistry,
    ServiceResponse,
    SupportsResponse,
)
from homeassistant.helpers import device_registry as dr
from homeassistant.helpers.device_registry import DeviceInfo
from homeassistant.helpers.entity_platform import (
    AddEntitiesCallback,
    async_get_current_platform,
)

from .const import CONF_IMAGE_TEMP_DIR, DOMAIN


async def async_setup_entry(
    hass: HomeAssistant, entry: ConfigEntry, async_add_devices: AddEntitiesCallback
):
    """Setup sensor platform."""  # noqa: D401

    if "recognition_camera_devices" in entry.options and isinstance(
        entry.options.get("recognition_camera_devices"), list
    ):
        recognition_camera_devices = entry.options.get("recognition_camera_devices")

        recognition_entities = []

        for device in recognition_camera_devices:
            entity = CompreFaceRecognitionSensor(
                hass, device, entry.data.get(CONF_IMAGE_TEMP_DIR)
            )
            recognition_entities.append(entity)

        async_add_devices(recognition_entities)

    platform = async_get_current_platform()

    platform.async_register_entity_service(
        "update", {}, "update_service_callback", supports_response=SupportsResponse.ONLY
    )

    return True


async def async_unload_entry(hass, entry):
    """Unload sensor platform."""
    return True


class CompreFaceRecognitionSensor(SensorEntity):
    """CompreFace recognition sensor class."""

    def __init__(self, hass: HomeAssistant, camera_device_id: str, image_temp_dir: str):
        self.hass = hass
        self.camera_device_id = camera_device_id
        self.image_temp_dir = image_temp_dir

        device_registry = dr.async_get(hass)
        device = device_registry.async_get(camera_device_id)

        self._name = f"{device.name} CompreFace Recognition Sensor"

        self._person = "none"

    @property
    def unique_id(self):
        """Return the unique ID."""
        return self.camera_device_id

    @property
    def name(self):
        """Return the name of the sensor."""
        return self._name

    @property
    def state(self):
        """Return the state of the sensor."""
        return self._person

    # @property
    # def icon(self):
    #     """Return the icon of the sensor."""
    #     return ICON

    # @property
    # def device_class(self):
    #     """Return de device class of the sensor."""
    #     return "compreface__custom_device_class"

    @property
    def device_info(self) -> DeviceInfo:
        """Return the device info."""
        return DeviceInfo(
            identifiers={
                # Serial numbers are unique identifiers within a specific domain
                (DOMAIN, self.unique_id)
            },
            name=self.name,
        )

    @property
    def should_poll(self):
        """Return the polling state."""
        return False

    async def update_service_callback(self) -> ServiceResponse:
        """Service to recognize a face from a camera entity."""

        #     self.hass.async_add_executor_job(self._async_update_internal)

        # async def _async_update_internal(self):
        recognition: RecognitionService = self.hass.data[DOMAIN]["recognition"]

        camera_device_id = self.camera_device_id

        # Generate filename based on datetime:
        img_filename = os.path.join(
            self.image_temp_dir,
            f"recognition_image_tmp_{datetime.now().strftime('%Y%m%d%H%M%S')}.jpg",
        )
        # img_filename = f"{self.image_temp_dir}/recognition_image_tmp_{datetime.now().strftime('%Y%m%d%H%M%S')}.jpg"

        await self.hass.services.async_call(
            "camera",
            "snapshot",
            target={"device_id": camera_device_id},
            service_data={
                "filename": img_filename
            },  # Use a secure location for the image file
        )

        # success = asyncio.run_coroutine_threadsafe(
        #     self._async_await_image(img_filename), self.hass.loop
        # ).result()

        success = await self.hass.async_add_executor_job(
            self._await_image_blocking, img_filename
        )

        if not success:
            self._person = "none"

        else:
            result = await self.hass.async_add_executor_job(
                recognition.recognize, img_filename
            )

            subject = None

            try:
                subject = result["result"][0]["subjects"][0]

                if subject["similarity"] > 0.8:
                    self._person = subject["subject"]
                else:
                    self._person = "none"
            # Keyerror and typeerror;
            except (KeyError, TypeError, IndexError):
                self._person = "none"

        # Remove the temporary image file
        self.hass.async_add_executor_job(self._delete_image_blocking, img_filename)

        self.async_schedule_update_ha_state()

        return {
            "success": success,
            "person": self._person,
        }

    def _await_image_blocking(self, img_filename):
        """Wait for the image to be created."""
        now = datetime.now()

        while not os.path.exists(img_filename):
            if (datetime.now() - now).seconds > 5:
                return False

            sleep(0.5)

        return True

    def _delete_image_blocking(self, img_filename):
        """Wait for the image to be deleted."""
        now = datetime.now()

        while not os.path.exists(img_filename):
            if (datetime.now() - now).seconds > 60:
                return
            sleep(1)

        os.remove(img_filename)
