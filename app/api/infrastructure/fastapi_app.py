import logging
from datetime import datetime
from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import BaseModel

from .camera_router import create_camera_router
from ...camera.infrastructure.error_handling_service import (
    get_error_handling_service,
    handle_errors,
)
from ...camera.domain.entities import (
    ErrorType,
    ErrorSeverity,
)
from ...sun_events.application.use_cases import (
    CheckUpcomingEventsRequest,
    CheckUpcomingSunEventsUseCase,
    GetCurrentEventRequest,
    GetCurrentSunEventUseCase,
)
from ...sun_events.infrastructure.json_repository import JSONSunEventRepository
from ...timelapse.application.use_cases import (
    CalculateTimelapseRequest,
    CalculateTimelapseUseCase,
)


class TimelapseRequestModel(BaseModel):
    """Pydantic model for timelapse calculation request."""

    period_type: str  # "sunrise" or "sunset"
    video_duration_seconds: int = 20
    video_fps: int = 60
    photo_size_mb: float = 10.0


class TimelapseResponseModel(BaseModel):
    """Pydantic model for timelapse calculation response."""

    period_type: str
    start_time: str
    end_time: str
    total_duration_seconds: float
    video_duration_seconds: int
    video_fps: int
    total_frames: int
    interval_seconds: float
    photos_needed: int
    estimated_file_size_mb: float


def create_app() -> FastAPI:
    """Create and configure the FastAPI application with error handling."""
    app = FastAPI(
        title="Sun Events API", version="1.0.0", docs_url="/docs", redoc_url="/redoc"
    )

    # Add CORS middleware
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],  # Configure appropriately for production
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # Initialize error handling service
    error_service = get_error_handling_service()
    logger = logging.getLogger(__name__)

    # Add request ID middleware
    @app.middleware("http")
    async def add_request_id_middleware(request: Request, call_next):
        """Add request ID to all requests."""
        request_id = error_service.generate_request_id()
        request.state.request_id = request_id

        # Add request ID to response headers
        response = await call_next(request)
        response.headers["X-Request-ID"] = request_id

        logger.info(f"Request {request_id} completed: {request.method} {request.url}")
        return response

    # Global exception handler
    @app.exception_handler(Exception)
    async def global_exception_handler(request: Request, exc: Exception):
        """Handle all unhandled exceptions."""
        request_id = getattr(request.state, "request_id", "unknown")

        error_response = error_service.handle_exception(
            exc,
            request_id=request_id,
            context={
                "method": request.method,
                "url": str(request.url),
                "client_ip": (request.client.host if request.client else "unknown"),
            },
        )

        return JSONResponse(
            status_code=error_response.status_code,
            content=error_response.to_dict(),
            headers={"X-Request-ID": request_id},
        )

    # Initialize dependencies
    sun_event_repository = JSONSunEventRepository()
    get_current_use_case = GetCurrentSunEventUseCase(sun_event_repository)
    get_upcoming_use_case = CheckUpcomingSunEventsUseCase(sun_event_repository)
    calculate_timelapse_use_case = CalculateTimelapseUseCase(sun_event_repository)

    # Include camera router with error handling
    camera_router = create_camera_router()
    app.include_router(camera_router)

    @app.get("/")
    async def root():
        """Root endpoint."""
        return {"message": "Sun Events API", "version": "1.0.0"}

    @app.get("/health")
    async def health_check():
        """Health check endpoint."""
        return {
            "status": "healthy",
            "timestamp": datetime.now().isoformat(),
            "service": "Sun Events API",
        }

    @app.get("/current")
    @handle_errors
    async def get_current_event(request: Request):
        """Get current sun event period if any."""
        try:
            response = get_current_use_case.execute(
                GetCurrentEventRequest(current_time=datetime.now())
            )

            if response.current_period:
                return {
                    "period_type": response.current_period.period_type,
                    "start_time": response.current_period.start_time.isoformat(),
                    "end_time": response.current_period.end_time.isoformat(),
                    "event_date": (
                        response.current_period.event_date.strftime("%Y-%m-%d")
                    ),
                }
            else:
                return {"message": "No current sun event period"}

        except Exception as e:
            error_service.record_error(
                ErrorType.APPLICATION_ERROR,
                str(e),
                ErrorSeverity.MEDIUM,
                request_id=getattr(request.state, "request_id", "unknown"),
                context={"endpoint": "/current"},
            )
            raise

    @app.get("/upcoming")
    @handle_errors
    async def get_upcoming_events(request: Request):
        """Get upcoming sun event periods."""
        try:
            response = get_upcoming_use_case.execute(
                CheckUpcomingEventsRequest(
                    current_time=datetime.now(), look_ahead_minutes=1440
                )
            )

            upcoming_periods = []
            for period in response.upcoming_periods:
                upcoming_periods.append(
                    {
                        "period_type": period.period_type,
                        "start_time": period.start_time.isoformat(),
                        "end_time": period.end_time.isoformat(),
                        "event_date": period.event_date.strftime("%Y-%m-%d"),
                    }
                )

            return {"upcoming_periods": upcoming_periods}

        except Exception as e:
            error_service.record_error(
                ErrorType.APPLICATION_ERROR,
                str(e),
                ErrorSeverity.MEDIUM,
                request_id=getattr(request.state, "request_id", "unknown"),
                context={"endpoint": "/upcoming"},
            )
            raise

    @app.post("/timelapse", response_model=TimelapseResponseModel)
    @handle_errors
    async def calculate_timelapse(
        request: Request, timelapse_request: TimelapseRequestModel
    ):
        """Calculate timelapse parameters for a sun event period."""
        try:
            response = calculate_timelapse_use_case.execute(
                CalculateTimelapseRequest(
                    period_type=timelapse_request.period_type,
                    video_duration_seconds=timelapse_request.video_duration_seconds,
                    video_fps=timelapse_request.video_fps,
                    photo_size_mb=timelapse_request.photo_size_mb,
                )
            )

            params = response.timelapse_parameters
            return TimelapseResponseModel(
                period_type=params.period_type,
                start_time=params.start_time.isoformat(),
                end_time=params.end_time.isoformat(),
                total_duration_seconds=params.total_duration_seconds,
                video_duration_seconds=params.video_duration_seconds,
                video_fps=params.video_fps,
                total_frames=params.total_frames,
                interval_seconds=params.interval_seconds,
                photos_needed=params.photos_needed,
                estimated_file_size_mb=params.estimated_file_size_mb,
            )

        except ValueError as e:
            error_service.record_error(
                ErrorType.VALIDATION_ERROR,
                str(e),
                ErrorSeverity.LOW,
                request_id=getattr(request.state, "request_id", "unknown"),
                context={
                    "endpoint": "/timelapse",
                    "request_data": timelapse_request.dict(),
                },
            )
            raise HTTPException(status_code=400, detail=str(e))

        except Exception as e:
            error_service.record_error(
                ErrorType.APPLICATION_ERROR,
                str(e),
                ErrorSeverity.MEDIUM,
                request_id=getattr(request.state, "request_id", "unknown"),
                context={
                    "endpoint": "/timelapse",
                    "request_data": timelapse_request.dict(),
                },
            )
            raise

    return app
