"""
Abstract base class for TTS (Text-to-Speech) services.

This module defines the interface that all TTS providers must implement,
following the Interface Segregation Principle (ISP) and Dependency Inversion
Principle (DIP) from SOLID.
"""

from abc import ABC, abstractmethod
from pathlib import Path
from typing import List, Dict, Any, Optional


class BaseTTSService(ABC):
    """
    Abstract base class defining the TTS service interface.

    All TTS providers (edge-tts, Chatterbox, etc.) must implement this interface.
    This enables easy switching between providers without changing client code.
    """

    def __init__(self):
        """Initialize the TTS service with common directories."""
        from app.config import settings

        self.output_dir = Path(settings.static_dir) / "audio"
        self.preview_dir = Path(settings.static_dir) / "previews"

    @abstractmethod
    async def generate_scene_audio(
        self,
        project_id: str,
        scene_id: str,
        text: str,
        voice_id: str,
        rate: str = "+0%",
        pitch: str = "+0Hz",
    ) -> str:
        """
        Generate audio for a script scene.

        Args:
            project_id: The project identifier
            scene_id: The scene identifier
            text: The text to synthesize
            voice_id: The voice identifier (provider-specific)
            rate: Speech rate adjustment (e.g., "+10%", "-5%")
            pitch: Pitch adjustment (e.g., "+5Hz", "-3Hz")

        Returns:
            Relative path to the generated audio file
        """
        pass

    @abstractmethod
    async def generate_preview(
        self, text: str, voice_id: str, rate: str = "+0%", pitch: str = "+0Hz"
    ) -> str:
        """
        Generate a preview audio file.

        Args:
            text: The text to synthesize
            voice_id: The voice identifier
            rate: Speech rate adjustment
            pitch: Pitch adjustment

        Returns:
            Relative path to the generated preview file
        """
        pass

    @abstractmethod
    async def get_voices(self) -> List[Dict[str, Any]]:
        """
        Get list of available voices for this provider.

        Returns:
            List of voice dictionaries with keys:
            - voice_id: Unique identifier
            - name: Display name
            - gender: Voice gender
            - locale: Language/locale code
        """
        pass

    @property
    @abstractmethod
    def provider_name(self) -> str:
        """Return the provider name for logging and identification."""
        pass
