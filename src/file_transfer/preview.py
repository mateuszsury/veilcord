"""
Image and video preview/thumbnail generation.

Uses Pillow for image thumbnails and ffmpeg for video frame extraction.
All thumbnails are JPEG format at 85% quality, max 300x300px.
"""

import io
import base64
import hashlib
from typing import Optional, Dict
from pathlib import Path

try:
    from PIL import Image, ImageOps
    PILLOW_AVAILABLE = True
except ImportError:
    PILLOW_AVAILABLE = False

try:
    import ffmpeg
    FFMPEG_AVAILABLE = True
except ImportError:
    FFMPEG_AVAILABLE = False

# Thumbnail settings
THUMBNAIL_SIZE = (300, 300)
THUMBNAIL_QUALITY = 85


def generate_image_thumbnail(image_data: bytes, max_size: tuple[int, int] = THUMBNAIL_SIZE) -> Optional[bytes]:
    """
    Generate JPEG thumbnail from image data.

    Handles EXIF rotation automatically.

    Args:
        image_data: Raw image bytes (any PIL-supported format)
        max_size: Maximum dimensions (width, height) - maintains aspect ratio

    Returns:
        JPEG thumbnail bytes or None if error
    """
    if not PILLOW_AVAILABLE:
        return None

    try:
        # Open image
        img = Image.open(io.BytesIO(image_data))

        # Handle EXIF rotation
        img = ImageOps.exif_transpose(img)

        # Convert to RGB if needed (handles RGBA, P, etc.)
        if img.mode not in ('RGB', 'L'):
            img = img.convert('RGB')

        # Create thumbnail (maintains aspect ratio)
        img.thumbnail(max_size, Image.Resampling.LANCZOS)

        # Save as JPEG
        output = io.BytesIO()
        img.save(output, format='JPEG', quality=THUMBNAIL_QUALITY, optimize=True)

        return output.getvalue()

    except Exception as e:
        print(f"Error generating image thumbnail: {e}")
        return None


def generate_video_thumbnail_from_data(
    video_data: bytes,
    timestamp_seconds: float = 1.0,
    max_size: tuple[int, int] = THUMBNAIL_SIZE
) -> Optional[bytes]:
    """
    Generate JPEG thumbnail from video data.

    Saves video to temp file and extracts frame via ffmpeg.

    Args:
        video_data: Raw video bytes
        timestamp_seconds: Time in video to extract frame (default 1.0s)
        max_size: Maximum dimensions (width, height)

    Returns:
        JPEG thumbnail bytes or None if error
    """
    if not FFMPEG_AVAILABLE or not PILLOW_AVAILABLE:
        return None

    import tempfile
    import os

    try:
        # Save to temp file
        with tempfile.NamedTemporaryFile(delete=False, suffix='.mp4') as tmp:
            tmp.write(video_data)
            tmp_path = tmp.name

        try:
            # Extract frame
            result = generate_video_thumbnail(tmp_path, timestamp_seconds, max_size)
            return result
        finally:
            # Clean up temp file
            if os.path.exists(tmp_path):
                os.unlink(tmp_path)

    except Exception as e:
        print(f"Error generating video thumbnail from data: {e}")
        return None


def generate_video_thumbnail(
    video_path: str,
    timestamp_seconds: float = 1.0,
    max_size: tuple[int, int] = THUMBNAIL_SIZE
) -> Optional[bytes]:
    """
    Generate JPEG thumbnail from video file.

    Uses ffmpeg to extract a frame at specified timestamp.

    Args:
        video_path: Path to video file
        timestamp_seconds: Time in video to extract frame (default 1.0s)
        max_size: Maximum dimensions (width, height)

    Returns:
        JPEG thumbnail bytes or None if error
    """
    if not FFMPEG_AVAILABLE or not PILLOW_AVAILABLE:
        return None

    try:
        # Extract frame using ffmpeg
        # -ss: seek to timestamp
        # -i: input file
        # -vframes 1: extract one frame
        # -f image2pipe: output to pipe
        # -vcodec png: use PNG for lossless intermediate
        out, _ = (
            ffmpeg
            .input(video_path, ss=timestamp_seconds)
            .output('pipe:', vframes=1, format='image2pipe', vcodec='png')
            .run(capture_stdout=True, capture_stderr=True, quiet=True)
        )

        # Convert PNG frame to JPEG thumbnail
        return generate_image_thumbnail(out, max_size)

    except ffmpeg.Error as e:
        print(f"FFmpeg error generating video thumbnail: {e.stderr.decode() if e.stderr else str(e)}")
        return None
    except Exception as e:
        print(f"Error generating video thumbnail: {e}")
        return None


class PreviewGenerator:
    """
    Preview generator with optional caching.

    Caches generated thumbnails by file_id to avoid regeneration.
    """

    def __init__(self, enable_cache: bool = True):
        """
        Args:
            enable_cache: If True, cache thumbnails in memory by file_id
        """
        self.enable_cache = enable_cache
        self._cache: Dict[str, bytes] = {}

    def get_preview(
        self,
        data: bytes,
        mime_type: str,
        file_id: Optional[str] = None
    ) -> Optional[bytes]:
        """
        Generate preview for file data.

        Args:
            data: File bytes
            mime_type: MIME type (e.g., 'image/png', 'video/mp4')
            file_id: Optional identifier for caching

        Returns:
            JPEG thumbnail bytes or None if unsupported/error
        """
        # Check cache first
        if file_id and self.enable_cache and file_id in self._cache:
            return self._cache[file_id]

        # Generate preview based on MIME type
        preview = None

        if mime_type.startswith('image/'):
            preview = generate_image_thumbnail(data)
        elif mime_type.startswith('video/'):
            preview = generate_video_thumbnail_from_data(data)

        # Cache if successful
        if preview and file_id and self.enable_cache:
            self._cache[file_id] = preview

        return preview

    def clear_cache(self):
        """Clear cached thumbnails."""
        self._cache.clear()


# Module-level convenience function
_generator: Optional[PreviewGenerator] = None


def get_preview_generator() -> PreviewGenerator:
    """Get or create singleton PreviewGenerator."""
    global _generator
    if _generator is None:
        _generator = PreviewGenerator()
    return _generator


def get_preview(data: bytes, mime_type: str, file_id: Optional[str] = None) -> Optional[bytes]:
    """
    Generate preview using singleton generator.

    Args:
        data: File bytes
        mime_type: MIME type
        file_id: Optional identifier for caching

    Returns:
        JPEG thumbnail bytes or None
    """
    return get_preview_generator().get_preview(data, mime_type, file_id)
