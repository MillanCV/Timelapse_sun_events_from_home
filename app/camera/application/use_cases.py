from dataclasses import dataclass
from typing import Optional, AsyncGenerator

from ..domain.entities import CameraCommand, LiveViewResult, LiveViewStream
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

    # Simplified request - no parameters needed
    pass


class ShootCameraUseCase:
    """Use case for shooting camera."""

    def __init__(self, camera_control_service: CameraControlService):
        self.camera_control_service = camera_control_service

    async def execute(self) -> ShootCameraResponse:
        """Execute the use case."""
        try:
            # Shoot camera
            result = await self.camera_control_service.shoot_camera()

            return ShootCameraResponse(
                success=result.success,
                message=result.message,
                shooting_id=result.shooting_id,
                image_path=result.image_path,
            )

        except Exception as e:
            return ShootCameraResponse(
                success=False,
                message=f"Error shooting camera: {str(e)}",
            )


class ExecuteCommandUseCase:
    """Use case for executing camera commands."""

    def __init__(self, camera_control_service: CameraControlService):
        self.camera_control_service = camera_control_service

    async def execute(self, request: ExecuteCommandRequest) -> ExecuteCommandResponse:
        """Execute the use case."""
        try:
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
            return ExecuteCommandResponse(
                success=False,
                message=f"Error executing command: {str(e)}",
            )


class TakeLiveViewSnapshotUseCase:
    """Use case for taking a live view snapshot."""

    def __init__(self, camera_control_service: CameraControlService):
        self.camera_control_service = camera_control_service

    async def execute(
        self, request: TakeLiveViewSnapshotRequest
    ) -> TakeLiveViewSnapshotResponse:
        """Execute the use case."""
        try:
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

    async def execute(
        self, request: StartLiveViewStreamRequest
    ) -> AsyncGenerator[LiveViewResult, None]:
        """Execute the use case."""
        try:
            # Create simple live view stream configuration
            config = LiveViewStream()

            # Start live view stream
            async for result in self.camera_control_service.start_live_view_stream(
                config
            ):
                yield result

        except Exception as e:
            # Yield error result
            yield LiveViewResult(
                success=False,
                message=f"Error starting live view stream: {str(e)}",
                image_data=None,
                image_format=None,
            )
