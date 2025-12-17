"""
Video composition service using moviepy.
"""
import asyncio
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
from typing import List, Tuple

from moviepy.editor import (
    AudioFileClip,
    TextClip,
    ColorClip,
    CompositeVideoClip,
    concatenate_videoclips
)
from app.config import settings
from app.utils.logging import get_logger

logger = get_logger(__name__)

# Limit concurrent video processing to avoid OOM
video_executor = ThreadPoolExecutor(max_workers=settings.max_concurrent_video_jobs)


class VideoService:
    """Service for composing videos."""

    def __init__(self):
        self.output_dir = Path(settings.static_dir) / "video"
        self.static_base = Path(settings.static_dir)

    async def create_video(
        self,
        project_id: str,
        audio_files: List[str],
        meta_data: List[dict]
    ) -> str:
        """
        Componse final video from audio clips and text overlays.
        Runs in a separate thread to not block the async event loop.
        """
        loop = asyncio.get_running_loop()

        # Determine full paths
        full_audio_paths = [self.static_base / path for path in audio_files]
        project_video_dir = self.output_dir / str(project_id)
        project_video_dir.mkdir(parents=True, exist_ok=True)
        output_path = project_video_dir / "final.mp4"

        try:
            logger.info("Starting video composition", project_id=project_id, clips=len(audio_files))

            # Execute blocking moviepy code in thread pool
            await loop.run_in_executor(
                video_executor,
                self._compose_video_sync,
                full_audio_paths,
                meta_data,
                output_path
            )

            # Return relative path
            relative_path = output_path.relative_to(self.static_base)
            return str(relative_path).replace("\\", "/")

        except Exception as e:
            logger.error("Video composition failed", project_id=project_id, error=str(e))
            raise

    def _compose_video_sync(
        self,
        audio_paths: List[Path],
        meta_data: List[dict],
        output_path: Path
    ) -> None:
        """Blocking moviepy video composition logic."""
        clips = []

        for audio_path, meta in zip(audio_paths, meta_data):
            if not audio_path.exists():
                logger.warning(f"Audio file missing: {audio_path}")
                continue

            # Create audio clip
            audio_clip = AudioFileClip(str(audio_path))
            duration = audio_clip.duration + 0.5

            # Create visual background (simple solid color for now)
            bg_color = (20, 20, 30)  
            bg_clip = ColorClip(
                size=(1280, 720), 
                color=bg_color, 
                duration=duration
            )

            # Create text overlay (Speaker Name + Subtitle)
            # Note: TextClip requires ImageMagick installed. 
            # If not available, we skip text or use a simpler approach.
            try:
                txt_clip = TextClip(
                    f"{meta['speaker']}\n\n{meta['line']}",
                    fontsize=30,
                    color='white',
                    font='Arial-Bold',
                    size=(1000, 600),
                    method='caption',
                    align='center'
                ).set_position('center').set_duration(duration)

                video_clip = CompositeVideoClip([bg_clip, txt_clip])
            except Exception:
                # Fallback if TextClip/ImageMagick fails
                logger.warning("TextClip failed (ImageMagick missing?), using plain bg")
                video_clip = bg_clip
            
            video_clip = video_clip.set_audio(audio_clip)
            clips.append(video_clip)
        
        if not clips:
            raise ValueError("No valid clips to concatenate")

        final_video = concatenate_videoclips(clips)

        # Write to file
        final_video.write_videofile(
            str(output_path),
            fps=24,
            codec="libx264",
            audio_codec="aac",
            threads=4,
            logger=None
        )

        # Close clips to free resources
        final_video.close()
        for clip in clips:
            clip.close()


# Singleton instance
video_service = VideoService()