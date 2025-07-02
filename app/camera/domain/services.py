from abc import ABC, abstractmethod
from typing import AsyncGenerator
from .entities import (
    CameraShootingResult,
    CameraCommand,
    LiveViewResult,
    LiveViewStream,
)


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

    @abstractmethod
    async def take_live_view_snapshot(
        self, include_overlay: bool = True
    ) -> LiveViewResult:
        """Take a live view snapshot and return the image data."""
        pass

    @abstractmethod
    async def start_live_view_stream(
        self, config: LiveViewStream
    ) -> AsyncGenerator[LiveViewResult, None]:
        """Start a live view stream and yield image frames."""
        pass

    @abstractmethod
    async def stop_live_view_stream(self) -> None:
        """Stop the live view stream."""
        pass
