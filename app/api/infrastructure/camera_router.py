from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Optional, Dict, Any, List
from fastapi.responses import FileResponse
import os
from datetime import datetime

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

    @router.get("/last-picture")
    async def get_last_picture():
        """Get the last picture taken by the camera as a file download."""
        try:
            # Get the latest image from the camera service
            image_path = camera_service._get_latest_image()

            if not image_path:
                raise HTTPException(status_code=404, detail="No pictures found")

            # Construct the full path to the image
            full_path = f"/home/arrumada/Images/{image_path}"

            if not os.path.exists(full_path):
                raise HTTPException(status_code=404, detail="Image file not found")

            # Return the image file directly
            return FileResponse(
                full_path,
                # Adjust based on actual image format
                media_type="image/jpeg",
                filename=image_path,
            )

        except HTTPException:
            # Re-raise HTTP exceptions as-is
            raise
        except Exception as e:
            raise HTTPException(status_code=500, detail=str(e))

    @router.get("/images", response_model=ListImagesResponseModel)
    async def list_images():
        """List all images in the camera output directory."""
        try:
            # Look for common image extensions
            image_extensions = [".jpg", ".jpeg", ".cr2", ".raw"]
            images = []

            output_directory = camera_service.output_directory

            if output_directory.exists():
                for ext in image_extensions:
                    for file_path in output_directory.glob(f"*{ext}"):
                        try:
                            # Get file stats
                            stat = file_path.stat()

                            # Create image info
                            image_info = ImageInfoModel(
                                filename=file_path.name,
                                size_bytes=stat.st_size,
                                modified_time=datetime.fromtimestamp(
                                    stat.st_mtime
                                ).isoformat(),
                                image_url=f"/camera/images/{file_path.name}",
                            )
                            images.append(image_info)
                        except Exception:
                            # Skip files that can't be read
                            continue

                # Sort by modification time (newest first)
                images.sort(key=lambda x: x.modified_time, reverse=True)

                return ListImagesResponseModel(
                    success=True,
                    message=f"Found {len(images)} images",
                    images=images,
                    total_count=len(images),
                )
            else:
                return ListImagesResponseModel(
                    success=False,
                    message="Output directory not found",
                    images=[],
                    total_count=0,
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
