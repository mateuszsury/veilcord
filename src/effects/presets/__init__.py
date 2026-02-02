"""
Effect preset management.

Provides preset save/load functionality for audio and video effects,
allowing users to save and quickly apply effect combinations.
"""

from src.effects.presets.preset_manager import PresetManager, EffectPreset
from src.effects.presets.built_in_presets import (
    BUILT_IN_PRESETS,
    get_preset,
    get_all_builtin_names
)

__all__ = [
    "PresetManager",
    "EffectPreset",
    "BUILT_IN_PRESETS",
    "get_preset",
    "get_all_builtin_names",
]
