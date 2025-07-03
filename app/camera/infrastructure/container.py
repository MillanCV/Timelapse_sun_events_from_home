import logging
from typing import Optional

from ..domain.entities import CameraConfiguration, ImageProcessingConfiguration
from ..domain.services import CameraControlService
from .subprocess_service import CHDKPTPSubprocessService
from .image_processing_service import OpenCVImageProcessingService
from .file_management_service import LocalFileManagementService
from .refactored_camera_service import RefactoredCHDKPTPCameraService


class CameraContainer:
    """Dependency injection container for camera module."""

    def __init__(self, config: Optional[CameraConfiguration] = None):
        self.config = config or self._create_default_config()
        self.logger = logging.getLogger(__name__)

        # Initialize services
        self._subprocess_service: Optional[CHDKPTPSubprocessService] = None
        self._image_service: Optional[OpenCVImageProcessingService] = None
        self._file_service: Optional[LocalFileManagementService] = None
        self._camera_service: Optional[RefactoredCHDKPTPCameraService] = None

    def _create_default_config(self) -> CameraConfiguration:
        """Create default configuration."""
        return CameraConfiguration(
            chdkptp_location="/home/arrumada/Dev/CanonCameraControl/ChdkPTP",
            output_directory="/home/arrumada/Images",
            frame_file_name="frame.ppm",
            default_jpeg_quality=80,
            max_framerate=8.0,
            command_timeout=30,
        )

    def _create_image_config(self) -> ImageProcessingConfiguration:
        """Create image processing configuration."""
        return ImageProcessingConfiguration(
            default_jpeg_quality=self.config.default_jpeg_quality,
            timestamp_font_scale=0.7,
            timestamp_font_thickness=2,
            timestamp_color=(255, 255, 255),  # white
            timestamp_outline_color=(0, 0, 0),  # black
        )

    @property
    def subprocess_service(self) -> CHDKPTPSubprocessService:
        """Get or create subprocess service."""
        if self._subprocess_service is None:
            self.logger.info("🔧 Creating CHDKPTP subprocess service")
            self._subprocess_service = CHDKPTPSubprocessService(
                self.config.chdkptp_location
            )
        return self._subprocess_service

    @property
    def image_service(self) -> OpenCVImageProcessingService:
        """Get or create image processing service."""
        if self._image_service is None:
            self.logger.info("🖼️ Creating OpenCV image processing service")
            image_config = self._create_image_config()
            self._image_service = OpenCVImageProcessingService(image_config)
        return self._image_service

    @property
    def file_service(self) -> LocalFileManagementService:
        """Get or create file management service."""
        if self._file_service is None:
            self.logger.info("📁 Creating local file management service")
            self._file_service = LocalFileManagementService(
                self.config.output_directory
            )
        return self._file_service

    @property
    def camera_service(self) -> CameraControlService:
        """Get or create camera control service."""
        if self._camera_service is None:
            self.logger.info("📸 Creating refactored camera service")
            self._camera_service = RefactoredCHDKPTPCameraService(
                subprocess_service=self.subprocess_service,
                image_service=self.image_service,
                file_service=self.file_service,
                config=self.config,
            )
        return self._camera_service

    def update_config(self, new_config: CameraConfiguration) -> None:
        """Update configuration and reset services."""
        self.logger.info("🔄 Updating camera configuration")
        self.config = new_config

        # Reset services to force recreation with new config
        self._subprocess_service = None
        self._image_service = None
        self._file_service = None
        self._camera_service = None

    async def initialize(self) -> bool:
        """Initialize the container and validate setup."""
        try:
            self.logger.info("🚀 Initializing camera container")

            # Validate CHDKPTP setup
            if not await self.subprocess_service.validate_executable("chdkptp.sh"):
                self.logger.error("❌ CHDKPTP script not found")
                return False

            # Ensure output directory exists
            if not await self.file_service.ensure_directory_exists(
                self.config.output_directory
            ):
                self.logger.error("❌ Could not create output directory")
                return False

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


# Global container instance
_camera_container: Optional[CameraContainer] = None


def get_camera_container(
    config: Optional[CameraConfiguration] = None,
) -> CameraContainer:
    """Get or create the global camera container instance."""
    global _camera_container

    if _camera_container is None:
        _camera_container = CameraContainer(config)

    return _camera_container


def reset_camera_container() -> None:
    """Reset the global camera container instance."""
    global _camera_container
    _camera_container = None
