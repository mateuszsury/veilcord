"""
Video effects track wrapper for aiortc MediaStreamTrack.

Wraps CameraVideoTrack or ScreenShareTrack with real-time video
effect processing via VideoEffectsPipeline.
"""

import asyncio
import logging
import threading
import time
from typing import Optional, List

import numpy as np
from aiortc import VideoStreamTrack
from av import VideoFrame

from src.effects.video.virtual_background import VirtualBackground
from src.effects.video.beauty_filters import BeautyFilter, VideoEffect
from src.effects.video.ar_overlays import AROverlayManager

logger = logging.getLogger(__name__)


class VideoEffectsPipeline:
    """
    Pipeline for orchestrating multiple video effects.

    Applies effects in the correct order:
    1. Virtual background (if enabled)
    2. Beauty filter (if enabled)
    3. Creative filters (in order)
    4. AR overlays (if enabled)

    Usage:
        pipeline = VideoEffectsPipeline()
        pipeline.virtual_background = VirtualBackground()
        pipeline.virtual_background.set_blur(50)

        result = await pipeline.process(frame)
    """

    def __init__(self):
        """Initialize empty video effects pipeline."""
        self.virtual_background: Optional[VirtualBackground] = None
        self.beauty_filter: Optional[BeautyFilter] = None
        self.creative_filters: List[VideoEffect] = []
        self.ar_overlay_manager: Optional[AROverlayManager] = None

    async def process(self, frame: np.ndarray) -> np.ndarray:
        """
        Apply all enabled effects in order.

        Args:
            frame: BGR image as numpy array

        Returns:
            Processed BGR image
        """
        result = frame

        # 1. Virtual background (background replacement/blur)
        if self.virtual_background and self.virtual_background.enabled:
            try:
                result = self.virtual_background.process(result)
            except Exception as e:
                logger.error(f"Virtual background error: {e}")

        # 2. Beauty filter (skin smoothing, lighting)
        if self.beauty_filter and self.beauty_filter.enabled:
            try:
                result = self.beauty_filter.process(result)
            except Exception as e:
                logger.error(f"Beauty filter error: {e}")

        # 3. Creative filters (color grading, effects)
        for creative_filter in self.creative_filters:
            if creative_filter.enabled:
                try:
                    result = creative_filter.process(result)
                except Exception as e:
                    logger.error(f"Creative filter error: {e}")

        # 4. AR overlays (face filters, stickers)
        if self.ar_overlay_manager:
            try:
                result = self.ar_overlay_manager.process(result)
            except Exception as e:
                logger.error(f"AR overlay error: {e}")

        return result

    def get_latency_ms(self) -> float:
        """
        Estimate total pipeline latency.

        Returns:
            Estimated processing time in milliseconds
        """
        total_ms = 0.0

        # Virtual background: ~20-50ms depending on model
        if self.virtual_background and self.virtual_background.enabled:
            total_ms += 35.0  # Average estimate

        # Beauty filter: ~5-15ms
        if self.beauty_filter and self.beauty_filter.enabled:
            total_ms += 10.0

        # Creative filters: ~5ms each
        total_ms += len([f for f in self.creative_filters if f.enabled]) * 5.0

        # AR overlays: ~10-30ms depending on complexity
        if self.ar_overlay_manager and self.ar_overlay_manager.overlays:
            total_ms += 20.0

        return total_ms


class VideoEffectsTrack(VideoStreamTrack):
    """
    VideoStreamTrack wrapper that applies effects in real-time.

    Wraps a source video track (like CameraVideoTrack or ScreenShareTrack)
    and processes frames through a VideoEffectsPipeline before passing to WebRTC.

    Uses threading to prevent frame drops when processing is slow.
    Effects can be toggled or swapped mid-call without interruption.

    Usage:
        # Wrap camera track with effects
        camera_track = CameraVideoTrack()
        pipeline = VideoEffectsPipeline()
        effects_track = VideoEffectsTrack(
            source_track=camera_track,
            pipeline=pipeline
        )
        pc.addTrack(effects_track)

        # Toggle effects mid-call
        effects_track.effects_enabled = False

        # Swap pipeline mid-call
        effects_track.set_pipeline(new_pipeline)
    """

    kind = "video"

    def __init__(
        self,
        source_track: VideoStreamTrack,
        pipeline: Optional[VideoEffectsPipeline] = None
    ):
        """
        Initialize video effects track.

        Args:
            source_track: Source video track to wrap (e.g., CameraVideoTrack)
            pipeline: Effect pipeline to apply, or None for empty pipeline
        """
        super().__init__()
        self._source_track = source_track
        self._pipeline = pipeline if pipeline is not None else VideoEffectsPipeline()
        self._effects_enabled = True

        # Threading for async processing
        self._lock = threading.Lock()
        self._processing = False
        self._last_processed_frame: Optional[np.ndarray] = None
        self._last_raw_frame: Optional[np.ndarray] = None

        # Performance monitoring
        self._processing_times = []
        self._frame_skip_count = 0

        logger.info(f"VideoEffectsTrack initialized wrapping {type(source_track).__name__}")

    @property
    def source_track(self) -> VideoStreamTrack:
        """Get the wrapped source track."""
        return self._source_track

    @property
    def pipeline(self) -> VideoEffectsPipeline:
        """Get the current effect pipeline."""
        return self._pipeline

    @pipeline.setter
    def pipeline(self, new_pipeline: VideoEffectsPipeline):
        """
        Set new effect pipeline (can be changed mid-call).

        Thread-safe: acquires lock to prevent race conditions.

        Args:
            new_pipeline: New VideoEffectsPipeline to use
        """
        with self._lock:
            self._pipeline = new_pipeline
            logger.info("Effect pipeline updated")

    def set_pipeline(self, new_pipeline: VideoEffectsPipeline):
        """
        Set new effect pipeline (convenience method).

        Args:
            new_pipeline: New VideoEffectsPipeline to use
        """
        self.pipeline = new_pipeline

    @property
    def effects_enabled(self) -> bool:
        """Check if effects are enabled."""
        return self._effects_enabled

    @effects_enabled.setter
    def effects_enabled(self, value: bool):
        """
        Enable or disable effects (master toggle).

        When disabled, video passes through unprocessed.

        Args:
            value: True to enable effects, False to disable
        """
        self._effects_enabled = value
        logger.info(f"Video effects {'enabled' if value else 'disabled'}")

    async def recv(self) -> VideoFrame:
        """
        Receive and process video frame.

        Gets frame from source track, applies effects if enabled,
        and returns processed frame.

        Uses frame skipping strategy: if processing is slow, returns
        the last processed frame rather than blocking.

        Returns:
            Processed VideoFrame with effects applied

        Raises:
            Exception: If source track fails
        """
        # Get frame from source track
        frame = await self._source_track.recv()

        # If effects disabled or no pipeline, return original
        if not self._effects_enabled or not self._pipeline:
            return frame

        try:
            # Convert frame to numpy (BGR)
            img = self._frame_to_numpy(frame)

            # Store raw frame for processing
            with self._lock:
                self._last_raw_frame = img

            # If already processing, return previous processed frame (frame skipping)
            if self._processing:
                with self._lock:
                    if self._last_processed_frame is not None:
                        self._frame_skip_count += 1
                        if self._frame_skip_count % 30 == 0:  # Log every 30 skips
                            logger.warning(
                                f"Video processing slow: skipped {self._frame_skip_count} frames. "
                                "Consider reducing effect quality."
                            )
                        return self._numpy_to_frame(self._last_processed_frame, frame)
                    else:
                        # No processed frame yet, return original
                        return frame

            # Mark as processing
            self._processing = True

            try:
                # Start processing timer
                start_time = time.perf_counter()

                # Process through pipeline
                processed_img = await self._pipeline.process(img)

                # Monitor processing time
                processing_time_ms = (time.perf_counter() - start_time) * 1000
                self._monitor_performance(processing_time_ms)

                # Store processed frame
                with self._lock:
                    self._last_processed_frame = processed_img

                # Convert back to VideoFrame
                processed_frame = self._numpy_to_frame(processed_img, frame)

                return processed_frame

            finally:
                # Always clear processing flag
                self._processing = False

        except Exception as e:
            logger.error(f"Error processing video effects: {e}")
            self._processing = False
            # Return original frame on error
            return frame

    def _frame_to_numpy(self, frame: VideoFrame) -> np.ndarray:
        """
        Convert av.VideoFrame to numpy array (BGR).

        Args:
            frame: Input VideoFrame

        Returns:
            BGR image as numpy array (H, W, 3)
        """
        # Use av's built-in conversion to BGR24
        img = frame.to_ndarray(format="bgr24")
        return img

    def _numpy_to_frame(self, img: np.ndarray, template: VideoFrame) -> VideoFrame:
        """
        Create VideoFrame from numpy array.

        Preserves timing information from template frame.

        Args:
            img: Processed BGR image as numpy array
            template: Original frame for timing metadata

        Returns:
            New VideoFrame with processed video
        """
        # Create VideoFrame from BGR numpy array
        new_frame = VideoFrame.from_ndarray(img, format="bgr24")

        # Copy timing metadata from template
        new_frame.pts = template.pts
        new_frame.time_base = template.time_base

        return new_frame

    def _monitor_performance(self, processing_time_ms: float):
        """
        Monitor processing time and warn if excessive.

        Tracks rolling average and warns if processing exceeds
        frame time (~33ms for 30fps).

        Args:
            processing_time_ms: Processing time in milliseconds
        """
        self._processing_times.append(processing_time_ms)

        # Keep last 30 measurements (1 second at 30fps)
        if len(self._processing_times) > 30:
            self._processing_times.pop(0)

        # Warn if exceeds frame time
        frame_time_ms = 33.3  # 30fps
        if processing_time_ms > frame_time_ms:
            avg_time = sum(self._processing_times) / len(self._processing_times)
            logger.warning(
                f"Video effect processing time ({processing_time_ms:.1f}ms) "
                f"exceeds frame time ({frame_time_ms:.1f}ms). "
                f"Average: {avg_time:.1f}ms. "
                "Consider reducing effect quality or disabling some effects."
            )

    async def stop(self):
        """
        Stop the effects track and source track.

        Cleans up resources and stops underlying source track.
        """
        try:
            # Stop source track
            if self._source_track:
                await self._source_track.stop()

            # Clean up pipeline resources
            if self._pipeline:
                # Close face tracker if using AR overlays
                if self._pipeline.ar_overlay_manager:
                    try:
                        self._pipeline.ar_overlay_manager.close()
                    except Exception as e:
                        logger.debug(f"Error closing AR overlay manager: {e}")

                # Close background segmenter if using virtual background
                if self._pipeline.virtual_background:
                    try:
                        if hasattr(self._pipeline.virtual_background, 'segmenter'):
                            self._pipeline.virtual_background.segmenter.close()
                    except Exception as e:
                        logger.debug(f"Error closing background segmenter: {e}")

            logger.info("VideoEffectsTrack stopped")

        except Exception as e:
            logger.error(f"Error stopping VideoEffectsTrack: {e}")

    def get_average_processing_time_ms(self) -> float:
        """
        Get average processing time over recent frames.

        Returns:
            Average processing time in milliseconds
        """
        if not self._processing_times:
            return 0.0
        return sum(self._processing_times) / len(self._processing_times)

    def get_frame_skip_count(self) -> int:
        """
        Get count of frames skipped due to slow processing.

        Returns:
            Number of skipped frames since track start
        """
        return self._frame_skip_count
