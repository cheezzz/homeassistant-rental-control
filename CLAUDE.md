# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Repository Context

This is a **fork** of [tykeal/homeassistant-rental-control](https://github.com/tykeal/homeassistant-rental-control) with custom modifications for LekkeSlaap calendar integration and deployment to a production Home Assistant instance.

**Branch strategy:**
- `main` - Tracks upstream for reference only (synced via `git fetch upstream && git merge upstream/main --ff-only`)
- `development` - **Production branch** running in Home Assistant (default branch, contains all custom changes)

**Key principle:** The `development` branch is stable production code. Only merge upstream changes when necessary (bug fixes, critical updates). See `MAINTENANCE.md` for upstream sync workflow.

## Development Commands

### Environment setup
```bash
python -m venv .venv
source .venv/bin/activate  # Unix/Mac
pip install -r requirements_dev.txt
```

### Testing
```bash
# Run all tests
python -m pytest -q

# Run specific test file
python -m pytest tests/test_config_flow.py -v

# Run with coverage report
python -m pytest --cov=custom_components.rental_control --cov-report=term-missing

# Note: Coverage requirement is 100% (enforced in pytest.ini)
```

### Validation and linting
```bash
# Install pre-commit hooks (recommended)
pre-commit install

# Run all pre-commit checks manually
pre-commit run --all-files

# Validate iCalendar files (custom script for LekkeSlaap compatibility testing)
python validate_ical.py
python scripts/validate_ical.py
```

### Pre-commit hooks enforce
- **ruff** (linting and formatting on `custom_components/`, `tests/`, `scripts/`)
- **mypy** (type checking)
- **interrogate** (docstring coverage - 100% required)
- **gitlint** (Conventional Commits format: `Feat:`, `Fix:`, `Chore:`, etc.)
- **reuse** (SPDX license headers)
- **no-commit-to-branch** (blocks direct commits to `main`)

## Architecture Overview

This is a Home Assistant custom integration that polls iCalendar (`.ics`) URLs from rental platforms (Airbnb, VRBO, LekkeSlaap, etc.) and manages:
1. Calendar entities for Home Assistant
2. Event sensors (current + upcoming reservations)
3. Optional door lock code generation via Keymaster integration

### Core components

**`coordinator.py` (RentalControlCoordinator)**
- Central orchestrator: fetches `.ics` from URL, parses events, manages state
- Polls calendar at configurable intervals (default: every 2 minutes)
- Handles timezone conversions (calendar TZ can differ from HA instance TZ)
- Implements retry logic for temporary empty calendar responses (Airbnb issue - see upstream commit 4f4bf2f)
- Coordinates with Keymaster slots if lock integration is enabled

**`calendar.py`**
- Provides Home Assistant calendar entity (`calendar.rental_control_<name>`)
- Exposes events to calendar cards and automations

**`sensor.py` + `sensors/calsensor.py`**
- Creates event sensors: `sensor.rental_control_<name>_event_0`, `event_1`, etc.
- `event_0` = current/next reservation, `event_1` = following reservation, etc.
- Each sensor includes attributes: guest name, door code, check-in/out times, phone, email, etc.

**`event_overrides.py` (EventOverrides)**
- Manages Keymaster lock slot assignments
- Tracks which calendar events map to which lock codes/slots
- Only instantiated if Keymaster integration is configured

**`config_flow.py`**
- GUI-based configuration (Home Assistant config flow)
- Supports reconfiguration after initial setup

**`const.py`**
- All constants, defaults, config keys
- Code generators: `date_based`, `static_random`, `last_four` (phone digits)

**`util.py`**
- Helper functions: slot name extraction, package reloading, etc.

### Data flow
1. Coordinator fetches `.ics` URL via aiohttp
2. `icalendar` library parses events (with `x-wr-timezone` normalization)
3. Events filtered by date range (default: next 365 days from today)
4. Events parsed for guest details via regex (phone, email, guest count, reservation URL)
5. Calendar entity + event sensors updated
6. If Keymaster enabled: door codes generated and slots updated

### Custom changes in this fork
- **LekkeSlaap compatibility fixes** (removed in development branch, see commit history for details)
- **Blocked calendar events fix** (`fix: Enable blocked calendar events to trigger active state` - commit 228d394)
- **Test infrastructure** (`pytest.ini`, `tests/` directory with real calendar tests)
- **Validation scripts** (`validate_ical.py`, `scripts/validate_ical.py`)
- **Custom default check-in/out times** (see `const.py` - may differ from upstream)

## Important patterns

### Event parsing and slot names
Events are identified by their "slot name" extracted from the iCalendar `SUMMARY` field:
- Airbnb: Extracts reservation code (e.g., `HM4XK9PDQR`)
- VRBO/Booking.com: Uses `SUMMARY` directly
- LekkeSlaap: Previously extracted `LS-XXXXXX` reference from `DESCRIPTION` (removed in current development)
- Custom calendars: Best practice is guest name in `SUMMARY`

**Critical:** Slot names must be unique across the configured number of event sensors, or Keymaster slot management will conflict.

### Timezone handling
- Each calendar can have its own timezone (configured during setup)
- `x-wr-timezone` library converts non-standard TZ definitions to standard ones
- All date/time operations use `homeassistant.util.dt` for consistency
- **Known limitation:** Keymaster check-in/out time overrides may behave unexpectedly if calendar TZ differs from HA system TZ

### Calendar miss retry mechanism (upstream commit 4f4bf2f)
- Airbnb occasionally returns empty calendars temporarily
- When `len(new_calendar) == 0` but `len(self.calendar) == 1`: retry up to `max_misses` (default: 2) before clearing calendar
- Prevents losing calendar state due to transient API failures

## Testing notes

- **Full coverage required** (`--cov-fail-under=100` in `pytest.ini`)
- `tests/test_real_calendars.py` - Tests against actual LekkeSlaap/platform calendars
- `tests/conftest.py` - Fixtures for Home Assistant test environment
- Use `asyncio_mode = auto` for async test handling

## Deployment

This integration is deployed to production Home Assistant via:
1. Manual copy of `custom_components/rental_control/` to HA `custom_components/` directory
2. Home Assistant restart to load updated integration
3. **OR** HACS installation (if configured in HACS as custom repository)

**Always test in a non-production HA instance before deploying to production.**

## Keymaster integration

If lock code management is needed:
- Keymaster must be fully configured and working **before** enabling in Rental Control
- Rental Control takes **full control** of assigned slots (overwrites existing codes)
- Slot range configured via `start_slot` and `max_events` (e.g., start_slot=10, max_events=5 → slots 10-14)
- Each event sensor maps to one Keymaster slot
- Door codes generated based on `code_generation` setting (date_based/static_random/last_four)

## Git workflow (see MAINTENANCE.md for details)

```bash
# Sync upstream changes into main
git fetch upstream
git checkout main
git merge upstream/main --ff-only
git push origin main

# Selectively merge upstream fixes into development
git checkout development
git cherry-pick <commit-hash>  # Recommended approach
# OR: git merge main  # Use with caution

# Push to production branch
git push origin development
```

**Commit message format:** Conventional Commits enforced by gitlint (e.g., `Feat: add feature`, `Fix: resolve bug`, `Chore: update deps`)
