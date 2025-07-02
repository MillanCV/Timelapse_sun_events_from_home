import asyncio
import logging
import os
import subprocess
import cv2
import numpy as np
from pathlib import Path
from typing import Optional, AsyncGenerator
from datetime import datetime

from ..domain.entities import (
    CameraShootingResult,
    CameraCommand,
    LiveViewResult,
    LiveViewStream,
)
from ..domain.services import CameraControlService


class CHDKPTPCameraService(CameraControlService):
    """CHDKPTP camera control service implementation."""

    def __init__(
        self,
        chdkptp_location: str = ("/home/arrumada/Dev/CanonCameraControl/ChdkPTP"),
        output_directory: str = "/home/arrumada/Images",
    ):
        self.chdkptp_location = Path(chdkptp_location)
        self.output_directory = Path(output_directory)
        self.logger = logging.getLogger(__name__)
        self._streaming = False
        self._frame_path = self.chdkptp_location / "frame.ppm"

    async def shoot_camera(self) -> CameraShootingResult:
        """Shoot camera and return the result with image path."""
        try:
            self.logger.info("Starting camera shooting")

            # Build CHDKPTP command using the simpler format
            chdkptp_script = self.chdkptp_location / "chdkptp.sh"

            if not chdkptp_script.exists():
                self.logger.error(f"CHDKPTP script not found: {chdkptp_script}")
                return CameraShootingResult(
                    success=False,
                    message="CHDKPTP script not found",
                    shooting_id=None,
                    image_path=None,
                    timestamp=datetime.now(),
                )

            # Use the simpler command format: connect, rec, rs, play, disconnect
            cmd = [
                "sudo",
                str(chdkptp_script),
                "-ec",  # connect
                "-erec",  # switch to record mode
                f"-ers {self.output_directory}",  # remote shoot
                "-eplay",  # switch to play mode
                "-edisconnect",  # disconnect
            ]

            self.logger.info(f"Executing camera shooting command: {' '.join(cmd)}")

            result = await self._run_chdkptp_command(cmd)

            if result.returncode == 0:
                self.logger.info("Camera shooting completed successfully")

                # Get the latest image from the output directory
                image_path = self._get_latest_image()
                shooting_id = f"shooting_{datetime.now().strftime('%Y%m%d_%H%M%S')}"

                self.logger.info(f"shoot_camera, image_path: {image_path}")

                return CameraShootingResult(
                    success=True,
                    message="Camera shooting completed",
                    shooting_id=shooting_id,
                    image_path=image_path,
                    timestamp=datetime.now(),
                )
            else:
                self.logger.error(f"Camera shooting failed: {result.stderr}")
                return CameraShootingResult(
                    success=False,
                    message=f"Camera shooting failed: {result.stderr}",
                    shooting_id=None,
                    image_path=None,
                    timestamp=datetime.now(),
                )

        except Exception as e:
            self.logger.error(f"Error shooting camera: {e}")
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
            self.logger.info(f"Executing camera command: {command.command_type}")

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
            self.logger.error(f"Error executing command: {e}")
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
            self.logger.info("Taking live view snapshot...")

            # Build CHDKPTP command for live view snapshot
            cmd = [
                "-c",  # connect
                "-erec",  # switch to record mode
            ]

            if include_overlay:
                cmd.extend(["-e", "lvdumpimg -vp=frame.ppm -bm=overlay.pam -count=1"])
            else:
                cmd.extend(["-e", "lvdumpimg -vp=frame.ppm -count=1"])

            # Execute the command
            result = await self._run_chdkptp_command(cmd)

            if result.returncode == 0:
                # Read the PPM image
                image_data = await self._read_ppm_image()

                if image_data:
                    # Convert to JPEG
                    jpeg_data = await self._convert_to_jpeg(image_data)

                    return LiveViewResult(
                        success=True,
                        message="Live view snapshot captured successfully",
                        image_data=jpeg_data,
                        image_format="jpeg",
                        timestamp=datetime.now(),
                    )
                else:
                    return LiveViewResult(
                        success=False,
                        message="Failed to read PPM image data",
                        image_data=None,
                        image_format=None,
                        timestamp=datetime.now(),
                    )
            else:
                return LiveViewResult(
                    success=False,
                    message=f"Live view snapshot failed: {result.stderr}",
                    image_data=None,
                    image_format=None,
                    timestamp=datetime.now(),
                )

        except Exception as e:
            self.logger.error(f"Error taking live view snapshot: {e}")
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
            self.logger.info("Starting live view stream...")
            self._streaming = True

            # Connect to camera
            connect_result = await self._run_chdkptp_command(["-c", "-erec"])
            if connect_result.returncode != 0:
                yield LiveViewResult(
                    success=False,
                    message="Failed to connect to camera for live view",
                    image_data=None,
                    image_format=None,
                    timestamp=datetime.now(),
                )
                return

            while self._streaming:
                try:
                    # Take snapshot
                    snapshot_result = await self.take_live_view_snapshot(
                        include_overlay=config.include_overlay
                    )

                    if snapshot_result.success:
                        yield snapshot_result
                    else:
                        self.logger.warning(
                            f"Snapshot failed: {snapshot_result.message}"
                        )

                    # Wait for next frame
                    await asyncio.sleep(1.0 / config.fps)

                except Exception as e:
                    self.logger.error(f"Error in live view stream: {e}")
                    yield LiveViewResult(
                        success=False,
                        message=f"Stream error: {str(e)}",
                        image_data=None,
                        image_format=None,
                        timestamp=datetime.now(),
                    )
                    break

        except Exception as e:
            self.logger.error(f"Error starting live view stream: {e}")
            yield LiveViewResult(
                success=False,
                message=f"Error starting live view stream: {str(e)}",
                image_data=None,
                image_format=None,
                timestamp=datetime.now(),
            )
        finally:
            self._streaming = False
            self.logger.info("Live view stream stopped")

    async def stop_live_view_stream(self) -> None:
        """Stop the live view stream."""
        self.logger.info("Stopping live view stream...")
        self._streaming = False

    async def _read_ppm_image(self) -> Optional[np.ndarray]:
        """Read a PPM image from the frame file."""
        try:
            if not self._frame_path.exists():
                self.logger.warning("Frame file not found")
                return None

            # Read PPM file
            image = cv2.imread(str(self._frame_path))
            if image is None:
                self.logger.warning("Could not read PPM image")
                return None

            return image

        except Exception as e:
            self.logger.error(f"Error reading PPM image: {e}")
            return None

    async def _convert_to_jpeg(self, image: np.ndarray, quality: int = 80) -> bytes:
        """Convert numpy image to JPEG bytes."""
        try:
            # Encode to JPEG
            encode_params = [cv2.IMWRITE_JPEG_QUALITY, quality]
            success, jpeg_data = cv2.imencode(".jpg", image, encode_params)

            if success:
                return jpeg_data.tobytes()
            else:
                raise Exception("Failed to encode JPEG")

        except Exception as e:
            self.logger.error(f"Error converting to JPEG: {e}")
            raise

    async def _execute_auto_shoot(self, parameters: dict) -> CameraShootingResult:
        """Execute automatic shooting with parameters."""
        try:
            # Extract parameters with defaults
            shots = parameters.get("shots", 1)
            interval = parameters.get("interval", 1.0)  # seconds
            delay = parameters.get("delay", 0)  # seconds before first shot

            self.logger.info(
                f"Auto shoot: {shots} shots, {interval}s interval, {delay}s delay"
            )

            # Wait for initial delay if specified
            if delay > 0:
                self.logger.info(f"Waiting {delay} seconds before shooting...")
                await asyncio.sleep(delay)

            # Take shots
            image_paths = []
            for i in range(shots):
                self.logger.info(f"Taking shot {i + 1}/{shots}")

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
                message=f"Auto shoot completed: {len(image_paths)}/{shots} shots taken",
                shooting_id=shooting_id,
                image_path=final_image_path,
                timestamp=datetime.now(),
            )

        except Exception as e:
            self.logger.error(f"Error in auto shoot: {e}")
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
            # Extract parameters with defaults
            shots = parameters.get("shots", 3)
            burst_interval = parameters.get("burst_interval", 0.5)  # seconds

            self.logger.info(f"Burst shoot: {shots} shots, {burst_interval}s interval")

            # Take rapid shots
            image_paths = []
            for i in range(shots):
                self.logger.info(f"Burst shot {i + 1}/{shots}")

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
            self.logger.error(f"Error in burst shoot: {e}")
            return CameraShootingResult(
                success=False,
                message=f"Burst shoot failed: {str(e)}",
                shooting_id=None,
                image_path=None,
                timestamp=datetime.now(),
            )

    def _get_latest_image(self) -> Optional[str]:
        """Get the latest image from the output directory."""
        try:
            # Look for common image extensions
            image_extensions = [".jpg", ".jpeg", ".cr2", ".raw"]
            image_paths = []

            # Get all files in the output directory
            if self.output_directory.exists():
                for ext in image_extensions:
                    image_paths.extend(
                        [str(f) for f in self.output_directory.glob(f"*{ext}")]
                    )

                # Sort by modification time (newest first) and return the latest
                image_paths.sort(key=lambda x: os.path.getmtime(x), reverse=True)

                # Return the most recent image
                self.logger.info(f"_get_latest_image: {image_paths}")
                return image_paths[0] if image_paths else None

            return None
        except Exception as e:
            self.logger.error(f"Error getting latest image: {e}")
            return None

    async def _run_chdkptp_command(self, cmd: list) -> subprocess.CompletedProcess:
        """Run CHDKPTP command asynchronously."""
        self.logger.info(f"🔧 _run_chdkptp_command called with: {cmd}")
        self.logger.info(f"🔧 Current working directory: {os.getcwd()}")
        self.logger.info(f"🔧 CHDKPTP location: {self.chdkptp_location}")

        # Change to CHDKPTP directory
        original_cwd = os.getcwd()
        os.chdir(self.chdkptp_location)
        self.logger.info(f"🔧 Changed to directory: {os.getcwd()}")

        try:
            # Check if this is a full command or just arguments
            if len(cmd) > 0 and not cmd[0].startswith("sudo"):
                # This is just arguments, need to build the full command
                chdkptp_script = (
                    self.chdkptp_location / "chdkptp.sh"
                )  # Use absolute path
                self.logger.info(f"🔧 Looking for script at: {chdkptp_script}")

                if not chdkptp_script.exists():
                    self.logger.error(
                        f"🔧 CHDKPTP script not found at: {chdkptp_script}"
                    )
                    raise FileNotFoundError(
                        f"CHDKPTP script not found: {chdkptp_script}"
                    )

                full_cmd = ["sudo", str(chdkptp_script)] + cmd
                self.logger.info(f"🔧 Built full command: {full_cmd}")
            else:
                # This is already a full command
                full_cmd = cmd
                self.logger.info(f"🔧 Using existing full command: {full_cmd}")

            self.logger.info(f"🔧 Final command to execute: {full_cmd}")
            self.logger.info(f"🔧 Working directory for execution: {os.getcwd()}")

            # Run the command
            process = await asyncio.create_subprocess_exec(
                *full_cmd,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
            )

            stdout, stderr = await process.communicate()

            self.logger.info(
                f"🔧 Command completed with return code: {process.returncode}"
            )
            if stdout:
                self.logger.info(f"🔧 stdout: {stdout.decode()}")
            if stderr:
                self.logger.info(f"🔧 stderr: {stderr.decode()}")

            return subprocess.CompletedProcess(
                args=full_cmd,
                returncode=process.returncode,
                stdout=stdout.decode() if stdout else "",
                stderr=stderr.decode() if stderr else "",
            )
        except Exception as e:
            self.logger.error(f"🔧 Exception in _run_chdkptp_command: {e}")
            raise
        finally:
            # Restore original directory
            os.chdir(original_cwd)
            self.logger.info(f"🔧 Restored directory to: {os.getcwd()}")
