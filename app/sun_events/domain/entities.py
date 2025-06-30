from dataclasses import dataclass
from datetime import datetime


@dataclass
class SunEvent:
    """Domain entity representing a sun event for a specific date."""

    id: int
    date: datetime
    dawn: datetime
    sunrise: datetime
    culmination: datetime
    sunset: datetime
    dusk: datetime
    sun_altitude: float
    azimuth: float
    magic_hour_morning_start: datetime
    magic_hour_morning_end: datetime
    magic_hour_evening_start: datetime
    magic_hour_evening_end: datetime
    golden_hour_morning_start: datetime
    golden_hour_morning_end: datetime
    golden_hour_evening_start: datetime
    golden_hour_evening_end: datetime
    blue_hour_morning_start: datetime
    blue_hour_morning_end: datetime
    blue_hour_evening_start: datetime
    blue_hour_evening_end: datetime


@dataclass
class SunEventPeriod:
    """Domain entity representing a sunrise or sunset period."""

    period_type: str  # "sunrise" or "sunset"
    event_date: datetime
    start_time: datetime
    end_time: datetime
