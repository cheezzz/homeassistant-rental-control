# SPDX-FileCopyrightText: 2021 Andrew Grimberg <tykeal@bardicgrove.org>
# SPDX-License-Identifier: Apache-2.0

"""Test real calendar integration with actual booking platform data."""

import requests
from icalendar import Calendar
from datetime import datetime, date
import pytz
import sys
import os

# Add the custom component to path for testing
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "custom_components"))

from custom_components.rental_control.util import extract_guest_info


def test_real_calendars():
    """Test integration with real Airbnb and Lekkeslaap calendars."""
    
    # Test URLs
    lekkeslaap_url = "https://www.lekkeslaap.co.za/suppliers/icalendar.ics?t=OXNwQldFNkFEL3ZhNU9nWUVNS3VzQT09"
    airbnb_url = "https://www.airbnb.co.za/calendar/ical/38286161.ics?s=5fcb6eb9175063e7c1abbcad94cbdf58"
    
    gmt_plus_2 = pytz.timezone('Africa/Johannesburg')
    
    print("=== TESTING REAL CALENDAR INTEGRATION ===")
    
    for name, url in [("Lekkeslaap", lekkeslaap_url), ("Airbnb", airbnb_url)]:
        print(f"\n--- Testing {name} Calendar ---")
        
        try:
            response = requests.get(url, timeout=30)
            response.raise_for_status()
            
            cal = Calendar.from_ical(response.content)
            events = [component for component in cal.walk() if component.name == 'VEVENT']
            
            print(f"✓ Successfully fetched {len(events)} events")
            
            # Test event processing similar to rental_control coordinator
            processed_events = []
            for event in events:
                dtstart = event.get('DTSTART')
                dtend = event.get('DTEND')
                
                if dtstart and dtend:
                    # Convert to proper datetime objects
                    start_dt = dtstart.dt
                    end_dt = dtend.dt
                    
                    if isinstance(start_dt, date) and not isinstance(start_dt, datetime):
                        start_dt = datetime.combine(start_dt, datetime.min.time())
                    if isinstance(end_dt, date) and not isinstance(end_dt, datetime):
                        end_dt = datetime.combine(end_dt, datetime.min.time())
                    
                    # Add timezone if naive
                    if start_dt.tzinfo is None:
                        start_dt = gmt_plus_2.localize(start_dt)
                    if end_dt.tzinfo is None:
                        end_dt = gmt_plus_2.localize(end_dt)
                    
                    # Test guest info extraction
                    description = str(event.get('DESCRIPTION', ''))
                    summary = str(event.get('SUMMARY', ''))
                    
                    try:
                        guest_info = extract_guest_info(description)
                        processed_events.append({
                            'start': start_dt,
                            'end': end_dt,
                            'summary': summary,
                            'guest_info': guest_info
                        })
                    except Exception as e:
                        print(f"  Warning: Guest info extraction failed for event: {e}")
            
            print(f"✓ Successfully processed {len(processed_events)} events")
            
            # Show sample of processed data (sanitized)
            for i, event_data in enumerate(processed_events[:2]):
                print(f"  Sample Event {i+1}:")
                print(f"    Start: {event_data['start']}")
                print(f"    End: {event_data['end']}")
                print(f"    Summary: {event_data['summary'][:50]}...")
                if event_data['guest_info']:
                    print(f"    Guest Info Extracted: {bool(event_data['guest_info'])}")
                
        except Exception as e:
            print(f"✗ Failed to process {name} calendar: {e}")
    
    print("\n=== INTEGRATION TEST COMPLETE ===")


if __name__ == "__main__":
    test_real_calendars()

