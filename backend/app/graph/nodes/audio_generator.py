"""
AudioGenerator Node - Generates audio for each script scene.

Uses the configured TTS provider (edge_tts or chatterbox) based on project settings.
"""

from typing import Dict, Any
from uuid import uuid4

from app.graph.state import GraphState
from app.services.tts_factory import get_tts_service
from app.models import Asset, AssetType, ProjectStatus
from app.database import get_session_context
from app.utils.logging import get_logger

logger = get_logger(__name__)


async def audio_generator_node(state: GraphState) -> GraphState:
    """
    Generate audio files for each scene in the script.

    Uses the TTS provider specified in state (edge_tts or chatterbox)
    with voice settings from cast assignments.
    Tracks failed scenes by index to maintain scene/audio alignment.

    Updates:
    - audio_files: List of paths to generated audio files (with None for failures)
    - progress: Incremented per scene, reaches 0.6 on completion
    """
    logger.info("AudioGenerator node started", project_id=state["project_id"])

    state["current_step"] = "generating_audio"

    # Get the TTS provider from state (defaults to settings if not specified)
    tts_provider = state.get("tts_provider")
    tts_service = get_tts_service(tts_provider)

    logger.info(
        "Using TTS provider",
        provider=tts_service.provider_name,
        project_id=state["project_id"],
    )

    script_json = state["script_json"]
    cast_list = state["cast_list"]
    scenes = script_json.get("scenes", [])

    # Use a list that preserves indices - None for failed scenes
    audio_files = []
    successful_count = 0
    scene_count = len(scenes)

    logger.info(
        "Starting audio generation",
        project_id=state["project_id"],
        total_scenes=scene_count,
    )

    async with get_session_context() as session:
        from app.models import Project

        for i, scene in enumerate(scenes):
            speaker = scene.get("speaker", "Unknown")
            line = scene.get("line", "")

            # Skip empty lines
            if not line or not line.strip():
                logger.warning(
                    "Empty line in scene, skipping", scene_index=i, speaker=speaker
                )
                audio_files.append(None)
                continue

            # Get voice settings for this speaker
            voice_settings = cast_list.get(
                speaker,
                {"voice_id": "en-US-AriaNeural", "pitch": "+0Hz", "rate": "+0%"},
            )

            try:
                # Generate audio file
                audio_path = await tts_service.generate_scene_audio(
                    project_id=state["project_id"],
                    scene_id=str(i),
                    text=line,
                    voice_id=voice_settings["voice_id"],
                    rate=voice_settings.get("rate", "+0%"),
                    pitch=voice_settings.get("pitch", "+0Hz"),
                )

                audio_files.append(audio_path)
                successful_count += 1

                # Create asset record
                asset = Asset(
                    id=uuid4(),
                    project_id=state["project_id"],
                    asset_type=AssetType.AUDIO,
                    file_path=audio_path,
                    character_name=speaker,
                )
                session.add(asset)

                logger.debug(
                    "Scene audio generated", scene=i, speaker=speaker, path=audio_path
                )

            except Exception as e:
                error_msg = f"Audio generation failed for scene {i}: {str(e)}"
                logger.warning(error_msg)
                state["errors"].append(error_msg)
                # Add None to preserve index alignment
                audio_files.append(None)

            # Update progress (0.3 to 0.6 range)
            state["progress"] = 0.3 + (0.3 * (i + 1) / scene_count)

        # Update project status
        from uuid import UUID as UUIDType

        project = await session.get(Project, UUIDType(state["project_id"]))
        if project:
            project.status = ProjectStatus.GENERATING_VIDEO
            session.add(project)

        await session.commit()

    # Filter out None values for the video composer
    # We'll pass both the valid files and their original indices
    valid_audio_files = []
    valid_indices = []
    for i, path in enumerate(audio_files):
        if path is not None:
            valid_audio_files.append(path)
            valid_indices.append(i)

    state["audio_files"] = valid_audio_files
    state["audio_scene_indices"] = valid_indices  # Track which scenes have audio
    state["progress"] = 0.6

    logger.info(
        "Audio generation completed",
        project_id=state["project_id"],
        successful=successful_count,
        failed=scene_count - successful_count,
        total=scene_count,
    )

    return state


def should_continue_after_audio(state: GraphState) -> str:
    """
    Conditional edge: Decide next step after audio generation.

    Returns:
    - "video_composer" if at least one audio file was generated
    - "end" if no audio files (complete failure)
    """
    if state.get("audio_files") and len(state["audio_files"]) > 0:
        return "video_composer"

    logger.error("No audio files generated", project_id=state["project_id"])
    return "end"
