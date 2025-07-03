import logging
from pathlib import Path
from typing import Optional, List
from datetime import datetime

from ..domain.services import FileManagementService


class LocalFileManagementService(FileManagementService):
    """Local file system management service."""

    def __init__(self, output_directory: str):
        self.output_directory = Path(output_directory)
        self.logger = logging.getLogger(__name__)

    async def get_latest_image(self, directory: str) -> Optional[str]:
        """Get the latest image file from directory."""
        try:
            dir_path = Path(directory)
            if not dir_path.exists():
                self.logger.warning(f"📁 Directory does not exist: {directory}")
                return None

            # Get all image files
            image_extensions = {".jpg", ".jpeg", ".png", ".bmp", ".tiff", ".cr2"}
            image_files = []

            for file_path in dir_path.iterdir():
                if file_path.is_file() and file_path.suffix.lower() in image_extensions:
                    image_files.append(file_path)

            if not image_files:
                self.logger.warning(
                    f"📁 No image files found in directory: {directory}"
                )
                return None

            # Sort by modification time (newest first)
            latest_file = max(image_files, key=lambda f: f.stat().st_mtime)

            self.logger.info(f"📁 Latest image found: {latest_file}")
            return str(latest_file)

        except Exception as e:
            self.logger.error(f"📁 Error getting latest image: {e}")
            return None

    async def ensure_directory_exists(self, directory: str) -> bool:
        """Ensure directory exists, create if necessary."""
        try:
            dir_path = Path(directory)

            if dir_path.exists():
                if dir_path.is_dir():
                    self.logger.info(f"📁 Directory already exists: {directory}")
                    return True
                else:
                    self.logger.error(
                        f"📁 Path exists but is not a directory: {directory}"
                    )
                    return False

            # Create directory and parents
            dir_path.mkdir(parents=True, exist_ok=True)
            self.logger.info(f"📁 Created directory: {directory}")
            return True

        except Exception as e:
            self.logger.error(f"📁 Error creating directory {directory}: {e}")
            return False

    async def file_exists(self, file_path: str) -> bool:
        """Check if file exists."""
        try:
            path = Path(file_path)
            exists = path.exists() and path.is_file()

            if exists:
                self.logger.info(f"📁 File exists: {file_path}")
            else:
                self.logger.warning(f"📁 File does not exist: {file_path}")

            return exists

        except Exception as e:
            self.logger.error(f"📁 Error checking file existence {file_path}: {e}")
            return False

    async def get_file_size(self, file_path: str) -> Optional[int]:
        """Get file size in bytes."""
        try:
            path = Path(file_path)
            if not path.exists():
                return None

            size = path.stat().st_size
            self.logger.info(f"📁 File size: {file_path} = {size} bytes")
            return size

        except Exception as e:
            self.logger.error(f"📁 Error getting file size {file_path}: {e}")
            return None

    async def get_file_modified_time(self, file_path: str) -> Optional[datetime]:
        """Get file modification time."""
        try:
            path = Path(file_path)
            if not path.exists():
                return None

            mtime = datetime.fromtimestamp(path.stat().st_mtime)
            self.logger.info(f"📁 File modified: {file_path} = {mtime}")
            return mtime

        except Exception as e:
            self.logger.error(f"📁 Error getting file modified time {file_path}: {e}")
            return None

    async def list_image_files(self, directory: str) -> List[str]:
        """List all image files in directory."""
        try:
            dir_path = Path(directory)
            if not dir_path.exists():
                self.logger.warning(f"📁 Directory does not exist: {directory}")
                return []

            # Get all image files
            image_extensions = {".jpg", ".jpeg", ".png", ".bmp", ".tiff", ".cr2"}
            image_files = []

            for file_path in dir_path.iterdir():
                if file_path.is_file() and file_path.suffix.lower() in image_extensions:
                    image_files.append(str(file_path))

            # Sort by modification time (newest first)
            image_files.sort(key=lambda f: Path(f).stat().st_mtime, reverse=True)

            self.logger.info(f"📁 Found {len(image_files)} image files in {directory}")
            return image_files

        except Exception as e:
            self.logger.error(f"📁 Error listing image files in {directory}: {e}")
            return []

    async def delete_file(self, file_path: str) -> bool:
        """Delete a file."""
        try:
            path = Path(file_path)
            if not path.exists():
                self.logger.warning(f"📁 File does not exist for deletion: {file_path}")
                return False

            path.unlink()
            self.logger.info(f"📁 Deleted file: {file_path}")
            return True

        except Exception as e:
            self.logger.error(f"📁 Error deleting file {file_path}: {e}")
            return False

    async def move_file(self, source_path: str, destination_path: str) -> bool:
        """Move a file from source to destination."""
        try:
            source = Path(source_path)
            destination = Path(destination_path)

            if not source.exists():
                self.logger.warning(f"📁 Source file does not exist: {source_path}")
                return False

            # Ensure destination directory exists
            destination.parent.mkdir(parents=True, exist_ok=True)

            # Move the file
            source.rename(destination)
            self.logger.info(f"📁 Moved file: {source_path} -> {destination_path}")
            return True

        except Exception as e:
            self.logger.error(
                f"📁 Error moving file {source_path} to {destination_path}: {e}"
            )
            return False
