from datetime import datetime

from app.sun_events.infrastructure.json_repository import JSONSunEventRepository


def test_repository_can_read_sun_events():
    """Test that the repository can read sun events from the JSON file."""
    repository = JSONSunEventRepository()

    # Test getting a specific date
    test_date = datetime(2025, 6, 28)
    event = repository.get_sun_event_by_date_sync(test_date)

    assert event is not None
    assert event.date == test_date
    assert event.dawn == datetime(2025, 6, 28, 6, 17, 11)
    assert event.sunrise == datetime(2025, 6, 28, 6, 47, 54)
    assert event.sunset == datetime(2025, 6, 28, 22, 25, 54)
    assert event.dusk == datetime(2025, 6, 28, 22, 56, 35)


def test_repository_handles_missing_date():
    """Test that the repository returns None for missing dates."""
    repository = JSONSunEventRepository()

    # Test getting a date that doesn't exist
    test_date = datetime(2025, 6, 27)
    event = repository.get_sun_event_by_date_sync(test_date)

    assert event is None


def test_repository_datetime_parsing():
    """Test that the repository correctly parses datetime strings."""
    repository = JSONSunEventRepository()

    test_date = datetime(2025, 6, 28)
    event = repository.get_sun_event_by_date_sync(test_date)

    assert event is not None
    # Test that all time fields are properly parsed as datetime
    assert isinstance(event.dawn, datetime)
    assert isinstance(event.sunrise, datetime)
    assert isinstance(event.culmination, datetime)
    assert isinstance(event.sunset, datetime)
    assert isinstance(event.dusk, datetime)


def test_repository_upcoming_events():
    """Test that the repository can find upcoming events."""
    repository = JSONSunEventRepository()

    # Test from a specific date
    from_date = datetime(2025, 6, 28)
    upcoming = repository.get_upcoming_sun_events_sync(from_date, limit=5)

    assert len(upcoming) > 0
    # Should find events for the current day and future days
    expected_date = datetime(2025, 6, 28)
    assert any(event.date == expected_date for event in upcoming)
