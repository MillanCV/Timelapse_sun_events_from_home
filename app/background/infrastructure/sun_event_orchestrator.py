import logging
from typing import Optional

from ...camera.application.use_cases import (
    StartTimelapseRecordingRequest,
    StartTimelapseRecordingUseCase,
)
from ...camera.domain.services import CameraControlService, TimelapseScriptGenerator
from ...sun_events.domain.entities import SunEventPeriod
from ...sun_events.domain.repositories import SunEventRepository
from ...timelapse.application.use_cases import (
    CalculateTimelapseRequest,
    CalculateTimelapseUseCase,
)
from ...video_processing.infrastructure.ffmpeg_video_processor import (
    FFmpegVideoProcessor,
)


class SunEventOrchestrator:
    """Orchestrates actions when sun events occur."""

    def __init__(
        self,
        sun_event_repository: SunEventRepository,
        timelapse_use_case: CalculateTimelapseUseCase,
        camera_control_service: CameraControlService,
        script_generator: TimelapseScriptGenerator,
        video_processor: FFmpegVideoProcessor,
    ):
        self.sun_event_repository = sun_event_repository
        self.timelapse_use_case = timelapse_use_case
        self.camera_control_service = camera_control_service
        self.script_generator = script_generator
        self.video_processor = video_processor

        # Initialize camera use cases
        self.start_recording_use_case = StartTimelapseRecordingUseCase(
            camera_control_service, script_generator
        )

        self.logger = logging.getLogger(__name__)
        self._current_recording_period: Optional[SunEventPeriod] = None

    async def handle_period_start(self, period: SunEventPeriod):
        """Handle the start of a sun event period."""
        try:
            # 1. Log the event
            self._log_period_start(period)

            # 2. Calculate timelapse parameters
            timelapse_params = await self._calculate_timelapse_parameters(period)

            # 3. Start camera recording if parameters are available
            if timelapse_params:
                await self._start_camera_recording(period, timelapse_params)
                self._current_recording_period = period

        except Exception as e:
            self.logger.error(f"Error handling period start: {e}")

    async def handle_period_end(self, period: SunEventPeriod):
        """Handle the end of a sun event period."""
        try:
            # 1. Log the event
            self._log_period_end(period)

            # 2. Process video for the completed recording
            # Camera will have stopped automatically when it finished taking pictures
            if (
                self._current_recording_period
                and self._current_recording_period == period
            ):
                await self._process_video(period)
                self._current_recording_period = None

        except Exception as e:
            self.logger.error(f"Error handling period end: {e}")

    async def _calculate_timelapse_parameters(self, period: SunEventPeriod):
        """Calculate and log timelapse parameters."""
        try:
            response = self.timelapse_use_case.execute(
                CalculateTimelapseRequest(period_type=period.period_type)
            )

            params = response.timelapse_parameters
            self.logger.info(
                f"📹 TIMELAPSE PARAMETERS for {period.period_type.upper()}:\n"
                f"   Period: {params.start_time.strftime('%H:%M:%S')} - "
                f"{params.end_time.strftime('%H:%M:%S')}\n"
                f"   Total duration: {params.total_duration_seconds / 60:.1f} minutes\n"
                f"   Video: {params.video_duration_seconds}s at {params.video_fps}fps\n"
                f"   Photos needed: {params.photos_needed}\n"
                f"   Interval: {params.interval_seconds:.1f} seconds\n"
                f"   Estimated size: {params.estimated_file_size_mb:.1f} MB"
            )

            return params

        except Exception as e:
            self.logger.error(f"Error calculating timelapse parameters: {e}")
            return None

    async def _start_camera_recording(self, period: SunEventPeriod, timelapse_params):
        """Start camera recording for timelapse."""
        try:
            # Check if camera is connected
            if not await self.camera_control_service.is_camera_connected():
                self.logger.warning("Camera not connected, skipping recording")
                return

            # Create recording request
            request = StartTimelapseRecordingRequest(
                shots=timelapse_params.photos_needed,
                interval_seconds=timelapse_params.interval_seconds,
                output_directory="/home/arrumada/Images",  # Could be configurable
                period_type=period.period_type,
                start_time=period.start_time,
                end_time=period.end_time,
            )

            # Start recording
            response = self.start_recording_use_case.execute(request)

            if response.success:
                self.logger.info(f"📸 Camera recording started: {response.message}")
                self.logger.info(
                    f"📸 Will take {timelapse_params.photos_needed} photos "
                    f"every {timelapse_params.interval_seconds:.1f} seconds"
                )
            else:
                self.logger.error(
                    f"📸 Failed to start camera recording: {response.message}"
                )

        except Exception as e:
            self.logger.error(f"Error starting camera recording: {e}")

    async def _process_video(self, period: SunEventPeriod):
        """Process video for completed recording."""
        try:
            self.logger.info(f"🎬 Starting video processing for {period.period_type}")

            # Process video directly
            success = await self.video_processor.create_video_from_photos(
                photos_directory="/home/arrumada/Images",
                output_video_path=f"/home/arrumada/Videos/{period.period_type}_{period.event_date.strftime('%Y%m%d')}.mp4",
                fps=60,
                video_duration_seconds=20,
                quality="high",
            )

            if success:
                self.logger.info(
                    f"🎬 Video processing completed for {period.period_type}"
                )
            else:
                self.logger.error(
                    f"🎬 Video processing failed for {period.period_type}"
                )

        except Exception as e:
            self.logger.error(f"Error processing video: {e}")

    def _log_period_start(self, period: SunEventPeriod):
        """Log when a sun event period starts."""
        duration_minutes = (period.end_time - period.start_time).total_seconds() / 60

        self.logger.info(
            f"🌅 {period.period_type.upper()} PERIOD STARTING\n"
            f"   Date: {period.event_date.strftime('%Y-%m-%d')}\n"
            f"   Start: {period.start_time.strftime('%H:%M:%S')}\n"
            f"   End: {period.end_time.strftime('%H:%M:%S')}\n"
            f"   Duration: {duration_minutes:.0f} minutes"
        )

    def _log_period_end(self, period: SunEventPeriod):
        """Log when a sun event period ends."""
        duration_minutes = (period.end_time - period.start_time).total_seconds() / 60

        self.logger.info(
            f"🌅 {period.period_type.upper()} PERIOD ENDED\n"
            f"   Date: {period.event_date.strftime('%Y-%m-%d')}\n"
            f"   Duration: {duration_minutes:.0f} minutes"
        )
