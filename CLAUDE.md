# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Development Commands

### Testing
- `pytest` - Run tests (with coverage reporting, requires 100% coverage)
- `pytest -qq --cov=custom_components.rental_control` - Run with specific coverage settings
- `pytest tests/test_specific_module.py` - Run tests for a specific module
- `pytest -v` - Run tests with verbose output

### Code Quality
- `flake8` - Lint Python code (configured in setup.cfg with line length 88, compatible with Black)
- `isort .` - Sort and format imports (configured for Black compatibility)  
- `mypy custom_components/rental_control` - Type checking (configured in mypy.ini)

### Home Assistant Validation
- Use `hassfest` action for Home Assistant integration validation
- Use HACS validation for Home Assistant Community Store compliance

### Development Setup
- `pip install -r requirements_dev.txt` - Install development dependencies
- `pip install -r requirements_test.txt` - Install test dependencies (includes dev dependencies)

## Architecture Overview

This is a Home Assistant custom integration for rental property management that:

1. **Fetches rental calendars** from ICS URLs (Airbnb, VRBO, custom calendars)
2. **Creates Home Assistant entities**: calendar entities and event sensors
3. **Integrates with Keymaster** for automated door lock code management
4. **Extracts guest information** from calendar event descriptions (phone numbers, email, guest count)

### Core Components

**RentalControlCoordinator** (`coordinator.py`): Central data coordinator that fetches and processes ICS calendar data, manages calendar events, and coordinates with Keymaster for lock management.

**Calendar Platform** (`calendar.py`): Creates Home Assistant calendar entities from rental booking data.

**Sensor Platform** (`sensor.py`): Creates event sensors (0 to N) representing current and upcoming rental events with detailed attributes.

**Config Flow** (`config_flow.py`): Handles integration setup and configuration through Home Assistant's UI.

### Key Features

- **Multiple code generators**: Date-based, static random, or last 4 digits of phone number
- **Timezone support**: Each calendar can have its own timezone separate from Home Assistant
- **Event processing**: Extracts guest details, phone numbers, email addresses from event descriptions
- **Keymaster integration**: Automatically manages door lock codes based on reservation dates
- **Custom calendar support**: Works with any HTTPS-accessible ICS calendar

### File Structure

- `custom_components/rental_control/` - Main integration directory
  - `__init__.py` - Integration setup, migrations, and listener management
  - `const.py` - Constants and configuration defaults
  - `coordinator.py` - Data coordination and ICS processing
  - `calendar.py` - Calendar entity implementation
  - `sensor.py` - Sensor entity setup
  - `sensors/calsensor.py` - Individual calendar sensor implementation
  - `config_flow.py` - Configuration flow handling
  - `manifest.json` - Integration metadata and dependencies

## Integration Dependencies

- **Keymaster**: Optional dependency for lock management (should be installed first)
- **icalendar>=6.1.0**: ICS calendar parsing
- **x-wr-timezone>=2.0.0**: Timezone handling for calendars

## Configuration Schema

The integration stores configuration in Home Assistant's config entries with the following key fields:
- Calendar name and ICS URL
- Check-in/check-out times
- Event sensor count (max_events)
- Refresh frequency (minutes)
- Door code generation method
- Keymaster lock integration settings
- Timezone settings

## Development Notes

- Uses SPDX license headers (Apache 2.0)
- Requires 100% test coverage
- Follows Home Assistant integration patterns
- Uses async/await patterns throughout
- Implements proper device registry integration
- Supports configuration migrations between versions

## Important Development Patterns

### Testing Approach
- Uses `pytest-homeassistant-custom-component` for Home Assistant integration testing
- All tests must maintain 100% coverage (enforced in setup.cfg)
- No dedicated tests directory exists in the project root - tests may be run via pytest discovery

### Code Style Enforcement
- Flake8 configured with Black compatibility (88 character line length)
- isort configured for Black compatibility with forced single-line imports
- MyPy type checking enabled with strict settings for external imports

### Home Assistant Integration Standards
- Integration metadata defined in `manifest.json`
- Supports configuration flow (GUI setup)
- Uses `DataUpdateCoordinator` pattern for data management
- Implements proper entity and device registry integration
- Uses Home Assistant's async patterns throughout

### ICS Calendar Processing
- Built on `icalendar>=6.1.0` and `x-wr-timezone>=2.0.0` libraries
- Handles timezone conversion between calendar and Home Assistant timezones
- Extracts guest information from event descriptions using regex patterns
- Processes both all-day and timed events with configurable check-in/check-out times