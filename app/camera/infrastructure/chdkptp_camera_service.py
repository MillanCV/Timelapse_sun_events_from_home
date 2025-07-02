import asyncio
import logging
import os
import subprocess
from pathlib import Path
from typing import Optional, List
from datetime import datetime

from ..domain.entities import (
    CameraStatus,
    TimelapseRecordingParameters,
    CameraShootingParameters,
    CameraShootingResult,
)
from ..domain.services import CameraControlService, TimelapseScriptGenerator


class CHDKPTPScriptGenerator(TimelapseScriptGenerator):
    """CHDKPTP script generator for timelapse recording."""

    def __init__(
        self,
        scripts_directory: str = (
            "/home/arrumada/Dev/CanonCameraControl/Scripts/Operations/"
            "OperationsWithParameters"
        ),
    ):
        self.scripts_directory = Path(scripts_directory)
        self.logger = logging.getLogger(__name__)

    def generate_timelapse_script(
        self, parameters: TimelapseRecordingParameters
    ) -> str:
        """Generate CHDKPTP script for timelapse recording."""
        script_content = f"""rec
clock -sync
rs "{parameters.output_directory}" -shots={parameters.shots} \
-int={parameters.interval_seconds}
play
dis
"""
        return script_content

    def generate_script_file_path(
        self, parameters: TimelapseRecordingParameters
    ) -> str:
        """Generate file path for the script."""
        timestamp = parameters.start_time.strftime("%Y%m%d_%H%M%S")
        filename = f"timelapse_{parameters.period_type}_{timestamp}.lua"
        return str(self.scripts_directory / filename)


class CHDKPTPCameraService(CameraControlService):
    """CHDKPTP camera control service implementation."""

    def __init__(
        self,
        script_generator: CHDKPTPScriptGenerator,
        chdkptp_location: str = ("/home/arrumada/Dev/CanonCameraControl/ChdkPTP"),
        output_directory: str = "/home/arrumada/Images",
    ):
        self.script_generator = script_generator
        self.chdkptp_location = Path(chdkptp_location)
        self.output_directory = Path(output_directory)
        self.logger = logging.getLogger(__name__)
        self._current_recording: Optional[TimelapseRecordingParameters] = None

    async def shoot_camera(
        self, parameters: CameraShootingParameters
    ) -> CameraShootingResult:
        """Shoot camera with given parameters."""
        try:
            self.logger.info(f"Starting camera shooting with {parameters.shots} shots")

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
                    message=(
                        f"Camera shooting completed "
                    ),
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

    def _get_latest_images(self) -> List[str]:
        """Get the latest images from the output directory."""
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

                # Return the most recent image (or a few if multiple shots)
                return image_paths[:5]  # Return up to 5 most recent images

            return []
        except Exception as e:
            self.logger.error(f"Error getting latest images: {e}")
            return []
        
    def _get_latest_image(self) -> str:
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

                # Return the most recent image (or a few if multiple shots)
                self.logger.error(f"_get_latest_image: {image_paths}")
                return image_paths[0]  # Return up to 5 most recent images

            return []
        except Exception as e:
            self.logger.error(f"Error getting latest images: {e}")
            return []

    async def start_timelapse_recording(
        self, parameters: TimelapseRecordingParameters
    ) -> bool:
        """Start timelapse recording with given parameters."""
        try:
            self.logger.info(
                f"Starting timelapse recording for {parameters.period_type}"
            )

            # Generate script content
            script_content = self.script_generator.generate_timelapse_script(parameters)

            # Create temporary script file
            script_path = self.script_generator.generate_script_file_path(parameters)

            # Write script to file
            with open(script_path, "w") as f:
                f.write(script_content)

            # Execute CHDKPTP command
            success = await self._execute_chdkptp_script(script_path)

            if success:
                self._current_recording = parameters
                self.logger.info("Timelapse recording started successfully")
            else:
                self.logger.error("Failed to start timelapse recording")

            # Clean up script file
            try:
                os.remove(script_path)
            except OSError:
                self.logger.warning(f"Could not remove temporary script: {script_path}")

            return success

        except Exception as e:
            self.logger.error(f"Error starting timelapse recording: {e}")
            return False

    async def get_camera_status(self) -> CameraStatus:
        """Get current camera status."""
        try:
            # Check if CHDKPTP is available and camera is connected
            is_connected = True
            # is_connected = await self.is_camera_connected()

            return CameraStatus(
                is_connected=is_connected,
                is_recording=self._current_recording is not None,
                current_mode=("timelapse" if self._current_recording else "idle"),
                battery_level=None,  # Could be implemented with CHDKPTP commands
                storage_available=None,  # Could be implemented with CHDKPTP commands
            )
        except Exception as e:
            self.logger.error(f"Error getting camera status: {e}")
            return CameraStatus(
                is_connected=False,
                is_recording=False,
                current_mode="error",
            )

    async def is_camera_connected(self) -> bool:
        """Check if camera is connected."""
        try:
            self.logger.info("🔍 Starting camera connection check...")
            # Try to run a simple CHDKPTP command to check connection
            result = await self._run_chdkptp_command(["-c", "ls"])
            self.logger.info(f"🔍 Camera connection check result: {result.returncode}")
            return result.returncode == 0
        except Exception as e:
            self.logger.error(f"🔍 Error checking camera connection: {e}")
            return False

    async def _execute_chdkptp_script(self, script_path: str) -> bool:
        """Execute CHDKPTP script."""
        try:
            chdkptp_script = self.chdkptp_location / "chdkptp.sh"

            if not chdkptp_script.exists():
                self.logger.error(f"CHDKPTP script not found: {chdkptp_script}")
                return False

            # Change to CHDKPTP directory and execute script
            cmd = ["sudo", str(chdkptp_script), "-e", f"source {script_path}"]

            self.logger.info(f"Executing CHDKPTP command: {' '.join(cmd)}")

            result = await self._run_chdkptp_command(cmd)

            if result.returncode == 0:
                self.logger.info("CHDKPTP script executed successfully")
                return True
            else:
                self.logger.error(f"CHDKPTP script failed: {result.stderr}")
                return False

        except Exception as e:
            self.logger.error(f"Error executing CHDKPTP script: {e}")
            return False

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
                chdkptp_script = Path("chdkptp.sh")  # Relative to current directory
                self.logger.info(
                    f"🔧 Looking for script at: {chdkptp_script.absolute()}"
                )

                if not chdkptp_script.exists():
                    self.logger.error(
                        f"🔧 CHDKPTP script not found at: {chdkptp_script.absolute()}"
                    )
                    raise FileNotFoundError(
                        f"CHDKPTP script not found: {chdkptp_script.absolute()}"
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
