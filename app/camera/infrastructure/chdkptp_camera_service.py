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

            # Use the simpler command format: connect, rec, rs, play,
            # disconnect
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
            self.logger.info("📸 Starting live view snapshot...")
            self.logger.info(f"📸 CHDKPTP location: {self.chdkptp_location}")
            self.logger.info(f"📸 Frame path: {self._frame_path}")

            # Validate CHDKPTP setup
            (
                is_valid,
                error_msg,
                chdkptp_script,
                chdkptp_dir,
            ) = await self._validate_chdkptp_setup()
            if not is_valid:
                return await self._create_live_view_result(False, error_msg)

            # Execute live view command
            success, result, error_msg = await self._execute_live_view_command(
                chdkptp_script, chdkptp_dir
            )
            if not success:
                return await self._create_live_view_result(False, error_msg)

            # Capture and process frame
            success, jpeg_data, error_msg = await self._capture_and_process_frame(
                quality=80, add_timestamp=include_overlay
            )
            if not success:
                return await self._create_live_view_result(False, error_msg)

            return await self._create_live_view_result(
                True, "Live view snapshot captured successfully", jpeg_data
            )

        except Exception as e:
            self.logger.error(f"📸 Error taking live view snapshot: {e}")
            return await self._create_live_view_result(
                False, f"Error taking live view snapshot: {str(e)}"
            )

    async def start_live_view_stream(
        self, config: LiveViewStream
    ) -> AsyncGenerator[LiveViewResult, None]:
        """Start a live view stream and yield image frames."""
        try:
            self.logger.info("🎥 Starting live view stream...")
            self.logger.info(f"🎥 CHDKPTP location: {self.chdkptp_location}")
            self.logger.info(f"🎥 Config: {config}")
            self._streaming = True

            # Validate CHDKPTP setup
            (
                is_valid,
                error_msg,
                chdkptp_script,
                chdkptp_dir,
            ) = await self._validate_chdkptp_setup()
            if not is_valid:
                yield await self._create_live_view_result(False, error_msg)
                return

            self.logger.info("🎥 Starting frame capture loop...")
            frame_count = 0

            while self._streaming:
                try:
                    frame_count += 1
                    self.logger.info(f"🎥 Taking frame {frame_count}...")

                    # Execute live view command using the same async pattern as snapshot
                    start_time = datetime.now()
                    success, result, error_msg = await self._execute_live_view_command(
                        chdkptp_script, chdkptp_dir
                    )
                    end_time = datetime.now()
                    duration = (end_time - start_time).total_seconds()

                    self.logger.info(f"🎥 Command completed in {duration:.3f}s")

                    if not success:
                        self.logger.warning(
                            f"🎥 Frame {frame_count} command failed: {error_msg}"
                        )
                        continue

                    # Capture and process frame with timestamp overlay
                    (
                        success,
                        jpeg_data,
                        error_msg,
                    ) = await self._capture_and_process_frame(
                        quality=config.quality, add_timestamp=True
                    )
                    if not success:
                        self.logger.warning(
                            f"🎥 Frame {frame_count} failed: {error_msg}"
                        )
                        continue

                    self.logger.info(
                        f"🎥 Frame {frame_count} captured successfully, size: {len(jpeg_data)} bytes"
                    )

                    yield await self._create_live_view_result(
                        True, f"Frame {frame_count} captured", jpeg_data
                    )

                    # Wait for next frame based on configured framerate
                    frame_interval = 1.0 / config.framerate
                    self.logger.info(
                        f"🎥 Waiting {frame_interval:.3f}s for next frame (target: {config.framerate} FPS)..."
                    )
                    await asyncio.sleep(frame_interval)

                except subprocess.CalledProcessError as e:
                    self.logger.error(f"🎥 Snapshot loop failed: {e}")
                    self.logger.error(f"🎥 Return code: {e.returncode}")
                    if e.stdout:
                        self.logger.error(f"🎥 Error stdout: {e.stdout}")
                    if e.stderr:
                        self.logger.error(f"🎥 Error stderr: {e.stderr}")
                    yield await self._create_live_view_result(
                        False, f"Snapshot failed: {str(e)}"
                    )
                    break
                except Exception as e:
                    self.logger.error(
                        f"🎥 Error in live view stream frame {frame_count}: {e}"
                    )
                    self.logger.error(f"🎥 Exception type: {type(e).__name__}")
                    import traceback

                    self.logger.error(f"🎥 Traceback: {traceback.format_exc()}")
                    yield await self._create_live_view_result(
                        False, f"Stream error: {str(e)}"
                    )
                    break

        except Exception as e:
            self.logger.error(f"🎥 Error starting live view stream: {e}")
            self.logger.error(f"🎥 Exception type: {type(e).__name__}")
            import traceback

            self.logger.error(f"🎥 Traceback: {traceback.format_exc()}")
            yield await self._create_live_view_result(
                False, f"Error starting live view stream: {str(e)}"
            )
        finally:
            self._streaming = False
            self.logger.info("🎥 Live view stream stopped")
            self.logger.info(f"🎥 Total frames processed: {frame_count}")

    async def stop_live_view_stream(self) -> None:
        """Stop the live view stream."""
        self.logger.info("🎥 Stopping live view stream...")
        self.logger.info(f"🎥 Current streaming state: {self._streaming}")
        self._streaming = False
        self.logger.info("🎥 Live view stream stop requested")

    async def _read_ppm_image(self) -> Optional[np.ndarray]:
        """Read a PPM image from the frame file."""
        try:
            if not self._frame_path.exists():
                self.logger.warning("Frame file not found")
                return None

            # Read PPM file
            image = cv2.imread(str(self._frame_path))

            # Log detailed information about the image
            self.logger.info(f"📸 cv2.imread result type: {type(image)}")
            if image is not None:
                self.logger.info(f"📸 Image shape: {image.shape}")
                self.logger.info(f"📸 Image dtype: {image.dtype}")
                self.logger.info(f"📸 Image size: {image.size}")
                self.logger.info(
                    f"📸 Image min/max values: {image.min()}/{image.max()}"
                )
            else:
                self.logger.warning("📸 cv2.imread returned None")
                self.logger.info(f"📸 Frame path exists: {self._frame_path.exists()}")
                if self._frame_path.exists():
                    self.logger.info(
                        f"📸 Frame path size: {self._frame_path.stat().st_size} bytes"
                    )

            # Check if image was loaded successfully (numpy array with
            # valid shape)
            if image is None or image.size == 0:
                self.logger.warning("Could not read PPM image")
                return None

            self.logger.info(f"📸 PPM image loaded successfully, shape: {image.shape}")
            return image

        except Exception as e:
            self.logger.error(f"Error reading PPM image: {e}")
            return None

    async def _convert_to_jpeg(self, image: np.ndarray, quality: int = 80) -> bytes:
        """Convert numpy image to JPEG bytes."""
        try:
            self.logger.info(
                f"📸 Starting JPEG conversion for image shape: {image.shape}"
            )

            # Use the simple working approach
            _, buffer = cv2.imencode(".jpg", image)
            jpeg_bytes = buffer.tobytes()

            self.logger.info(
                f"📸 JPEG conversion successful, size: {len(jpeg_bytes)} bytes"
            )
            return jpeg_bytes

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
                message=(
                    f"Auto shoot completed: {len(image_paths)}/{shots} shots taken"
                ),
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
                message=(
                    f"Burst shoot completed: {len(image_paths)}/{shots} shots taken"
                ),
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
            self.logger.info(
                f"🔍 _get_latest_image: checking directory {self.output_directory}"
            )

            # Look for common image extensions
            image_extensions = [".jpg", ".jpeg", ".cr2", ".raw"]
            image_paths = []

            # Get all files in the output directory
            if self.output_directory.exists():
                self.logger.info(f"🔍 Output directory exists: {self.output_directory}")

                # List all files in directory for debugging
                all_files = list(self.output_directory.iterdir())
                self.logger.info(
                    f"🔍 All files in directory: {[f.name for f in all_files]}"
                )

                for ext in image_extensions:
                    found_files = list(self.output_directory.glob(f"*{ext}"))
                    self.logger.info(
                        f"🔍 Found {len(found_files)} files with extension {ext}: {[f.name for f in found_files]}"
                    )
                    image_paths.extend([str(f) for f in found_files])

                self.logger.info(f"🔍 Total image files found: {len(image_paths)}")

                if image_paths:
                    # Sort by modification time (newest first) and return the
                    # latest
                    image_paths.sort(key=lambda x: os.path.getmtime(x), reverse=True)

                    # Log the top 5 most recent images
                    self.logger.info("🔍 Top 5 most recent images:")
                    for i, path in enumerate(image_paths[:5]):
                        mtime = os.path.getmtime(path)
                        self.logger.info(
                            f"🔍   {i + 1}. {path} (modified: {datetime.fromtimestamp(mtime)})"
                        )

                    latest = image_paths[0]
                    self.logger.info(f"🔍 Returning latest image: {latest}")
                    return latest
                else:
                    self.logger.warning("🔍 No image files found in output directory")
                    return None
            else:
                self.logger.error(
                    f"🔍 Output directory does not exist: {self.output_directory}"
                )
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

    async def _validate_chdkptp_setup(
        self,
    ) -> tuple[bool, str, Optional[Path], Optional[str]]:
        """Validate CHDKPTP setup and return paths if valid."""
        chdkptp_script = self.chdkptp_location / "chdkptp.sh"
        chdkptp_dir = str(self.chdkptp_location)

        if not chdkptp_script.exists():
            error_msg = f"CHDKPTP script not found: {chdkptp_script}"
            self.logger.error(f"📸 {error_msg}")
            return False, error_msg, None, None

        if not Path(chdkptp_dir).exists():
            error_msg = f"CHDKPTP directory not found: {chdkptp_dir}"
            self.logger.error(f"📸 {error_msg}")
            return False, error_msg, None, None

        return True, "", chdkptp_script, chdkptp_dir

    async def _execute_live_view_command(
        self, chdkptp_script: Path, chdkptp_dir: str
    ) -> tuple[bool, Optional[subprocess.CompletedProcess], str]:
        """Execute the live view command and return success status, result, and error message."""
        cmd = [
            "sudo",
            str(chdkptp_script),
            "-c",  # connect
            "-erec",  # switch to record mode
            "-elvdumpimg -vp=frame.ppm -count=1",  # live view dump
        ]

        self.logger.info(f"📸 Executing command: {' '.join(cmd)}")

        try:
            result = await self._run_chdkptp_command(cmd)
            self.logger.info(
                f"📸 Command completed with return code: {result.returncode}"
            )

            if result.stdout:
                self.logger.info(f"📸 Command stdout: {result.stdout}")
            if result.stderr:
                self.logger.info(f"📸 Command stderr: {result.stderr}")

            if result.returncode == 0:
                return True, result, ""
            else:
                error_msg = f"Live view command failed: {result.stderr}"
                self.logger.error(f"📸 {error_msg}")
                return False, result, error_msg

        except Exception as e:
            error_msg = f"Error executing live view command: {str(e)}"
            self.logger.error(f"📸 {error_msg}")
            return False, None, error_msg

    async def _capture_and_process_frame(
        self, quality: int = 80, add_timestamp: bool = False
    ) -> tuple[bool, Optional[bytes], str]:
        """Capture a frame and process it to JPEG bytes."""
        try:
            # Check if frame file was created
            frame_path_obj = Path(self._frame_path)
            if not frame_path_obj.exists():
                error_msg = f"Frame file not found: {self._frame_path}"
                self.logger.warning(f"📸 {error_msg}")
                return False, None, error_msg

            frame_size = frame_path_obj.stat().st_size
            self.logger.info(f"📸 Frame file size: {frame_size} bytes")

            # Read image
            self.logger.info(f"📸 Reading image from: {self._frame_path}")
            image = cv2.imread(str(self._frame_path))

            if image is None:
                error_msg = "Could not read frame.ppm"
                self.logger.warning(f"📸 {error_msg}")
                return False, None, error_msg

            self.logger.info(f"📸 Image loaded successfully, shape: {image.shape}")

            # Add timestamp overlay if requested
            if add_timestamp:
                image = self._add_timestamp_overlay(image)

            # Convert to JPEG
            self.logger.info(f"📸 Converting to JPEG with quality {quality}...")
            ret, jpeg = cv2.imencode(".jpg", image, [cv2.IMWRITE_JPEG_QUALITY, quality])
            if not ret:
                error_msg = "Could not encode JPEG"
                self.logger.warning(f"📸 {error_msg}")
                return False, None, error_msg

            jpeg_bytes = jpeg.tobytes()
            self.logger.info(
                f"📸 JPEG conversion successful, size: {len(jpeg_bytes)} bytes"
            )

            return True, jpeg_bytes, ""

        except Exception as e:
            error_msg = f"Error capturing and processing frame: {str(e)}"
            self.logger.error(f"📸 {error_msg}")
            return False, None, error_msg

    def _add_timestamp_overlay(self, image: np.ndarray) -> np.ndarray:
        """Add timestamp overlay to the image."""
        now = datetime.now()
        timestamp_str = now.strftime("%Y-%m-%d %H:%M:%S.%f")[:-3]  # trim to ms
        font = cv2.FONT_HERSHEY_SIMPLEX
        font_scale = 0.7
        font_thickness = 2
        text_x = 10
        text_y = image.shape[0] - 10

        # Draw black outline
        cv2.putText(
            image,
            timestamp_str,
            (text_x, text_y),
            font,
            font_scale,
            (0, 0, 0),
            font_thickness + 2,
            cv2.LINE_AA,
        )
        # Draw white text
        cv2.putText(
            image,
            timestamp_str,
            (text_x, text_y),
            font,
            font_scale,
            (255, 255, 255),
            font_thickness,
            cv2.LINE_AA,
        )

        return image

    async def _create_live_view_result(
        self, success: bool, message: str, image_data: Optional[bytes] = None
    ) -> LiveViewResult:
        """Create a LiveViewResult with consistent timestamp."""
        return LiveViewResult(
            success=success,
            message=message,
            image_data=image_data,
            image_format="jpeg" if image_data else None,
            timestamp=datetime.now(),
        )
