"""
VideoComposer Node - Composes final video from audio clips.
"""
from typing import Dict, Any
from uuid import uuid4

from app.graph.state import GraphState
from app.services.video_service import video_service
from app.models import Asset, AssetType, ProjectStatus
from app.database import get_session_context
from app.utils.logging import get_logger

logger = get_logger(__name__)

async def video_composer_node(state: GraphState) -> GraphState:
    """
    Compose the final video from audio clips and text overlays.
    
    Uses moviepy to:
    1. Create colored backgrounds
    2. Add text overlays with speaker names and lines
    3. Sync audio with video
    4. Concatenate all clips
    
    Updates:
    - video_path: Path to the final video file
    - progress: Updated to 0.9 on success
    """
    logger.info("VideoComposer node started", project_id=state["project_id"])
    
    state["current_step"] = "generating_video"

    try:
        # Prepare metadata for each audio clip
        scenes = state["script_json"].get("scenes", [])
        audio_files = state["audio_files"]

        # Match audio files with scene metadata
        # Audio files are named by index (0.mp3, 1.mp3, etc.)
        meta_data = []
        for i, audio_path in enumerate(audio_files):
            if i < len(scenes):
                meta_data.append({
                    "speaker": scenes[i]["speaker"],
                    "line": scenes[i]["line"][:100]  # Truncate for display
                })
            else:
                meta_data.append({
                    "speaker": "Unknown",
                    "line": ""
                })

        # Compose video
        video_path = await video_service.create_video(
            project_id=state["project_id"],
            audio_files=audio_files,
            meta_data=meta_data
        )

        # Save asset record
        async with get_session_context() as session:
            from app.models import Project
            import os
            from pathlib import Path
            from app.config import settings

            # Get file size
            full_path = Path(settings.static_dir) / video_path
            file_size = full_path.stat().st_size if full_path.exists() else 0

            asset = Asset(
                id=uuid4(),
                project_id=state["project_id"],
                asset_type=AssetType.VIDEO,
                file_path=video_path,
                file_size_bytes=file_size
            )
            session.add(asset)

            # Update project status
            from uuid import UUID as UUIDType
            project = await session.get(Project, UUIDType(state["project_id"]))
            if project:
                project.status = ProjectStatus.COMPLETED
                session.add(project)

            await session.commit()

        state["video_path"] = video_path
        state["progress"] = 0.9

        logger.info(
            "Video composition completed",
            project_id=state["project_id"],
            path=video_path
        )

    except Exception as e:
        error_msg = f"Video composition failed: {str(e)}"
        logger.error(error_msg, project_id=state["project_id"])
        state["errors"].append(error_msg)

        # Mark project as failed
        async with get_session_context() as session:
            from app.models import Project
            from uuid import UUID as UUIDType
            project = await session.get(Project, UUIDType(state["project_id"]))
            if project:
                project.status = ProjectStatus.FAILED
                project.error_message = error_msg
                session.add(project)
                await session.commit()
    
    return state

def should_upload_to_youtube(state: GraphState) -> str:
    """
    Conditional edge: Decide whether to upload to YouTube.
    
    Returns:
    - "youtube_uploader" if video exists, auto_upload is True, and metadata is available
    - "end" otherwise
    """
    if not state.get("video_path"):
        return "end"

    if not state.get("auto_upload", False):
        logger.info("Auto-upload disabled", project_id=state["project_id"])
        return "end"

    if not state.get("youtube_metadata"):
        logger.info("No YouTube metadata provided", project_id=state["project_id"])
        return "end"

    return "youtube_uploader"