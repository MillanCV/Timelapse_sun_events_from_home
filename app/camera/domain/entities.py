from dataclasses import dataclass
from datetime import datetime
from typing import Optional, Generic, TypeVar, Dict, Any
from enum import Enum
from pathlib import Path


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


class ErrorType(Enum):
    """Error type enumeration for categorizing errors."""

    VALIDATION_ERROR = "validation_error"
    CONFIGURATION_ERROR = "configuration_error"
    CAMERA_ERROR = "camera_error"
    CHDKPTP_ERROR = "chdkptp_error"
    FILE_ERROR = "file_error"
    NETWORK_ERROR = "network_error"
    PERMISSION_ERROR = "permission_error"
    TIMEOUT_ERROR = "timeout_error"
    RESOURCE_ERROR = "resource_error"
    APPLICATION_ERROR = "application_error"
    UNKNOWN_ERROR = "unknown_error"


class ErrorSeverity(Enum):
    """Error severity enumeration for prioritizing error handling."""

    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


@dataclass
class ErrorDetails:
    """Detailed error information."""

    error_type: ErrorType
    message: str
    code: Optional[str] = None
    details: Optional[Dict[str, Any]] = None
    timestamp: datetime = None
    context: Optional[Dict[str, Any]] = None

    def __post_init__(self):
        if self.timestamp is None:
            self.timestamp = datetime.now()


@dataclass
class ErrorResponse:
    """Standardized error response for API endpoints."""

    success: bool = False
    error_type: str = "unknown_error"
    message: str = "An unexpected error occurred"
    code: Optional[str] = None
    details: Optional[Dict[str, Any]] = None
    timestamp: datetime = None
    request_id: Optional[str] = None
    status_code: int = 500

    def __post_init__(self):
        if self.timestamp is None:
            self.timestamp = datetime.now()

    def to_dict(self) -> Dict[str, Any]:
        """Convert the error response to a dictionary for JSON serialization."""
        return {
            "success": self.success,
            "error_type": self.error_type,
            "message": self.message,
            "code": self.code,
            "details": self.details,
            "timestamp": self.timestamp.isoformat() if self.timestamp else None,
            "request_id": self.request_id,
            "status_code": self.status_code,
        }


# Custom Exceptions
class CameraControlError(Exception):
    """Base exception for camera control errors."""

    def __init__(
        self,
        message: str,
        error_type: ErrorType = ErrorType.CAMERA_ERROR,
        code: Optional[str] = None,
        details: Optional[Dict[str, Any]] = None,
    ):
        super().__init__(message)
        self.error_type = error_type
        self.code = code
        self.details = details or {}
        self.timestamp = datetime.now()


class ConfigurationError(CameraControlError):
    """Exception for configuration-related errors."""

    def __init__(
        self,
        message: str,
        code: Optional[str] = None,
        details: Optional[Dict[str, Any]] = None,
    ):
        super().__init__(message, ErrorType.CONFIGURATION_ERROR, code, details)


class ValidationError(CameraControlError):
    """Exception for validation errors."""

    def __init__(
        self,
        message: str,
        code: Optional[str] = None,
        details: Optional[Dict[str, Any]] = None,
    ):
        super().__init__(message, ErrorType.VALIDATION_ERROR, code, details)


class CHDKPTPError(CameraControlError):
    """Exception for CHDKPTP-related errors."""

    def __init__(
        self,
        message: str,
        code: Optional[str] = None,
        details: Optional[Dict[str, Any]] = None,
    ):
        super().__init__(message, ErrorType.CHDKPTP_ERROR, code, details)


class FileOperationError(CameraControlError):
    """Exception for file operation errors."""

    def __init__(
        self,
        message: str,
        code: Optional[str] = None,
        details: Optional[Dict[str, Any]] = None,
    ):
        super().__init__(message, ErrorType.FILE_ERROR, code, details)


class TimeoutError(CameraControlError):
    """Exception for timeout errors."""

    def __init__(
        self,
        message: str,
        code: Optional[str] = None,
        details: Optional[Dict[str, Any]] = None,
    ):
        super().__init__(message, ErrorType.TIMEOUT_ERROR, code, details)


class PermissionError(CameraControlError):
    """Exception for permission errors."""

    def __init__(
        self,
        message: str,
        code: Optional[str] = None,
        details: Optional[Dict[str, Any]] = None,
    ):
        super().__init__(message, ErrorType.PERMISSION_ERROR, code, details)


class ResourceError(CameraControlError):
    """Exception for resource-related errors."""

    def __init__(
        self,
        message: str,
        code: Optional[str] = None,
        details: Optional[Dict[str, Any]] = None,
    ):
        super().__init__(message, ErrorType.RESOURCE_ERROR, code, details)


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

    # Validation ranges
    MIN_JPEG_QUALITY: int = 1
    MAX_JPEG_QUALITY: int = 100
    MIN_FRAMERATE: float = 0.1
    MAX_FRAMERATE: float = 8.0
    MIN_TIMEOUT: int = 5
    MAX_TIMEOUT: int = 300

    def validate(self) -> Result[None]:
        """Validate configuration values."""
        try:
            # Validate paths
            if not Path(self.chdkptp_location).exists():
                return Result.failure(
                    f"CHDKPTP location does not exist: {self.chdkptp_location}"
                )

            # Validate output directory (create if doesn't exist)
            output_path = Path(self.output_directory)
            if not output_path.exists():
                output_path.mkdir(parents=True, exist_ok=True)

            # Validate JPEG quality
            if not (
                self.MIN_JPEG_QUALITY
                <= self.default_jpeg_quality
                <= self.MAX_JPEG_QUALITY
            ):
                return Result.failure(
                    f"JPEG quality must be between {self.MIN_JPEG_QUALITY} and {self.MAX_JPEG_QUALITY}"
                )

            # Validate framerate
            if not (self.MIN_FRAMERATE <= self.max_framerate <= self.MAX_FRAMERATE):
                return Result.failure(
                    f"Max framerate must be between {self.MIN_FRAMERATE} and {self.MAX_FRAMERATE}"
                )

            # Validate timeout
            if not (self.MIN_TIMEOUT <= self.command_timeout <= self.MAX_TIMEOUT):
                return Result.failure(
                    f"Command timeout must be between {self.MIN_TIMEOUT} and {self.MAX_TIMEOUT} seconds"
                )

            return Result.success(None)

        except Exception as e:
            return Result.failure(f"Configuration validation error: {str(e)}")


@dataclass
class ImageProcessingConfiguration:
    """Domain entity for image processing configuration."""

    default_jpeg_quality: int = 80
    timestamp_font_scale: float = 0.7
    timestamp_font_thickness: int = 2
    timestamp_color: tuple[int, int, int] = (255, 255, 255)  # white
    timestamp_outline_color: tuple[int, int, int] = (0, 0, 0)  # black

    # Validation ranges
    MIN_JPEG_QUALITY: int = 1
    MAX_JPEG_QUALITY: int = 100
    MIN_FONT_SCALE: float = 0.1
    MAX_FONT_SCALE: float = 5.0
    MIN_FONT_THICKNESS: int = 1
    MAX_FONT_THICKNESS: int = 10

    def validate(self) -> Result[None]:
        """Validate image processing configuration."""
        try:
            # Validate JPEG quality
            if not (
                self.MIN_JPEG_QUALITY
                <= self.default_jpeg_quality
                <= self.MAX_JPEG_QUALITY
            ):
                return Result.failure(
                    f"JPEG quality must be between {self.MIN_JPEG_QUALITY} and {self.MAX_JPEG_QUALITY}"
                )

            # Validate font scale
            if not (
                self.MIN_FONT_SCALE <= self.timestamp_font_scale <= self.MAX_FONT_SCALE
            ):
                return Result.failure(
                    f"Font scale must be between {self.MIN_FONT_SCALE} and {self.MAX_FONT_SCALE}"
                )

            # Validate font thickness
            if not (
                self.MIN_FONT_THICKNESS
                <= self.timestamp_font_thickness
                <= self.MAX_FONT_THICKNESS
            ):
                return Result.failure(
                    f"Font thickness must be between {self.MIN_FONT_THICKNESS} and {self.MAX_FONT_THICKNESS}"
                )

            # Validate colors (RGB values 0-255)
            for color_name, color_value in [
                ("timestamp_color", self.timestamp_color),
                ("timestamp_outline_color", self.timestamp_outline_color),
            ]:
                if len(color_value) != 3:
                    return Result.failure(
                        f"{color_name} must have exactly 3 RGB values"
                    )
                for i, component in enumerate(color_value):
                    if not (0 <= component <= 255):
                        return Result.failure(
                            f"{color_name} component {i} must be between 0 and 255"
                        )

            return Result.success(None)

        except Exception as e:
            return Result.failure(
                f"Image processing configuration validation error: {str(e)}"
            )


@dataclass
class EnvironmentConfiguration:
    """Environment-specific configuration."""

    # Environment
    environment: str = "development"
    debug: bool = False

    # Logging
    log_level: str = "INFO"
    log_format: str = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"

    # Security
    enable_authentication: bool = False
    api_key_required: bool = False

    # Performance
    max_concurrent_streams: int = 5
    stream_buffer_size: int = 1024 * 1024  # 1MB

    # Validation ranges
    MIN_CONCURRENT_STREAMS: int = 1
    MAX_CONCURRENT_STREAMS: int = 20
    MIN_BUFFER_SIZE: int = 1024  # 1KB
    MAX_BUFFER_SIZE: int = 10 * 1024 * 1024  # 10MB

    def validate(self) -> Result[None]:
        """Validate environment configuration."""
        try:
            # Validate environment
            valid_environments = ["development", "staging", "production"]
            if self.environment not in valid_environments:
                return Result.failure(
                    f"Environment must be one of: {valid_environments}"
                )

            # Validate log level
            valid_log_levels = ["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"]
            if self.log_level.upper() not in valid_log_levels:
                return Result.failure(f"Log level must be one of: {valid_log_levels}")

            # Validate concurrent streams
            if not (
                self.MIN_CONCURRENT_STREAMS
                <= self.max_concurrent_streams
                <= self.MAX_CONCURRENT_STREAMS
            ):
                return Result.failure(
                    f"Max concurrent streams must be between {self.MIN_CONCURRENT_STREAMS} and {self.MAX_CONCURRENT_STREAMS}"
                )

            # Validate buffer size
            if not (
                self.MIN_BUFFER_SIZE <= self.stream_buffer_size <= self.MAX_BUFFER_SIZE
            ):
                return Result.failure(
                    f"Stream buffer size must be between {self.MIN_BUFFER_SIZE} and {self.MAX_BUFFER_SIZE} bytes"
                )

            return Result.success(None)

        except Exception as e:
            return Result.failure(
                f"Environment configuration validation error: {str(e)}"
            )


@dataclass
class ApplicationConfiguration:
    """Complete application configuration."""

    camera: CameraConfiguration
    image_processing: ImageProcessingConfiguration
    environment: EnvironmentConfiguration

    def validate(self) -> Result[None]:
        """Validate complete application configuration."""
        try:
            # Validate each configuration section
            camera_result = self.camera.validate()
            if not camera_result.is_success:
                return camera_result

            image_result = self.image_processing.validate()
            if not image_result.is_success:
                return image_result

            env_result = self.environment.validate()
            if not env_result.is_success:
                return env_result

            return Result.success(None)

        except Exception as e:
            return Result.failure(
                f"Application configuration validation error: {str(e)}"
            )


@dataclass
class ManualShootingParameters:
    """Domain entity for manual shooting parameters."""

    subject_distance: int  # Subject distance (sd parameter)
    speed: str  # Shutter speed (tv parameter)
    iso: int  # ISO value (isomode parameter)
    shots: int  # Number of shots
    interval: int  # Interval time between shots in seconds

    def __post_init__(self):
        """Validate parameters after initialization."""
        if self.shots <= 0:
            raise ValueError("Number of shots must be greater than 0")
        if self.interval < 0:
            raise ValueError("Interval must be non-negative")
        if self.iso <= 0:
            raise ValueError("ISO value must be greater than 0")
        if self.subject_distance <= 0:
            raise ValueError("Subject distance must be greater than 0")
        if not self.speed:
            raise ValueError("Speed parameter cannot be empty")


@dataclass
class ManualShootingResult:
    """Domain entity for manual shooting results."""

    success: bool
    message: str
    shooting_id: Optional[str] = None
    images_captured: int = 0
    image_paths: list[str] = None
    timestamp: datetime = None

    def __post_init__(self):
        if self.timestamp is None:
            self.timestamp = datetime.now()
        if self.image_paths is None:
            self.image_paths = []
