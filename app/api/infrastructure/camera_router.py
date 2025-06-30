from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Optional, List
from fastapi.responses import FileResponse
import os

from ...camera.application.use_cases import (
    ShootCameraRequest,
    ShootCameraUseCase,
    GetCameraStatusUseCase,
)
from ...camera.infrastructure.chdkptp_camera_service import (
    CHDKPTPCameraService,
    CHDKPTPScriptGenerator,
)


class ShootCameraRequestModel(BaseModel):
    """Pydantic model for camera shooting request."""

    subject_distance: float
    speed: float
    iso_value: int
    shots: int
    interval: float


class ShootCameraResponseModel(BaseModel):
    """Pydantic model for camera shooting response."""

    success: bool
    message: str
    shooting_id: Optional[str] = None
    image_paths: List[str] = []


class CameraStatusResponseModel(BaseModel):
    """Pydantic model for camera status response."""

    is_connected: bool
    is_recording: bool
    current_mode: Optional[str] = None
    battery_level: Optional[int] = None
    storage_available: Optional[int] = None


class CameraSettingsResponseModel(BaseModel):
    """Pydantic model for camera settings response."""

    focal_length: Optional[float] = None
    iso: Optional[int] = None
    shutter_speed: Optional[float] = None
    aperture: Optional[float] = None
    mode: Optional[str] = None  # "rec" or "play"


class SetCameraSettingRequestModel(BaseModel):
    """Pydantic model for setting camera parameters."""

    value: float | int | str


def create_camera_router() -> APIRouter:
    """Create and configure the camera router."""
    router = APIRouter(prefix="/camera", tags=["camera"])

    # Initialize camera dependencies
    script_generator = CHDKPTPScriptGenerator()
    camera_service = CHDKPTPCameraService(script_generator)
    shoot_camera_use_case = ShootCameraUseCase(camera_service)
    get_camera_status_use_case = GetCameraStatusUseCase(camera_service)

    @router.post("/shoot", response_model=ShootCameraResponseModel)
    async def shoot_camera(request: ShootCameraRequestModel):
        """Shoot camera with given parameters."""
        try:
            response = shoot_camera_use_case.execute(
                ShootCameraRequest(
                    subject_distance=request.subject_distance,
                    speed=request.speed,
                    iso_value=request.iso_value,
                    shots=request.shots,
                    interval=request.interval,
                )
            )

            return ShootCameraResponseModel(
                success=response.success,
                message=response.message,
                shooting_id=response.shooting_id,
                image_paths=response.image_paths,
            )
        except Exception as e:
            raise HTTPException(status_code=500, detail=str(e))

    @router.get("/status", response_model=CameraStatusResponseModel)
    async def get_camera_status():
        """Get current camera status."""
        try:
            response = get_camera_status_use_case.execute()
            status = response.camera_status

            return CameraStatusResponseModel(
                is_connected=status.is_connected,
                is_recording=status.is_recording,
                current_mode=status.current_mode,
                battery_level=status.battery_level,
                storage_available=status.storage_available,
            )
        except Exception as e:
            raise HTTPException(status_code=500, detail=str(e))

    @router.get("/settings", response_model=CameraSettingsResponseModel)
    async def get_camera_settings():
        """Get current camera settings (dummy implementation)."""
        # TODO: Implement actual camera settings retrieval
        return CameraSettingsResponseModel(
            focal_length=50.0,
            iso=100,
            shutter_speed=1.0 / 60.0,
            aperture=5.6,
            mode="rec",
        )

    @router.get("/settings/focal_length")
    async def get_focal_length():
        """Get current focal length (dummy implementation)."""
        # TODO: Implement actual focal length retrieval
        return {"focal_length": 50.0}

    @router.post("/settings/focal_length")
    async def set_focal_length(request: SetCameraSettingRequestModel):
        """Set focal length (dummy implementation)."""
        # TODO: Implement actual focal length setting
        if not isinstance(request.value, (int, float)):
            raise HTTPException(status_code=400, detail="Focal length must be numeric")

        return {
            "success": True,
            "message": f"Focal length set to {request.value}mm",
            "focal_length": request.value,
        }

    @router.get("/settings/iso")
    async def get_iso():
        """Get current ISO value (dummy implementation)."""
        # TODO: Implement actual ISO retrieval
        return {"iso": 100}

    @router.post("/settings/iso")
    async def set_iso(request: SetCameraSettingRequestModel):
        """Set ISO value (dummy implementation)."""
        # TODO: Implement actual ISO setting
        if not isinstance(request.value, int):
            raise HTTPException(status_code=400, detail="ISO must be an integer")

        return {
            "success": True,
            "message": f"ISO set to {request.value}",
            "iso": request.value,
        }

    @router.get("/settings/shutter_speed")
    async def get_shutter_speed():
        """Get current shutter speed (dummy implementation)."""
        # TODO: Implement actual shutter speed retrieval
        return {"shutter_speed": 1.0 / 60.0}

    @router.post("/settings/shutter_speed")
    async def set_shutter_speed(request: SetCameraSettingRequestModel):
        """Set shutter speed (dummy implementation)."""
        # TODO: Implement actual shutter speed setting
        if not isinstance(request.value, (int, float)):
            raise HTTPException(status_code=400, detail="Shutter speed must be numeric")

        return {
            "success": True,
            "message": f"Shutter speed set to 1/{request.value}s",
            "shutter_speed": request.value,
        }

    @router.get("/settings/aperture")
    async def get_aperture():
        """Get current aperture value (dummy implementation)."""
        # TODO: Implement actual aperture retrieval
        return {"aperture": 5.6}

    @router.post("/settings/aperture")
    async def set_aperture(request: SetCameraSettingRequestModel):
        """Set aperture value (dummy implementation)."""
        # TODO: Implement actual aperture setting
        if not isinstance(request.value, (int, float)):
            raise HTTPException(status_code=400, detail="Aperture must be numeric")

        return {
            "success": True,
            "message": f"Aperture set to f/{request.value}",
            "aperture": request.value,
        }

    @router.get("/settings/mode")
    async def get_mode():
        """Get current camera mode (dummy implementation)."""
        # TODO: Implement actual mode retrieval
        return {"mode": "rec"}

    @router.post("/settings/mode")
    async def set_mode(request: SetCameraSettingRequestModel):
        """Set camera mode (dummy implementation)."""
        # TODO: Implement actual mode setting
        if not isinstance(request.value, str):
            raise HTTPException(status_code=400, detail="Mode must be a string")

        if request.value not in ["rec", "play"]:
            raise HTTPException(status_code=400, detail="Mode must be 'rec' or 'play'")

        return {
            "success": True,
            "message": f"Camera mode set to {request.value}",
            "mode": request.value,
        }

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

    @router.post("/test-shoot")
    async def test_camera_shoot():
        """Test endpoint to verify camera functionality with minimal parameters."""
        try:
            # Use minimal test parameters
            response = shoot_camera_use_case.execute(
                ShootCameraRequest(
                    subject_distance=1.0,  # 1 meter
                    speed=1.0 / 60.0,  # 1/60 second
                    iso_value=100,  # ISO 100
                    shots=1,  # Just 1 shot
                    interval=1.0,  # 1 second interval
                )
            )

            return {
                "success": response.success,
                "message": response.message,
                "shooting_id": response.shooting_id,
                "image_paths": response.image_paths,
                "test_parameters": {
                    "subject_distance": 1.0,
                    "speed": "1/60s",
                    "iso": 100,
                    "shots": 1,
                    "interval": 1.0,
                },
            }
        except Exception as e:
            raise HTTPException(status_code=500, detail=str(e))

    return router
