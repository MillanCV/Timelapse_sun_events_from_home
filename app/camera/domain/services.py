from abc import ABC, abstractmethod
from typing import AsyncGenerator, Optional
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


class ImageProcessingService(ABC):
    """Abstract image processing service."""

    @abstractmethod
    async def convert_to_jpeg(self, image_data: bytes, quality: int = 80) -> bytes:
        """Convert image data to JPEG format."""
        pass

    @abstractmethod
    async def add_timestamp_overlay(self, image_data: bytes) -> bytes:
        """Add timestamp overlay to image."""
        pass

    @abstractmethod
    async def read_ppm_image(self, file_path: str) -> Optional[bytes]:
        """Read PPM image from file."""
        pass


class FileManagementService(ABC):
    """Abstract file management service."""

    @abstractmethod
    async def get_latest_image(self, directory: str) -> Optional[str]:
        """Get the latest image file from directory."""
        pass

    @abstractmethod
    async def ensure_directory_exists(self, directory: str) -> bool:
        """Ensure directory exists, create if necessary."""
        pass

    @abstractmethod
    async def file_exists(self, file_path: str) -> bool:
        """Check if file exists."""
        pass


class SubprocessService(ABC):
    """Abstract subprocess execution service."""

    @abstractmethod
    async def execute_command(
        self, command: list, working_directory: str
    ) -> tuple[bool, str, str]:
        """Execute command and return (success, stdout, stderr)."""
        pass

    @abstractmethod
    async def validate_executable(self, executable_path: str) -> bool:
        """Validate if executable exists and is accessible."""
        pass
