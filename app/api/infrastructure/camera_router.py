from fastapi import APIRouter, HTTPException, Depends, Query, Request
from pydantic import BaseModel
from typing import Optional, Dict, Any, List
from fastapi.responses import StreamingResponse, Response
import logging

from ...camera.application.use_cases import (
    CameraShootingUseCase,
    CameraStatusUseCase,
    LiveViewSnapshotUseCase,
    LiveViewStreamUseCase,
)
from ...camera.domain.entities import (
    CameraShootingRequest,
    CameraStatusRequest,
    LiveViewSnapshotRequest,
    LiveViewStreamRequest,
    LiveViewStream,
)
from ...camera.infrastructure.container import get_camera_container
from ...camera.infrastructure.error_handling_service import get_error_handling_service


class ShootCameraResponseModel(BaseModel):
    """Pydantic model for camera shooting response."""

    success: bool
    message: str
    shooting_id: Optional[str] = None
    image_path: Optional[str] = None


class ExecuteCommandRequestModel(BaseModel):
    """Pydantic model for executing camera commands."""

    command_type: str
    parameters: Dict[str, Any] = {}


class ExecuteCommandResponseModel(BaseModel):
    """Pydantic model for command execution response."""

    success: bool
    message: str
    shooting_id: Optional[str] = None
    image_path: Optional[str] = None


class ImageInfoModel(BaseModel):
    """Pydantic model for image information."""

    filename: str
    size_bytes: int
    modified_time: str
    image_url: str


class ListImagesResponseModel(BaseModel):
    """Pydantic model for listing images response."""

    success: bool
    message: str
    images: List[ImageInfoModel]
    total_count: int


def create_camera_router() -> APIRouter:
    """Create and configure the camera router."""
    router = APIRouter(prefix="/camera", tags=["camera"])
    logger = logging.getLogger(__name__)

    def get_camera_container_dependency():
        """Dependency to get camera container."""
        return get_camera_container()

    def get_error_handling_service_dependency():
        """Dependency to get error handling service."""
        return get_error_handling_service()

    @router.post("/shoot")
    async def shoot_camera(
        request: Request,
        container=Depends(get_camera_container_dependency),
        error_service=Depends(get_error_handling_service_dependency),
    ):
        """Take a single photo with the camera."""
        request_id = str(request.headers.get("X-Request-ID", ""))

        try:
            logger.info("📸 Starting camera shooting")

            use_case = CameraShootingUseCase(container.camera_service)
            request_data = CameraShootingRequest()

            result = await use_case.execute(request_data)

            if result.is_success:
                logger.info(f"✅ Camera shooting successful: {result.value.message}")
                return error_service.create_success_response(
                    {
                        "message": result.value.message,
                        "shooting_id": result.value.shooting_id,
                        "image_path": result.value.image_path,
                        "timestamp": result.value.timestamp.isoformat()
                        if result.value.timestamp
                        else None,
                    },
                    request_id,
                )
            else:
                logger.error(f"❌ Camera shooting failed: {result.error}")
                error_response = error_service.handle_error(
                    Exception(result.error),
                    {"operation": "camera_shooting"},
                    request_id,
                )
                raise HTTPException(status_code=500, detail=error_response.dict())

        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"❌ Unexpected error in camera shooting: {e}")
            error_response = error_service.handle_error(
                e, {"operation": "camera_shooting"}, request_id
            )
            raise HTTPException(status_code=500, detail=error_response.dict())

    @router.get("/status")
    async def get_camera_status(
        request: Request,
        container=Depends(get_camera_container_dependency),
        error_service=Depends(get_error_handling_service_dependency),
    ):
        """Get the current status of the camera."""
        request_id = str(request.headers.get("X-Request-ID", ""))

        try:
            logger.info("📊 Getting camera status")

            use_case = CameraStatusUseCase(container.camera_service)
            request_data = CameraStatusRequest()

            result = await use_case.execute(request_data)

            if result.is_success:
                status = result.value
                logger.info(
                    f"✅ Camera status retrieved: connected={status.is_connected}"
                )
                return error_service.create_success_response(
                    {
                        "is_connected": status.is_connected,
                        "is_recording": status.is_recording,
                        "current_mode": status.current_mode,
                        "battery_level": status.battery_level,
                        "storage_available": status.storage_available,
                    },
                    request_id,
                )
            else:
                logger.error(f"❌ Failed to get camera status: {result.error}")
                error_response = error_service.handle_error(
                    Exception(result.error), {"operation": "camera_status"}, request_id
                )
                raise HTTPException(status_code=500, detail=error_response.dict())

        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"❌ Unexpected error getting camera status: {e}")
            error_response = error_service.handle_error(
                e, {"operation": "camera_status"}, request_id
            )
            raise HTTPException(status_code=500, detail=error_response.dict())

    @router.get("/live-view/snapshot")
    async def take_live_view_snapshot(
        request: Request,
        quality: Optional[int] = Query(None, description="JPEG quality (1-100)"),
        container=Depends(get_camera_container_dependency),
        error_service=Depends(get_error_handling_service_dependency),
    ):
        """Take a live view snapshot."""
        request_id = str(request.headers.get("X-Request-ID", ""))

        try:
            logger.info(f"📸 Taking live view snapshot with quality={quality}")

            # Get default quality from configuration if not provided
            if quality is None:
                image_config = container.image_config
                if image_config:
                    quality = image_config.default_jpeg_quality
                else:
                    quality = 80  # Fallback default

            use_case = LiveViewSnapshotUseCase(container.camera_service)
            request_data = LiveViewSnapshotRequest(quality=quality)

            result = await use_case.execute(request_data)

            if result.is_success:
                live_view_result = result.value
                logger.info(
                    f"✅ Live view snapshot successful: {live_view_result.message}"
                )

                # Add cache-busting headers to prevent browser caching
                headers = {
                    "Cache-Control": "no-cache, no-store, must-revalidate",
                    "Pragma": "no-cache",
                    "Expires": "0",
                    "X-Request-ID": request_id,
                }

                return Response(
                    content=live_view_result.image_data,
                    media_type=f"image/{live_view_result.image_format}",
                    headers=headers,
                )
            else:
                logger.error(f"❌ Live view snapshot failed: {result.error}")
                error_response = error_service.handle_error(
                    Exception(result.error),
                    {"operation": "live_view_snapshot", "quality": quality},
                    request_id,
                )
                raise HTTPException(status_code=500, detail=error_response.dict())

        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"❌ Unexpected error in live view snapshot: {e}")
            error_response = error_service.handle_error(
                e, {"operation": "live_view_snapshot", "quality": quality}, request_id
            )
            raise HTTPException(status_code=500, detail=error_response.dict())

    @router.get("/live-view/stream")
    async def start_live_view_stream(
        request: Request,
        framerate: Optional[float] = Query(
            None, description="Frames per second (0.1-8.0)"
        ),
        quality: Optional[int] = Query(None, description="JPEG quality (1-100)"),
        container=Depends(get_camera_container_dependency),
        error_service=Depends(get_error_handling_service_dependency),
    ):
        """Start a live view stream."""
        request_id = str(request.headers.get("X-Request-ID", ""))

        try:
            logger.info(
                f"🎥 Starting live view stream with framerate={framerate}, quality={quality}"
            )

            # Get default values from configuration if not provided
            if framerate is None:
                camera_config = container.camera_config
                if camera_config:
                    framerate = camera_config.max_framerate
                else:
                    framerate = 5.0  # Fallback default

            if quality is None:
                image_config = container.image_config
                if image_config:
                    quality = image_config.default_jpeg_quality
                else:
                    quality = 80  # Fallback default

            # Validate parameters
            if framerate < 0.1 or framerate > 8.0:
                error_response = error_service.handle_error(
                    ValueError("Framerate must be between 0.1 and 8.0 FPS"),
                    {
                        "operation": "live_view_stream",
                        "framerate": framerate,
                        "quality": quality,
                    },
                    request_id,
                )
                raise HTTPException(status_code=400, detail=error_response.dict())

            if quality < 1 or quality > 100:
                error_response = error_service.handle_error(
                    ValueError("JPEG quality must be between 1 and 100"),
                    {
                        "operation": "live_view_stream",
                        "framerate": framerate,
                        "quality": quality,
                    },
                    request_id,
                )
                raise HTTPException(status_code=400, detail=error_response.dict())

            use_case = LiveViewStreamUseCase(container.camera_service)
            request_data = LiveViewStreamRequest(
                stream_config=LiveViewStream(framerate=framerate, quality=quality)
            )

            result = await use_case.execute(request_data)

            if result.is_success:
                logger.info("✅ Live view stream started successfully")

                # Add cache-busting headers
                headers = {
                    "Cache-Control": "no-cache, no-store, must-revalidate",
                    "Pragma": "no-cache",
                    "Expires": "0",
                    "X-Request-ID": request_id,
                }

                return StreamingResponse(
                    result.value,
                    media_type="multipart/x-mixed-replace; boundary=frame",
                    headers=headers,
                )
            else:
                logger.error(f"❌ Live view stream failed: {result.error}")
                error_response = error_service.handle_error(
                    Exception(result.error),
                    {
                        "operation": "live_view_stream",
                        "framerate": framerate,
                        "quality": quality,
                    },
                    request_id,
                )
                raise HTTPException(status_code=500, detail=error_response.dict())

        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"❌ Unexpected error in live view stream: {e}")
            error_response = error_service.handle_error(
                e,
                {
                    "operation": "live_view_stream",
                    "framerate": framerate,
                    "quality": quality,
                },
                request_id,
            )
            raise HTTPException(status_code=500, detail=error_response.dict())

    @router.get("/last-picture")
    async def get_last_picture(
        request: Request,
        container=Depends(get_camera_container_dependency),
        error_service=Depends(get_error_handling_service_dependency),
    ):
        """Get the last picture taken by the camera."""
        request_id = str(request.headers.get("X-Request-ID", ""))

        try:
            logger.info("🖼️ Getting last picture")

            # This would typically use a use case, but for now we'll access the service directly
            # In a full implementation, you'd create a GetLastPictureUseCase

            # For now, return a placeholder response
            # TODO: Implement proper last picture retrieval
            error_response = error_service.handle_error(
                NotImplementedError("Last picture retrieval not yet implemented"),
                {"operation": "get_last_picture"},
                request_id,
            )
            raise HTTPException(status_code=501, detail=error_response.dict())

        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"❌ Unexpected error getting last picture: {e}")
            error_response = error_service.handle_error(
                e, {"operation": "get_last_picture"}, request_id
            )
            raise HTTPException(status_code=500, detail=error_response.dict())

    @router.get("/configuration")
    async def get_configuration(
        request: Request,
        container=Depends(get_camera_container_dependency),
        error_service=Depends(get_error_handling_service_dependency),
    ):
        """Get current application configuration."""
        request_id = str(request.headers.get("X-Request-ID", ""))

        try:
            logger.info("⚙️ Getting application configuration")

            config_service = container.configuration_service
            if not config_service:
                error_response = error_service.handle_error(
                    RuntimeError("Configuration service not available"),
                    {"operation": "get_configuration"},
                    request_id,
                )
                raise HTTPException(status_code=500, detail=error_response.dict())

            config = config_service.configuration
            if not config:
                error_response = error_service.handle_error(
                    RuntimeError("Configuration not loaded"),
                    {"operation": "get_configuration"},
                    request_id,
                )
                raise HTTPException(status_code=500, detail=error_response.dict())

            return error_service.create_success_response(
                {
                    "camera": {
                        "chdkptp_location": config.camera.chdkptp_location,
                        "output_directory": config.camera.output_directory,
                        "frame_file_name": config.camera.frame_file_name,
                        "default_jpeg_quality": config.camera.default_jpeg_quality,
                        "max_framerate": config.camera.max_framerate,
                        "command_timeout": config.camera.command_timeout,
                    },
                    "image_processing": {
                        "default_jpeg_quality": config.image_processing.default_jpeg_quality,
                        "timestamp_font_scale": config.image_processing.timestamp_font_scale,
                        "timestamp_font_thickness": config.image_processing.timestamp_font_thickness,
                        "timestamp_color": config.image_processing.timestamp_color,
                        "timestamp_outline_color": config.image_processing.timestamp_outline_color,
                    },
                    "environment": {
                        "environment": config.environment.environment,
                        "debug": config.environment.debug,
                        "log_level": config.environment.log_level,
                        "log_format": config.environment.log_format,
                        "enable_authentication": config.environment.enable_authentication,
                        "api_key_required": config.environment.api_key_required,
                        "max_concurrent_streams": config.environment.max_concurrent_streams,
                        "stream_buffer_size": config.environment.stream_buffer_size,
                    },
                },
                request_id,
            )

        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"❌ Unexpected error getting configuration: {e}")
            error_response = error_service.handle_error(
                e, {"operation": "get_configuration"}, request_id
            )
            raise HTTPException(status_code=500, detail=error_response.dict())

    @router.post("/configuration/reload")
    async def reload_configuration(
        request: Request,
        container=Depends(get_camera_container_dependency),
        error_service=Depends(get_error_handling_service_dependency),
    ):
        """Reload application configuration."""
        request_id = str(request.headers.get("X-Request-ID", ""))

        try:
            logger.info("🔄 Reloading application configuration")

            success = container.reload_configuration()

            if success:
                logger.info("✅ Configuration reloaded successfully")
                return error_service.create_success_response(
                    {"message": "Configuration reloaded successfully"}, request_id
                )
            else:
                logger.error("❌ Failed to reload configuration")
                error_response = error_service.handle_error(
                    RuntimeError("Failed to reload configuration"),
                    {"operation": "reload_configuration"},
                    request_id,
                )
                raise HTTPException(status_code=500, detail=error_response.dict())

        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"❌ Unexpected error reloading configuration: {e}")
            error_response = error_service.handle_error(
                e, {"operation": "reload_configuration"}, request_id
            )
            raise HTTPException(status_code=500, detail=error_response.dict())

    return router
