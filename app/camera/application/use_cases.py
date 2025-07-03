from dataclasses import dataclass
from typing import Optional, AsyncGenerator
import logging

from ..domain.entities import CameraCommand, LiveViewResult, LiveViewStream, Result
from ..domain.services import CameraControlService


@dataclass
class ShootCameraResponse:
    """Response for shooting camera."""

    success: bool
    message: str
    shooting_id: Optional[str] = None
    image_path: Optional[str] = None


@dataclass
class ExecuteCommandRequest:
    """Request for executing a camera command."""

    command_type: str
    parameters: dict


@dataclass
class ExecuteCommandResponse:
    """Response for executing a camera command."""

    success: bool
    message: str
    shooting_id: Optional[str] = None
    image_path: Optional[str] = None


@dataclass
class TakeLiveViewSnapshotRequest:
    """Request for taking a live view snapshot."""

    include_overlay: bool = True


@dataclass
class TakeLiveViewSnapshotResponse:
    """Response for taking a live view snapshot."""

    success: bool
    message: str
    image_data: Optional[bytes] = None
    image_format: Optional[str] = None


@dataclass
class StartLiveViewStreamRequest:
    """Request for starting a live view stream."""

    framerate: float = 5.0
    quality: int = 80


class ShootCameraUseCase:
    """Use case for shooting camera."""

    def __init__(self, camera_control_service: CameraControlService):
        self.camera_control_service = camera_control_service
        self.logger = logging.getLogger(__name__)

    async def execute(self) -> ShootCameraResponse:
        """Execute the use case."""
        try:
            self.logger.info("Executing shoot camera use case")

            # Shoot camera
            result = await self.camera_control_service.shoot_camera()

            return ShootCameraResponse(
                success=result.success,
                message=result.message,
                shooting_id=result.shooting_id,
                image_path=result.image_path,
            )

        except Exception as e:
            self.logger.error(f"Error in shoot camera use case: {e}")
            return ShootCameraResponse(
                success=False,
                message=f"Error shooting camera: {str(e)}",
            )


class ExecuteCommandUseCase:
    """Use case for executing camera commands."""

    def __init__(self, camera_control_service: CameraControlService):
        self.camera_control_service = camera_control_service
        self.logger = logging.getLogger(__name__)

    def _validate_command(self, request: ExecuteCommandRequest) -> Result[None]:
        """Validate command request."""
        if not request.command_type:
            return Result.failure("Command type is required")

        valid_commands = {"shoot", "auto_shoot", "burst_shoot"}
        if request.command_type not in valid_commands:
            return Result.failure(f"Invalid command type: {request.command_type}")

        return Result.success(None)

    async def execute(self, request: ExecuteCommandRequest) -> ExecuteCommandResponse:
        """Execute the use case."""
        try:
            self.logger.info(f"Executing command use case: {request.command_type}")

            # Validate command
            validation_result = self._validate_command(request)
            if not validation_result.is_success:
                return ExecuteCommandResponse(
                    success=False, message=validation_result.error
                )

            # Create camera command
            command = CameraCommand(
                command_type=request.command_type,
                parameters=request.parameters,
            )

            # Execute command
            result = await self.camera_control_service.execute_command(command)

            return ExecuteCommandResponse(
                success=result.success,
                message=result.message,
                shooting_id=result.shooting_id,
                image_path=result.image_path,
            )

        except Exception as e:
            self.logger.error(f"Error in execute command use case: {e}")
            return ExecuteCommandResponse(
                success=False,
                message=f"Error executing command: {str(e)}",
            )


class TakeLiveViewSnapshotUseCase:
    """Use case for taking a live view snapshot."""

    def __init__(self, camera_control_service: CameraControlService):
        self.camera_control_service = camera_control_service
        self.logger = logging.getLogger(__name__)

    async def execute(
        self, request: TakeLiveViewSnapshotRequest
    ) -> TakeLiveViewSnapshotResponse:
        """Execute the use case."""
        try:
            self.logger.info("Executing take live view snapshot use case")

            # Take live view snapshot
            result = await self.camera_control_service.take_live_view_snapshot(
                include_overlay=request.include_overlay
            )

            return TakeLiveViewSnapshotResponse(
                success=result.success,
                message=result.message,
                image_data=result.image_data,
                image_format=result.image_format,
            )

        except Exception as e:
            self.logger.error(f"Error in take live view snapshot use case: {e}")
            return TakeLiveViewSnapshotResponse(
                success=False,
                message=f"Error taking live view snapshot: {str(e)}",
                image_data=None,
                image_format=None,
            )


class StartLiveViewStreamUseCase:
    """Use case for starting a live view stream."""

    def __init__(self, camera_control_service: CameraControlService):
        self.camera_control_service = camera_control_service
        self.logger = logging.getLogger(__name__)

    def _validate_stream_config(
        self, request: StartLiveViewStreamRequest
    ) -> Result[None]:
        """Validate stream configuration."""
        if request.framerate <= 0:
            return Result.failure("Framerate must be greater than 0")

        if request.framerate > 8.0:
            return Result.failure(
                "Framerate cannot exceed 8.0 FPS due to hardware limitations"
            )

        if request.quality < 1 or request.quality > 100:
            return Result.failure("Quality must be between 1 and 100")

        return Result.success(None)

    async def execute(
        self, request: StartLiveViewStreamRequest
    ) -> AsyncGenerator[LiveViewResult, None]:
        """Execute the use case."""
        try:
            self.logger.info("Executing start live view stream use case")

            # Validate configuration
            validation_result = self._validate_stream_config(request)
            if not validation_result.is_success:
                yield LiveViewResult(
                    success=False,
                    message=validation_result.error,
                    image_data=None,
                    image_format=None,
                )
                return

            # Create live view stream configuration with parameters
            config = LiveViewStream(
                framerate=request.framerate, quality=request.quality
            )

            # Start live view stream
            async for result in self.camera_control_service.start_live_view_stream(
                config
            ):
                yield result

        except Exception as e:
            self.logger.error(f"Error in start live view stream use case: {e}")
            # Yield error result
            yield LiveViewResult(
                success=False,
                message=f"Error starting live view stream: {str(e)}",
                image_data=None,
                image_format=None,
            )
