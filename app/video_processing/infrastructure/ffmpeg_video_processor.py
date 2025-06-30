import asyncio
import logging
from pathlib import Path


class FFmpegVideoProcessor:
    """FFmpeg-based video processor for creating videos from photos."""

    def __init__(self, ffmpeg_path: str = "ffmpeg"):
        self.ffmpeg_path = ffmpeg_path
        self.logger = logging.getLogger(__name__)

    async def create_video_from_photos(
        self,
        photos_directory: str,
        output_video_path: str,
        fps: int = 60,
        video_duration_seconds: int = 20,
        quality: str = "high",
    ) -> bool:
        """Create video from photos using FFmpeg."""
        try:
            self.logger.info(f"Starting video creation from {photos_directory}")

            # Check if input directory exists and contains photos
            input_path = Path(photos_directory)
            if not input_path.exists():
                self.logger.error(f"Input directory does not exist: {input_path}")
                return False

            # Find image files
            image_files = list(input_path.glob("*.jpg"))
            if not image_files:
                self.logger.error(f"No image files found in {input_path}")
                return False

            # Sort files by name (assuming they have sequential numbering)
            image_files.sort()

            self.logger.info(f"Found {len(image_files)} images to process")

            # Create output directory if it doesn't exist
            output_path = Path(output_video_path)
            output_path.parent.mkdir(parents=True, exist_ok=True)

            # Build FFmpeg command
            cmd = self._build_ffmpeg_command(
                image_files, output_video_path, fps, quality
            )

            # Execute FFmpeg command
            success = await self._execute_ffmpeg_command(cmd)

            if success:
                self.logger.info(f"Video created successfully: {output_video_path}")
            else:
                self.logger.error("Failed to create video")

            return success

        except Exception as e:
            self.logger.error(f"Error creating video: {e}")
            return False

    def _build_ffmpeg_command(
        self, image_files: list, output_path: str, fps: int, quality: str
    ) -> list:
        """Build FFmpeg command for video creation."""
        # Create a file list for FFmpeg
        file_list_path = self._create_file_list(image_files)

        # Build command
        cmd = [
            self.ffmpeg_path,
            "-f",
            "concat",  # Use concat demuxer
            "-safe",
            "0",
            "-i",
            str(file_list_path),  # Input file list
            "-c:v",
            "libx264",  # Video codec
            "-pix_fmt",
            "yuv420p",  # Pixel format for compatibility
            "-r",
            str(fps),  # Output frame rate
            "-y",  # Overwrite output file
            output_path,  # Output file
        ]

        # Add quality settings
        if quality == "high":
            cmd.extend(["-crf", "18"])  # High quality
        elif quality == "medium":
            cmd.extend(["-crf", "23"])  # Medium quality
        else:  # low
            cmd.extend(["-crf", "28"])  # Lower quality

        return cmd

    def _create_file_list(self, image_files: list) -> Path:
        """Create a file list for FFmpeg concat demuxer."""
        file_list_path = Path("/tmp/ffmpeg_file_list.txt")

        with open(file_list_path, "w") as f:
            for image_file in image_files:
                # Format: file 'path/to/image.jpg'
                f.write(f"file '{image_file.absolute()}'\n")
                # Add duration for each frame
                f.write("duration 0.1\n")  # 0.1 seconds per frame

        return file_list_path

    async def _execute_ffmpeg_command(self, cmd: list) -> bool:
        """Execute FFmpeg command asynchronously."""
        try:
            self.logger.info(f"Executing FFmpeg command: {' '.join(cmd)}")

            # Run FFmpeg process
            process = await asyncio.create_subprocess_exec(
                *cmd,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
            )

            # Wait for completion
            stdout, stderr = await process.communicate()

            if process.returncode == 0:
                self.logger.info("FFmpeg command completed successfully")
                return True
            else:
                self.logger.error(f"FFmpeg command failed: {stderr.decode()}")
                return False

        except Exception as e:
            self.logger.error(f"Error executing FFmpeg command: {e}")
            return False
