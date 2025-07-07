import logging
import asyncio
from pathlib import Path
from typing import AsyncGenerator
from datetime import datetime

from ..domain.entities import (
    CameraConfiguration,
    CameraShootingResult,
    LiveViewResult,
    LiveViewStream,
    CameraCommand,
)
from ..domain.services import CameraControlService
from .subprocess_service import CHDKPTPSubprocessService
from .image_processing_service import OpenCVImageProcessingService
from .file_management_service import LocalFileManagementService


class RefactoredCHDKPTPCameraService(CameraControlService):
    """Refactored CHDKPTP-based camera service with better separation of concerns."""

    def __init__(
        self,
        subprocess_service: CHDKPTPSubprocessService,
        image_service: OpenCVImageProcessingService,
        file_service: LocalFileManagementService,
        config: CameraConfiguration,
    ):
        self.subprocess_service = subprocess_service
        self.image_service = image_service
        self.file_service = file_service
        self.config = config
        self.logger = logging.getLogger(__name__)
        self._streaming = False
        self._frame_path = Path(config.chdkptp_location) / config.frame_file_name

    async def shoot_camera(self) -> CameraShootingResult:
        """Shoot camera and return the result with image path."""
        try:
            self.logger.info("📸 Starting camera shooting")

            # Validate CHDKPTP setup
            if not await self.subprocess_service.validate_executable("chdkptp.sh"):
                return CameraShootingResult(
                    success=False,
                    message="CHDKPTP script not found",
                    shooting_id=None,
                    image_path=None,
                    timestamp=datetime.now(),
                )

            # Build shooting command
            cmd_args = [
                "-ec",  # connect
                "-erec",  # switch to record mode
                f"-ers {self.config.output_directory}",  # remote shoot
                "-eplay",  # switch to play mode
                "-edisconnect",  # disconnect
            ]

            # Execute command
            (
                success,
                stdout,
                stderr,
            ) = await self.subprocess_service.execute_chdkptp_command(cmd_args)

            if success:
                self.logger.info("📸 Camera shooting completed successfully")

                # Get the latest image
                image_path = await self.file_service.get_latest_image(
                    self.config.output_directory
                )
                shooting_id = f"shooting_{datetime.now().strftime('%Y%m%d_%H%M%S')}"

                return CameraShootingResult(
                    success=True,
                    message="Camera shooting completed",
                    shooting_id=shooting_id,
                    image_path=image_path,
                    timestamp=datetime.now(),
                )
            else:
                self.logger.error(f"📸 Camera shooting failed: {stderr}")
                return CameraShootingResult(
                    success=False,
                    message=f"Camera shooting failed: {stderr}",
                    shooting_id=None,
                    image_path=None,
                    timestamp=datetime.now(),
                )

        except Exception as e:
            self.logger.error(f"📸 Error shooting camera: {e}")
            return CameraShootingResult(
                success=False,
                message=f"Error shooting camera: {str(e)}",
                shooting_id=None,
                image_path=None,
                timestamp=datetime.now(),
            )

    async def execute_command(self, command: CameraCommand) -> CameraShootingResult:
        """Execute a camera command and return the result."""
        try:
            self.logger.info(f"📸 Executing camera command: {command.command_type}")

            if command.command_type == "shoot":
                return await self.shoot_camera()
            elif command.command_type == "auto_shoot":
                return await self._execute_auto_shoot(command.parameters)
            elif command.command_type == "burst_shoot":
                return await self._execute_burst_shoot(command.parameters)
            else:
                return CameraShootingResult(
                    success=False,
                    message=f"Unknown command type: {command.command_type}",
                    shooting_id=None,
                    image_path=None,
                    timestamp=datetime.now(),
                )

        except Exception as e:
            self.logger.error(f"📸 Error executing command: {e}")
            return CameraShootingResult(
                success=False,
                message=f"Error executing command: {str(e)}",
                shooting_id=None,
                image_path=None,
                timestamp=datetime.now(),
            )

    async def take_live_view_snapshot(
        self, include_overlay: bool = True
    ) -> LiveViewResult:
        """Take a live view snapshot and return the image data."""
        try:
            self.logger.info("📸 Starting live view snapshot...")

            # Execute live view command
            cmd_args = [
                "-c",  # connect
                "-erec",  # switch to record mode
                "-elvdumpimg -vp=frame.ppm -count=1",  # live view dump
            ]

            (
                success,
                stdout,
                stderr,
            ) = await self.subprocess_service.execute_chdkptp_command(cmd_args)

            if not success:
                return LiveViewResult(
                    success=False,
                    message=f"Live view command failed: {stderr}",
                    image_data=None,
                    image_format=None,
                    timestamp=datetime.now(),
                )

            # Read and process frame
            frame_data = await self.image_service.read_ppm_image(str(self._frame_path))
            if frame_data is None:
                return LiveViewResult(
                    success=False,
                    message="Failed to read PPM image data",
                    image_data=None,
                    image_format=None,
                    timestamp=datetime.now(),
                )

            # Convert to JPEG with optional timestamp
            if include_overlay:
                jpeg_data = await self.image_service.add_timestamp_overlay(frame_data)
            else:
                jpeg_data = await self.image_service.convert_to_jpeg(
                    frame_data, self.config.default_jpeg_quality
                )

            return LiveViewResult(
                success=True,
                message="Live view snapshot captured successfully",
                image_data=jpeg_data,
                image_format="jpeg",
                timestamp=datetime.now(),
            )

        except Exception as e:
            self.logger.error(f"📸 Error taking live view snapshot: {e}")
            return LiveViewResult(
                success=False,
                message=f"Error taking live view snapshot: {str(e)}",
                image_data=None,
                image_format=None,
                timestamp=datetime.now(),
            )

    async def start_live_view_stream(
        self, config: LiveViewStream
    ) -> AsyncGenerator[LiveViewResult, None]:
        """Start a live view stream and yield image frames."""
        try:
            self.logger.info("🎥 Starting live view stream...")
            self._streaming = True
            frame_count = 0

            while self._streaming:
                try:
                    frame_count += 1
                    self.logger.info(f"🎥 Taking frame {frame_count}...")

                    # Execute live view command
                    cmd_args = [
                        "-c",  # connect
                        "-erec",  # switch to record mode
                        "-elvdumpimg -vp=frame.ppm -count=1",  # live view dump
                    ]

                    (
                        success,
                        stdout,
                        stderr,
                    ) = await self.subprocess_service.execute_chdkptp_command(cmd_args)

                    if not success:
                        self.logger.warning(
                            f"🎥 Frame {frame_count} command failed: {stderr}"
                        )
                        continue

                    # Read frame
                    frame_data = await self.image_service.read_ppm_image(
                        str(self._frame_path)
                    )
                    if frame_data is None:
                        self.logger.warning(f"🎥 Frame {frame_count} failed to read")
                        continue

                    # Convert to JPEG with timestamp overlay
                    jpeg_data = await self.image_service.add_timestamp_overlay(
                        frame_data
                    )

                    yield LiveViewResult(
                        success=True,
                        message=f"Frame {frame_count} captured",
                        image_data=jpeg_data,
                        image_format="jpeg",
                        timestamp=datetime.now(),
                    )

                    # Wait for next frame
                    frame_interval = 1.0 / config.framerate
                    await asyncio.sleep(frame_interval)

                except Exception as e:
                    self.logger.error(
                        f"🎥 Error in live view stream frame {frame_count}: {e}"
                    )
                    yield LiveViewResult(
                        success=False,
                        message=f"Stream error: {str(e)}",
                        image_data=None,
                        image_format=None,
                        timestamp=datetime.now(),
                    )
                    break

        except Exception as e:
            self.logger.error(f"🎥 Error starting live view stream: {e}")
            yield LiveViewResult(
                success=False,
                message=f"Error starting live view stream: {str(e)}",
                image_data=None,
                image_format=None,
                timestamp=datetime.now(),
            )
        finally:
            self._streaming = False
            self.logger.info("🎥 Live view stream stopped")

    async def stop_live_view_stream(self) -> None:
        """Stop the live view stream."""
        self.logger.info("🎥 Stopping live view stream...")
        self._streaming = False

    async def _execute_auto_shoot(self, parameters: dict) -> CameraShootingResult:
        """Execute automatic shooting with parameters."""
        try:
            shots = parameters.get("shots", 1)
            interval = parameters.get("interval", 1.0)
            delay = parameters.get("delay", 0)

            self.logger.info(
                f"📸 Auto shoot: {shots} shots, {interval}s interval, {delay}s delay"
            )

            # Wait for initial delay
            if delay > 0:
                await asyncio.sleep(delay)

            # Take shots
            image_paths = []
            for i in range(shots):
                self.logger.info(f"📸 Taking shot {i + 1}/{shots}")
                result = await self.shoot_camera()

                if result.success and result.image_path:
                    image_paths.append(result.image_path)

                # Wait between shots (except for the last shot)
                if i < shots - 1:
                    await asyncio.sleep(interval)

            # Return the last image path
            final_image_path = image_paths[-1] if image_paths else None
            shooting_id = f"auto_shoot_{datetime.now().strftime('%Y%m%d_%H%M%S')}"

            return CameraShootingResult(
                success=len(image_paths) > 0,
                message=(
                    f"Auto shoot completed: {len(image_paths)}/{shots} shots taken"
                ),
                shooting_id=shooting_id,
                image_path=final_image_path,
                timestamp=datetime.now(),
            )

        except Exception as e:
            self.logger.error(f"📸 Error in auto shoot: {e}")
            return CameraShootingResult(
                success=False,
                message=f"Auto shoot failed: {str(e)}",
                shooting_id=None,
                image_path=None,
                timestamp=datetime.now(),
            )

    async def _execute_burst_shoot(self, parameters: dict) -> CameraShootingResult:
        """Execute burst shooting (rapid fire)."""
        try:
            shots = parameters.get("shots", 3)
            burst_interval = parameters.get("burst_interval", 0.5)

            self.logger.info(
                f"📸 Burst shoot: {shots} shots, {burst_interval}s interval"
            )

            # Take rapid shots
            image_paths = []
            for i in range(shots):
                self.logger.info(f"📸 Burst shot {i + 1}/{shots}")
                result = await self.shoot_camera()

                if result.success and result.image_path:
                    image_paths.append(result.image_path)

                # Short wait between burst shots
                if i < shots - 1:
                    await asyncio.sleep(burst_interval)

            # Return the last image path
            final_image_path = image_paths[-1] if image_paths else None
            shooting_id = f"burst_shoot_{datetime.now().strftime('%Y%m%d_%H%M%S')}"

            return CameraShootingResult(
                success=len(image_paths) > 0,
                message=f"Burst shoot completed: {len(image_paths)}/{shots} shots taken",
                shooting_id=shooting_id,
                image_path=final_image_path,
                timestamp=datetime.now(),
            )

        except Exception as e:
            self.logger.error(f"📸 Error in burst shoot: {e}")
            return CameraShootingResult(
                success=False,
                message=f"Burst shoot failed: {str(e)}",
                shooting_id=None,
                image_path=None,
                timestamp=datetime.now(),
            )
