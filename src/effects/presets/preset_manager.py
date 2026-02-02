"""
Effect preset management with hardware validation.

Provides PresetManager for saving/loading effect combinations with
hardware compatibility checking and automatic fallbacks.
"""

import json
import logging
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Optional, List, Tuple, Dict, Any

from src.effects.hardware.gpu_detector import HardwareDetector

logger = logging.getLogger(__name__)


@dataclass
class EffectPreset:
    """
    Effect preset containing audio and video effect configurations.

    Attributes:
        name: User-visible preset name
        version: Preset format version (e.g., "1.0")
        audio: Audio effect configuration
        video: Video effect configuration
        hardware_requirements: Hardware requirements for this preset
        created_at: Creation timestamp
        is_builtin: True for built-in presets (read-only)
    """
    name: str
    version: str = "1.0"
    audio: Dict[str, Any] = field(default_factory=dict)
    video: Dict[str, Any] = field(default_factory=dict)
    hardware_requirements: Dict[str, Any] = field(default_factory=dict)
    created_at: datetime = field(default_factory=datetime.now)
    is_builtin: bool = False

    def to_dict(self) -> dict:
        """
        Serialize preset to JSON-compatible dictionary.

        Returns:
            Dictionary representation of preset
        """
        return {
            "name": self.name,
            "version": self.version,
            "audio": self.audio,
            "video": self.video,
            "hardware_requirements": self.hardware_requirements,
            "created_at": self.created_at.isoformat(),
            "is_builtin": self.is_builtin,
        }

    @classmethod
    def from_dict(cls, data: dict) -> "EffectPreset":
        """
        Deserialize preset from dictionary.

        Args:
            data: Dictionary containing preset data

        Returns:
            EffectPreset instance
        """
        # Parse datetime
        created_at = data.get("created_at")
        if isinstance(created_at, str):
            created_at = datetime.fromisoformat(created_at)
        elif created_at is None:
            created_at = datetime.now()

        return cls(
            name=data.get("name", "Unnamed"),
            version=data.get("version", "1.0"),
            audio=data.get("audio", {}),
            video=data.get("video", {}),
            hardware_requirements=data.get("hardware_requirements", {}),
            created_at=created_at,
            is_builtin=data.get("is_builtin", False),
        )


class PresetManager:
    """
    Manages effect preset save/load with hardware validation.

    Provides functionality to save, load, validate, and manage user effect
    presets. Automatically handles hardware compatibility checking and
    CPU fallbacks when GPU effects are unavailable.

    Usage:
        manager = PresetManager()

        # Save preset
        preset = EffectPreset(name="My Setup", audio={...}, video={...})
        manager.save_preset(preset)

        # Load preset
        loaded = manager.load_preset("My Setup")

        # Validate before applying
        valid, msg = manager.validate_preset(loaded)
        if not valid:
            loaded = manager.apply_fallbacks(loaded)
    """

    def __init__(self, presets_dir: Optional[Path] = None):
        """
        Initialize preset manager.

        Args:
            presets_dir: Directory for storing user presets.
                        Defaults to ~/.discordopus/presets/
        """
        if presets_dir is None:
            presets_dir = Path.home() / ".discordopus" / "presets"

        self.presets_dir = Path(presets_dir)
        self.presets_dir.mkdir(parents=True, exist_ok=True)

        # Load hardware detector for validation
        self.hardware = HardwareDetector()

        logger.info(f"PresetManager initialized: {self.presets_dir}")

    def save_preset(self, preset: EffectPreset) -> Path:
        """
        Save preset to disk.

        Args:
            preset: EffectPreset to save

        Returns:
            Path to saved preset file

        Raises:
            ValueError: If trying to save a built-in preset
        """
        if preset.is_builtin:
            raise ValueError("Cannot save built-in presets")

        # Generate filename from preset name
        filename = f"{preset.name}.json"
        filepath = self.presets_dir / filename

        # Serialize to JSON
        with open(filepath, "w") as f:
            json.dump(preset.to_dict(), f, indent=2)

        logger.info(f"Saved preset '{preset.name}' to {filepath}")
        return filepath

    def load_preset(self, name: str) -> EffectPreset:
        """
        Load preset from disk.

        Args:
            name: Preset name (without .json extension)

        Returns:
            Loaded EffectPreset

        Raises:
            FileNotFoundError: If preset doesn't exist
        """
        # First check built-in presets
        from src.effects.presets.built_in_presets import get_preset
        builtin = get_preset(name)
        if builtin is not None:
            return builtin

        # Try loading user preset
        filepath = self.presets_dir / f"{name}.json"

        if not filepath.exists():
            raise FileNotFoundError(f"Preset '{name}' not found")

        with open(filepath, "r") as f:
            data = json.load(f)

        preset = EffectPreset.from_dict(data)
        logger.info(f"Loaded preset '{name}' from {filepath}")
        return preset

    def delete_preset(self, name: str) -> bool:
        """
        Delete a user preset.

        Built-in presets cannot be deleted.

        Args:
            name: Preset name to delete

        Returns:
            True if deleted, False if not found or is built-in
        """
        # Check if it's a built-in preset
        from src.effects.presets.built_in_presets import get_preset
        if get_preset(name) is not None:
            logger.warning(f"Cannot delete built-in preset '{name}'")
            return False

        filepath = self.presets_dir / f"{name}.json"

        if not filepath.exists():
            logger.warning(f"Preset '{name}' not found for deletion")
            return False

        filepath.unlink()
        logger.info(f"Deleted preset '{name}'")
        return True

    def list_presets(self) -> List[str]:
        """
        List all available presets (user + built-in).

        Returns:
            List of preset names
        """
        from src.effects.presets.built_in_presets import get_all_builtin_names

        # Get built-in presets
        presets = set(get_all_builtin_names())

        # Add user presets
        for filepath in self.presets_dir.glob("*.json"):
            presets.add(filepath.stem)

        return sorted(presets)

    def list_user_presets(self) -> List[str]:
        """
        List only user-created presets (excludes built-ins).

        Returns:
            List of user preset names
        """
        return sorted([f.stem for f in self.presets_dir.glob("*.json")])

    def validate_preset(self, preset: EffectPreset) -> Tuple[bool, str]:
        """
        Validate preset hardware compatibility.

        Checks if current hardware can run the preset's requirements.

        Args:
            preset: EffectPreset to validate

        Returns:
            Tuple of (valid, message) where message explains why invalid or "OK"
        """
        hw_reqs = preset.hardware_requirements

        # Check GPU requirement
        requires_gpu = hw_reqs.get("requires_gpu", False)
        if requires_gpu and self.hardware.device == "cpu":
            return False, "Preset requires GPU but only CPU available"

        # Check VRAM requirement (if CUDA available)
        min_vram_mb = hw_reqs.get("min_vram_mb", 0)
        if min_vram_mb > 0 and self.hardware.has_cuda:
            try:
                import torch
                vram_available = torch.cuda.get_device_properties(0).total_memory / (1024 * 1024)
                if vram_available < min_vram_mb:
                    return False, f"Preset requires {min_vram_mb}MB VRAM, only {int(vram_available)}MB available"
            except Exception as e:
                logger.warning(f"Could not check VRAM: {e}")

        # Check for specific effects that require GPU
        audio_config = preset.audio
        if audio_config.get("noise_cancellation") == "deepfilter":
            if self.hardware.device == "cpu":
                return False, "DeepFilter noise cancellation requires GPU"

        return True, "OK"

    def apply_fallbacks(self, preset: EffectPreset) -> EffectPreset:
        """
        Apply hardware fallbacks to preset.

        Substitutes GPU effects with CPU alternatives when GPU unavailable.
        Creates a new preset instance with fallback configuration.

        Args:
            preset: Original preset

        Returns:
            New EffectPreset with CPU-compatible settings
        """
        # Create a copy of the preset
        fallback_audio = preset.audio.copy()
        fallback_video = preset.video.copy()
        fallback_hw = preset.hardware_requirements.copy()

        # Apply audio fallbacks
        if self.hardware.device == "cpu":
            # Substitute DeepFilter with RNNoise
            if fallback_audio.get("noise_cancellation") == "deepfilter":
                fallback_audio["noise_cancellation"] = "rnnoise"
                logger.info("Applied fallback: DeepFilter → RNNoise")

        # Apply video fallbacks
        if self.hardware.device == "cpu":
            # Simplify background processing
            bg_config = fallback_video.get("background", {})
            if isinstance(bg_config, dict):
                bg_type = bg_config.get("type")
                if bg_type in ["replace", "virtual_room"]:
                    fallback_video["background"] = {"type": "blur", "intensity": "medium"}
                    logger.info("Applied fallback: Virtual background → Blur")

            # Reduce beauty filter intensity
            beauty_config = fallback_video.get("beauty_filter", {})
            if isinstance(beauty_config, dict) and beauty_config.get("enabled"):
                intensity = beauty_config.get("intensity", 50)
                if intensity > 30:
                    fallback_video["beauty_filter"]["intensity"] = 30
                    logger.info("Applied fallback: Reduced beauty filter intensity")

        # Update hardware requirements
        fallback_hw["requires_gpu"] = False
        fallback_hw["recommended_quality"] = "medium" if self.hardware.device == "cpu" else "high"

        # Create new preset with fallbacks
        fallback_preset = EffectPreset(
            name=preset.name,
            version=preset.version,
            audio=fallback_audio,
            video=fallback_video,
            hardware_requirements=fallback_hw,
            created_at=preset.created_at,
            is_builtin=preset.is_builtin,
        )

        return fallback_preset

    def export_preset(self, name: str, path: Path) -> Path:
        """
        Export preset to external file for sharing.

        Args:
            name: Preset name to export
            path: Destination file path

        Returns:
            Path to exported file

        Raises:
            FileNotFoundError: If preset doesn't exist
        """
        preset = self.load_preset(name)

        # Ensure path has .json extension
        path = Path(path)
        if path.suffix != ".json":
            path = path.with_suffix(".json")

        # Write to destination
        with open(path, "w") as f:
            json.dump(preset.to_dict(), f, indent=2)

        logger.info(f"Exported preset '{name}' to {path}")
        return path

    def import_preset(self, path: Path) -> EffectPreset:
        """
        Import preset from external file.

        Validates preset before importing to user presets directory.

        Args:
            path: Path to preset file

        Returns:
            Imported EffectPreset

        Raises:
            FileNotFoundError: If file doesn't exist
            ValueError: If preset format is invalid
        """
        path = Path(path)

        if not path.exists():
            raise FileNotFoundError(f"Preset file not found: {path}")

        # Load and validate
        with open(path, "r") as f:
            data = json.load(f)

        preset = EffectPreset.from_dict(data)

        # Validate hardware compatibility
        valid, msg = self.validate_preset(preset)
        if not valid:
            logger.warning(f"Imported preset not compatible: {msg}")
            # Apply fallbacks automatically
            preset = self.apply_fallbacks(preset)

        # Save to user presets
        self.save_preset(preset)

        logger.info(f"Imported preset '{preset.name}' from {path}")
        return preset
