"""
Face tracking using MediaPipe Face Mesh.

Provides real-time face landmark detection with 478 facial landmarks
for AR overlays, face filters, and virtual accessory placement.
"""

import logging
from dataclasses import dataclass
from typing import List, Optional, Tuple
from collections import deque

import numpy as np

logger = logging.getLogger(__name__)

try:
    import mediapipe as mp
    MEDIAPIPE_AVAILABLE = True
except ImportError:
    MEDIAPIPE_AVAILABLE = False
    logger.warning("MediaPipe not available - face tracking will be disabled")


@dataclass
class FaceLandmarks:
    """
    Container for face landmark data.

    Attributes:
        landmarks: List of 478 (x, y, z) normalized coordinates (0.0-1.0)
        image_width: Original image width in pixels
        image_height: Original image height in pixels
    """

    landmarks: List[Tuple[float, float, float]]
    image_width: int
    image_height: int

    # Key landmark indices (MediaPipe Face Mesh standard indices)
    LEFT_EYE_CENTER = 33
    RIGHT_EYE_CENTER = 263
    NOSE_TIP = 1
    LEFT_EAR = 234
    RIGHT_EAR = 454
    CHIN = 152
    FOREHEAD = 10
    LEFT_EYEBROW = 105
    RIGHT_EYEBROW = 334
    UPPER_LIP = 13
    LOWER_LIP = 14

    def get_landmark(self, index: int) -> Tuple[int, int]:
        """
        Get landmark at index in pixel coordinates.

        Args:
            index: Landmark index (0-477)

        Returns:
            Tuple of (x, y) pixel coordinates

        Raises:
            IndexError: If index is out of range
        """
        if index < 0 or index >= len(self.landmarks):
            raise IndexError(f"Landmark index {index} out of range (0-{len(self.landmarks)-1})")

        x_norm, y_norm, _ = self.landmarks[index]
        x_pixel = int(x_norm * self.image_width)
        y_pixel = int(y_norm * self.image_height)

        return (x_pixel, y_pixel)


class FaceTracker:
    """
    Real-time face tracking using MediaPipe Face Mesh.

    Detects 478 facial landmarks with temporal smoothing to reduce jitter.
    Includes "last known good" fallback to handle tracking loss during
    fast motion.

    Usage:
        tracker = FaceTracker(max_faces=1)
        landmarks = tracker.process(frame)
        if landmarks:
            eye_distance = tracker.get_eye_distance(landmarks)
        tracker.close()
    """

    def __init__(
        self,
        max_faces: int = 1,
        refine_landmarks: bool = True,
        min_detection_confidence: float = 0.5,
        min_tracking_confidence: float = 0.5
    ):
        """
        Initialize face tracker.

        Args:
            max_faces: Maximum number of faces to detect
            refine_landmarks: Enable iris tracking for more accurate eye landmarks
            min_detection_confidence: Minimum confidence for initial detection
            min_tracking_confidence: Minimum confidence for tracking (lower = more stable)
        """
        self.max_faces = max_faces
        self.refine_landmarks = refine_landmarks

        # Initialize tracking state (always needed for close() method)
        self._landmark_history = deque(maxlen=3)
        self._last_good_landmarks: Optional[FaceLandmarks] = None
        self._frames_since_detection = 0
        self._max_fallback_frames = 5  # Use fallback for up to 5 frames

        if not MEDIAPIPE_AVAILABLE:
            logger.error("Cannot initialize FaceTracker - MediaPipe not installed")
            self.face_mesh = None
            return

        # Initialize MediaPipe Face Mesh
        try:
            self.mp_face_mesh = mp.solutions.face_mesh
            self.face_mesh = self.mp_face_mesh.FaceMesh(
                static_image_mode=False,
                max_num_faces=max_faces,
                refine_landmarks=refine_landmarks,
                min_detection_confidence=min_detection_confidence,
                min_tracking_confidence=min_tracking_confidence
            )
            logger.info(
                f"FaceTracker initialized: max_faces={max_faces}, "
                f"refine_landmarks={refine_landmarks}"
            )
        except Exception as e:
            logger.error(f"Failed to initialize MediaPipe Face Mesh: {e}")
            self.face_mesh = None

    def process(self, frame: np.ndarray) -> Optional[FaceLandmarks]:
        """
        Process frame and return face landmarks for first detected face.

        Args:
            frame: BGR image as numpy array (OpenCV format)

        Returns:
            FaceLandmarks object if face detected, None otherwise
        """
        if self.face_mesh is None:
            return None

        try:
            # Convert BGR to RGB (MediaPipe requirement)
            frame_rgb = frame[:, :, ::-1]  # Faster than cv2.cvtColor
            h, w = frame.shape[:2]

            # Process with MediaPipe
            results = self.face_mesh.process(frame_rgb)

            if results.multi_face_landmarks:
                # Face detected - extract first face
                face = results.multi_face_landmarks[0]

                # Convert landmarks to list of tuples
                landmarks = [
                    (lm.x, lm.y, lm.z)
                    for lm in face.landmark
                ]

                # Create FaceLandmarks object
                face_landmarks = FaceLandmarks(
                    landmarks=landmarks,
                    image_width=w,
                    image_height=h
                )

                # Apply temporal smoothing
                smoothed_landmarks = self._apply_temporal_smoothing(face_landmarks)

                # Update tracking state
                self._last_good_landmarks = smoothed_landmarks
                self._frames_since_detection = 0

                return smoothed_landmarks

            else:
                # No face detected - use fallback if available
                self._frames_since_detection += 1

                if (self._last_good_landmarks and
                    self._frames_since_detection <= self._max_fallback_frames):
                    logger.debug(
                        f"No face detected, using fallback "
                        f"(frame {self._frames_since_detection}/{self._max_fallback_frames})"
                    )
                    return self._last_good_landmarks

                # Fallback expired
                return None

        except Exception as e:
            logger.error(f"Error processing frame in FaceTracker: {e}")
            return None

    def process_all(self, frame: np.ndarray) -> List[FaceLandmarks]:
        """
        Process frame and return landmarks for all detected faces.

        Args:
            frame: BGR image as numpy array (OpenCV format)

        Returns:
            List of FaceLandmarks objects (empty if no faces detected)
        """
        if self.face_mesh is None:
            return []

        try:
            # Convert BGR to RGB
            frame_rgb = frame[:, :, ::-1]
            h, w = frame.shape[:2]

            # Process with MediaPipe
            results = self.face_mesh.process(frame_rgb)

            if not results.multi_face_landmarks:
                return []

            # Extract all faces
            all_faces = []
            for face in results.multi_face_landmarks:
                landmarks = [
                    (lm.x, lm.y, lm.z)
                    for lm in face.landmark
                ]

                face_landmarks = FaceLandmarks(
                    landmarks=landmarks,
                    image_width=w,
                    image_height=h
                )

                all_faces.append(face_landmarks)

            return all_faces

        except Exception as e:
            logger.error(f"Error processing all faces: {e}")
            return []

    def _apply_temporal_smoothing(self, landmarks: FaceLandmarks) -> FaceLandmarks:
        """
        Apply temporal smoothing to reduce landmark jitter.

        Averages landmarks with previous 2-3 frames to smooth motion.

        Args:
            landmarks: Current frame's landmarks

        Returns:
            Smoothed landmarks
        """
        # Add current landmarks to history
        self._landmark_history.append(landmarks.landmarks)

        if len(self._landmark_history) < 2:
            # Not enough history - return original
            return landmarks

        # Average landmarks across history
        num_frames = len(self._landmark_history)
        num_landmarks = len(landmarks.landmarks)

        smoothed = []
        for i in range(num_landmarks):
            # Average each landmark across frames
            x_sum = sum(frame[i][0] for frame in self._landmark_history)
            y_sum = sum(frame[i][1] for frame in self._landmark_history)
            z_sum = sum(frame[i][2] for frame in self._landmark_history)

            x_avg = x_sum / num_frames
            y_avg = y_sum / num_frames
            z_avg = z_sum / num_frames

            smoothed.append((x_avg, y_avg, z_avg))

        return FaceLandmarks(
            landmarks=smoothed,
            image_width=landmarks.image_width,
            image_height=landmarks.image_height
        )

    def get_eye_distance(self, landmarks: FaceLandmarks) -> float:
        """
        Calculate distance between eye centers in pixels.

        Useful for scaling AR overlays (glasses, masks) to face size.

        Args:
            landmarks: Face landmarks

        Returns:
            Distance in pixels
        """
        try:
            left_eye = landmarks.get_landmark(FaceLandmarks.LEFT_EYE_CENTER)
            right_eye = landmarks.get_landmark(FaceLandmarks.RIGHT_EYE_CENTER)

            distance = np.sqrt(
                (right_eye[0] - left_eye[0]) ** 2 +
                (right_eye[1] - left_eye[1]) ** 2
            )

            return float(distance)

        except (IndexError, ValueError) as e:
            logger.error(f"Error calculating eye distance: {e}")
            return 0.0

    def get_face_angle(self, landmarks: FaceLandmarks) -> Tuple[float, float, float]:
        """
        Estimate face rotation angles (yaw, pitch, roll) from landmarks.

        Uses key facial points to estimate 3D head orientation.
        Useful for rotating AR overlays to match face angle.

        Args:
            landmarks: Face landmarks

        Returns:
            Tuple of (yaw, pitch, roll) in degrees
        """
        try:
            # Get key points for angle estimation
            nose = np.array(landmarks.get_landmark(FaceLandmarks.NOSE_TIP))
            chin = np.array(landmarks.get_landmark(FaceLandmarks.CHIN))
            left_eye = np.array(landmarks.get_landmark(FaceLandmarks.LEFT_EYE_CENTER))
            right_eye = np.array(landmarks.get_landmark(FaceLandmarks.RIGHT_EYE_CENTER))
            forehead = np.array(landmarks.get_landmark(FaceLandmarks.FOREHEAD))

            # Calculate roll (head tilt left/right)
            eye_center = (left_eye + right_eye) / 2.0
            dx = right_eye[0] - left_eye[0]
            dy = right_eye[1] - left_eye[1]
            roll = np.degrees(np.arctan2(dy, dx))

            # Calculate pitch (head tilt up/down)
            # Simplified estimation based on nose-chin vertical distance
            face_height = np.linalg.norm(forehead - chin)
            nose_chin_distance = np.linalg.norm(nose - chin)
            pitch_ratio = nose_chin_distance / face_height if face_height > 0 else 0.5
            pitch = (pitch_ratio - 0.5) * 60  # Scale to approximate degrees

            # Calculate yaw (head turn left/right)
            # Based on horizontal offset of nose from eye center
            nose_offset = nose[0] - eye_center[0]
            eye_distance = np.linalg.norm(right_eye - left_eye)
            yaw = (nose_offset / eye_distance) * 45 if eye_distance > 0 else 0  # Scale to degrees

            return (float(yaw), float(pitch), float(roll))

        except (IndexError, ValueError, ZeroDivisionError) as e:
            logger.error(f"Error calculating face angle: {e}")
            return (0.0, 0.0, 0.0)

    def close(self):
        """Release MediaPipe resources."""
        if self.face_mesh:
            self.face_mesh.close()
            self.face_mesh = None
            logger.info("FaceTracker closed")

        self._landmark_history.clear()
        self._last_good_landmarks = None
