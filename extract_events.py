#!/usr/bin/env python3
"""
Script to extract sun events from SQLite database and convert to JSON format.
"""

import json
import sqlite3
from datetime import datetime
from typing import Dict, Any


def parse_datetime(dt_str: str) -> str:
    """Parse datetime string from SQLite and return time only."""
    # Handle timezone info if present
    if "+" in dt_str:
        dt_str = dt_str.split("+")[0]
    elif "-" in dt_str and dt_str.count("-") > 2:
        # Handle timezone offset in the middle
        parts = dt_str.split("-")
        if len(parts) > 3:
            dt_str = "-".join(parts[:-2]) + parts[-1]

    # Try different formats
    formats = [
        "%Y-%m-%dT%H:%M:%S.%f",
        "%Y-%m-%dT%H:%M:%S",
        "%Y-%m-%d %H:%M:%S.%f",
        "%Y-%m-%d %H:%M:%S",
    ]

    for fmt in formats:
        try:
            dt = datetime.strptime(dt_str, fmt)
            return dt.strftime("%H:%M:%S")
        except ValueError:
            continue

    raise ValueError(f"Could not parse datetime: {dt_str}")


def extract_sun_events(db_path: str = "sun_events.db") -> Dict[str, Any]:
    """Extract sun events from SQLite database."""
    sun_events = {}

    try:
        with sqlite3.connect(db_path) as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM sun_events ORDER BY date")
            rows = cursor.fetchall()

            for row in rows:
                # Extract date from the first column
                date_str = row[1]  # date column
                if "T" in date_str:
                    date_only = date_str.split("T")[0]
                else:
                    date_only = date_str.split(" ")[0]

                # Convert row to event data
                event_data = {
                    "dawn": parse_datetime(row[2]),
                    "sunrise": parse_datetime(row[3]),
                    "culmination": parse_datetime(row[4]),
                    "sunset": parse_datetime(row[5]),
                    "dusk": parse_datetime(row[6]),
                    "sun_altitude": float(row[7]),
                    "azimuth": float(row[8]),
                    "magic_hour_morning_start": parse_datetime(row[9]),
                    "magic_hour_morning_end": parse_datetime(row[10]),
                    "magic_hour_evening_start": parse_datetime(row[11]),
                    "magic_hour_evening_end": parse_datetime(row[12]),
                    "golden_hour_morning_start": parse_datetime(row[13]),
                    "golden_hour_morning_end": parse_datetime(row[14]),
                    "golden_hour_evening_start": parse_datetime(row[15]),
                    "golden_hour_evening_end": parse_datetime(row[16]),
                    "blue_hour_morning_start": parse_datetime(row[17]),
                    "blue_hour_morning_end": parse_datetime(row[18]),
                    "blue_hour_evening_start": parse_datetime(row[19]),
                    "blue_hour_evening_end": parse_datetime(row[20]),
                }

                sun_events[date_only] = event_data

    except sqlite3.Error as e:
        print(f"Database error: {e}")
        return {}
    except Exception as e:
        print(f"Error: {e}")
        return {}

    return {"sun_events": sun_events}


def main():
    """Main function to extract and save sun events."""
    print("Extracting sun events from SQLite database...")

    # Extract events
    events_data = extract_sun_events()

    if not events_data.get("sun_events"):
        print("No events found or error occurred.")
        return

    # Save to JSON file
    output_file = "config/sun_events.json"
    try:
        with open(output_file, "w") as f:
            json.dump(events_data, f, indent=2)

        print(f"✅ Successfully extracted {len(events_data['sun_events'])} events")
        print(f"📁 Saved to: {output_file}")

        # Show sample of extracted data
        print("\n📋 Sample of extracted data:")
        first_date = list(events_data["sun_events"].keys())[0]
        first_event = events_data["sun_events"][first_date]
        print(f"Date: {first_date}")
        print(f"  Dawn: {first_event['dawn']}")
        print(f"  Sunrise: {first_event['sunrise']}")
        print(f"  Sunset: {first_event['sunset']}")
        print(f"  Dusk: {first_event['dusk']}")

    except Exception as e:
        print(f"❌ Error saving to JSON: {e}")


if __name__ == "__main__":
    main()
