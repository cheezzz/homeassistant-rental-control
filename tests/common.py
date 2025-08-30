# SPDX-FileCopyrightText: 2021 Andrew Grimberg <tykeal@bardicgrove.org>
# SPDX-License-Identifier: Apache-2.0

"""Common test fixtures and utilities for rental control tests."""
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import CONF_NAME, CONF_URL

from custom_components.rental_control.const import DOMAIN


class MockConfigEntry(ConfigEntry):
    """Mock config entry for testing."""

    def __init__(self, **kwargs):
        """Initialize mock config entry."""
        super().__init__(
            version=1,
            domain=DOMAIN,
            title=kwargs.get(CONF_NAME, "Test Calendar"),
            data=kwargs.get("data", {}),
            source="test",
            **kwargs
        )

