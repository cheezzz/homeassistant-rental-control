# SPDX-FileCopyrightText: 2021 Andrew Grimberg <tykeal@bardicgrove.org>
# SPDX-License-Identifier: Apache-2.0

"""Test rental control init."""
from unittest.mock import patch

import pytest
from homeassistant.config_entries import ConfigEntryState
from homeassistant.core import HomeAssistant

from custom_components.rental_control.const import DOMAIN

from pytest_homeassistant_custom_component.common import MockConfigEntry


@pytest.mark.asyncio
async def test_setup_unload_and_reload_entry(hass: HomeAssistant) -> None:
    """Test entry setup and unload."""
    # Setup the config entry
    config_entry = MockConfigEntry(
        domain=DOMAIN,
        data={
            "name": "Test Calendar",
            "url": "https://example.com/calendar.ics",
        },
    )
    config_entry.add_to_hass(hass)

    with patch("custom_components.rental_control.RentalControlCoordinator.async_refresh"):
        await hass.config_entries.async_setup(config_entry.entry_id)
        await hass.async_block_till_done()

    assert config_entry.state == ConfigEntryState.LOADED
    assert DOMAIN in hass.data

    # Test unload
    await hass.config_entries.async_unload(config_entry.entry_id)
    await hass.async_block_till_done()

    assert config_entry.state == ConfigEntryState.NOT_LOADED

