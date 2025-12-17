"""
AudioGenerator Node - Generates audio for each script scene.
"""
from typing import Dict, Any
from uuid import uuid4

from app.graph.state import GraphState
from app.services.tts_service import tts_service
from app.models import Asset, AssetType, ProjectStatus
from app.database import get_session_context
from app.utils.logging import get_logger

logger = get_logger(__name__)


async def audio_generator_node(state: GraphState) -> GraphState:
    """
    Generate audio files for each scene in the script.
    
    Uses edge-tts with the voice settings from cast assignments.
    Skips failed scenes and continues with the rest.
    
    Updates:
    - audio_files: List of paths to generated audio files
    - progress: Incremented per scene, reaches 0.6 on completion
    """
    logger.info("AudioGenerator node started", project_id=state["project_id"])
    
    state["current_step"] = "generating_audio"
    
    script_json = state["script_json"]
    cast_list = state["cast_list"]
    scenes = script_json.get("scenes", [])

    audio_files = []
    scene_count = len(scenes)

    async with get_session_context() as session:
        from app.models import Project

        for i, scene in enumerate(scenes):
            speaker = scene["speaker"]
            line = scene["line"]
            
            # Get voice settings for this speaker
            voice_settings = cast_list.get(speaker, {
                "voice_id": "en-US-AriaNeural",
                "pitch": "+0Hz",
                "rate": "+0%"
            })

            try:
                # Generate audio file
                audio_path = await tts_service.generate_scene_audio(
                    project_id=state["project_id"],
                    scene_id=str(i),
                    text=line,
                    voice_id=voice_settings["voice_id"],
                    rate=voice_settings.get("rate", "+0%"),
                    pitch=voice_settings.get("pitch", "+0Hz")
                )
                
                audio_files.append(audio_path)
                
                # Create asset record
                asset = Asset(
                    id=uuid4(),
                    project_id=state["project_id"],
                    asset_type=AssetType.AUDIO,
                    file_path=audio_path,
                    character_name=speaker
                )
                session.add(asset)
                
                logger.debug(
                    "Scene audio generated",
                    scene=i,
                    speaker=speaker,
                    path=audio_path
                )

            except Exception as e:
                error_msg = f"Audio generation failed for scene {i}: {str(e)}"
                logger.warning(error_msg)
                state["errors"].append(error_msg)
                # Continue with next scene

            # Update progress (0.3 to 0.6 range)
            state["progress"] = 0.3 + (0.3 * (i + 1) / scene_count)

        # Update project status
        project = await session.get(Project, state["project_id"])
        if project:
            project.status = ProjectStatus.GENERATING_VIDEO
            session.add(project)
        
        await session.commit()

    state["audio_files"] = audio_files
    state["progress"] = 0.6

    logger.info(
        "Audio generation completed",
        project_id=state["project_id"],
        generated=len(audio_files),
        total=scene_count
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