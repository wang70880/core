"""Config flow to configure Readiness."""
import logging

import voluptuous as vol

from homeassistant import config_entries

from .const import DOMAIN, READINESS_ID, SUPPORTED_DEVICE_TYPE, SUPPORTED_PLATFORMS

DATA_SCHEMA = {
    vol.Required("platform", default="all"): str,
    vol.Required("device_type", default="all"): str,
}


class ForenReadinessConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Readiness Configuration Interface"""

    # This is the readiness configuration interface to guide the Forensic Readiness Phase
    # User forensic preferences for platforms and device types are configured here: Filter List.
    # More configuration is left to be designed.
    VERSION = 1
    _LOGGER = logging.getLogger(__name__)

    async def async_step_user(self, user_input=None):
        if not user_input:
            return await self._show_form()
        else:
            # Check user input here
            flag = self.check_user_input(user_input)
            if flag == 1:
                await self.async_set_unique_id(READINESS_ID)
                self._abort_if_unique_id_configured()
                return self.async_create_entry(title=READINESS_ID, data=user_input)
            else:
                return self.async_abort(reason="Input is not valid!")

    async def _show_form(self, errors=None):
        return self.async_show_form(
            step_id="user",
            data_schema=vol.Schema(DATA_SCHEMA),
            errors=errors if errors else {},
        )

    def check_user_input(self, user_input):
        # TODO: Implement the check list
        platform_inputs = user_input["platform"].split(",")
        device_type_inputs = user_input["device_type"].split(",")
        if set(platform_inputs) > set(SUPPORTED_PLATFORMS) or set(
            device_type_inputs
        ) > set(SUPPORTED_DEVICE_TYPE):
            return 0
        return 1
