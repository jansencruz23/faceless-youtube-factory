"""
Whisper-based transcription service for word-level timestamps.
Uses faster-whisper for efficient transcription.
"""

from pathlib import Path
from typing import List, Dict, Optional
import os

from app.utils.logging import get_logger

logger = get_logger(__name__)

# Lazy load model to avoid memory issues
_whisper_model = None


def get_whisper_model():
    """Get or create Whisper model (lazy loading)."""
    global _whisper_model
    if _whisper_model is None:
        try:
            from faster_whisper import WhisperModel
            import os

            # Use 'small' for better multilingual accuracy (Filipino, etc.)
            # Can be overridden via WHISPER_MODEL env var
            model_size = os.environ.get("WHISPER_MODEL", "medium")
            logger.info(f"Loading Whisper model ({model_size}, CPU mode)...")
            _whisper_model = WhisperModel(
                model_size,  # 'small' is better for non-English
                device="cpu",  # Use CPU to avoid CUDA issues
                compute_type="int8",  # Faster inference on CPU
            )
            logger.info("Whisper model loaded successfully")
        except Exception as e:
            logger.error(f"Failed to load Whisper model: {e}")
            raise
    return _whisper_model


def transcribe_audio_with_timestamps(audio_path: Path) -> List[Dict]:
    """
    Transcribe audio and extract word-level timestamps.

    Returns:
        List of dicts with 'word', 'start', 'end' keys
    """
    try:
        model = get_whisper_model()

        logger.info(f"Transcribing: {audio_path.name}")

        segments, info = model.transcribe(
            str(audio_path),
            word_timestamps=True,  # Enable word-level timestamps
            language=None,  # Auto-detect language (supports Filipino/Tagalog)
        )

        detected_lang = info.language if hasattr(info, "language") else "unknown"
        logger.info(f"  Detected language: {detected_lang}")

        words = []
        for segment in segments:
            if segment.words:
                for word_info in segment.words:
                    words.append(
                        {
                            "word": word_info.word.strip(),
                            "start": word_info.start,
                            "end": word_info.end,
                        }
                    )

        logger.info(f"  Found {len(words)} words")
        return words

    except Exception as e:
        logger.error(f"Transcription failed: {e}")
        return []


def transcribe_multiple_audio_files(
    audio_paths: List[Path],
) -> List[Dict]:
    """
    Transcribe multiple audio files and return combined word list
    with adjusted timestamps.
    """
    all_words = []
    current_offset = 0.0

    for i, audio_path in enumerate(audio_paths):
        if not audio_path.exists():
            logger.warning(f"Audio file not found: {audio_path}")
            continue

        # Get words from this file
        words = transcribe_audio_with_timestamps(audio_path)

        # Adjust timestamps by offset
        for word in words:
            all_words.append(
                {
                    "word": word["word"],
                    "start": word["start"] + current_offset,
                    "end": word["end"] + current_offset,
                }
            )

        # Update offset for next file
        # Get audio duration
        try:
            from moviepy.editor import AudioFileClip

            audio = AudioFileClip(str(audio_path))
            current_offset += audio.duration
            audio.close()
        except Exception as e:
            logger.warning(f"Could not get audio duration: {e}")
            # Estimate from last word end time
            if words:
                current_offset = all_words[-1]["end"] + 0.1

    logger.info(f"Total words transcribed: {len(all_words)}")
    return all_words
