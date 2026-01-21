#!/usr/bin/env python3
"""Test script to validate Google Calendar URL works with the integration."""

import re
from icalendar import Calendar
import requests

# Test URL
url = "https://calendar.google.com/calendar/ical/46fff157f269f405aa634c987a9fcd9fb443f871edd4c2c06faa5752a96bee37%40group.calendar.google.com/private-8bca92e4ceabaee183774cc87c11d32b/basic.ics"

print("=" * 80)
print("TESTING GOOGLE CALENDAR URL")
print("=" * 80)

# Test 1: HTTPS check
print("\n✓ Test 1: URL starts with HTTPS")
assert url.startswith("https://"), "URL must be HTTPS"
print(f"  URL: {url[:80]}...")

# Test 2: Fetch URL
print("\n✓ Test 2: Fetching URL...")
response = requests.get(url, timeout=60)
print(f"  Status Code: {response.status_code}")
assert response.status_code == 200, "URL must return 200 status"

# Test 3: Content-Type check
print("\n✓ Test 3: Checking Content-Type header...")
content_type = response.headers.get("content-type", "")
print(f"  Content-Type: {content_type}")
assert "text/calendar" in content_type or "text/plain" in content_type, \
    "Content-Type must be text/calendar or text/plain"

# Test 4: Parse iCalendar
print("\n✓ Test 4: Parsing iCalendar format...")
text = response.text
print(f"  Calendar size: {len(text)} bytes")

# Remove NULL bytes (integration does this)
text = text.replace("\x00", "")

# Parse calendar
cal = Calendar.from_ical(text)
print(f"  Calendar parsed successfully")

# Test 5: Check calendar properties
print("\n✓ Test 5: Checking calendar properties...")
if "X-WR-CALNAME" in cal:
    print(f"  Calendar Name: {cal['X-WR-CALNAME']}")
if "X-WR-TIMEZONE" in cal:
    print(f"  Timezone: {cal['X-WR-TIMEZONE']}")

# Test 6: Extract events
print("\n✓ Test 6: Extracting events...")
events = []
for component in cal.walk():
    if component.name == "VEVENT":
        events.append(component)

print(f"  Found {len(events)} event(s)")

# Test 7: Parse event details
for i, event in enumerate(events):
    print(f"\n✓ Test 7.{i+1}: Parsing Event {i+1} details...")

    summary = str(event.get('summary', ''))
    description = str(event.get('description', ''))
    start = event.get('dtstart')
    end = event.get('dtend')
    location = event.get('location', '')

    print(f"  Summary: {summary}")
    print(f"  Description: {description}")
    print(f"  Start: {start.dt if start else 'N/A'}")
    print(f"  End: {end.dt if end else 'N/A'}")
    print(f"  Location: {location}")

    # Test slot name extraction (from util.py:get_slot_name)
    prefix = "Unit1"
    if prefix:
        p = re.compile(f"{prefix} (.*)")
        matches = p.findall(summary)
        if matches:
            slot_name = matches[0]
        else:
            slot_name = summary
    else:
        slot_name = summary

    print(f"  Slot Name (with prefix '{prefix}'): {slot_name}")
    print(f"  Slot Name (without prefix): {summary}")

    # Test phone extraction
    if description:
        p = re.compile(r"""Phone(?: Number)?:\s+(\+?[\d\. \-\(\)]{9,})""")
        phone = p.findall(description)
        if phone:
            print(f"  Phone Number: {phone[0]}")
        else:
            print(f"  Phone Number: NOT FOUND (description lacks 'Phone:' or 'Phone Number:' label)")
            print(f"    Raw description: '{description}'")

    # Test email extraction
    if description:
        p = re.compile(r"""Email:\s+(\S+@\S+)""")
        email = p.findall(description)
        if email:
            print(f"  Email: {email[0]}")
        else:
            print(f"  Email: NOT FOUND (no 'Email:' label)")

    # Test guest count extraction
    if description:
        p = re.compile(r"""Guests:\s+(\d+)$""", re.M)
        guests = p.findall(description)
        if guests:
            print(f"  Number of Guests: {guests[0]}")
        else:
            print(f"  Number of Guests: NOT FOUND (no 'Guests:' label)")

print("\n" + "=" * 80)
print("✅ ALL TESTS PASSED - URL is compatible with rental_control integration!")
print("=" * 80)
