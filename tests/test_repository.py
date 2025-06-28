from datetime import datetime

from app.infrastructure.repositories import SQLiteSunEventRepository


def test_repository_can_read_sun_events():
    """Test that the repository can read sun events from the database."""
    repository = SQLiteSunEventRepository()

    # Test getting a specific date
    test_date = datetime(2025, 6, 27)
    event = repository.get_sun_event_by_date_sync(test_date)

    assert event is not None
    assert event.date.date() == test_date.date()
    assert event.sun_altitude > 0
    assert event.azimuth > 0


def test_repository_handles_missing_date():
    """Test that the repository returns None for missing dates."""
    repository = SQLiteSunEventRepository()

    # Test getting a date that doesn't exist
    test_date = datetime(1900, 1, 1)
    event = repository.get_sun_event_by_date_sync(test_date)

    assert event is None


def test_repository_datetime_parsing():
    """Test that the repository can parse datetime strings correctly."""
    repository = SQLiteSunEventRepository()

    # Test getting a known date
    test_date = datetime(2025, 6, 27)
    event = repository.get_sun_event_by_date_sync(test_date)

    if event:
        # Verify all datetime fields are properly parsed
        assert isinstance(event.dawn, datetime)
        assert isinstance(event.sunrise, datetime)
        assert isinstance(event.sunset, datetime)
        assert isinstance(event.dusk, datetime)
        assert isinstance(event.golden_hour_morning_start, datetime)
        assert isinstance(event.golden_hour_morning_end, datetime)
        assert isinstance(event.golden_hour_evening_start, datetime)
        assert isinstance(event.golden_hour_evening_end, datetime)
