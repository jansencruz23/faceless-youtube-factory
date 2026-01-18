"""
Edge-TTS Service - Text-to-Speech using Microsoft Edge TTS.

This module provides TTS functionality using the edge-tts library,
implementing the BaseTTSService interface.
"""

import re
from pathlib import Path
from typing import List, Dict, Any
from uuid import uuid4

import edge_tts

from app.services.base_tts_service import BaseTTSService
from app.config import settings
from app.utils.logging import get_logger

logger = get_logger(__name__)


def sanitize_text_for_tts(text: str) -> str:
    """
    Sanitize text to prevent edge-tts from generating corrupted audio.

    Removes or replaces characters that can cause issues:
    - Emojis and special Unicode characters
    - Control characters
    - Excessive whitespace
    - Characters that conflict with SSML
    """
    if not text:
        return ""

    # Remove emojis and special unicode characters (keep basic Latin, punctuation, numbers)
    text = re.sub(r'[^\w\s.,!?;:\'"()\-–—…\u00C0-\u024F]', "", text, flags=re.UNICODE)

    # Remove control characters
    text = re.sub(r"[\x00-\x1f\x7f-\x9f]", "", text)

    # Replace multiple spaces/newlines with single space
    text = re.sub(r"\s+", " ", text)

    # Escape characters that might conflict with SSML
    text = text.replace("&", "and")
    text = text.replace("<", "")
    text = text.replace(">", "")

    # Strip leading/trailing whitespace
    text = text.strip()

    # Ensure we have some text
    if not text:
        text = "..."

    return text


class EdgeTTSService(BaseTTSService):
    """
    TTS service implementation using Microsoft Edge TTS.

    Provides access to a wide variety of high-quality neural voices
    across many languages and locales.
    """

    @property
    def provider_name(self) -> str:
        return "edge_tts"

    async def get_voices(self) -> List[Dict[str, Any]]:
        """Get list of available edge-tts voices."""
        try:
            voices = await edge_tts.list_voices()
            return [
                {
                    "voice_id": v["ShortName"],
                    "name": v["FriendlyName"],
                    "gender": v["Gender"],
                    "locale": v["Locale"],
                    "tags": v.get("VoiceTag", {}),
                    "provider": "edge_tts",
                }
                for v in voices
            ]
        except Exception as e:
            logger.error("Failed to get voices", error=str(e))
            return []

    async def generate_preview(
        self, text: str, voice_id: str, rate: str = "+0%", pitch: str = "+0Hz"
    ) -> str:
        """Generate a temporary preview audio file."""
        self.preview_dir.mkdir(parents=True, exist_ok=True)

        filename = f"{uuid4()}.mp3"
        output_path = self.preview_dir / filename

        return await self._generate_file(
            text=text,
            voice_id=voice_id,
            rate=rate,
            pitch=pitch,
            output_path=output_path,
        )

    async def generate_scene_audio(
        self,
        project_id: str,
        scene_id: str,
        text: str,
        voice_id: str,
        rate: str = "+0%",
        pitch: str = "+0Hz",
    ) -> str:
        """Generate audio for a script scene."""
        # Create project-specific directory
        project_dir = self.output_dir / str(project_id)
        project_dir.mkdir(parents=True, exist_ok=True)

        filename = f"{scene_id}.mp3"
        output_path = project_dir / filename

        return await self._generate_file(
            text=text,
            voice_id=voice_id,
            rate=rate,
            pitch=pitch,
            output_path=output_path,
        )

    async def _generate_file(
        self, text: str, voice_id: str, rate: str, pitch: str, output_path: Path
    ) -> str:
        """Internal method to generate audio file using edge-tts."""
        try:
            clean_text = sanitize_text_for_tts(text)

            logger.debug(
                "Generating Edge-TTS audio",
                voice_id=voice_id,
                text_preview=clean_text[:50],
                rate=rate,
                pitch=pitch,
            )

            communicate = edge_tts.Communicate(
                clean_text, voice_id, rate=rate, pitch=pitch
            )

            await communicate.save(str(output_path))

            # Verify the file was created and has content
            if not output_path.exists():
                raise RuntimeError(f"Audio file was not created: {output_path}")

            file_size = output_path.stat().st_size
            if file_size < 100:
                logger.warning(
                    "Generated audio file is suspiciously small",
                    path=str(output_path),
                    size=file_size,
                )

            # Return path relative to static dir
            relative_path = output_path.relative_to(Path(settings.static_dir))
            return str(relative_path).replace("\\", "/")

        except Exception as e:
            logger.error(
                "Edge-TTS generation failed",
                voice_id=voice_id,
                text_preview=text[:30],
                error=str(e),
            )
            raise


# Factory function for dependency injection
def create_edge_tts_service() -> EdgeTTSService:
    """Create a new EdgeTTSService instance."""
    return EdgeTTSService()


# Backward-compatible singleton (deprecated, use factory instead)
# Kept for compatibility with existing code during transition
class TTSService(EdgeTTSService):
    """Deprecated: Use EdgeTTSService directly or via TTS factory."""

    pass


tts_service = TTSService()
