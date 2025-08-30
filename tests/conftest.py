# SPDX-FileCopyrightText: 2021 Andrew Grimberg <tykeal@bardicgrove.org>
# SPDX-License-Identifier: Apache-2.0

"""Fixtures for Home Assistant rental control tests."""
import pytest
from pytest_homeassistant_custom_component.common import MockConfigEntry

from homeassistant.core import HomeAssistant
from homeassistant.setup import async_setup_component

from custom_components.rental_control.const import DOMAIN


pytest_plugins = "pytest_homeassistant_custom_component"


@pytest.fixture(name="skip_notifications", autouse=True)
def skip_notifications_fixture():
    """Skip notification calls."""
    with pytest.MonkeyPatch.context() as m:
        m.setattr("homeassistant.components.persistent_notification.async_create", lambda *args, **kwargs: None)
        m.setattr("homeassistant.components.persistent_notification.async_dismiss", lambda *args, **kwargs: None)
        yield


@pytest.fixture
def mock_config_entry():
    """Return a mock config entry."""
    return MockConfigEntry(
        domain=DOMAIN,
        title="Test Calendar",
        data={
            "name": "Test Calendar",
            "url": "https://example.com/calendar.ics",
        },
    )

