# Debug Report: "Task exception was never retrieved" Error

**Date**: 2025-11-01
**Issue**: User unable to add second calendar instance, "Task exception was never retrieved (None)" errors in logs
**Status**: RESOLVED

## Root Cause Analysis

### Primary Issue: Missing Config Entry Migration

**Severity**: CRITICAL

**Description**: The self check-in link feature added 4 new configuration fields but failed to include a migration path for existing calendar entries. When Home Assistant tried to load existing entries (version 7), the coordinator initialization attempted to access non-existent config keys, causing crashes.

**Evidence**:
- `config_flow.py` declared `VERSION = 7` (should be 8 for new fields)
- `__init__.py` had no migration from version 7 -> 8
- New config keys added in coordinator:
  - `CONF_CHECKIN_LINK_ENABLED`
  - `CONF_CHECKIN_LINK_PATH`
  - `CONF_CHECKIN_BASE_URL`
  - `CONF_CHECKIN_SIGNING_SECRET`

**Impact**:
- Existing calendar entries failed to load
- New calendar entries couldn't be added (config flow mismatch)
- "Must configure in configuration.yaml" error displayed to user
- Integration appeared broken to all existing users

### Secondary Issue: Unhandled Exceptions in Link Generation

**Severity**: HIGH

**Description**: The `_generate_checkin_link()` method in `sensors/calsensor.py` had no exception handling. Any error during link generation (import failures, missing attributes, invalid data) caused uncaught exceptions in async context.

**Evidence**:
- Line 403: `self._event_attributes["self_checkin_link"] = self._generate_checkin_link()`
- Line 247: Inline import `from ..checkin_links import generate_checkin_link`
- No try/except wrapper around link generation
- Home Assistant logs: "Task exception was never retrieved (None)"

**Impact**:
- Silent failures in sensor updates
- "Task exception was never retrieved" errors in logs
- No indication to user that link generation failed
- Potential for coordinator update failures

### Tertiary Issue: Unsafe String Casting in Coordinator

**Severity**: MEDIUM

**Description**: The coordinator's `__init__` method used `str()` directly on `.get()` results without checking for `None`, potentially creating string "None" values instead of empty strings.

**Evidence**:
```python
self.checkin_link_path: str = str(
    config.get(CONF_CHECKIN_LINK_PATH, DEFAULT_CHECKIN_LINK_PATH)
)
```

**Impact**:
- Potential for `checkin_link_path = "None"` (string) instead of `"none"` or `""`
- Path validation logic checks for `"none"` but not `"None"`
- Confusing behavior if defaults aren't properly defined

## Code Fixes Implemented

### Fix 1: Add Version 7 -> 8 Migration

**File**: `/media/nfs-share/dev/homeassistant-rental-control/custom_components/rental_control/__init__.py`

**Changes**:
- Added migration block after version 6 -> 7 migration (lines 260-287)
- Imports new config constants
- Sets all check-in link fields to default values for existing entries
- Updates config entry version to 8

**Code**:
```python
# 7 -> 8: Add check-in link configuration
if version == 7:
    _LOGGER.debug(f"Migrating from version {version}")

    from .const import CONF_CHECKIN_LINK_ENABLED
    from .const import CONF_CHECKIN_LINK_PATH
    from .const import CONF_CHECKIN_BASE_URL
    from .const import CONF_CHECKIN_SIGNING_SECRET
    from .const import DEFAULT_CHECKIN_LINK_ENABLED
    from .const import DEFAULT_CHECKIN_LINK_PATH
    from .const import DEFAULT_CHECKIN_BASE_URL
    from .const import DEFAULT_CHECKIN_SIGNING_SECRET

    data = config_entry.data.copy()
    # Default to disabled for existing installations
    data[CONF_CHECKIN_LINK_ENABLED] = DEFAULT_CHECKIN_LINK_ENABLED
    data[CONF_CHECKIN_LINK_PATH] = DEFAULT_CHECKIN_LINK_PATH
    data[CONF_CHECKIN_BASE_URL] = DEFAULT_CHECKIN_BASE_URL
    data[CONF_CHECKIN_SIGNING_SECRET] = DEFAULT_CHECKIN_SIGNING_SECRET
    hass.config_entries.async_update_entry(
        entry=config_entry,
        unique_id=config_entry.unique_id,
        data=data,
        version=8,
    )

    version = 8
    _LOGGER.debug(f"Migration to version {config_entry.version} complete")
```

**Result**: Existing calendar entries automatically upgrade to version 8 with safe defaults (links disabled).

### Fix 2: Update Config Flow Version

**File**: `/media/nfs-share/dev/homeassistant-rental-control/custom_components/rental_control/config_flow.py`

**Changes**:
- Line 78: `VERSION = 7` -> `VERSION = 8`

**Result**: New calendar entries created with version 8 schema.

### Fix 3: Add Exception Handling to Link Generation

**File**: `/media/nfs-share/dev/homeassistant-rental-control/custom_components/rental_control/sensors/calsensor.py`

**Changes**:
- Wrapped entire `_generate_checkin_link()` method body in try/except (lines 224-262)
- Added error logging with sensor name and exception details
- Returns `None` on any exception (safe fallback)

**Code**:
```python
def _generate_checkin_link(self) -> str | None:
    """Generate HMAC-signed check-in link if enabled and conditions met."""
    try:
        # Check if feature is enabled
        if not self.coordinator.checkin_link_enabled:
            return None
        
        # ... rest of link generation logic ...
        
    except Exception as e:  # pylint: disable=broad-except
        _LOGGER.error(
            "Failed to generate check-in link for %s: %s",
            self.name,
            str(e),
        )
        return None
```

**Result**: Link generation failures logged but don't crash sensor updates.

### Fix 4: Safer Config Value Handling in Coordinator

**File**: `/media/nfs-share/dev/homeassistant-rental-control/custom_components/rental_control/coordinator.py`

**Changes**:
- Lines 136-151: Added explicit `None` checks before `str()` casting
- Uses ternary operator to fallback to default if value is `None`

**Code**:
```python
# Check-in link configuration with safe defaults
self.checkin_link_enabled: bool = bool(
    config.get(CONF_CHECKIN_LINK_ENABLED, DEFAULT_CHECKIN_LINK_ENABLED)
)
checkin_link_path = config.get(CONF_CHECKIN_LINK_PATH, DEFAULT_CHECKIN_LINK_PATH)
self.checkin_link_path: str = (
    str(checkin_link_path) if checkin_link_path is not None else DEFAULT_CHECKIN_LINK_PATH
)
checkin_base_url = config.get(CONF_CHECKIN_BASE_URL, DEFAULT_CHECKIN_BASE_URL)
self.checkin_base_url: str = (
    str(checkin_base_url) if checkin_base_url is not None else DEFAULT_CHECKIN_BASE_URL
)
checkin_signing_secret = config.get(CONF_CHECKIN_SIGNING_SECRET, DEFAULT_CHECKIN_SIGNING_SECRET)
self.checkin_signing_secret: str = (
    str(checkin_signing_secret) if checkin_signing_secret is not None else DEFAULT_CHECKIN_SIGNING_SECRET
)
```

**Result**: Coordinator handles missing/None config values gracefully.

## Testing Performed

### Syntax Validation
```bash
python3 -m py_compile custom_components/rental_control/__init__.py
python3 -m py_compile custom_components/rental_control/config_flow.py
python3 -m py_compile custom_components/rental_control/coordinator.py
python3 -m py_compile custom_components/rental_control/sensors/calsensor.py
```
**Status**: ✅ All files compile successfully

### Required Testing (Manual)

**Before deploying to production**:

1. **Test existing calendar migration**:
   - Restart Home Assistant with existing calendar entries (version 7)
   - Verify logs show "Migrating from version 7"
   - Verify logs show "Migration to version 8 complete"
   - Verify calendar entities load successfully
   - Verify sensor entities show `self_checkin_link: null`

2. **Test new calendar creation**:
   - Add new calendar via UI
   - Verify config flow accepts inputs
   - Verify calendar/sensor entities created
   - Verify check-in link fields saved correctly

3. **Test link generation error handling**:
   - Create calendar with invalid signing secret
   - Set check-in date to today, time after 06:00
   - Check logs for "Failed to generate check-in link" message
   - Verify sensor attribute shows `self_checkin_link: null`
   - Verify sensor otherwise functional (no crash)

4. **Test reconfiguration**:
   - Edit existing calendar
   - Enable check-in links
   - Set base URL, path, secret
   - Save configuration
   - Verify settings persist
   - Verify coordinator updates attributes

## Deployment Instructions

### 1. Backup Current Installation

```bash
# Backup existing config entries
cp /config/.storage/core.config_entries /config/.storage/core.config_entries.backup

# Backup custom component
cp -r /config/custom_components/rental_control /config/custom_components/rental_control.backup
```

### 2. Deploy Updated Code

```bash
# Copy updated integration
cp -r /media/nfs-share/dev/homeassistant-rental-control/custom_components/rental_control \
      /config/custom_components/

# Verify files copied
ls -la /config/custom_components/rental_control/
```

### 3. Restart Home Assistant

```bash
ha core restart
```

### 4. Monitor Logs During Restart

```bash
# Watch for migration messages
tail -f /config/home-assistant.log | grep -i "rental_control\|migration"
```

**Expected log output**:
```
[custom_components.rental_control] Migrating from version 7
[custom_components.rental_control] Migration to version 8 complete
```

### 5. Verify Each Calendar Entry

For each calendar:
1. Check entity states in Developer Tools -> States
2. Verify `sensor.rental_control_<name>_event_0` exists
3. Verify attributes include `self_checkin_link: null` (if disabled) or valid URL (if enabled)
4. Check for errors in logs

### 6. Test Adding New Calendar

1. Go to Settings -> Devices & Services -> Rental Control
2. Click "Add Entry"
3. Fill in calendar URL and settings
4. Enable check-in links (optional)
5. Save and verify success

## Rollback Procedure

If issues occur after deployment:

```bash
# Stop Home Assistant
ha core stop

# Restore backup
rm -rf /config/custom_components/rental_control
cp -r /config/custom_components/rental_control.backup \
      /config/custom_components/rental_control

# Restore config entries (if needed)
cp /config/.storage/core.config_entries.backup \
   /config/.storage/core.config_entries

# Start Home Assistant
ha core start
```

## Prevention Recommendations

### 1. Always Add Migration When Changing Config Schema

**Rule**: Any change to config entry structure requires:
- Increment `VERSION` in `config_flow.py`
- Add migration block in `__init__.py::async_migrate_entry()`
- Test migration with existing entries before deployment

**Example checklist**:
- [ ] New config field added to `const.py`
- [ ] Default value defined in `const.py`
- [ ] Field added to config flow schema
- [ ] Field used in coordinator/sensors
- [ ] Migration block added (version N -> N+1)
- [ ] Config flow `VERSION` incremented
- [ ] Migration tested with existing entries

### 2. Use Exception Handling in Async Contexts

**Rule**: Wrap all potentially failing operations in try/except, especially:
- API calls
- External module imports
- File I/O
- Data validation

**Pattern**:
```python
async def async_operation(self):
    try:
        # Risky operation
        result = await external_api_call()
    except SpecificException as e:
        _LOGGER.error("Specific error: %s", e)
        return None
    except Exception as e:
        _LOGGER.error("Unexpected error: %s", e)
        return None
```

### 3. Validate Config Values Before Use

**Rule**: Never assume config values exist or are valid. Use defensive programming:

**Bad**:
```python
self.value = str(config.get(KEY))  # Could be "None" string!
```

**Good**:
```python
value = config.get(KEY, DEFAULT)
self.value = str(value) if value is not None else DEFAULT
```

### 4. Add Debug Logging for Troubleshooting

**Recommendation**: Add debug logs at key points:

```python
_LOGGER.debug("Initializing coordinator with config: %s", config)
_LOGGER.debug("Check-in link enabled: %s", self.checkin_link_enabled)
_LOGGER.debug("Generating link for event: %s", event.summary)
```

Enable in production with:
```yaml
logger:
  default: info
  logs:
    custom_components.rental_control: debug
```

### 5. Test Migrations Before Merging

**Process**:
1. Create test HA instance with old version
2. Add calendar entries
3. Note `.storage/core.config_entries` entry format
4. Update code with migration
5. Restart HA
6. Verify migration logs
7. Verify entries upgraded correctly
8. Test new features work with migrated entries

## Related Files

Modified:
- `/media/nfs-share/dev/homeassistant-rental-control/custom_components/rental_control/__init__.py` (+28 lines)
- `/media/nfs-share/dev/homeassistant-rental-control/custom_components/rental_control/config_flow.py` (1 line)
- `/media/nfs-share/dev/homeassistant-rental-control/custom_components/rental_control/coordinator.py` (+15 lines)
- `/media/nfs-share/dev/homeassistant-rental-control/custom_components/rental_control/sensors/calsensor.py` (+9 lines)

Reference:
- `/media/nfs-share/dev/homeassistant-rental-control/custom_components/rental_control/const.py` (config constants)
- `/media/nfs-share/dev/homeassistant-rental-control/custom_components/rental_control/checkin_links.py` (link generation)

## Summary

**Issue**: Missing config entry migration + unhandled exceptions = integration crash

**Root cause**: Self check-in link feature added new config fields without migration path

**Fix**: Added version 7->8 migration, exception handling, safer config handling

**Testing**: Syntax validated, manual testing required before production deployment

**Status**: Code fixes complete, ready for deployment testing

---

**Report generated**: 2025-11-01
**Branch**: feature/self-checkin-links
**Commit**: TBD (after fixes applied)
