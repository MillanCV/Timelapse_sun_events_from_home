import asyncio
import logging
import os
import subprocess
from pathlib import Path
from typing import Optional

from ..domain.entities import (
    CameraStatus,
    TimelapseRecordingParameters,
    CameraShootingParameters,
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
rs "{parameters.output_directory}" -shots={parameters.shots} -int={parameters.interval_seconds}
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
        chdkptp_location: str = "/home/arrumada/Dev/CanonCameraControl/ChdkPTP",
        output_directory: str = "/home/arrumada/Images",
    ):
        self.script_generator = script_generator
        self.chdkptp_location = Path(chdkptp_location)
        self.output_directory = Path(output_directory)
        self.logger = logging.getLogger(__name__)
        self._current_recording: Optional[TimelapseRecordingParameters] = None

    async def shoot_camera(self, parameters: CameraShootingParameters) -> bool:
        """Shoot camera with given parameters."""
        try:
            self.logger.info(f"Starting camera shooting with {parameters.shots} shots")

            # Build CHDKPTP command based on the bash script
            chdkptp_script = self.chdkptp_location / "chdkptp.sh"

            if not chdkptp_script.exists():
                self.logger.error(f"CHDKPTP script not found: {chdkptp_script}")
                return False

            # Construct the command similar to the bash script
            rs_command = (
                f"rs {self.output_directory} -shots={parameters.shots} "
                f"-int={parameters.interval} -tv={parameters.speed} "
                f"-sd={parameters.subject_distance} -isomode={parameters.iso_value}"
            )

            cmd = [
                "sudo",
                str(chdkptp_script),
                "-ec",
                "-erec",
                "-eclock -sync",
                "-eluar set_lcd_display(0)",
                "-eluar set_mf(1)",
                "-eluar set_aelock(1)",
                "-eluar set_aflock(1)",
                f"-e {rs_command}",
                "-eplay",
                "-ed A/rawopint.csv /home/arrumada/Dev/CanonCameraControl/Scripts/Logs",
                "-edis",
            ]

            self.logger.info(f"Executing camera shooting command: {' '.join(cmd)}")

            result = await self._run_chdkptp_command(cmd)

            if result.returncode == 0:
                self.logger.info("Camera shooting completed successfully")
                return True
            else:
                self.logger.error(f"Camera shooting failed: {result.stderr}")
                return False

        except Exception as e:
            self.logger.error(f"Error shooting camera: {e}")
            return False

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
            is_connected = await self.is_camera_connected()

            return CameraStatus(
                is_connected=is_connected,
                is_recording=self._current_recording is not None,
                current_mode="timelapse" if self._current_recording else "idle",
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
            # Try to run a simple CHDKPTP command to check connection
            result = await self._run_chdkptp_command(["-c", "ls"])
            return result.returncode == 0
        except Exception as e:
            self.logger.error(f"Error checking camera connection: {e}")
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
        # Change to CHDKPTP directory
        original_cwd = os.getcwd()
        os.chdir(self.chdkptp_location)

        try:
            # Run the command
            process = await asyncio.create_subprocess_exec(
                *cmd,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
            )

            stdout, stderr = await process.communicate()

            return subprocess.CompletedProcess(
                args=cmd,
                returncode=process.returncode,
                stdout=stdout.decode() if stdout else "",
                stderr=stderr.decode() if stderr else "",
            )
        finally:
            # Restore original directory
            os.chdir(original_cwd)
