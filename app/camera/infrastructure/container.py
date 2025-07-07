import logging
from typing import Optional

from ..domain.entities import CameraConfiguration, ImageProcessingConfiguration
from ..domain.services import CameraControlService
from .subprocess_service import CHDKPTPSubprocessService
from .image_processing_service import OpenCVImageProcessingService
from .file_management_service import LocalFileManagementService
from .refactored_camera_service import RefactoredCHDKPTPCameraService
from .configuration_service import get_configuration_service


class CameraContainer:
    """Dependency injection container for camera module."""

    def __init__(self, config_file_path: Optional[str] = None):
        self.config_file_path = config_file_path
        self.logger = logging.getLogger(__name__)

        # Initialize configuration service
        self._config_service = get_configuration_service(config_file_path)

        # Initialize services
        self._subprocess_service: Optional[CHDKPTPSubprocessService] = None
        self._image_service: Optional[OpenCVImageProcessingService] = None
        self._file_service: Optional[LocalFileManagementService] = None
        self._camera_service: Optional[RefactoredCHDKPTPCameraService] = None

    @property
    def configuration_service(self):
        """Get the configuration service."""
        return self._config_service

    @property
    def camera_config(self) -> Optional[CameraConfiguration]:
        """Get camera configuration."""
        return self._config_service.get_camera_config()

    @property
    def image_config(self) -> Optional[ImageProcessingConfiguration]:
        """Get image processing configuration."""
        return self._config_service.get_image_processing_config()

    @property
    def environment_config(self):
        """Get environment configuration."""
        return self._config_service.get_environment_config()

    @property
    def subprocess_service(self) -> Optional[CHDKPTPSubprocessService]:
        """Get or create subprocess service."""
        if self._subprocess_service is None:
            camera_config = self.camera_config
            if not camera_config:
                self.logger.warning("Camera configuration not available")
                return None

            self.logger.info("🔧 Creating CHDKPTP subprocess service")
            self._subprocess_service = CHDKPTPSubprocessService(
                camera_config.chdkptp_location
            )
        return self._subprocess_service

    @property
    def image_service(self) -> Optional[OpenCVImageProcessingService]:
        """Get or create image processing service."""
        if self._image_service is None:
            image_config = self.image_config
            if not image_config:
                self.logger.warning("Image processing configuration not available")
                return None

            self.logger.info("🖼️ Creating OpenCV image processing service")
            self._image_service = OpenCVImageProcessingService(image_config)
        return self._image_service

    @property
    def file_service(self) -> Optional[LocalFileManagementService]:
        """Get or create file management service."""
        if self._file_service is None:
            camera_config = self.camera_config
            if not camera_config:
                self.logger.warning("Camera configuration not available")
                return None

            self.logger.info("📁 Creating local file management service")
            self._file_service = LocalFileManagementService(
                camera_config.output_directory
            )
        return self._file_service

    @property
    def camera_service(self) -> Optional[CameraControlService]:
        """Get or create camera control service."""
        if self._camera_service is None:
            camera_config = self.camera_config
            if not camera_config:
                self.logger.warning("Camera configuration not available")
                return None

            # Check if all required services are available
            subprocess_service = self.subprocess_service
            image_service = self.image_service
            file_service = self.file_service

            if not all([subprocess_service, image_service, file_service]):
                self.logger.warning("Required camera services not available")
                return None

            self.logger.info("📸 Creating refactored camera service")
            self._camera_service = RefactoredCHDKPTPCameraService(
                subprocess_service=subprocess_service,
                image_service=image_service,
                file_service=file_service,
                config=camera_config,
            )
        return self._camera_service

    def reload_configuration(self) -> bool:
        """Reload configuration and reset services."""
        try:
            self.logger.info("🔄 Reloading camera configuration")

            # Reload configuration
            result = self._config_service.reload_configuration()
            if not result.is_success:
                self.logger.error(f"Failed to reload configuration: {result.error}")
                return False

            # Reset services to force recreation with new config
            self._subprocess_service = None
            self._image_service = None
            self._file_service = None
            self._camera_service = None

            self.logger.info("✅ Configuration reloaded successfully")
            return True

        except Exception as e:
            self.logger.error(f"Error reloading configuration: {e}")
            return False

    async def initialize(self) -> bool:
        """Initialize the container and validate setup."""
        try:
            self.logger.info("🚀 Initializing camera container")

            # Load and validate configuration
            result = self._config_service.load_configuration()
            if not result.is_success:
                self.logger.warning(f"Configuration validation failed: {result.error}")
                # Don't fail initialization, just log warning
                return True

            # Try to validate CHDKPTP setup if configuration is available
            subprocess_service = self.subprocess_service
            if subprocess_service:
                if not await subprocess_service.validate_executable("chdkptp.sh"):
                    self.logger.warning("❌ CHDKPTP script not found")
                    # Don't fail initialization, just log warning

            # Try to ensure output directory exists if configuration is available
            file_service = self.file_service
            camera_config = self.camera_config
            if file_service and camera_config:
                if not await file_service.ensure_directory_exists(
                    camera_config.output_directory
                ):
                    self.logger.warning("❌ Could not create output directory")
                    # Don't fail initialization, just log warning

            self.logger.info("✅ Camera container initialized successfully")
            return True

        except Exception as e:
            self.logger.error(f"❌ Error initializing camera container: {e}")
            return False

    async def cleanup(self) -> None:
        """Clean up resources."""
        self.logger.info("🧹 Cleaning up camera container")

        # Stop any active streams
        if self._camera_service:
            await self._camera_service.stop_live_view_stream()

        # Reset services
        self._subprocess_service = None
        self._image_service = None
        self._file_service = None
        self._camera_service = None

        self.logger.info("✅ Camera container cleanup completed")

    def export_configuration(self, file_path: str) -> bool:
        """Export current configuration to file."""
        try:
            result = self._config_service.export_configuration(file_path)
            return result.is_success
        except Exception as e:
            self.logger.error(f"Error exporting configuration: {e}")
            return False


# Global container instance
_camera_container: Optional[CameraContainer] = None


def get_camera_container(config_file_path: Optional[str] = None) -> CameraContainer:
    """Get or create the global camera container instance."""
    global _camera_container

    if _camera_container is None:
        _camera_container = CameraContainer(config_file_path)

    return _camera_container


def reset_camera_container() -> None:
    """Reset the global camera container instance."""
    global _camera_container
    _camera_container = None
