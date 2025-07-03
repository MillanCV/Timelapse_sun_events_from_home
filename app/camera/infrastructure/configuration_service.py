import os
import json
import logging
from pathlib import Path
from typing import Optional, Dict, Any
from functools import lru_cache

from ..domain.entities import (
    CameraConfiguration,
    ImageProcessingConfiguration,
    EnvironmentConfiguration,
    ApplicationConfiguration,
    Result,
)


class ConfigurationService:
    """Service for managing application configuration."""

    def __init__(self, config_file_path: Optional[str] = None):
        self.config_file_path = config_file_path
        self.logger = logging.getLogger(__name__)
        self._config: Optional[ApplicationConfiguration] = None

    def _get_env_var(self, key: str, default: Any = None) -> Any:
        """Get environment variable with type conversion."""
        value = os.getenv(key, default)

        if value is None:
            return default

        # If value is the same as default, return it (no environment variable set)
        if value == default:
            return default

        # Convert string values to appropriate types
        if isinstance(default, bool):
            return value.lower() in ("true", "1", "yes", "on")
        elif isinstance(default, int):
            try:
                return int(value)
            except ValueError:
                self.logger.warning(f"Invalid integer value for {key}: {value}")
                return default
        elif isinstance(default, float):
            try:
                return float(value)
            except ValueError:
                self.logger.warning(f"Invalid float value for {key}: {value}")
                return default
        elif isinstance(default, tuple):
            try:
                # Handle tuple values like "255,255,255"
                return tuple(int(x.strip()) for x in value.split(","))
            except ValueError:
                self.logger.warning(f"Invalid tuple value for {key}: {value}")
                return default

        return value

    def _load_from_file(self) -> Dict[str, Any]:
        """Load configuration from file."""
        if not self.config_file_path or not Path(self.config_file_path).exists():
            self.logger.info("No configuration file found, using defaults")
            return {}

        try:
            with open(self.config_file_path, "r") as f:
                config_data = json.load(f)
            self.logger.info(f"Loaded configuration from {self.config_file_path}")
            return config_data
        except Exception as e:
            self.logger.warning(f"Error loading configuration file: {e}")
            return {}

    def _get_camera_config(self, file_config: Dict[str, Any]) -> CameraConfiguration:
        """Create camera configuration from environment and file."""
        return CameraConfiguration(
            chdkptp_location=self._get_env_var(
                "CHDKPTP_LOCATION",
                file_config.get("camera", {}).get(
                    "chdkptp_location", "/home/arrumada/Dev/CanonCameraControl/ChdkPTP"
                ),
            ),
            output_directory=self._get_env_var(
                "CAMERA_OUTPUT_DIRECTORY",
                file_config.get("camera", {}).get(
                    "output_directory", "/home/arrumada/Images"
                ),
            ),
            frame_file_name=self._get_env_var(
                "CAMERA_FRAME_FILE_NAME",
                file_config.get("camera", {}).get("frame_file_name", "frame.ppm"),
            ),
            default_jpeg_quality=self._get_env_var(
                "CAMERA_DEFAULT_JPEG_QUALITY",
                file_config.get("camera", {}).get("default_jpeg_quality", 80),
            ),
            max_framerate=self._get_env_var(
                "CAMERA_MAX_FRAMERATE",
                file_config.get("camera", {}).get("max_framerate", 8.0),
            ),
            command_timeout=self._get_env_var(
                "CAMERA_COMMAND_TIMEOUT",
                file_config.get("camera", {}).get("command_timeout", 30),
            ),
        )

    def _get_image_processing_config(
        self, file_config: Dict[str, Any]
    ) -> ImageProcessingConfiguration:
        """Create image processing configuration from environment and file."""
        return ImageProcessingConfiguration(
            default_jpeg_quality=self._get_env_var(
                "IMAGE_DEFAULT_JPEG_QUALITY",
                file_config.get("image_processing", {}).get("default_jpeg_quality", 80),
            ),
            timestamp_font_scale=self._get_env_var(
                "IMAGE_TIMESTAMP_FONT_SCALE",
                file_config.get("image_processing", {}).get(
                    "timestamp_font_scale", 0.7
                ),
            ),
            timestamp_font_thickness=self._get_env_var(
                "IMAGE_TIMESTAMP_FONT_THICKNESS",
                file_config.get("image_processing", {}).get(
                    "timestamp_font_thickness", 2
                ),
            ),
            timestamp_color=self._get_env_var(
                "IMAGE_TIMESTAMP_COLOR",
                file_config.get("image_processing", {}).get(
                    "timestamp_color", (255, 255, 255)
                ),
            ),
            timestamp_outline_color=self._get_env_var(
                "IMAGE_TIMESTAMP_OUTLINE_COLOR",
                file_config.get("image_processing", {}).get(
                    "timestamp_outline_color", (0, 0, 0)
                ),
            ),
        )

    def _get_environment_config(
        self, file_config: Dict[str, Any]
    ) -> EnvironmentConfiguration:
        """Create environment configuration from environment and file."""
        return EnvironmentConfiguration(
            environment=self._get_env_var(
                "ENVIRONMENT",
                file_config.get("environment", {}).get("environment", "development"),
            ),
            debug=self._get_env_var(
                "DEBUG", file_config.get("environment", {}).get("debug", False)
            ),
            log_level=self._get_env_var(
                "LOG_LEVEL", file_config.get("environment", {}).get("log_level", "INFO")
            ),
            log_format=self._get_env_var(
                "LOG_FORMAT",
                file_config.get("environment", {}).get(
                    "log_format", "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
                ),
            ),
            enable_authentication=self._get_env_var(
                "ENABLE_AUTHENTICATION",
                file_config.get("environment", {}).get("enable_authentication", False),
            ),
            api_key_required=self._get_env_var(
                "API_KEY_REQUIRED",
                file_config.get("environment", {}).get("api_key_required", False),
            ),
            max_concurrent_streams=self._get_env_var(
                "MAX_CONCURRENT_STREAMS",
                file_config.get("environment", {}).get("max_concurrent_streams", 5),
            ),
            stream_buffer_size=self._get_env_var(
                "STREAM_BUFFER_SIZE",
                file_config.get("environment", {}).get(
                    "stream_buffer_size", 1024 * 1024
                ),
            ),
        )

    def load_configuration(self) -> Result[ApplicationConfiguration]:
        """Load and validate application configuration."""
        try:
            self.logger.info("Loading application configuration")

            # Load configuration from file
            file_config = self._load_from_file()

            # Create configuration objects
            camera_config = self._get_camera_config(file_config)
            image_config = self._get_image_processing_config(file_config)
            env_config = self._get_environment_config(file_config)

            # Create complete configuration
            config = ApplicationConfiguration(
                camera=camera_config,
                image_processing=image_config,
                environment=env_config,
            )

            # Validate configuration
            validation_result = config.validate()
            if not validation_result.is_success:
                return validation_result

            self._config = config
            self.logger.info("Configuration loaded and validated successfully")

            return Result.success(config)

        except Exception as e:
            error_msg = f"Error loading configuration: {str(e)}"
            self.logger.error(error_msg)
            return Result.failure(error_msg)

    @property
    def configuration(self) -> Optional[ApplicationConfiguration]:
        """Get the current configuration."""
        if self._config is None:
            result = self.load_configuration()
            if result.is_success:
                self._config = result.value
            else:
                self.logger.error(f"Failed to load configuration: {result.error}")
                return None
        return self._config

    def get_camera_config(self) -> Optional[CameraConfiguration]:
        """Get camera configuration."""
        config = self.configuration
        return config.camera if config else None

    def get_image_processing_config(self) -> Optional[ImageProcessingConfiguration]:
        """Get image processing configuration."""
        config = self.configuration
        return config.image_processing if config else None

    def get_environment_config(self) -> Optional[EnvironmentConfiguration]:
        """Get environment configuration."""
        config = self.configuration
        return config.environment if config else None

    def reload_configuration(self) -> Result[ApplicationConfiguration]:
        """Reload configuration from sources."""
        self._config = None
        return self.load_configuration()

    def export_configuration(self, file_path: str) -> Result[None]:
        """Export current configuration to file."""
        try:
            config = self.configuration
            if not config:
                return Result.failure("No configuration to export")

            # Convert configuration to dictionary
            config_dict = {
                "camera": {
                    "chdkptp_location": config.camera.chdkptp_location,
                    "output_directory": config.camera.output_directory,
                    "frame_file_name": config.camera.frame_file_name,
                    "default_jpeg_quality": config.camera.default_jpeg_quality,
                    "max_framerate": config.camera.max_framerate,
                    "command_timeout": config.camera.command_timeout,
                },
                "image_processing": {
                    "default_jpeg_quality": config.image_processing.default_jpeg_quality,
                    "timestamp_font_scale": config.image_processing.timestamp_font_scale,
                    "timestamp_font_thickness": config.image_processing.timestamp_font_thickness,
                    "timestamp_color": config.image_processing.timestamp_color,
                    "timestamp_outline_color": config.image_processing.timestamp_outline_color,
                },
                "environment": {
                    "environment": config.environment.environment,
                    "debug": config.environment.debug,
                    "log_level": config.environment.log_level,
                    "log_format": config.environment.log_format,
                    "enable_authentication": config.environment.enable_authentication,
                    "api_key_required": config.environment.api_key_required,
                    "max_concurrent_streams": config.environment.max_concurrent_streams,
                    "stream_buffer_size": config.environment.stream_buffer_size,
                },
            }

            # Write to file
            with open(file_path, "w") as f:
                json.dump(config_dict, f, indent=2)

            self.logger.info(f"Configuration exported to {file_path}")
            return Result.success(None)

        except Exception as e:
            error_msg = f"Error exporting configuration: {str(e)}"
            self.logger.error(error_msg)
            return Result.failure(error_msg)


# Global configuration service instance
_configuration_service: Optional[ConfigurationService] = None


@lru_cache(maxsize=1)
def get_configuration_service(
    config_file_path: Optional[str] = None,
) -> ConfigurationService:
    """Get or create the global configuration service instance."""
    global _configuration_service

    if _configuration_service is None:
        _configuration_service = ConfigurationService(config_file_path)

    return _configuration_service


def reset_configuration_service() -> None:
    """Reset the global configuration service instance."""
    global _configuration_service
    _configuration_service = None
