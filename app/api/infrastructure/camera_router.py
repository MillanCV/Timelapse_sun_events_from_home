from fastapi import APIRouter, HTTPException, Depends, Query, Request
from pydantic import BaseModel
from typing import Optional, Dict, Any, List
from fastapi.responses import StreamingResponse, Response
import logging
import os

from ...camera.application.use_cases import (
    ShootCameraUseCase,
    TakeLiveViewSnapshotUseCase,
    StartLiveViewStreamUseCase,
    TakeLiveViewSnapshotRequest,
    StartLiveViewStreamRequest,
)
from ...camera.infrastructure.container import get_camera_container
from ...camera.infrastructure.error_handling_service import (
    get_error_handling_service,
)


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

            camera_service = container.camera_service
            if not camera_service:
                error_response = error_service.handle_error(
                    RuntimeError("Camera service not available - check configuration"),
                    {"operation": "camera_shooting"},
                    request_id,
                )
                raise HTTPException(status_code=503, detail=error_response.to_dict())

            use_case = ShootCameraUseCase(camera_service)
            result = await use_case.execute()

            if result.success:
                logger.info(f"✅ Camera shooting successful: {result.message}")
                return error_service.create_success_response(
                    {
                        "message": result.message,
                        "shooting_id": result.shooting_id,
                        "image_path": result.image_path,
                    },
                    request_id,
                )
            else:
                logger.error(f"❌ Camera shooting failed: {result.message}")
                error_response = error_service.handle_error(
                    Exception(result.message),
                    {"operation": "camera_shooting"},
                    request_id,
                )
                raise HTTPException(status_code=500, detail=error_response.to_dict())

        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"❌ Unexpected error in camera shooting: {e}")
            error_response = error_service.handle_error(
                e, {"operation": "camera_shooting"}, request_id
            )
            raise HTTPException(status_code=500, detail=error_response.to_dict())

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

            camera_service = container.camera_service
            if not camera_service:
                error_response = error_service.handle_error(
                    RuntimeError("Camera service not available - check configuration"),
                    {"operation": "live_view_snapshot"},
                    request_id,
                )
                raise HTTPException(status_code=503, detail=error_response.to_dict())

            # Get default quality from configuration if not provided
            if quality is None:
                image_config = container.image_config
                if image_config:
                    quality = image_config.default_jpeg_quality
                else:
                    quality = 80  # Fallback default

            use_case = TakeLiveViewSnapshotUseCase(camera_service)
            request_data = TakeLiveViewSnapshotRequest()

            result = await use_case.execute(request_data)

            if result.success:
                logger.info(f"✅ Live view snapshot successful: {result.message}")

                # Add cache-busting headers to prevent browser caching
                headers = {
                    "Cache-Control": "no-cache, no-store, must-revalidate",
                    "Pragma": "no-cache",
                    "Expires": "0",
                    "X-Request-ID": request_id,
                }

                return Response(
                    content=result.image_data,
                    media_type="image/jpeg",
                    headers=headers,
                )
            else:
                logger.error(f"❌ Live view snapshot failed: {result.message}")
                error_response = error_service.handle_error(
                    Exception(result.message),
                    {"operation": "live_view_snapshot"},
                    request_id,
                )
                raise HTTPException(status_code=500, detail=error_response.to_dict())

        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"❌ Unexpected error in live view snapshot: {e}")
            error_response = error_service.handle_error(
                e, {"operation": "live_view_snapshot"}, request_id
            )
            raise HTTPException(status_code=500, detail=error_response.to_dict())

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
                f"🎥 Starting live view stream with framerate={framerate}, "
                f"quality={quality}"
            )

            camera_service = container.camera_service
            if not camera_service:
                error_response = error_service.handle_error(
                    RuntimeError("Camera service not available - check configuration"),
                    {"operation": "live_view_stream"},
                    request_id,
                )
                raise HTTPException(status_code=503, detail=error_response.to_dict())

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
                raise HTTPException(status_code=400, detail=error_response.to_dict())

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
                raise HTTPException(status_code=400, detail=error_response.to_dict())

            use_case = StartLiveViewStreamUseCase(camera_service)
            request_data = StartLiveViewStreamRequest(
                framerate=framerate, quality=quality
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
                raise HTTPException(status_code=500, detail=error_response.to_dict())

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
            raise HTTPException(status_code=500, detail=error_response.to_dict())

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

            # Get the file management service from the container
            file_service = container.file_service
            if not file_service:
                error_response = error_service.handle_error(
                    RuntimeError("File management service not available"),
                    {"operation": "get_last_picture"},
                    request_id,
                )
                raise HTTPException(status_code=500, detail=error_response.to_dict())

            # Get the output directory from configuration
            camera_config = container.camera_config
            if not camera_config:
                error_response = error_service.handle_error(
                    RuntimeError("Camera configuration not available"),
                    {"operation": "get_last_picture"},
                    request_id,
                )
                raise HTTPException(status_code=500, detail=error_response.to_dict())

            # Get the latest image
            latest_image_path = await file_service.get_latest_image(
                camera_config.output_directory
            )

            if not latest_image_path:
                error_response = error_service.handle_error(
                    FileNotFoundError("No images found in the output directory"),
                    {
                        "operation": "get_last_picture",
                        "directory": camera_config.output_directory,
                    },
                    request_id,
                )
                raise HTTPException(status_code=404, detail=error_response.to_dict())

            # Read the image file
            try:
                with open(latest_image_path, "rb") as f:
                    image_data = f.read()

                logger.info(f"✅ Last picture retrieved: {latest_image_path}")

                # Add cache-busting headers
                headers = {
                    "Cache-Control": "no-cache, no-store, must-revalidate",
                    "Pragma": "no-cache",
                    "Expires": "0",
                    "X-Request-ID": request_id,
                    "Content-Disposition": f"attachment; filename={os.path.basename(latest_image_path)}",
                }

                return Response(
                    content=image_data,
                    media_type="image/jpeg",
                    headers=headers,
                )

            except Exception as e:
                error_response = error_service.handle_error(
                    e,
                    {"operation": "get_last_picture", "file_path": latest_image_path},
                    request_id,
                )
                raise HTTPException(status_code=500, detail=error_response.to_dict())

        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"❌ Unexpected error getting last picture: {e}")
            error_response = error_service.handle_error(
                e, {"operation": "get_last_picture"}, request_id
            )
            raise HTTPException(status_code=500, detail=error_response.to_dict())

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
                raise HTTPException(status_code=500, detail=error_response.to_dict())

            config = config_service.configuration
            if not config:
                # Return partial configuration with error message
                logger.warning("Configuration not loaded, returning partial config")
                return error_service.create_success_response(
                    {
                        "status": "partial",
                        "message": "Configuration not fully loaded due to validation errors",
                        "camera": None,
                        "image_processing": None,
                        "environment": None,
                    },
                    request_id,
                )

            return error_service.create_success_response(
                {
                    "status": "complete",
                    "camera": {
                        "chdkptp_location": config.camera.chdkptp_location,
                        "output_directory": config.camera.output_directory,
                        "frame_file_name": config.camera.frame_file_name,
                        "default_jpeg_quality": (config.camera.default_jpeg_quality),
                        "max_framerate": config.camera.max_framerate,
                        "command_timeout": config.camera.command_timeout,
                    },
                    "image_processing": {
                        "default_jpeg_quality": (
                            config.image_processing.default_jpeg_quality
                        ),
                        "timestamp_font_scale": (
                            config.image_processing.timestamp_font_scale
                        ),
                        "timestamp_font_thickness": (
                            config.image_processing.timestamp_font_thickness
                        ),
                        "timestamp_color": (config.image_processing.timestamp_color),
                        "timestamp_outline_color": (
                            config.image_processing.timestamp_outline_color
                        ),
                    },
                    "environment": {
                        "environment": config.environment.environment,
                        "debug": config.environment.debug,
                        "log_level": config.environment.log_level,
                        "log_format": config.environment.log_format,
                        "enable_authentication": (
                            config.environment.enable_authentication
                        ),
                        "api_key_required": (config.environment.api_key_required),
                        "max_concurrent_streams": (
                            config.environment.max_concurrent_streams
                        ),
                        "stream_buffer_size": (config.environment.stream_buffer_size),
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
            raise HTTPException(status_code=500, detail=error_response.to_dict())

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
                    {"message": "Configuration reloaded successfully"},
                    request_id,
                )
            else:
                logger.error("❌ Failed to reload configuration")
                error_response = error_service.handle_error(
                    RuntimeError("Failed to reload configuration"),
                    {"operation": "reload_configuration"},
                    request_id,
                )
                raise HTTPException(status_code=500, detail=error_response.to_dict())

        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"❌ Unexpected error reloading configuration: {e}")
            error_response = error_service.handle_error(
                e, {"operation": "reload_configuration"}, request_id
            )
            raise HTTPException(status_code=500, detail=error_response.to_dict())

    return router
