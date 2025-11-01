# Self Check-In Links Feature

**Branch**: `feature/self-checkin-links`

This branch adds automatic generation of HMAC-signed, expiring check-in links for rental guests on their arrival day.

## Overview

When enabled, this feature generates secure, time-limited URLs that guests can use to access a self-service check-in portal on their check-in day. Links are cryptographically signed using HMAC-SHA256 and automatically expire after 24 hours to prevent unauthorized access.

### Key Features

- **Automatic generation**: Links appear at 6:00 AM (event timezone) on check-in day
- **Cryptographic security**: HMAC-SHA256 signed URLs prevent tampering
- **Time-limited**: Links expire 24 hours after generation
- **Per-calendar configuration**: Different properties can have different check-in portals
- **Integration-ready**: Works with Cloudflare Worker verification system
- **Event sensor attributes**: Links accessible via `self_checkin_link` attribute

## How It Works

### Link Generation Flow

1. **Coordinator polls** calendar every 2 minutes (default refresh interval)
2. **Event sensors** check if:
   - Current date matches event check-in date (in event timezone)
   - Current time is >= 6:00 AM (in event timezone)
   - Check-in links are enabled for this calendar
   - A check-in path is configured (not "none")
3. **Link generated** using:
   - Base URL (e.g., `https://karooandko.co.za`)
   - Path (e.g., `/checkin/cottage`)
   - Signing secret (shared with Cloudflare Worker)
   - Expiry timestamp (current time + 24 hours)
4. **HMAC signature** computed: `HMAC-SHA256("{normalized_path}|{expiry}", secret)`
5. **Final URL**: `{base_url}{path}/?t={expiry}&sig={signature}`

### Example Generated Link

```
https://karooandko.co.za/checkin/cottage/?t=1730527200&sig=abc123def456...
```

Where:
- `t=1730527200` - Unix timestamp when link expires
- `sig=abc123...` - 64-character HMAC-SHA256 signature

## Configuration

### Prerequisites

1. **Cloudflare Worker** (or compatible verification endpoint) deployed to validate signatures
2. **Shared secret** generated and stored securely in both HA and Worker
3. **HTTPS base URL** for production (HTTP allowed only for testing)

### Per-Calendar Settings

Configure via Home Assistant UI when adding/editing a Rental Control calendar:

| Setting | Config Key | Description | Example |
|---------|-----------|-------------|---------|
| **Enable Check-In Links** | `checkin_link_enabled` | Enable feature for this calendar | `true` |
| **Base URL** | `checkin_base_url` | Base URL of check-in portal | `https://karooandko.co.za` |
| **Check-In Path** | `checkin_link_path` | Path to check-in page | `/checkin/cottage` |
| **Signing Secret** | `checkin_signing_secret` | HMAC secret (min 32 chars) | `4f3a2b1c...` |

### Predefined Path Options

The config flow offers these path presets:

- **None**: Disable links for this calendar
- **Custom**: Enter your own path
- Common paths: `/checkin/cottage`, `/checkin/tiny-home`, `/checkin/guest-house`

## Security Best Practices

### 1. Generate Strong Secrets

Use cryptographically secure random values (minimum 32 characters):

```bash
# Generate 64-character hex secret
openssl rand -hex 32

# Example output:
# 4f3a2b1c9d8e7f6a5b4c3d2e1f0a9b8c7d6e5f4a3b2c1d0e9f8a7b6c5d4e3f2a
```

### 2. Always Use HTTPS in Production

**Critical**: HTTP URLs expose the signature to man-in-the-middle attacks, allowing attackers to:
- Steal signatures and reuse them before expiry
- Intercept the secret if the Worker is also HTTP

**Current limitation**: Config flow accepts HTTP URLs for local testing. See [BACKLOG.md](./BACKLOG.md) item #1 for enforcement plans.

### 3. Never Commit Secrets to Git

```bash
# Add to .gitignore
echo ".env" >> .gitignore
echo "secrets.yaml" >> .gitignore
```

Store secrets in:
- Home Assistant `secrets.yaml`
- Cloudflare Worker environment variables
- Password manager (for backup)

### 4. Secret Rotation

When rotating secrets:
1. Generate new secret: `openssl rand -hex 32`
2. Update Cloudflare Worker environment variable
3. Update Home Assistant calendar config
4. Test new link generation
5. Revoke old secret from both systems

**Warning**: Links generated with old secret will fail validation immediately after rotation.

## Usage

### Accessing Links in Automations

Links appear as sensor attributes:

```yaml
sensor.rental_control_cottage_event_0:
  state: "John Smith - 1 November 2025 14:00"
  attributes:
    self_checkin_link: "https://karooandko.co.za/checkin/cottage/?t=1730527200&sig=abc123..."
    slot_code: "0111"
    start_time: "2025-11-01 14:00:00+02:00"
    end_time: "2025-11-03 10:00:00+02:00"
    guest_name: "John Smith"
    phone: "+27821234567"
```

### Example Automation: Send Link via WhatsApp

```yaml
automation:
  - alias: "Send Check-In Link on Arrival Day"
    description: "Send self check-in link when it becomes available"
    trigger:
      - platform: state
        entity_id: sensor.rental_control_cottage_event_0
        attribute: self_checkin_link
    condition:
      - condition: template
        value_template: "{{ trigger.to_state.attributes.self_checkin_link is not none }}"
    action:
      - service: notify.whatsapp
        data:
          message: |
            Hi {{ state_attr('sensor.rental_control_cottage_event_0', 'guest_name') }}!

            Welcome to Karoo & Ko Cottage.

            Your self check-in link:
            {{ state_attr('sensor.rental_control_cottage_event_0', 'self_checkin_link') }}

            This link expires in 24 hours.
```

### Example Automation: Display in Lovelace

```yaml
type: entities
entities:
  - entity: sensor.rental_control_cottage_event_0
    name: "Current Reservation"
    secondary_info: last-changed
    card_mod:
      style: |
        :host {
          --paper-item-icon-color:
            {% if state_attr('sensor.rental_control_cottage_event_0', 'self_checkin_link') %}
              green
            {% else %}
              grey
            {% endif %}
        }
  - type: attribute
    entity: sensor.rental_control_cottage_event_0
    attribute: self_checkin_link
    name: "Check-In Link"
    icon: mdi:link-variant
```

## Technical Details

### Implementation Files

| File | Purpose | Lines | Tests |
|------|---------|-------|-------|
| `checkin_links.py` | Core HMAC implementation | 94 | 11 tests |
| `coordinator.py` | Config loading, attribute passing | +32 | - |
| `sensors/calsensor.py` | Link generation logic, time checks | +51 | - |
| `config_flow.py` | UI configuration form | +83 | - |
| `const.py` | Constants, defaults, path options | +15 | - |
| `strings.json` + `translations/en.json` | UI labels, help text | +24 each | - |

### Algorithm Details

**Signature computation**:
```python
normalized_path = normalize_path(path)  # "/checkin/cottage/" -> "/checkin/cottage"
expiry = int(time.time()) + 86400  # Current Unix timestamp + 24 hours
message = f"{normalized_path}|{expiry}"
signature = HMAC-SHA256(message, secret).hexdigest()
```

**Path normalization rules**:
- Add leading `/` if missing: `checkin/cottage` → `/checkin/cottage`
- Remove trailing `/` (except root): `/checkin/cottage/` → `/checkin/cottage`
- Root stays as-is: `/` → `/`

**Output path formatting**:
- Ensure trailing `/` (except root): `/checkin/cottage` → `/checkin/cottage/`

**Why different rules?** Signature uses normalized path (no trailing slash) for consistency, but output URL includes trailing slash for better URL structure.

### Timezone Handling

Link generation uses **event timezone**, not Home Assistant system timezone.

**Example scenario**:
- HA instance timezone: `UTC`
- Calendar timezone: `Africa/Johannesburg` (UTC+2)
- Event check-in: November 1, 2025, 14:00 SAST

Link generates:
- November 1, 2025 at **06:00 SAST** (04:00 UTC)
- Expires November 2, 2025 at **06:00 SAST** (04:00 UTC)

**Rationale**: Guests expect links at 6 AM in their local time, not the server's timezone.

### Link Regeneration Behavior

**Current implementation**:
- Links regenerate every 2 minutes (coordinator update interval)
- Each regeneration creates a new expiry timestamp
- Signatures change with each regeneration

**Example**:
- 06:00 AM: Link expires November 2 at 06:00 AM
- 06:02 AM: New link expires November 2 at 06:02 AM
- 06:04 AM: New link expires November 2 at 06:04 AM

**Impact**: If guest saves link at 06:00 and refreshes sensor at 06:10, they get a link with slightly later expiry.

**Future enhancement**: See [BACKLOG.md](./BACKLOG.md) item #10 for link caching proposal (1-hour cache to stabilize expiry time).

## Testing

### Running Tests

```bash
# Activate virtual environment
source .venv/bin/activate

# Run all check-in link tests
python -m pytest tests/test_checkin_links.py -v

# Run with coverage
python -m pytest tests/test_checkin_links.py --cov=custom_components.rental_control.checkin_links --cov-report=term-missing
```

### Test Coverage

11 tests covering:
- ✅ Path normalization (leading/trailing slashes, root)
- ✅ Basic link generation
- ✅ JavaScript implementation compatibility
- ✅ Different expiry times produce different signatures
- ✅ Different secrets produce different signatures
- ✅ Different paths produce different signatures
- ✅ Base URL normalization (with/without trailing slash)
- ✅ Invalid expiry values raise `ValueError`
- ✅ Missing inputs return `None`

**Coverage**: 100% (required by `pytest.ini`)

### Manual Testing Checklist

- [ ] Link appears at 06:00 AM on check-in day (event timezone)
- [ ] Link is `None` before 06:00 AM
- [ ] Link is `None` on days other than check-in day
- [ ] Link includes correct expiry timestamp (`t` parameter)
- [ ] Signature is 64-character hex string
- [ ] Signature validates on Cloudflare Worker
- [ ] Link expires after 24 hours
- [ ] Expired link rejected by Cloudflare Worker
- [ ] Different secrets produce different signatures
- [ ] HTTP URLs accepted (testing only)
- [ ] HTTPS URLs accepted (production)

## Deployment

### 1. Merge to Development Branch

```bash
# Ensure all tests pass
python -m pytest -q

# Ensure pre-commit checks pass
pre-commit run --all-files

# Merge to development (production branch)
git checkout development
git merge feature/self-checkin-links
git push origin development
```

### 2. Deploy to Home Assistant

#### Option A: Manual Copy
```bash
# Copy integration to HA custom_components directory
cp -r custom_components/rental_control /path/to/homeassistant/custom_components/

# Restart Home Assistant
ha core restart
```

#### Option B: HACS (if configured)
1. Update repository in HACS
2. Restart Home Assistant
3. Reconfigure calendars to enable check-in links

### 3. Configure Cloudflare Worker

Ensure Worker has matching verification logic:

```javascript
// Example Worker verification (simplified)
async function verifySignature(path, expiry, signature, secret) {
  const message = `${path}|${expiry}`;
  const encoder = new TextEncoder();
  const key = await crypto.subtle.importKey(
    'raw',
    encoder.encode(secret),
    { name: 'HMAC', hash: 'SHA-256' },
    false,
    ['verify']
  );

  const expectedSig = await crypto.subtle.sign(
    'HMAC',
    key,
    encoder.encode(message)
  );

  return signature === bufferToHex(expectedSig);
}
```

### 4. Test End-to-End

1. Create test reservation with check-in date = today
2. Wait for 06:00 AM (or manually adjust HA time for testing)
3. Check event sensor attributes for `self_checkin_link`
4. Copy link and verify signature on Worker
5. Confirm link expires after 24 hours

## Known Issues & Future Improvements

See [BACKLOG.md](./BACKLOG.md) for full list. Key items:

### High Priority (Security)
1. **Enforce HTTPS**: Config flow should reject `http://` URLs in production
2. **Path traversal validation**: Prevent `../` patterns in path parameter
3. **Secret strength validation**: Require minimum 32 characters
4. **Exception handling**: Wrap link generation in try/catch

### Medium Priority (Code Quality)
5. **Debug logging**: Add detailed logs for troubleshooting
6. **Move magic numbers to constants**: `86400` (expiry), `6` (generation hour)
7. **Simplify path conversion**: Replace `next()` generator with dict lookup
8. **URL encoding**: Use `urllib.parse.urlencode` for query parameters

### Low Priority (Enhancements)
10. **Link caching**: Cache links for 1 hour to stabilize expiry time
11. **Edge case tests**: Unicode paths, very long secrets, existing query params
12. **Timezone documentation**: Clarify event TZ vs system TZ behavior
13. **Secret storage warning**: Document secure storage practices

## Troubleshooting

### Link Not Appearing

**Symptom**: `self_checkin_link` attribute is `None` on check-in day

**Possible causes**:

1. **Time before 6:00 AM**
   - Check current time in event timezone
   - Verify event `start_time` timezone

2. **Links disabled**
   - Check `checkin_link_enabled` in calendar config
   - Reconfigure calendar if needed

3. **Path set to "none"**
   - Check `checkin_link_path` in calendar config
   - Select valid path or enter custom path

4. **Coordinator not updating**
   - Check Home Assistant logs for errors
   - Force update: edit calendar config and save

**Debugging**:
```bash
# Enable debug logging for rental_control
# In configuration.yaml:
logger:
  default: info
  logs:
    custom_components.rental_control: debug
```

### Link Shows "Invalid Signature" on Worker

**Symptom**: Cloudflare Worker rejects link with "Invalid signature" error

**Possible causes**:

1. **Secrets don't match**
   - Verify HA secret: Check calendar configuration
   - Verify Worker secret: Check environment variables
   - Ensure no extra whitespace or newlines

2. **Path normalization mismatch**
   - Verify Worker uses same normalization (remove trailing `/` before signing)
   - Check Worker strips leading `/` or ensures it's present

3. **Timestamp drift**
   - Verify HA system time is accurate
   - Check if Worker validates expiry correctly

**Test signature manually**:
```python
import hmac, hashlib, time

path = "/checkin/cottage"  # Normalized (no trailing slash)
secret = "your-secret-here"
expiry = 1730527200  # From link's ?t= parameter

message = f"{path}|{expiry}"
sig = hmac.new(secret.encode(), message.encode(), hashlib.sha256).hexdigest()
print(f"Expected signature: {sig}")
```

### Link Expired

**Symptom**: Link worked earlier, now shows "Link expired" on Worker

**Expected behavior**: Links expire 24 hours after generation (at 6:00 AM next day if generated at 6:00 AM).

**Workaround**: Wait for next coordinator update (max 2 minutes) to get fresh link.

**Future fix**: See BACKLOG.md item #10 for link caching to extend validity.

## Contributing

When working on this feature:

1. **Maintain 100% test coverage** (`pytest --cov-fail-under=100`)
2. **Follow Conventional Commits** (`Feat:`, `Fix:`, `Chore:`, etc.)
3. **Run pre-commit hooks** (`pre-commit run --all-files`)
4. **Update BACKLOG.md** when identifying new issues
5. **Never commit secrets** to git

## References

- **Original Cloudflare Worker**: `self-checkin-worker/generate_link.js` (reference implementation)
- **Upstream project**: [tykeal/homeassistant-rental-control](https://github.com/tykeal/homeassistant-rental-control)
- **HMAC specification**: [RFC 2104](https://www.rfc-editor.org/rfc/rfc2104)
- **SHA-256**: [FIPS 180-4](https://nvlpubs.nist.gov/nistpubs/FIPS/NIST.FIPS.180-4.pdf)

## License

SPDX-License-Identifier: Apache-2.0

## Authors

- Feature implementation: cheezzz (with Claude Code assistance)
- Original integration: Andrew Grimberg (tykeal)

---

**Last Updated**: 2025-11-01
**Branch**: feature/self-checkin-links
**Commit**: 8a65f89
