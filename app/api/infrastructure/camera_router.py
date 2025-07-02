from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Optional, Dict, Any
from fastapi.responses import FileResponse
import os

from ...camera.application.use_cases import (
    ShootCameraUseCase,
    ExecuteCommandUseCase,
    ExecuteCommandRequest,
)
from ...camera.infrastructure.chdkptp_camera_service import (
    CHDKPTPCameraService,
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


def create_camera_router() -> APIRouter:
    """Create and configure the camera router."""
    router = APIRouter(prefix="/camera", tags=["camera"])

    # Initialize camera dependencies
    camera_service = CHDKPTPCameraService()
    shoot_camera_use_case = ShootCameraUseCase(camera_service)
    execute_command_use_case = ExecuteCommandUseCase(camera_service)

    @router.post("/shoot", response_model=ShootCameraResponseModel)
    async def shoot_camera():
        """Shoot camera and return the image path."""
        try:
            response = await shoot_camera_use_case.execute()

            return ShootCameraResponseModel(
                success=response.success,
                message=response.message,
                shooting_id=response.shooting_id,
                image_path=response.image_path,
            )
        except Exception as e:
            raise HTTPException(status_code=500, detail=str(e))

    @router.post("/command", response_model=ExecuteCommandResponseModel)
    async def execute_command(request: ExecuteCommandRequestModel):
        """Execute a camera command."""
        try:
            response = await execute_command_use_case.execute(
                ExecuteCommandRequest(
                    command_type=request.command_type,
                    parameters=request.parameters,
                )
            )

            return ExecuteCommandResponseModel(
                success=response.success,
                message=response.message,
                shooting_id=response.shooting_id,
                image_path=response.image_path,
            )
        except Exception as e:
            raise HTTPException(status_code=500, detail=str(e))

    @router.get("/images/{image_path:path}")
    async def get_image(image_path: str):
        """Serve a captured image."""
        try:
            # Construct the full path to the image
            full_path = f"/home/arrumada/Images/{image_path}"

            if not os.path.exists(full_path):
                raise HTTPException(status_code=404, detail="Image not found")

            return FileResponse(full_path)
        except Exception as e:
            raise HTTPException(status_code=500, detail=str(e))

    return router
