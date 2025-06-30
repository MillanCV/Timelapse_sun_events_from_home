from dataclasses import dataclass
from datetime import datetime
from typing import Optional, List

from ..domain.entities import (
    CameraStatus,
    TimelapseRecordingParameters,
    CameraShootingParameters,
)
from ..domain.services import CameraControlService, TimelapseScriptGenerator


@dataclass
class StartTimelapseRecordingRequest:
    """Request for starting timelapse recording."""

    shots: int
    interval_seconds: float
    output_directory: str
    period_type: str
    start_time: datetime
    end_time: datetime


@dataclass
class StartTimelapseRecordingResponse:
    """Response for starting timelapse recording."""

    success: bool
    message: str
    recording_id: Optional[str] = None


@dataclass
class ShootCameraRequest:
    """Request for shooting camera."""

    subject_distance: float
    speed: float
    iso_value: int
    shots: int
    interval: float


@dataclass
class ShootCameraResponse:
    """Response for shooting camera."""

    success: bool
    message: str
    shooting_id: Optional[str] = None
    image_paths: List[str] = None


@dataclass
class GetCameraStatusResponse:
    """Response for getting camera status."""

    camera_status: CameraStatus


class StartTimelapseRecordingUseCase:
    """Use case for starting timelapse recording."""

    def __init__(
        self,
        camera_control_service: CameraControlService,
        script_generator: TimelapseScriptGenerator,
    ):
        self.camera_control_service = camera_control_service
        self.script_generator = script_generator

    async def execute(
        self, request: StartTimelapseRecordingRequest
    ) -> StartTimelapseRecordingResponse:
        """Execute the use case."""
        try:
            # Check if camera is connected
            if not await self.camera_control_service.is_camera_connected():
                return StartTimelapseRecordingResponse(
                    success=False,
                    message="Camera is not connected",
                )

            # Create recording parameters
            parameters = TimelapseRecordingParameters(
                shots=request.shots,
                interval_seconds=request.interval_seconds,
                output_directory=request.output_directory,
                period_type=request.period_type,
                start_time=request.start_time,
                end_time=request.end_time,
            )

            # Start recording
            success = await self.camera_control_service.start_timelapse_recording(
                parameters
            )

            if success:
                return StartTimelapseRecordingResponse(
                    success=True,
                    message=f"Timelapse recording started for {request.period_type}",
                    recording_id=(
                        f"{request.period_type}_"
                        f"{request.start_time.strftime('%Y%m%d_%H%M%S')}"
                    ),
                )
            else:
                return StartTimelapseRecordingResponse(
                    success=False,
                    message="Failed to start timelapse recording",
                )

        except Exception as e:
            return StartTimelapseRecordingResponse(
                success=False,
                message=f"Error starting timelapse recording: {str(e)}",
            )


class ShootCameraUseCase:
    """Use case for shooting camera."""

    def __init__(self, camera_control_service: CameraControlService):
        self.camera_control_service = camera_control_service

    async def execute(self, request: ShootCameraRequest) -> ShootCameraResponse:
        """Execute the use case."""
        try:
            # Check if camera is connected
            # if not await self.camera_control_service.is_camera_connected():
            #    return ShootCameraResponse(
            #        success=False,
            #        message="Camera is not connected",
            #    )

            # Create shooting parameters
            parameters = CameraShootingParameters(
                subject_distance=request.subject_distance,
                speed=request.speed,
                iso_value=request.iso_value,
                shots=request.shots,
                interval=request.interval,
            )

            # Shoot camera
            result = await self.camera_control_service.shoot_camera(parameters)

            return ShootCameraResponse(
                success=result.success,
                message=result.message,
                shooting_id=result.shooting_id,
                image_paths=result.image_paths,
            )

        except Exception as e:
            return ShootCameraResponse(
                success=False,
                message=f"Error shooting camera: {str(e)}",
            )


class GetCameraStatusUseCase:
    """Use case for getting camera status."""

    def __init__(self, camera_control_service: CameraControlService):
        self.camera_control_service = camera_control_service

    async def execute(self) -> GetCameraStatusResponse:
        """Execute the use case."""
        try:
            camera_status = await self.camera_control_service.get_camera_status()
            return GetCameraStatusResponse(camera_status=camera_status)
        except Exception:
            # Return a default status with error indication
            return GetCameraStatusResponse(
                camera_status=CameraStatus(
                    is_connected=False,
                    is_recording=False,
                    current_mode="error",
                )
            )
