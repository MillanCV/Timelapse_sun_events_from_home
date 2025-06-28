# Sun Events Monitor

A FastAPI-based service that monitors sun events (sunrise and sunset periods) using a background task. The service checks for upcoming sun events and provides real-time information about current and upcoming periods.

## Features

- **Background Monitoring**: Continuous monitoring of sun events using a non-drifting background task
- **Sunrise Period Detection**: Detects sunrise periods from dawn to end of morning golden hour + 30 minutes
- **Sunset Period Detection**: Detects sunset periods from evening golden hour - 30 minutes to dusk
- **REST API**: Provides endpoints to check current status, upcoming events, and service health
- **Real-time Logging**: Comprehensive logging of sun event periods and transitions

## Architecture

The project follows clean architecture principles with the following layers:

- **Domain**: Contains entities and repository interfaces
- **Application**: Contains use cases that encapsulate business logic
- **Infrastructure**: Contains FastAPI endpoints, repository implementations, and background services

## Installation

1. Install dependencies using `uv`:

```bash
uv sync
```

2. The project uses the existing `sun_events.db` SQLite database with sun event data.

## Usage

### Running the Service

Start the FastAPI server:

```bash
python main.py
```

Or using uvicorn directly:

```bash
uvicorn app.infrastructure.api:app --host 0.0.0.0 --port 8000 --reload
```

The service will start and begin monitoring sun events in the background.

### API Endpoints

- `GET /`: Root endpoint with API information
- `GET /status`: Get current service status and active sun event period
- `GET /current`: Get current sun event period if any
- `GET /upcoming?look_ahead_minutes=30`: Get upcoming sun events

### Background Task Behavior

The background task:

1. **Checks for current periods**: Determines if currently in a sunrise or sunset period
2. **Monitors upcoming events**: Looks ahead for events starting within 30 minutes
3. **Smart waiting**:
   - During active periods: Waits until the period ends
   - Before upcoming periods: Waits until the period starts
   - No events: Checks every 5 minutes
4. **Non-drifting timing**: Uses absolute time calculations to prevent drift

### Sun Event Periods

- **Sunrise Period**: From dawn to end of morning golden hour + 30 minutes
- **Sunset Period**: From evening golden hour - 30 minutes to dusk

## Testing

Run tests with pytest:

```bash
uv run pytest tests/
```

## Project Structure

```
remoteIxus/
├── app/
│   ├── domain/
│   │   ├── entities.py          # Domain entities
│   │   └── repositories.py      # Repository interfaces
│   ├── application/
│   │   └── use_cases.py         # Business logic use cases
│   └── infrastructure/
│       ├── repositories.py      # SQLite repository implementation
│       ├── background_service.py # Background monitoring service
│       └── api.py               # FastAPI application
├── tests/
│   └── test_repository.py       # Repository tests
├── main.py                      # Application entry point
├── pyproject.toml               # Project configuration
└── sun_events.db                # SQLite database with sun events
```

## Background Task Implementation

The background task uses a sophisticated approach to prevent timing drift:

1. **Absolute time calculations**: All wait times are calculated based on absolute timestamps
2. **Event-driven waiting**: The task waits for specific events rather than fixed intervals
3. **Graceful error handling**: Continues operation even if individual cycles fail
4. **Resource cleanup**: Proper cleanup of resources on shutdown

This ensures the monitoring remains accurate over long periods without accumulating timing errors.
