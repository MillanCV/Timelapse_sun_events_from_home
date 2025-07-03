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

            # Build CHDKPTP command using the same pattern as shoot_camera
            chdkptp_script = self.chdkptp_location / "chdkptp.sh"
            self.logger.info(f"📸 Looking for script at: {chdkptp_script}")

            if not chdkptp_script.exists():
                self.logger.error(f"📸 CHDKPTP script not found: {chdkptp_script}")
                return LiveViewResult(
                    success=False,
                    message="CHDKPTP script not found",
                    image_data=None,
                    image_format=None,
                    timestamp=datetime.now(),
                )

            self.logger.info("📸 CHDKPTP script found, building command...")

            # Build command with proper structure (ignore overlay parameter)
            cmd = [
                "sudo",
                str(chdkptp_script),
                "-c",  # connect
                "-erec",  # switch to record mode
                "-elvdumpimg -vp=frame.ppm -count=1",  # live view dump
            ]

            self.logger.info(f"📸 Built command: {cmd}")
            self.logger.info("📸 Executing live view command...")

            # Execute the command
            result = await self._run_chdkptp_command(cmd)

            self.logger.info(
                f"📸 Command completed with return code: {result.returncode}"
            )
            if result.stdout:
                self.logger.info(f"📸 Command stdout: {result.stdout}")
            if result.stderr:
                self.logger.info(f"📸 Command stderr: {result.stderr}")

            if result.returncode == 0:
                self.logger.info("📸 Command successful, reading PPM image...")

                # Read the PPM image
                image_data = await self._read_ppm_image()
                print(f"📸 image_data: {image_data}")
                if image_data is not None:
                    self.logger.info(
                        f"📸 PPM image loaded successfully, shape: {image_data.shape}"
                    )

                    # Convert to JPEG
                    self.logger.info("📸 Converting to JPEG...")
                    jpeg_data = await self._convert_to_jpeg(image_data)
                    self.logger.info(
                        f"📸 JPEG conversion successful, size: {len(jpeg_data)} bytes"
                    )

                    return LiveViewResult(
                        success=True,
                        message="Live view snapshot captured successfully",
                        image_data=jpeg_data,
                        image_format="jpeg",
                        timestamp=datetime.now(),
                    )
                else:
                    self.logger.error("📸 Failed to read PPM image data")
                    return LiveViewResult(
                        success=False,
                        message="Failed to read PPM image data",
                        image_data=None,
                        image_format=None,
                        timestamp=datetime.now(),
                    )
            else:
                self.logger.error(f"📸 Live view command failed: {result.stderr}")
                return LiveViewResult(
                    success=False,
                    message=f"Live view snapshot failed: {result.stderr}",
                    image_data=None,
                    image_format=None,
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
            self.logger.info(f"🎥 CHDKPTP location: {self.chdkptp_location}")
            self.logger.info(f"🎥 Config: {config}")
            self._streaming = True

            # Get CHDKPTP paths
            chdkptp_script = str(self.chdkptp_location / "chdkptp.sh")
            chdkptp_dir = str(self.chdkptp_location)
            frame_path = str(self._frame_path)

            self.logger.info(f"🎥 CHDKPTP script path: {chdkptp_script}")
            self.logger.info(f"🎥 CHDKPTP directory: {chdkptp_dir}")
            self.logger.info(f"🎥 Frame path: {frame_path}")

            # Check if paths exist
            if not Path(chdkptp_script).exists():
                self.logger.error(f"🎥 CHDKPTP script not found: {chdkptp_script}")
                yield LiveViewResult(
                    success=False,
                    message=f"CHDKPTP script not found: {chdkptp_script}",
                    image_data=None,
                    image_format=None,
                    timestamp=datetime.now(),
                )
                return

            if not Path(chdkptp_dir).exists():
                self.logger.error(f"🎥 CHDKPTP directory not found: {chdkptp_dir}")
                yield LiveViewResult(
                    success=False,
                    message=f"CHDKPTP directory not found: {chdkptp_dir}",
                    image_data=None,
                    image_format=None,
                    timestamp=datetime.now(),
                )
                return

            self.logger.info("🎥 Starting frame capture loop...")
            frame_count = 0

            while self._streaming:
                try:
                    frame_count += 1
                    self.logger.info(f"🎥 Taking frame {frame_count}...")

                    # Build command
                    cmd = [
                        "sudo",
                        chdkptp_script,
                        "-c",
                        "-erec",
                        "-elvdumpimg -vp=frame.ppm -count=1",
                    ]
                    self.logger.info(f"🎥 Executing command: {' '.join(cmd)}")
                    self.logger.info(f"🎥 Working directory: {chdkptp_dir}")

                    # Use the proven working pattern
                    start_time = datetime.now()
                    result = subprocess.run(
                        cmd,
                        cwd=chdkptp_dir,
                        check=True,
                        capture_output=True,
                        text=True,
                    )
                    end_time = datetime.now()
                    duration = (end_time - start_time).total_seconds()

                    self.logger.info(f"🎥 Command completed in {duration:.3f}s")
                    if result.stdout:
                        self.logger.info(f"🎥 Command stdout: {result.stdout}")
                    if result.stderr:
                        self.logger.info(f"🎥 Command stderr: {result.stderr}")

                    # Check if frame file was created
                    frame_path_obj = Path(frame_path)
                    if not frame_path_obj.exists():
                        self.logger.warning(f"🎥 Frame file not found: {frame_path}")
                        continue

                    frame_size = frame_path_obj.stat().st_size
                    self.logger.info(f"🎥 Frame file size: {frame_size} bytes")

                    # Read image
                    self.logger.info(f"🎥 Reading image from: {frame_path}")
                    image = cv2.imread(frame_path)

                    if image is None:
                        self.logger.warning("🎥 Could not read frame.ppm")
                        self.logger.info(
                            f"🎥 Frame path exists: {frame_path_obj.exists()}"
                        )
                        if frame_path_obj.exists():
                            self.logger.info(f"🎥 Frame path size: {frame_size} bytes")
                        continue

                    self.logger.info(
                        f"🎥 Image loaded successfully, shape: {image.shape}"
                    )
                    self.logger.info(f"🎥 Image dtype: {image.dtype}")
                    self.logger.info(f"🎥 Image size: {image.size}")

                    # Overlay datetime with milliseconds
                    now = datetime.now()
                    timestamp_str = now.strftime("%Y-%m-%d %H:%M:%S.%f")[
                        :-3
                    ]  # trim to ms
                    font = cv2.FONT_HERSHEY_SIMPLEX
                    font_scale = 0.7
                    font_thickness = 2
                    text_size, _ = cv2.getTextSize(
                        timestamp_str, font, font_scale, font_thickness
                    )
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

                    # Convert to JPEG with configured quality
                    self.logger.info(
                        f"🎥 Converting to JPEG with quality {config.quality}..."
                    )
                    ret, jpeg = cv2.imencode(
                        ".jpg", image, [cv2.IMWRITE_JPEG_QUALITY, config.quality]
                    )
                    if not ret:
                        self.logger.warning("🎥 Could not encode JPEG")
                        continue

                    jpeg_bytes = jpeg.tobytes()
                    self.logger.info(
                        f"🎥 Frame {frame_count} captured successfully, size: {len(jpeg_bytes)} bytes"
                    )

                    yield LiveViewResult(
                        success=True,
                        message=f"Frame {frame_count} captured",
                        image_data=jpeg_bytes,
                        image_format="jpeg",
                        timestamp=datetime.now(),
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
                    yield LiveViewResult(
                        success=False,
                        message=f"Snapshot failed: {str(e)}",
                        image_data=None,
                        image_format=None,
                        timestamp=datetime.now(),
                    )
                    break
                except Exception as e:
                    self.logger.error(
                        f"🎥 Error in live view stream frame {frame_count}: {e}"
                    )
                    self.logger.error(f"🎥 Exception type: {type(e).__name__}")
                    import traceback

                    self.logger.error(f"🎥 Traceback: {traceback.format_exc()}")
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
            self.logger.error(f"🎥 Exception type: {type(e).__name__}")
            import traceback

            self.logger.error(f"🎥 Traceback: {traceback.format_exc()}")
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
