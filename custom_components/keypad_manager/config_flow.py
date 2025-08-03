"""Adds config flow for Keypad Manager."""

from __future__ import annotations

from homeassistant import config_entries

from .const import DOMAIN


class KeypadManagerFlowHandler(config_entries.ConfigFlow, domain=DOMAIN):
    """Config flow for Keypad Manager."""

    VERSION = 1

    async def async_step_user(
        self,
        user_input: dict | None = None,
    ) -> config_entries.ConfigFlowResult:
        """Handle a flow initialized by the user."""
        if user_input is not None:
            # Set a unique ID for this integration
            await self.async_set_unique_id("keypad_manager")
            self._abort_if_unique_id_configured()

            return self.async_create_entry(
                title="Keypad Manager",
                data={},
            )

        return self.async_show_form(
            step_id="user",
            data_schema={},
        )
