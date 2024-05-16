"""Adds config flow for CompreFace."""

import socket

import voluptuous as vol

from homeassistant import config_entries
from homeassistant.core import callback
from homeassistant.helpers.selector import (
    DeviceSelector,
    DeviceSelectorConfig,
    EntityFilterSelectorConfig,
)

from .const import (
    CONF_DETECT_API_KEY,
    CONF_HOST,
    CONF_RECOGNIZE_API_KEY,
    CONF_VERIFY_API_KEY,
    CONFIG_FLOW_DATA_SCHEMA_USER,
    DOMAIN,
)


class CompreFaceFlowHandler(config_entries.ConfigFlow, domain=DOMAIN):
    """Config flow for compreface."""

    VERSION = 1
    CONNECTION_CLASS = config_entries.CONN_CLASS_CLOUD_POLL

    def __init__(self) -> None:
        """Initialize."""
        self._errors = {}

    async def async_step_user(self, user_input=None):
        """Handle a flow initialized by the user."""
        self._errors = {}

        # Uncomment the next 2 lines if only a single instance of the integration is allowed:
        if self._async_current_entries():
            return self.async_abort(reason="single_instance_allowed")

        if user_input is not None:
            valid = self._test_host(user_input[CONF_HOST])
            valid = valid and self._test_API_keys(user_input)
            if valid:
                return self.async_create_entry(title="CompreFace", data=user_input)

            self._errors["base"] = "value_error"

            return self.async_show_form(
                step_id="user",
                data_schema=CONFIG_FLOW_DATA_SCHEMA_USER,
                errors=self._errors,
            )

        return self.async_show_form(
            step_id="user",
            data_schema=CONFIG_FLOW_DATA_SCHEMA_USER,
            errors=self._errors,
        )

    @staticmethod
    @callback
    def async_get_options_flow(config_entry):
        """Get the options flow for this handler."""
        return CompreFaceOptionsFlowHandler(config_entry)

    def _test_host(self, host) -> bool:
        """Return true if host is a valid IP address."""
        try:
            socket.gethostbyname(host)
        except OSError:
            return False

        return True

    def _test_API_keys(self, user_input) -> bool:
        """Return false if all API keys are empty."""

        for key in [CONF_RECOGNIZE_API_KEY, CONF_VERIFY_API_KEY, CONF_DETECT_API_KEY]:
            if user_input[key] != "":
                return True

        return False


class CompreFaceOptionsFlowHandler(config_entries.OptionsFlow):
    """Config flow options handler for compreface."""

    def __init__(self, config_entry):
        """Initialize HACS options flow."""
        self.config_entry = config_entry
        self.options = dict(config_entry.options)

        self._compre_face_services = []

        if (
            CONF_RECOGNIZE_API_KEY in config_entry.data
            and config_entry.data.get(CONF_RECOGNIZE_API_KEY) is not None
            and config_entry.data.get(CONF_RECOGNIZE_API_KEY) != ""
        ):
            self._compre_face_services.append("recognition")

        if (
            CONF_VERIFY_API_KEY in config_entry.data
            and config_entry.data.get(CONF_VERIFY_API_KEY) is not None
            and config_entry.data.get(CONF_VERIFY_API_KEY) != ""
        ):
            self._compre_face_services.append("verification")

        if (
            CONF_DETECT_API_KEY in config_entry.data
            and config_entry.data.get(CONF_DETECT_API_KEY) is not None
            and config_entry.data.get(CONF_DETECT_API_KEY) != ""
        ):
            self._compre_face_services.append("detection")

    async def async_next_step(self, user_input=None):
        """Find and advance to the next step."""

        if len(self._compre_face_services) == 0:
            return await self._update_options()

        srv = self._compre_face_services.pop(0)

        if srv == "recognition":
            return await self.async_step_recognition(user_input=user_input)

        if srv == "verification":
            return await self.async_step_verification(user_input=user_input)

        if srv == "detection":
            return await self.async_step_detection(user_input=user_input)

    async def async_step_init(self, user_input=None):
        """Manage the flow."""

        return await self.async_next_step(user_input)

    async def async_step_recognition(self, user_input=None):
        """Handle options for recognition service."""

        if user_input is not None:
            self.options.update(user_input)
            return await self.async_next_step()

        return self.async_show_form(
            step_id="recognition",
            data_schema=vol.Schema(
                {
                    "recognition_camera_devices": DeviceSelector(
                        DeviceSelectorConfig(
                            multiple=True,
                            entity=EntityFilterSelectorConfig(domain="camera"),
                        )
                    )
                }
            ),
        )

    async def async_step_verification(self, user_input=None):
        """Handle options for verification service."""

        if user_input is not None:
            self.options.update(user_input)
            return await self.async_next_step()

        return self.async_show_form(
            step_id="verification",
            data_schema=vol.Schema(
                {
                    "verification_camera_devices": DeviceSelector(
                        DeviceSelectorConfig(
                            multiple=True,
                            entity=EntityFilterSelectorConfig(domain="camera"),
                        )
                    )
                }
            ),
        )

    async def async_step_detection(self, user_input=None):
        """Handle options for detection service."""

        if user_input is not None:
            self.options.update(user_input)
            return await self.async_next_step()

        return self.async_show_form(
            step_id="detection",
            data_schema=vol.Schema(
                {
                    "detection_camera_devices": DeviceSelector(
                        DeviceSelectorConfig(
                            multiple=True,
                            entity=EntityFilterSelectorConfig(domain="camera"),
                        )
                    )
                }
            ),
        )

    async def _update_options(self):
        """Update config entry options."""
        return self.async_create_entry(title="Test", data=self.options)
