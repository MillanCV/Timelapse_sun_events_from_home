from abc import ABC, abstractmethod
from .entities import CameraShootingResult, CameraCommand


class CameraControlService(ABC):
    """Abstract camera control service."""

    @abstractmethod
    async def shoot_camera(self) -> CameraShootingResult:
        """Shoot camera and return the result with image path."""
        pass

    @abstractmethod
    async def execute_command(self, command: CameraCommand) -> CameraShootingResult:
        """Execute a camera command and return the result."""
        pass
