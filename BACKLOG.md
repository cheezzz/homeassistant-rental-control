# Self Check-In Links - Technical Debt Backlog

This document tracks remaining improvements and enhancements for the self check-in link feature identified during code review.

---

## 🔴 High Priority (Security & Reliability)

### 1. Enforce HTTPS for Base URL
**File**: `custom_components/rental_control/config_flow.py`
**Location**: Lines 455-468 (validation section)

**Issue**: Currently allows `http://` URLs which are vulnerable to man-in-the-middle attacks.

**Fix**:
```python
if user_input[CONF_CHECKIN_LINK_ENABLED]:
    if not user_input[CONF_CHECKIN_BASE_URL]:
        errors[CONF_CHECKIN_BASE_URL] = "missing_base_url"
    elif not user_input[CONF_CHECKIN_BASE_URL].startswith("https://"):
        errors[CONF_CHECKIN_BASE_URL] = "must_use_https"
```

**Translation string needed**:
```json
"must_use_https": "Base URL must use HTTPS in production for security"
```

---

### 2. Add Path Traversal Validation
**File**: `custom_components/rental_control/checkin_links.py`
**Location**: Lines 48-76 (`generate_checkin_link()`)

**Issue**: No validation against `../` patterns in path parameter.

**Fix**:
```python
if not base_url or not path or not secret:
    return None

# Validate path doesn't contain dangerous patterns
if ".." in path or not path.startswith("/"):
    raise ValueError("Invalid path: must be absolute and not contain '..'")
```

---

### 3. Validate Signing Secret Strength
**File**: `custom_components/rental_control/config_flow.py`
**Location**: Lines 464-465 (validation section)

**Issue**: Accepts any string as secret, even weak values like `"123"`.

**Fix**:
```python
if user_input[CONF_CHECKIN_SIGNING_SECRET]:
    if len(user_input[CONF_CHECKIN_SIGNING_SECRET]) < 32:
        errors[CONF_CHECKIN_SIGNING_SECRET] = "secret_too_weak"
```

**Translation string needed**:
```json
"secret_too_weak": "Signing secret must be at least 32 characters (use: openssl rand -hex 32)"
```

**Documentation needed**: Add to `CLAUDE.md` instructions on generating strong secrets.

---

### 4. Add Exception Handling for Link Generation
**File**: `custom_components/rental_control/sensors/calsensor.py`
**Location**: Line 398

**Issue**: If `_generate_checkin_link()` raises an exception, it will propagate uncaught.

**Fix**:
```python
try:
    self._event_attributes["self_checkin_link"] = self._generate_checkin_link()
except Exception as err:
    _LOGGER.exception("Failed to generate check-in link for %s: %s", self._name, err)
    self._event_attributes["self_checkin_link"] = None
```

---

## 🟡 Medium Priority (Code Quality)

### 5. Add Debug Logging for Link Generation
**File**: `custom_components/rental_control/sensors/calsensor.py`
**Location**: Lines 213-254 (`_generate_checkin_link()`)

**Issue**: Silent `None` returns make troubleshooting difficult.

**Fix**: Add debug logging at each return point:
```python
if not self.coordinator.checkin_link_enabled:
    _LOGGER.debug("Check-in links disabled for %s", self._name)
    return None

if self.coordinator.checkin_link_path == "none":
    _LOGGER.debug("No check-in path configured for %s", self._name)
    return None

if not start:
    _LOGGER.debug("No start time available for %s, skipping link generation", self._name)
    return None

if not (is_checkin_day and is_past_6am):
    _LOGGER.debug(
        "Not generating link for %s: is_checkin_day=%s, is_past_6am=%s",
        self._name, is_checkin_day, is_past_6am
    )
    return None

_LOGGER.debug("Generated check-in link for %s", self._name)
```

---

### 6. Move Magic Numbers to Constants
**File**: `custom_components/rental_control/const.py`

**Issue**: Hardcoded values scattered throughout code.

**Add**:
```python
DEFAULT_CHECKIN_LINK_EXPIRY = 86400  # 24 hours in seconds
DEFAULT_CHECKIN_LINK_GENERATION_HOUR = 6  # 6:00 AM
```

**Then update `calsensor.py`**:
```python
from ..const import DEFAULT_CHECKIN_LINK_EXPIRY, DEFAULT_CHECKIN_LINK_GENERATION_HOUR

# Line 241
is_past_6am = now.time() >= time(DEFAULT_CHECKIN_LINK_GENERATION_HOUR, 0)

# Line 253
expires_in_seconds=DEFAULT_CHECKIN_LINK_EXPIRY,
```

---

### 7. Simplify Path Conversion Helper
**File**: `custom_components/rental_control/config_flow.py`
**Location**: Lines 177-187

**Issue**: Uses `next()` with generator which raises `StopIteration` if not found.

**Fix**:
```python
def _checkin_link_path_convert(path: str, to_id: bool = True) -> str:
    """Convert between path ID and display name for check-in links."""
    lookup = {item[1]: item[0] for item in CHECKIN_LINK_PATHS}
    reverse_lookup = {item[0]: item[1] for item in CHECKIN_LINK_PATHS}

    if to_id:
        return lookup.get(path, DEFAULT_CHECKIN_LINK_PATH)
    else:
        return reverse_lookup.get(path, "None")
```

---

### 8. Remove Unnecessary String Coercion
**File**: `custom_components/rental_control/coordinator.py`
**Location**: Lines 131-139, 347-355

**Issue**: Explicit `str()` wrapping is inconsistent with other fields.

**Investigation needed**: Determine if `str()` is truly necessary. Config values should already be validated by schema.

---

### 9. Use URL Encoding for Query Parameters
**File**: `custom_components/rental_control/checkin_links.py`
**Location**: Line 94

**Issue**: Manual string concatenation for URLs is error-prone.

**Fix**:
```python
from urllib.parse import urlencode

# In generate_checkin_link()
params = urlencode({"t": expiry, "sig": sig})
return f"{base_url.rstrip('/')}{out_path}?{params}"
```

---

## 🟢 Low Priority (Enhancements)

### 10. Implement Link Caching
**File**: `custom_components/rental_control/sensors/calsensor.py`
**Location**: `_generate_checkin_link()` method

**Issue**: Link regenerates every 2 minutes (every coordinator update), causing expiry timestamp to shift.

**Impact**: If guest saves link at 6:00 AM (expires 6:00 AM next day), but refreshes at 6:02 AM, new link expires at 6:02 AM next day.

**Fix**: Cache link for 1 hour to avoid regeneration:
```python
# Add to __init__
self._cached_checkin_link = None
self._cached_checkin_link_generated_at = None

# In _generate_checkin_link
if self._cached_checkin_link and self._cached_checkin_link_generated_at:
    cache_age = (now - self._cached_checkin_link_generated_at).total_seconds()
    if cache_age < 3600:  # 1 hour cache
        _LOGGER.debug("Using cached check-in link for %s (age: %.0fs)", self._name, cache_age)
        return self._cached_checkin_link

# After generating link
self._cached_checkin_link = link
self._cached_checkin_link_generated_at = now
```

---

### 11. Add Edge Case Tests
**File**: `tests/test_checkin_links.py`

**Missing test cases**:
- Base URL containing existing query parameters
- Unicode characters in paths
- Very long secrets (1000+ chars)
- `expires_in_seconds` at maximum `int` value
- Empty/whitespace-only strings for parameters

---

### 12. Document Timezone Behavior
**File**: `custom_components/rental_control/sensors/calsensor.py`
**Location**: Lines 237-241

**Issue**: Timezone handling across HA instance TZ vs calendar TZ may be confusing.

**Add comment**:
```python
# Check if today is check-in day and time >= 06:00 AM
# Note: All comparisons use the event's timezone. If HA is in UTC and
# the calendar is in PST, a 6 AM PST check-in will be 2 PM UTC.
# Links generate based on event timezone for guest convenience.
now = dt.now(start.tzinfo)
```

**Add to `CLAUDE.md`**:
```markdown
### Timezone Handling

Link generation uses the **event's timezone**, not Home Assistant's system timezone.

Example:
- HA instance: UTC
- Calendar: US/Pacific (PST)
- Event check-in: Nov 1, 2025 14:00 PST
- Link generates: Nov 1, 2025 at 06:00 PST (14:00 UTC)

This ensures links appear at the right local time for guests.
```

---

### 13. Add Secret Storage Warning
**File**: `custom_components/rental_control/coordinator.py`
**Location**: Lines 137-139

**Add comment**:
```python
# SECURITY: This is a cryptographic secret used for HMAC signing.
# It must match the Cloudflare Worker secret exactly.
# Store this securely and never commit to git.
self.checkin_signing_secret: str = str(
    config.get(CONF_CHECKIN_SIGNING_SECRET, DEFAULT_CHECKIN_SIGNING_SECRET)
)
```

---

## 📚 Documentation Tasks

### 14. Update CLAUDE.md
Add comprehensive section on self check-in links:

```markdown
## Self Check-In Links

Generates HMAC-signed, expiring check-in links for guests on check-in day.

### Configuration

Per-calendar settings:
- `checkin_link_enabled`: Enable feature (default: False)
- `checkin_link_path`: Path to check-in page (e.g., `/checkin/cottage`)
- `checkin_base_url`: Base URL (**must be HTTPS in production**)
- `checkin_signing_secret`: HMAC secret (min 32 chars)

### Behavior

- Links generated only on check-in day after 6:00 AM (event timezone)
- Links expire 24 hours after generation
- Secret must match Cloudflare Worker secret exactly
- Links regenerate every 2 minutes (coordinator update interval)

### Security Best Practices

1. **Generate strong secret**:
   ```bash
   openssl rand -hex 32
   ```

2. **Always use HTTPS** in production (prevents MITM attacks)

3. **Never commit secret to git** (add `.env` to `.gitignore`)

4. **Secret rotation**: Update both HA config and Cloudflare Worker simultaneously

### Troubleshooting

**Link not appearing?**
- Check coordinator logs for "Check-in links disabled"
- Verify time is past 6:00 AM on check-in day
- Ensure `checkin_link_path` is not "none"

**Link shows "Invalid signature" on Cloudflare?**
- Secrets don't match between HA and Worker
- Check for extra whitespace in secret configuration
```

---

### 15. Add README Example
**File**: `README.md`

Add section showing example sensor attributes:

```markdown
### Self Check-In Links

When enabled, event sensors include a `self_checkin_link` attribute:

```yaml
sensor.rental_control_cottage_event_0:
  state: "John Smith - 1 November 2025 14:00"
  attributes:
    self_checkin_link: "https://karooandko.co.za/checkin/cottage/?t=1730527200&sig=abc123..."
    slot_code: "0111"
    start_time: "2025-11-01 14:00:00"
    end_time: "2025-11-03 10:00:00"
```

Use in automations:

```yaml
automation:
  - alias: "Send Check-In Link via WhatsApp"
    trigger:
      - platform: state
        entity_id: sensor.rental_control_cottage_event_0
        attribute: self_checkin_link
    condition:
      - condition: template
        value_template: "{{ trigger.to_state.attributes.self_checkin_link != None }}"
    action:
      - service: notify.whatsapp
        data:
          message: |
            Welcome! Your check-in link:
            {{ state_attr('sensor.rental_control_cottage_event_0', 'self_checkin_link') }}
```
```

---

## Completed ✅

- ✅ Add translation strings for error messages
- ✅ Add translation strings for config fields
- ✅ Fix imports (move `time` to module level)
- ✅ Use Home Assistant's `dt.now()` instead of `datetime.now()`
- ✅ Add docstring explaining 6 AM cutoff time

---

## Notes

- Priority is subjective - adjust based on production needs
- Security items should be addressed before deploying to production
- Code quality items improve maintainability but don't affect functionality
- Enhancements are nice-to-have optimizations

**Last Updated**: 2025-11-01
