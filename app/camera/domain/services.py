from abc import ABC, abstractmethod

from .entities import (
    CameraStatus,
    TimelapseRecordingParameters,
    CameraShootingParameters,
)


class CameraControlService(ABC):
    """Abstract camera control service."""

    @abstractmethod
    async def start_timelapse_recording(
        self, parameters: TimelapseRecordingParameters
    ) -> bool:
        """Start timelapse recording with given parameters."""
        pass

    @abstractmethod
    async def shoot_camera(self, parameters: CameraShootingParameters) -> bool:
        """Shoot camera with given parameters."""
        pass

    @abstractmethod
    async def get_camera_status(self) -> CameraStatus:
        """Get current camera status."""
        pass

    @abstractmethod
    async def is_camera_connected(self) -> bool:
        """Check if camera is connected."""
        pass


class TimelapseScriptGenerator(ABC):
    """Abstract timelapse script generator."""

    @abstractmethod
    def generate_timelapse_script(
        self, parameters: TimelapseRecordingParameters
    ) -> str:
        """Generate CHDKPTP script for timelapse recording."""
        pass

    @abstractmethod
    def generate_script_file_path(
        self, parameters: TimelapseRecordingParameters
    ) -> str:
        """Generate file path for the script."""
        pass
