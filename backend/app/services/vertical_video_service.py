"""
Vertical Video Service for Shorts/TikTok.
Handles 9:16 video composition with word-by-word captions.
"""

import asyncio
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
from typing import List, Optional
import re

from moviepy.editor import (
    CompositeVideoClip,
    concatenate_videoclips,
    AudioFileClip,
    VideoFileClip,
    ColorClip,
    TextClip,
    CompositeAudioClip,
)

from app.config import settings
from app.utils.logging import get_logger

logger = get_logger(__name__)

# Dedicated executor for video processing
vertical_video_executor = ThreadPoolExecutor(max_workers=1)

# Video dimension (9:16 vertical)
WIDTH = 1080
HEIGHT = 1920


class VerticalVideoService:
    """Service for creating vertical videos for Shorts/TikTok."""

    def __init__(self):
        self.static_base = Path(settings.static_dir)
        self.output_dir = self.static_base / "shorts"
        self.output_dir.mkdir(parents=True, exist_ok=True)

    async def create_vertical_video(
        self,
        project_id: str,
        audio_files: List[str],
        meta_data: List[dict],
        image_files: List[str] = None,
        image_scene_indices: List[int] = None,
        background_video_url: Optional[str] = None,
        background_music_url: Optional[str] = None,
        music_volume: float = 0.3,
    ) -> str:
        """
        Create a vertical video with word-by-word captions.

        Args:
            project_id: Project UUID
            audio_files: List of audio file paths
            meta_data: List of scene metadata (speaker, line)
            image_files: List of background image paths
            image_scene_indices: Mapping of scene to image index
            background_video_url: Background video path (loops)
            background_music_url: Background music path
            music_volume: Volume for background music (0-1)

        Returns:
            Relative path to output video
        """
        try:
            output_path = self.output_dir / f"{project_id}.mp4"

            # Convert paths
            audio_paths = [self.static_base / p for p in audio_files]
            image_paths = (
                [self.static_base / p for p in image_files] if image_files else []
            )
            bg_video_path = (
                self.static_base / background_video_url
                if background_video_url
                else None
            )
            bg_music_path = (
                self.static_base / background_music_url
                if background_music_url
                else None
            )

            loop = asyncio.get_event_loop()
            await loop.run_in_executor(
                vertical_video_executor,
                self._compose_vertical_video_sync,
                audio_paths,
                meta_data,
                output_path,
                image_paths,
                image_scene_indices,
                bg_video_path,
                bg_music_path,
                music_volume,
            )

            relative_path = output_path.relative_to(self.static_base)
            return str(relative_path).replace("\\", "/")

        except Exception as e:
            logger.error(
                "Vertical video composition failed", project_id=project_id, error=str(e)
            )
            raise

    def _compose_vertical_video_sync(
        self,
        audio_paths: List[Path],
        meta_data: List[dict],
        output_path: Path,
        image_paths: List[Path] = None,
        image_scene_indices: List[int] = None,
        bg_video_path: Path = None,
        bg_music_path: Path = None,
        music_volume: float = 0.3,
    ) -> None:
        """Synchronous vertical video composition with word-by-word captions."""

        clips = []
        total_duration = 0

        # Determine if using single (static) or muultiple
        unique_image = set(image_paths) if image_paths else set()
        use_static = len(unique_image) <= 1

        # Load background video if provided
        bg_video_clip = None
        if bg_video_path and bg_video_path.exists():
            bg_video_clip = VideoFileClip(str(bg_video_path))
            # Resize to fit vertical format
            bg_video_clip = bg_video_clip.resize(height=HEIGHT)
            if bg_video_clip.w > WIDTH:
                bg_video_clip = bg_video_clip.crop(
                    x_center=bg_video_clip.w / 2, width=WIDTH
                )

        for i, (audio_path, meta) in enumerate(zip(audio_paths, meta_data)):
            if not audio_path.exists():
                logger.warning(f"Audio missing: {audio_path}")
                continue

            audio_clip = AudioFileClip(str(audio_path))
            duration = audio_clip.duration + 0.3

            # Create background
            if bg_video_clip:
                # Loop video background
                video_bg = self._loop_video(bg_video_clip, duration, total_duration)
            elif image_paths and image_scene_indices and i < len(image_scene_indices):
                img_idx = image_scene_indices[i]
                if 0 <= img_idx < len(image_paths) and image_paths[img_idx].exists():
                    video_bg = self._create_image_background(
                        str(image_paths[img_idx]), duration, use_static
                    )
                else:
                    video_bg = self._create_solid_background(duration)
            else:
                video_bg = self._create_solid_background(duration)

            # Create word-by-word captions
            line = meta.get("line", "")
            caption_clips = self._create_word_by_word_captions(line, duration)

            # Composite background + captions
            scene_clip = CompositeVideoClip(
                [video_bg] + caption_clips, size=(WIDTH, HEIGHT)
            ).set_duration(duration)

            scene_clip = scene_clip.set_audio(audio_clip)
            clips.append(scene_clip)
            total_duration += duration

        if not clips:
            raise ValueError("No valid clips to concatenate")

        # Concatenate all scenes
        final_video = concatenate_videoclips(clips, method="compose")

        # Add background music
        if bg_music_path and bg_music_path.exists():
            final_video = self._add_background_music(
                final_video, bg_music_path, music_volume
            )

        # Export
        final_video.write_videofile(
            str(output_path),
            fps=30,
            codec="libx264",
            audio_codec="aac",
            threads=4,
            logger=None,
        )

        # Cleanup
        final_video.close()
        for clip in clips:
            clip.close()
        if bg_video_clip:
            bg_video_clip.close()

    def _create_word_by_word_captions(
        self,
        text: str,
        duration: float,
    ) -> List[TextClip]:
        """Create word-by-word caption clips."""

        # Split into words
        words = text.split()
        if not words:
            return []

        time_per_word = duration / len(words)
        caption_clips = []

        for i, word in enumerate(words):
            start_time = i * time_per_word

            try:
                txt_clip = (
                    TextClip(
                        word.upper(),
                        fontsize=120,
                        color="white",
                        font="Arial-Bold",
                        stroke_color="black",
                        stroke_width=4,
                        method="label",
                    )
                    .set_position("center")
                    .set_start(start_time)
                    .set_duration(time_per_word)
                )
                caption_clips.append(txt_clip)

            except Exception as e:
                logger.warning(f"Failed to create caption for '{word}': {e}")

        return caption_clips

    def _create_image_background(
        self,
        image_path: str,
        duration: float,
        use_static: bool = False,
    ):
        """Create background from image, optionally with Ken Burns effect."""
        from moviepy.editor import ImageClip

        img_clip = ImageClip(image_path)

        # Resize to fill vertical frame
        img_clip = img_clip.resize(height=HEIGHT)
        if img_clip.w < WIDTH:
            img_clip = img_clip.resize(width=WIDTH)

        if use_static:
            # Static image
            final = CompositeVideoClip(
                [img_clip.set_position("center")], size=(WIDTH, HEIGHT)
            ).set_duration(duration)
        else:
            # Ken Burns effect
            import random

            zoom_in = random.choice([True, False])
            start_scale = 1.0 if zoom_in else 1.1
            end_scale = 1.1 if zoom_in else 1.0

            def resize_func(t):
                progress = t / duration
                return start_scale + (end_scale - start_scale) * progress

            zoomed = img_clip.resize(lambda t: resize_func(t))
            zoomed = zoomed.set_duration(duration)

            final = CompositeVideoClip(
                [zoomed.set_position("center")], size=(WIDTH, HEIGHT)
            ).set_duration(duration)

        return final

    def _create_solid_background(self, duration: float):
        """Create solid color background."""
        return ColorClip(size=(WIDTH, HEIGHT), color=(15, 15, 25), duration=duration)

    def _loop_video(self, video_clip, duration: float, offset: float = 0):
        """Loop video to fill duration, starting at offset."""
        from moviepy.editor import vfx

        video_duration = video_clip.duration
        start_time = offset % video_duration

        # Create looped version
        looped = video_clip.loop(duration=duration + start_time)
        looped = looped.subclip(start_time, start_time + duration)

        return CompositeVideoClip(
            [looped.set_position("center")], size=(WIDTH, HEIGHT)
        ).set_duration(duration)

    def _add_background_music(
        self,
        video: CompositeVideoClip,
        music_path: Path,
        volume: float,
    ):
        """Add background music to video."""
        music = AudioFileClip(str(music_path))

        # Loop music if shorter than video
        if music.duration < video.duration:
            music = music.loop(duration=video.duration)
        else:
            music = music.subclip(0, video.duration)

        # Adjust volume
        music = music.volumex(volume)

        # Mix with original audio
        original_audio = video.audio
        if original_audio:
            mixed_audio = CompositeAudioClip([original_audio, music])
            return video.set_audio(mixed_audio)
        else:
            return video.set_audio(music)


# Singleton instance
vertical_video_service = VerticalVideoService()
