from dataclasses import dataclass
from typing import Optional

from ..domain.entities import CameraCommand
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
