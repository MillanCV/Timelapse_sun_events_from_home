import asyncio
import logging
import os
from pathlib import Path
from typing import Tuple

from ..domain.services import SubprocessService


class CHDKPTPSubprocessService(SubprocessService):
    """CHDKPTP subprocess execution service."""

    def __init__(self, chdkptp_location: str):
        self.chdkptp_location = Path(chdkptp_location)
        self.logger = logging.getLogger(__name__)

    async def validate_executable(self, executable_path: str) -> bool:
        """Validate if executable exists and is accessible."""
        try:
            chdkptp_script = self.chdkptp_location / "chdkptp.sh"
            return chdkptp_script.exists()
        except Exception as e:
            self.logger.error(f"Error validating executable {executable_path}: {e}")
            return False

    async def execute_command(
        self, command: list, working_directory: str
    ) -> Tuple[bool, str, str]:
        """Execute command and return (success, stdout, stderr)."""
        try:
            self.logger.info(f"🔧 Executing command: {' '.join(command)}")
            self.logger.info(f"🔧 Working directory: {working_directory}")

            # Change to working directory
            original_cwd = os.getcwd()
            os.chdir(working_directory)
            self.logger.info(f"🔧 Changed to directory: {os.getcwd()}")

            try:
                # Run the command
                process = await asyncio.create_subprocess_exec(
                    *command,
                    stdout=asyncio.subprocess.PIPE,
                    stderr=asyncio.subprocess.PIPE,
                )

                stdout, stderr = await process.communicate()

                success = process.returncode == 0
                stdout_str = stdout.decode() if stdout else ""
                stderr_str = stderr.decode() if stderr else ""

                self.logger.info(
                    f"🔧 Command completed with return code: {process.returncode}"
                )
                if stdout_str:
                    self.logger.info(f"🔧 stdout: {stdout_str}")
                if stderr_str:
                    self.logger.info(f"🔧 stderr: {stderr_str}")

                return success, stdout_str, stderr_str

            finally:
                # Restore original directory
                os.chdir(original_cwd)
                self.logger.info(f"🔧 Restored directory to: {os.getcwd()}")

        except Exception as e:
            self.logger.error(f"🔧 Exception in execute_command: {e}")
            return False, "", str(e)

    async def build_chdkptp_command(self, arguments: list) -> list:
        """Build a complete CHDKPTP command with sudo and script path."""
        chdkptp_script = self.chdkptp_location / "chdkptp.sh"

        if not chdkptp_script.exists():
            raise FileNotFoundError(f"CHDKPTP script not found: {chdkptp_script}")

        # Check if this is a full command or just arguments
        if arguments and not arguments[0].startswith("sudo"):
            # This is just arguments, need to build the full command
            full_cmd = ["sudo", str(chdkptp_script)] + arguments
            self.logger.info(f"🔧 Built full command: {full_cmd}")
        else:
            # This is already a full command
            full_cmd = arguments
            self.logger.info(f"🔧 Using existing full command: {full_cmd}")

        return full_cmd

    async def execute_chdkptp_command(self, arguments: list) -> Tuple[bool, str, str]:
        """Execute a CHDKPTP command with proper setup."""
        try:
            # Build the command
            command = await self.build_chdkptp_command(arguments)

            # Execute in CHDKPTP directory
            working_directory = str(self.chdkptp_location)

            return await self.execute_command(command, working_directory)

        except Exception as e:
            self.logger.error(f"🔧 Error executing CHDKPTP command: {e}")
            return False, "", str(e)
