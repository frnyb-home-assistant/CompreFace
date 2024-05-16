"""Constants for CompreFace."""

import voluptuous as vol

# Base component constants
NAME = "CompreFace"
DOMAIN = "compreface"
DOMAIN_DATA = f"{DOMAIN}_data"
VERSION = "0.0.0"

PLATFORMS = ["sensor"]

STARTUP_MESSAGE = f"Starting {NAME}..."

# Configuration
CONF_HOST = "host"
CONF_PORT = "port"
CONF_RECOGNIZE_API_KEY = "recognize_api_key"
CONF_VERIFY_API_KEY = "verify_api_key"
CONF_DETECT_API_KEY = "detect_api_key"

CONFIG_FLOW_DATA_SCHEMA_USER = vol.Schema(
    {
        vol.Required(CONF_HOST): str,
        vol.Required(CONF_PORT): int,
        vol.Optional(
            CONF_RECOGNIZE_API_KEY,
        ): str,
        vol.Optional(
            CONF_VERIFY_API_KEY,
        ): str,
        vol.Optional(
            CONF_DETECT_API_KEY,
        ): str,
    }
)

# Options
