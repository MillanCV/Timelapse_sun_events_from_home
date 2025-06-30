import asyncio
import logging
import threading
from contextlib import asynccontextmanager

import uvicorn
from fastapi import FastAPI

from app.api.infrastructure.fastapi_app import create_app
from app.background.infrastructure.sun_event_monitor_service import (
    SunEventMonitorService,
)
from app.background.infrastructure.sun_event_orchestrator import SunEventOrchestrator
from app.camera.infrastructure.chdkptp_camera_service import (
    CHDKPTPCameraService,
    CHDKPTPScriptGenerator,
)
from app.sun_events.infrastructure.json_repository import JSONSunEventRepository
from app.timelapse.application.use_cases import CalculateTimelapseUseCase
from app.video_processing.infrastructure.ffmpeg_video_processor import (
    FFmpegVideoProcessor,
)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)

# Global variables for service management
monitor_service: SunEventMonitorService = None
monitor_thread: threading.Thread = None


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Manage application lifespan."""
    global monitor_service, monitor_thread

    # Startup
    logging.info("Starting application...")

    # Initialize sun event repository
    sun_event_repository = JSONSunEventRepository()

    # Initialize timelapse use case
    timelapse_use_case = CalculateTimelapseUseCase(sun_event_repository)

    # Initialize camera services
    script_generator = CHDKPTPScriptGenerator()
    camera_service = CHDKPTPCameraService(script_generator)

    # Initialize video processor
    video_processor = FFmpegVideoProcessor()

    # Initialize orchestrator
    orchestrator = SunEventOrchestrator(
        sun_event_repository=sun_event_repository,
        timelapse_use_case=timelapse_use_case,
        camera_control_service=camera_service,
        script_generator=script_generator,
        video_processor=video_processor,
    )

    # Initialize background service with orchestrator
    monitor_service = SunEventMonitorService(
        sun_event_repository=sun_event_repository,
        orchestrator=orchestrator,
    )

    # Start background service in separate thread
    def run_background_service():
        asyncio.run(monitor_service.start())

    monitor_thread = threading.Thread(target=run_background_service, daemon=True)
    monitor_thread.start()

    logging.info("Application started successfully")

    yield

    # Shutdown
    logging.info("Shutting down application...")

    if monitor_service:
        monitor_service.stop()

    if monitor_thread and monitor_thread.is_alive():
        monitor_thread.join(timeout=5)

    logging.info("Application shutdown complete")


# Create FastAPI app instance with lifespan
app = create_app()
app.router.lifespan_context = lifespan


def main():
    """Main application entry point."""

    uvicorn.run(
        app,
        host="127.0.0.1",
        port=8000,
        log_level="info",
    )


if __name__ == "__main__":
    main()
