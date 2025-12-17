"""
Text-to-Speech service using edge-tts.
"""
import edge_tts
import asyncio
import os
from pathlib import Path
from typing import List, Dict, Any

import edge_tts
from app.config import settings
from app.utils.loggin import get_logger

logger = get_logger(__name__)


class TTSService:
    """Service for generating audio from text."""

    def __init__(self):
        self.output_dir = Path(settings.static_dir) / "audio"
        self.preview_dir = Path(settings.static_dir) / "previews"

    async def get_voices(self) -> List[Dict[str, Any]]:
        """Get list of available voices."""
        try:
            voices = await edge_tts.list_voices()
            # Formar for frontend
            return [
                {
                    "voice_id": v["ShortName"],
                    "name": v["FriendlyName"],
                    "gender": v["Gender"],
                    "locale": v["Locale"],
                    "tags": v.get("VoiceTag", {})
                }
                for v in voices
            ]
        except Exception as e:
            logger.error("Failed to get voices", error=str(e))
            return []

    async def generate_preview(
        self,
        text: str,
        voice_id: str,
        rate: str="+0%",
        pitch: str="+0Hz" 
    ) -> str:
        """
        Generate a temporary preview audio file.
        
        Returns:
            Relative path to the generated file.
        """
        import uuid

        filename = f"{uuid.uuid4()}.mp3"
        output_path = self.preview_dir / filename

        return await self._generate_file(
            text=text,
            voice_id=voice_id,
            rate=rate,
            pitch=pitch,
            output_path=output_path
        )

    async def generate_scene_audio(
        self,
        project_id: str,
        scene_id: str,
        text: str,
        voice_id: str,
        rate: str="+0%",
        pitch: str="+0Hz"
    ) -> str:
        """
        Generate audio for a script scene.

        Returns:
            Relative path to the generated file.
        """
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
            output_path=output_path
        )

    async def _generate_file(
        self,
        text: str,
        voice_id: str,
        rate: str,
        pitch: str,
        output_path: Path
    ) -> str:
        """Internal method to generate audio file."""
        try:
            communicate = edge_tts.Communicate(
                text,
                voice_id,
                rate=rate,
                pitch=pitch
            )

            await communicate.save(str(output_path))

            # Return path relative to static dir for URL generation
            # e.g., "audio/<project_id>/<scene_id>.mp3"
            relative_path = output_path.relative_to(Path(settings.static_dir))
            return str(relative_path).replace("\\", "/")

        except Exception as e:
            logger.error(
                "TTS generation failed",
                voice_id=voice_id,
                text_preview=text[:30],
                error=str(e)
            )
            raise


# Singleton instance
tts_service = TTSService()