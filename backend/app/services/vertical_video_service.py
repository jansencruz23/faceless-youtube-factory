"""
Vertical Video Service for Shorts/TikTok.
Uses Whisper for word-level timestamps and animated ASS subtitles.
"""

import asyncio
import subprocess
import shutil
import time
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
from typing import List, Optional

from moviepy.editor import AudioFileClip

from app.config import settings
from app.utils.logging import get_logger

logger = get_logger(__name__)

# Dedicated executor for video processing
vertical_video_executor = ThreadPoolExecutor(max_workers=1)

# Video dimensions (9:16 vertical, 1080p)
WIDTH = 1080
HEIGHT = 1920


class VerticalVideoService:
    """Service for creating vertical videos for Shorts/TikTok."""

    def __init__(self):
        self.static_base = Path(settings.static_dir)
        self.output_dir = self.static_base / "shorts"
        self.output_dir.mkdir(parents=True, exist_ok=True)
        self.temp_dir = self.static_base / "temp"
        self.temp_dir.mkdir(parents=True, exist_ok=True)

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
        enable_captions: bool = True,
    ) -> str:
        """Create a vertical video with Whisper-powered captions."""
        try:
            output_path = self.output_dir / f"{project_id}.mp4"

            audio_paths = [self.static_base / p for p in audio_files]
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

            # Process image paths if provided
            image_paths = None
            if image_files:
                image_paths = [self.static_base / p for p in image_files]

            loop = asyncio.get_event_loop()
            await loop.run_in_executor(
                vertical_video_executor,
                self._compose_with_whisper,
                project_id,
                audio_paths,
                meta_data,
                output_path,
                bg_video_path,
                bg_music_path,
                music_volume,
                enable_captions,
                image_paths,
                image_scene_indices,
            )

            relative_path = output_path.relative_to(self.static_base)
            return str(relative_path).replace("\\", "/")

        except Exception as e:
            logger.error(
                "Vertical video composition failed", project_id=project_id, error=str(e)
            )
            raise

    def _compose_with_whisper(
        self,
        project_id: str,
        audio_paths: List[Path],
        meta_data: List[dict],
        output_path: Path,
        bg_video_path: Optional[Path],
        bg_music_path: Optional[Path],
        music_volume: float,
        enable_captions: bool,
        image_paths: Optional[List[Path]] = None,
        image_scene_indices: Optional[List[int]] = None,
    ) -> None:
        """Compose video with Whisper transcription for accurate captions."""
        start_time = time.time()

        valid_audio_paths = [p for p in audio_paths if p.exists()]
        if not valid_audio_paths:
            raise ValueError("No valid audio files found")

        # Step 1: Merge all audio
        logger.info(f"[1/5] Merging {len(valid_audio_paths)} audio files...")
        merged_audio_path = self.temp_dir / f"{project_id}_merged.mp3"
        self._merge_audio_ffmpeg(valid_audio_paths, merged_audio_path)

        # Get total duration
        audio = AudioFileClip(str(merged_audio_path))
        total_duration = audio.duration
        audio.close()
        logger.info(f"  Total duration: {total_duration:.1f}s")

        # Step 2: Mix with background music if provided
        if bg_music_path and bg_music_path.exists():
            logger.info("[2/5] Adding background music...")
            final_audio_path = self.temp_dir / f"{project_id}_final_audio.mp3"
            self._mix_audio_with_music(
                merged_audio_path,
                bg_music_path,
                final_audio_path,
                music_volume,
                total_duration,
            )
            merged_audio_path.unlink()
            merged_audio_path = final_audio_path
        else:
            logger.info("[2/5] No background music, skipping...")

        # Step 3: Create base video
        logger.info("[3/5] Creating base video...")
        temp_video_path = self.temp_dir / f"{project_id}_temp.mp4"

        # Get individual audio durations for scene-based images
        scene_durations = []
        for audio_path in valid_audio_paths:
            try:
                clip = AudioFileClip(str(audio_path))
                scene_durations.append(clip.duration)
                clip.close()
            except Exception:
                scene_durations.append(3.0)  # Default fallback

        # Priority: Images > Background Video > Solid Color
        valid_images = []
        if image_paths:
            valid_images = [p for p in image_paths if p and p.exists()]

        if valid_images and image_scene_indices:
            logger.info(f"  Using {len(valid_images)} scene-based images")
            self._create_video_with_images_ffmpeg(
                valid_images,
                image_scene_indices,
                scene_durations,
                merged_audio_path,
                temp_video_path,
                total_duration,
            )
        elif bg_video_path and bg_video_path.exists():
            self._create_video_with_bg_ffmpeg(
                bg_video_path, merged_audio_path, temp_video_path, total_duration
            )
        else:
            self._create_solid_video_ffmpeg(
                merged_audio_path, temp_video_path, total_duration
            )

        # Step 4: Transcribe with Whisper for word-level timestamps
        if enable_captions:
            logger.info("[4/5] Transcribing audio with Whisper...")
            try:
                from app.services.whisper_service import (
                    transcribe_audio_with_timestamps,
                )

                words = transcribe_audio_with_timestamps(merged_audio_path)

                if words:
                    logger.info(f"  Got {len(words)} words with timestamps")

                    # Generate animated ASS subtitles
                    ass_path = self.temp_dir / f"{project_id}.ass"
                    self._generate_animated_ass(words, ass_path)

                    # Burn subtitles
                    logger.info("[5/5] Burning animated captions...")
                    self._burn_subtitles_ffmpeg(temp_video_path, ass_path, output_path)

                    temp_video_path.unlink()
                    ass_path.unlink()
                else:
                    logger.warning(
                        "  No words transcribed, using video without captions"
                    )
                    shutil.move(str(temp_video_path), str(output_path))

            except Exception as e:
                logger.error(f"Whisper transcription failed: {e}")
                logger.info("[5/5] Falling back to no captions...")
                shutil.move(str(temp_video_path), str(output_path))
        else:
            logger.info("[4/5] Captions disabled, skipping...")
            logger.info("[5/5] Finalizing...")
            shutil.move(str(temp_video_path), str(output_path))

        # Cleanup
        if merged_audio_path.exists():
            merged_audio_path.unlink()

        elapsed = time.time() - start_time
        logger.info(f"Video created in {elapsed:.1f}s: {output_path}")

    def _generate_animated_ass(self, words: List[dict], output_path: Path) -> None:
        """Generate ASS subtitles with clean, punchy animations."""

        # Clean, bold style with thick black outline for readability
        # Larger font (130pt), thick outline (8px), strong shadow
        ass_content = f"""[Script Info]
Title: Animated Captions
ScriptType: v4.00+
PlayResX: {WIDTH}
PlayResY: {HEIGHT}
WrapStyle: 0

[V4+ Styles]
Format: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, OutlineColour, BackColour, Bold, Italic, Underline, StrikeOut, ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline, Shadow, Alignment, MarginL, MarginR, MarginV, Encoding
Style: Pop,Impact,130,&H00FFFFFF,&H000000FF,&H00000000,&HCC000000,1,0,0,0,100,100,3,0,1,8,4,5,10,10,350,1

[Events]
Format: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text
"""

        for word_info in words:
            start_time = self._seconds_to_ass_time(word_info["start"])
            end_time = self._seconds_to_ass_time(word_info["end"])
            word = word_info["word"].upper()

            # Clean the word
            word = word.replace("\\", "").replace("{", "").replace("}", "")

            # Calculate animation timing
            duration_ms = int((word_info["end"] - word_info["start"]) * 1000)
            pop_time = min(50, duration_ms // 4)  # Quick pop (50ms max)
            settle_time = min(40, duration_ms // 5)  # Quick settle

            # Clean pop animation:
            # - Start at 0% scale
            # - Pop to 120% quickly (surprising overshoot)
            # - Settle to 100% smoothly
            animated_text = (
                f"{{\\fscx0\\fscy0"
                f"\\t(0,{pop_time},\\fscx120\\fscy120)"
                f"\\t({pop_time},{pop_time + settle_time},\\fscx100\\fscy100)"
                f"}}{word}"
            )

            ass_content += (
                f"Dialogue: 0,{start_time},{end_time},Pop,,0,0,0,,{animated_text}\n"
            )

        with open(output_path, "w", encoding="utf-8") as f:
            f.write(ass_content)

        logger.info(f"  Generated animated ASS with {len(words)} words")

    def _seconds_to_ass_time(self, seconds: float) -> str:
        """Convert seconds to ASS time format (H:MM:SS.CC)"""
        hours = int(seconds // 3600)
        minutes = int((seconds % 3600) // 60)
        secs = int(seconds % 60)
        centisecs = int((seconds % 1) * 100)
        return f"{hours}:{minutes:02d}:{secs:02d}.{centisecs:02d}"

    def _merge_audio_ffmpeg(self, audio_paths: List[Path], output_path: Path) -> None:
        """Merge multiple audio files using FFmpeg filter_complex."""
        if len(audio_paths) == 1:
            shutil.copy(audio_paths[0], output_path)
            return

        input_args = []
        for path in audio_paths:
            input_args.extend(["-i", str(path)])

        filter_parts = "".join([f"[{i}:a]" for i in range(len(audio_paths))])
        filter_str = f"{filter_parts}concat=n={len(audio_paths)}:v=0:a=1[out]"

        cmd = (
            ["ffmpeg", "-y"]
            + input_args
            + ["-filter_complex", filter_str, "-map", "[out]", str(output_path)]
        )

        result = subprocess.run(cmd, capture_output=True, text=True)

        if result.returncode != 0:
            logger.error(f"Audio merge failed: {result.stderr}")
            raise RuntimeError("Failed to merge audio files")

    def _mix_audio_with_music(
        self,
        voice_path: Path,
        music_path: Path,
        output_path: Path,
        music_volume: float,
        duration: float,
    ) -> None:
        """Mix voice audio with background music."""
        # Boost voice volume by 1.5x for clearer TTS
        voice_boost = 1.5
        cmd = [
            "ffmpeg",
            "-y",
            "-i",
            str(voice_path),
            "-stream_loop",
            "-1",
            "-i",
            str(music_path),
            "-filter_complex",
            f"[0:a]volume={voice_boost}[voice];[1:a]volume={music_volume}[music];[voice][music]amix=inputs=2:duration=first[out]",
            "-map",
            "[out]",
            "-t",
            str(duration),
            str(output_path),
        ]

        result = subprocess.run(cmd, capture_output=True, text=True)
        if result.returncode != 0:
            logger.warning("Music mixing failed")
            shutil.copy(voice_path, output_path)

    def _create_solid_video_ffmpeg(
        self, audio_path: Path, output_path: Path, duration: float
    ) -> None:
        """Create video with solid color background."""
        cmd = [
            "ffmpeg",
            "-y",
            "-f",
            "lavfi",
            "-i",
            f"color=c=0x0f0f19:s={WIDTH}x{HEIGHT}:d={duration}:r=24",
            "-i",
            str(audio_path),
            "-c:v",
            "libx264",
            "-preset",
            "ultrafast",
            "-crf",
            "28",
            "-c:a",
            "aac",
            "-shortest",
            str(output_path),
        ]

        result = subprocess.run(cmd, capture_output=True, text=True)
        if result.returncode != 0:
            logger.error(f"Video creation failed: {result.stderr}")
            raise RuntimeError("Failed to create video")

    def _create_video_with_bg_ffmpeg(
        self, bg_video_path: Path, audio_path: Path, output_path: Path, duration: float
    ) -> None:
        """Create video with looping background video."""
        cmd = [
            "ffmpeg",
            "-y",
            "-stream_loop",
            "-1",
            "-i",
            str(bg_video_path),
            "-i",
            str(audio_path),
            "-filter_complex",
            f"[0:v]scale={WIDTH}:{HEIGHT}:force_original_aspect_ratio=increase,crop={WIDTH}:{HEIGHT}[v]",
            "-map",
            "[v]",
            "-map",
            "1:a",
            "-c:v",
            "libx264",
            "-preset",
            "ultrafast",
            "-crf",
            "28",
            "-c:a",
            "aac",
            "-t",
            str(duration),
            str(output_path),
        ]

        result = subprocess.run(cmd, capture_output=True, text=True)
        if result.returncode != 0:
            logger.error(f"Video creation failed: {result.stderr}")
            raise RuntimeError("Failed to create video with background")

    def _create_video_with_images_ffmpeg(
        self,
        image_paths: List[Path],
        image_scene_indices: List[int],
        scene_durations: List[float],
        audio_path: Path,
        output_path: Path,
        total_duration: float,
    ) -> None:
        """Create video from scene-based images with smooth Ken Burns effect."""

        # Build list of (image_path, duration) for each scene
        scene_clips = []
        for i, duration in enumerate(scene_durations):
            if i < len(image_scene_indices):
                img_idx = image_scene_indices[i]
                if img_idx >= 0 and img_idx < len(image_paths):
                    scene_clips.append((image_paths[img_idx], duration))
                else:
                    scene_clips.append((None, duration))
            else:
                scene_clips.append((None, duration))

        if not scene_clips:
            # Fallback to solid color
            self._create_solid_video_ffmpeg(audio_path, output_path, total_duration)
            return

        # Create individual scene videos and concatenate
        scene_video_paths = []
        concat_list_path = self.temp_dir / "concat_list.txt"

        try:
            for i, (img_path, duration) in enumerate(scene_clips):
                scene_video_path = self.temp_dir / f"scene_{i}.mp4"

                if img_path and img_path.exists():
                    # Create video from image with ultra-smooth Ken Burns effect
                    # Use higher fps for buttery smooth animation
                    fps = 30
                    total_frames = int(duration * fps)

                    # Ultra-smooth linear zoom - very subtle (5% total)
                    # Simple linear progression: zoom = 1.0 + (0.05 * frame / total_frames)
                    zoom_expr = f"1.0+0.05*on/{total_frames}"

                    # Consistent slow pan to the LEFT (one direction only)
                    # Pan 30 pixels total over the duration for subtle movement
                    pan_pixels = 30
                    x_expr = (
                        f"iw/2-(iw/zoom/2)+{pan_pixels}-{pan_pixels}*on/{total_frames}"
                    )
                    y_expr = "ih/2-(ih/zoom/2)"

                    cmd = [
                        "ffmpeg",
                        "-y",
                        "-loop",
                        "1",
                        "-i",
                        str(img_path),
                        "-vf",
                        f"scale=-1:2160,crop=1080:1920,zoompan=z='{zoom_expr}':x='{x_expr}':y='{y_expr}':d={total_frames}:s={WIDTH}x{HEIGHT}:fps={fps}",
                        "-c:v",
                        "libx264",
                        "-preset",
                        "ultrafast",
                        "-crf",
                        "28",
                        "-t",
                        str(duration),
                        "-pix_fmt",
                        "yuv420p",
                        str(scene_video_path),
                    ]

                    result = subprocess.run(cmd, capture_output=True, text=True)
                    if result.returncode != 0:
                        logger.warning(
                            f"Scene {i} image video failed, using solid color: {result.stderr[:200]}"
                        )
                        # Fallback to solid color for this scene
                        self._create_scene_solid_video(scene_video_path, duration)
                else:
                    # No image - create solid color scene
                    self._create_scene_solid_video(scene_video_path, duration)

                scene_video_paths.append(scene_video_path)

            # Create concat list file - use relative paths from temp_dir
            with open(concat_list_path, "w", encoding="utf-8") as f:
                for vpath in scene_video_paths:
                    # Use just the filename since we'll run ffmpeg from temp_dir
                    f.write(f"file '{vpath.name}'\n")

            logger.info(f"  Concat list created with {len(scene_video_paths)} scenes")

            # Concatenate all scene videos and add audio
            # Run from temp_dir to use relative paths
            cmd = [
                "ffmpeg",
                "-y",
                "-f",
                "concat",
                "-safe",
                "0",
                "-i",
                str(concat_list_path),
                "-i",
                str(audio_path),
                "-c:v",
                "copy",  # Copy video stream (no re-encode for speed)
                "-c:a",
                "aac",
                "-shortest",
                str(output_path),
            ]

            logger.info(f"  Running concat command...")
            result = subprocess.run(
                cmd, capture_output=True, text=True, cwd=str(self.temp_dir)
            )
            if result.returncode != 0:
                logger.error(f"Video concatenation failed: {result.stderr[:500]}")
                # Try alternate approach: filter_complex concat
                logger.info("  Trying alternate concat method...")
                self._concat_videos_filter(scene_video_paths, audio_path, output_path)
            else:
                logger.info(
                    f"  Created video with {len(scene_clips)} image-based scenes"
                )

        finally:
            # Cleanup temp scene videos and concat list
            for vpath in scene_video_paths:
                try:
                    if vpath.exists():
                        vpath.unlink()
                except Exception:
                    pass
            try:
                if concat_list_path.exists():
                    concat_list_path.unlink()
            except Exception:
                pass

    def _concat_videos_filter(
        self, video_paths: List[Path], audio_path: Path, output_path: Path
    ) -> None:
        """Fallback concat using filter_complex (more compatible on Windows)."""
        if not video_paths:
            raise RuntimeError("No videos to concatenate")

        # Build input arguments
        input_args = []
        for vpath in video_paths:
            input_args.extend(["-i", str(vpath)])
        input_args.extend(["-i", str(audio_path)])

        # Build filter_complex string
        n = len(video_paths)
        filter_parts = "".join([f"[{i}:v]" for i in range(n)])
        filter_str = f"{filter_parts}concat=n={n}:v=1:a=0[outv]"

        cmd = (
            ["ffmpeg", "-y"]
            + input_args
            + [
                "-filter_complex",
                filter_str,
                "-map",
                "[outv]",
                "-map",
                f"{n}:a",  # Audio is the last input
                "-c:v",
                "libx264",
                "-preset",
                "ultrafast",
                "-crf",
                "28",
                "-c:a",
                "aac",
                "-shortest",
                str(output_path),
            ]
        )

        result = subprocess.run(cmd, capture_output=True, text=True)
        if result.returncode != 0:
            logger.error(f"Filter concat also failed: {result.stderr[:500]}")
            raise RuntimeError("Failed to concatenate scene videos")

        logger.info(f"  Concat via filter_complex succeeded")

    def _create_scene_solid_video(self, output_path: Path, duration: float) -> None:
        """Create a short solid color video for a single scene."""
        cmd = [
            "ffmpeg",
            "-y",
            "-f",
            "lavfi",
            "-i",
            f"color=c=0x0f0f19:s={WIDTH}x{HEIGHT}:d={duration}:r=24",
            "-c:v",
            "libx264",
            "-preset",
            "ultrafast",
            "-crf",
            "28",
            "-pix_fmt",
            "yuv420p",
            str(output_path),
        ]
        result = subprocess.run(cmd, capture_output=True, text=True)
        if result.returncode != 0:
            logger.warning(f"Scene solid video failed: {result.stderr[:200]}")

    def _burn_subtitles_ffmpeg(
        self, input_path: Path, ass_path: Path, output_path: Path
    ) -> None:
        """Burn ASS subtitles into video."""
        import tempfile
        import os

        # Copy ASS to a simple temp path (avoids Windows path escaping issues)
        temp_dir = tempfile.gettempdir()
        simple_ass_path = Path(temp_dir) / "captions.ass"
        shutil.copy(ass_path, simple_ass_path)

        # Use forward slashes and escape colon
        ass_escaped = str(simple_ass_path).replace("\\", "/").replace(":", "\\:")

        cmd = [
            "ffmpeg",
            "-y",
            "-hwaccel",
            "auto",
            "-i",
            str(input_path),
            "-vf",
            f"ass='{ass_escaped}'",
            "-c:a",
            "copy",
            "-c:v",
            "libx264",
            "-preset",
            "ultrafast",
            "-crf",
            "28",
            "-threads",
            "0",
            str(output_path),
        ]

        logger.info(f"  FFmpeg command: {' '.join(cmd[:8])}...")
        result = subprocess.run(cmd, capture_output=True, text=True)

        # Clean up temp ASS
        try:
            simple_ass_path.unlink()
        except:
            pass

        if result.returncode != 0:
            logger.error(f"Subtitle burning failed!")
            logger.error(f"  FFmpeg stderr: {result.stderr[:500]}")
            shutil.copy(input_path, output_path)
        else:
            logger.info("  Subtitles burned successfully")


# Singleton instance
vertical_video_service = VerticalVideoService()
