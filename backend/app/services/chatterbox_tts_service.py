"""
Chatterbox TTS Service - High-quality text-to-speech using Chatterbox.

Chatterbox is a state-of-the-art open-source TTS model from Resemble AI.
It supports voice cloning and paralinguistic tags like [laugh], [cough], etc.
"""

import asyncio
import re
from pathlib import Path
from typing import List, Dict, Any, Optional
from uuid import uuid4

from app.services.base_tts_service import BaseTTSService
from app.config import settings
from app.utils.logging import get_logger

logger = get_logger(__name__)

# Lazy-loaded model instance (singleton pattern for efficiency)
_chatterbox_model = None
_model_lock = asyncio.Lock()


def sanitize_text_for_tts(text: str) -> str:
    """
    Sanitize text for Chatterbox TTS.

    Chatterbox supports paralinguistic tags like [laugh], [cough], [chuckle]
    so we preserve those while cleaning other special characters.
    """
    if not text:
        return ""

    # Preserve Chatterbox paralinguistic tags
    paralinguistic_tags = re.findall(
        r"\[(?:laugh|cough|chuckle|sigh|gasp)\]", text, re.IGNORECASE
    )

    # Remove other special characters but keep basic punctuation
    text = re.sub(
        r'[^\w\s.,!?;:\'"()\-–—…\u00C0-\u024F\[\]]', "", text, flags=re.UNICODE
    )

    # Remove control characters
    text = re.sub(r"[\x00-\x1f\x7f-\x9f]", "", text)

    # Normalize whitespace
    text = re.sub(r"\s+", " ", text)

    # Escape SSML-conflicting characters
    text = text.replace("&", "and")
    text = text.replace("<", "")
    text = text.replace(">", "")

    text = text.strip()

    if not text:
        text = "..."

    return text


async def get_chatterbox_model():
    """
    Get or initialize the Chatterbox model (lazy loading singleton).

    Uses async lock to prevent multiple simultaneous initializations.
    """
    global _chatterbox_model

    async with _model_lock:
        if _chatterbox_model is None:
            logger.info(
                "Initializing Chatterbox TTS model",
                device=settings.chatterbox_device,
                model_type=settings.chatterbox_model,
            )

            # Run model loading in thread pool to avoid blocking
            loop = asyncio.get_event_loop()
            _chatterbox_model = await loop.run_in_executor(None, _load_chatterbox_model)

            logger.info("Chatterbox model loaded successfully")

        return _chatterbox_model


def _load_chatterbox_model():
    """Load the Chatterbox model synchronously (called in executor)."""
    try:
        from chatterbox.tts_turbo import ChatterboxTurboTTS
        from chatterbox.tts import ChatterboxTTS
        from chatterbox.mtl_tts import ChatterboxMultilingualTTS

        device = settings.chatterbox_device
        model_type = settings.chatterbox_model

        if model_type == "turbo":
            return ChatterboxTurboTTS.from_pretrained(device=device)
        elif model_type == "multilingual":
            return ChatterboxMultilingualTTS.from_pretrained(device=device)
        else:
            return ChatterboxTTS.from_pretrained(device=device)

    except ImportError as e:
        logger.error(
            "Chatterbox not installed. Install with: pip install chatterbox-tts",
            error=str(e),
        )
        raise RuntimeError(
            "Chatterbox TTS is not installed. Install with: pip install chatterbox-tts"
        ) from e


class ChatterboxTTSService(BaseTTSService):
    """
    TTS service implementation using Chatterbox.

    Provides high-quality neural TTS with support for:
    - Voice cloning (with reference audio)
    - Paralinguistic tags ([laugh], [cough], etc.)
    - Multiple model variants (turbo, standard, multilingual)
    """

    @property
    def provider_name(self) -> str:
        return "chatterbox"

    async def get_voices(self) -> List[Dict[str, Any]]:
        """
        Get available voices for Chatterbox.

        Chatterbox uses voice cloning, so there's a default voice
        and the ability to clone from reference audio.
        """
        # Chatterbox doesn't have predefined voices like edge-tts
        # It uses voice cloning from reference audio
        return [
            {
                "voice_id": "default",
                "name": "Chatterbox Default",
                "gender": "Neutral",
                "locale": "en-US",
                "provider": "chatterbox",
            }
        ]

    async def generate_preview(
        self, text: str, voice_id: str, rate: str = "+0%", pitch: str = "+0Hz"
    ) -> str:
        """Generate a preview audio file."""
        self.preview_dir.mkdir(parents=True, exist_ok=True)

        filename = f"{uuid4()}.wav"
        output_path = self.preview_dir / filename

        await self._generate_audio(text, output_path)

        # Return relative path
        relative_path = output_path.relative_to(Path(settings.static_dir))
        return str(relative_path).replace("\\", "/")

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

        # Chatterbox outputs WAV, we'll keep it as WAV for quality
        filename = f"{scene_id}.wav"
        output_path = project_dir / filename

        await self._generate_audio(text, output_path)

        # Return relative path
        relative_path = output_path.relative_to(Path(settings.static_dir))
        return str(relative_path).replace("\\", "/")

    async def _generate_audio(self, text: str, output_path: Path) -> None:
        """
        Internal method to generate audio using Chatterbox.

        Args:
            text: Text to synthesize
            output_path: Path to save the audio file
        """
        try:
            clean_text = sanitize_text_for_tts(text)

            logger.debug(
                "Generating Chatterbox audio",
                text_preview=clean_text[:50],
                output_path=str(output_path),
            )

            model = await get_chatterbox_model()

            # Run generation in thread pool
            loop = asyncio.get_event_loop()
            wav = await loop.run_in_executor(None, lambda: model.generate(clean_text))

            # Save the audio
            await loop.run_in_executor(
                None, lambda: self._save_audio(wav, model.sr, output_path)
            )

            # Verify file was created
            if not output_path.exists():
                raise RuntimeError(f"Audio file was not created: {output_path}")

            file_size = output_path.stat().st_size
            if file_size < 100:
                logger.warning(
                    "Generated audio file is suspiciously small",
                    path=str(output_path),
                    size=file_size,
                )

            logger.debug(
                "Chatterbox audio generated successfully",
                path=str(output_path),
                size=file_size,
            )

        except Exception as e:
            logger.error(
                "Chatterbox TTS generation failed", text_preview=text[:30], error=str(e)
            )
            raise

    def _save_audio(self, wav, sample_rate: int, output_path: Path) -> None:
        """Save audio tensor to file."""
        import torchaudio as ta

        ta.save(str(output_path), wav, sample_rate)


# Factory function for dependency injection
def create_chatterbox_service() -> ChatterboxTTSService:
    """Create a new ChatterboxTTSService instance."""
    return ChatterboxTTSService()
