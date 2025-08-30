# SPDX-FileCopyrightText: 2024 Claude Code Assistant
# SPDX-License-Identifier: Apache-2.0

import icalendar

ical_data = """
BEGIN:VCALENDAR
VERSION:2.0
PRODID:-//Sabre//Sabre VObject 4.4.1//EN
CALSCALE:GREGORIAN
BEGIN:VEVENT
UID:LS-5C384T@lekkeslaap.co.za
DTSTAMP:20250726T182328Z
DESCRIPTION:BOOKING SUMMARY:Reference: LS-5C384T\nView at: https://www.lekkeslaap.co.za/supplie rs/bookings/quotation/LS-5C384T
DTSTART;VALUE=DATE:20260109
DTEND;VALUE=DATE:20260110
END:VEVENT
BEGIN:VEVENT
UID:LS-5CWKXC@lekkeslaap.co.za
DTSTAMP:20250726T182328Z
DESCRIPTION:BOOKING SUMMARY:Reference: LS-5CWKXC\nView at: https://www.lekkeslaap.co.za/supplie rs/bookings/quotation/LS-5CWKXC
DTSTART;VALUE=DATE:20251206
DTEND;VALUE=DATE:20251207
END:VEVENT
END:VCALENDAR
"""

try:
    cal = icalendar.Calendar.from_ical(ical_data)
    print("iCalendar data is valid.")
    # You can add more specific validation here if needed, e.g., checking for required components/properties
    # for component in cal.walk():
    #     print(component.name)
except ValueError as e:
    print(f"iCalendar data is invalid: {e}")
except Exception as e:
    print(f"An unexpected error occurred during iCalendar validation: {e}")

