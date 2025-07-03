from dataclasses import dataclass
from datetime import datetime
from typing import Optional, Generic, TypeVar
from enum import Enum


class ResultType(Enum):
    """Result type enumeration."""

    SUCCESS = "success"
    FAILURE = "failure"


T = TypeVar("T")


@dataclass
class Result(Generic[T]):
    """Generic result pattern for operations."""

    is_success: bool
    value: Optional[T] = None
    error: Optional[str] = None
    timestamp: datetime = None

    @classmethod
    def success(cls, value: T) -> "Result[T]":
        """Create a successful result."""
        return cls(is_success=True, value=value, timestamp=datetime.now())

    @classmethod
    def failure(cls, error: str) -> "Result[T]":
        """Create a failed result."""
        return cls(is_success=False, error=error, timestamp=datetime.now())


@dataclass
class CameraShootingResult:
    """Domain entity for camera shooting results."""

    success: bool
    message: str
    shooting_id: Optional[str] = None
    image_path: Optional[str] = None
    timestamp: datetime = None


@dataclass
class CameraCommand:
    """Domain entity for camera commands."""

    command_type: str  # "shoot", "auto_shoot", "burst_shoot", etc.
    parameters: dict
    timestamp: datetime = None


@dataclass
class CameraStatus:
    """Domain entity for camera status."""

    is_connected: bool
    is_recording: bool
    current_mode: Optional[str] = None
    battery_level: Optional[int] = None
    storage_available: Optional[int] = None  # in MB


@dataclass
class LiveViewResult:
    """Domain entity for live view results."""

    success: bool
    message: str
    image_data: Optional[bytes] = None
    image_format: Optional[str] = None  # "jpeg", "ppm", etc.
    timestamp: datetime = None


@dataclass
class LiveViewStream:
    """Domain entity for live view stream configuration."""

    framerate: float = 5.0  # FPS (max: 8 FPS due to camera hardware)
    quality: int = 80  # JPEG quality (1-100), default 80


@dataclass
class CameraConfiguration:
    """Domain entity for camera configuration."""

    chdkptp_location: str
    output_directory: str
    frame_file_name: str = "frame.ppm"
    default_jpeg_quality: int = 80
    max_framerate: float = 8.0
    command_timeout: int = 30  # seconds


@dataclass
class ImageProcessingConfiguration:
    """Domain entity for image processing configuration."""

    default_jpeg_quality: int = 80
    timestamp_font_scale: float = 0.7
    timestamp_font_thickness: int = 2
    timestamp_color: tuple[int, int, int] = (255, 255, 255)  # white
    timestamp_outline_color: tuple[int, int, int] = (0, 0, 0)  # black
