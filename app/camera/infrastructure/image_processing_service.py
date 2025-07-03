import logging
import cv2
import numpy as np
from pathlib import Path
from typing import Optional
from datetime import datetime

from ..domain.services import ImageProcessingService
from ..domain.entities import ImageProcessingConfiguration


class OpenCVImageProcessingService(ImageProcessingService):
    """OpenCV-based image processing service."""

    def __init__(self, config: ImageProcessingConfiguration):
        self.config = config
        self.logger = logging.getLogger(__name__)

    async def convert_to_jpeg(self, image_data: bytes, quality: int = 80) -> bytes:
        """Convert image data to JPEG format."""
        try:
            # Convert bytes to numpy array
            nparr = np.frombuffer(image_data, np.uint8)
            image = cv2.imdecode(nparr, cv2.IMREAD_COLOR)

            if image is None:
                raise ValueError("Could not decode image data")

            self.logger.info(f"🖼️ Converting image to JPEG with quality {quality}")

            # Encode to JPEG
            ret, buffer = cv2.imencode(
                ".jpg", image, [cv2.IMWRITE_JPEG_QUALITY, quality]
            )

            if not ret:
                raise ValueError("Could not encode JPEG")

            jpeg_bytes = buffer.tobytes()
            self.logger.info(
                f"🖼️ JPEG conversion successful, size: {len(jpeg_bytes)} bytes"
            )

            return jpeg_bytes

        except Exception as e:
            self.logger.error(f"🖼️ Error converting to JPEG: {e}")
            raise

    async def add_timestamp_overlay(self, image_data: bytes) -> bytes:
        """Add timestamp overlay to image."""
        try:
            # Convert bytes to numpy array
            nparr = np.frombuffer(image_data, np.uint8)
            image = cv2.imdecode(nparr, cv2.IMREAD_COLOR)

            if image is None:
                raise ValueError("Could not decode image data")

            # Add timestamp
            image = self._add_timestamp_to_image(image)

            # Convert back to bytes
            ret, buffer = cv2.imencode(".jpg", image)
            if not ret:
                raise ValueError("Could not encode image with timestamp")

            return buffer.tobytes()

        except Exception as e:
            self.logger.error(f"🖼️ Error adding timestamp overlay: {e}")
            raise

    async def read_ppm_image(self, file_path: str) -> Optional[bytes]:
        """Read PPM image from file."""
        try:
            if not Path(file_path).exists():
                self.logger.warning(f"🖼️ PPM file not found: {file_path}")
                return None

            # Read PPM file using OpenCV
            image = cv2.imread(file_path)

            if image is None:
                self.logger.warning(f"🖼️ Could not read PPM image: {file_path}")
                return None

            self.logger.info(f"🖼️ PPM image loaded successfully, shape: {image.shape}")

            # Convert to bytes
            ret, buffer = cv2.imencode(".jpg", image)
            if not ret:
                raise ValueError("Could not encode image to bytes")

            return buffer.tobytes()

        except Exception as e:
            self.logger.error(f"🖼️ Error reading PPM image: {e}")
            return None

    def _add_timestamp_to_image(self, image: np.ndarray) -> np.ndarray:
        """Add timestamp overlay to numpy image array."""
        now = datetime.now()
        timestamp_str = now.strftime("%Y-%m-%d %H:%M:%S.%f")[:-3]  # trim to ms

        font = cv2.FONT_HERSHEY_SIMPLEX
        font_scale = self.config.timestamp_font_scale
        font_thickness = self.config.timestamp_font_thickness
        text_x = 10
        text_y = image.shape[0] - 10

        # Draw black outline
        cv2.putText(
            image,
            timestamp_str,
            (text_x, text_y),
            font,
            font_scale,
            self.config.timestamp_outline_color,
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
            self.config.timestamp_color,
            font_thickness,
            cv2.LINE_AA,
        )

        return image

    async def process_frame_to_jpeg(
        self, image: np.ndarray, quality: int = 80, add_timestamp: bool = False
    ) -> bytes:
        """Process a numpy image array to JPEG bytes with optional timestamp."""
        try:
            # Add timestamp if requested
            if add_timestamp:
                image = self._add_timestamp_to_image(image)

            # Convert to JPEG
            self.logger.info(f"🖼️ Converting to JPEG with quality {quality}")
            ret, jpeg = cv2.imencode(".jpg", image, [cv2.IMWRITE_JPEG_QUALITY, quality])

            if not ret:
                raise ValueError("Could not encode JPEG")

            jpeg_bytes = jpeg.tobytes()
            self.logger.info(
                f"🖼️ JPEG conversion successful, size: {len(jpeg_bytes)} bytes"
            )

            return jpeg_bytes

        except Exception as e:
            self.logger.error(f"🖼️ Error processing frame to JPEG: {e}")
            raise
