"""
YouTubeUploader Node - Uploads video to YouTube.
"""

from typing import Dict, Any
from pathlib import Path

from app.graph.state import GraphState
from app.services.youtube_service import youtube_service
from app.services.encryption_service import encryption_service
from app.models import ProjectStatus, YouTubeConnection
from app.database import get_session_context
from app.config import settings
from app.utils.logging import get_logger
from sqlmodel import select

logger = get_logger(__name__)


async def youtube_uploader_node(state: GraphState) -> GraphState:
    """
    Upload the completed video to YouTube.

    Steps:
    1. Fetch user's YouTube connection
    2. Refresh token if expired
    3. Upload video with metadata
    4. Save video ID to project

    Updates:
    - youtube_video_id: The uploaded video's YouTube ID
    - progress: Updated to 1.0 on success
    """
    logger.info("YouTubeUploader node started", project_id=state["project_id"])

    state["current_step"] = "uploading_youtube"

    try:
        async with get_session_context() as session:
            from app.models import Project

            # Get YouTube connection for this user
            stmt = select(YouTubeConnection).where(
                YouTubeConnection.user_id == state["user_id"],
                YouTubeConnection.is_active == True,
            )
            result = await session.execute(stmt)
            connection = result.scalar_one_or_none()

            if not connection:
                raise ValueError("No active YouTube connection found")

            # Decrypt tokens
            access_token = encryption_service.decrypt(connection.access_token)
            refresh_token = encryption_service.decrypt(connection.refresh_token)

            # Check if token needs refresh
            if connection.needs_refresh():
                logger.info("Refreshing YouTube token", user_id=state["user_id"])

                new_tokens = await youtube_service.refresh_token(refresh_token)

                # Update connection with new token
                connection.access_token = encryption_service.encrypt(
                    new_tokens["token"]
                )
                connection.token_expires_at = new_tokens["expiry"]
                session.add(connection)

                access_token = new_tokens["token"]

            # Update project status
            from uuid import UUID as UUIDType

            project = await session.get(Project, UUIDType(state["project_id"]))
            if project:
                project.status = ProjectStatus.UPLOADING_YOUTUBE
                session.add(project)
                await session.commit()

            # Prepare full file path
            video_full_path = str(Path(settings.static_dir) / state["video_path"])

            # Get metadata
            metadata = state.get("youtube_metadata", {})

            # Upload to YouTube
            video_id = await youtube_service.upload_video(
                access_token=access_token,
                file_path=video_full_path,
                metadata=metadata,
                refresh_token=refresh_token,
            )

            # Update project with YouTube info
            if project:
                project.youtube_video_id = video_id
                project.youtube_url = f"https://youtube.com/watch?v={video_id}"
                project.status = ProjectStatus.PUBLISHED
                session.add(project)
                await session.commit()

            state["youtube_video_id"] = video_id
            state["progress"] = 1.0

            logger.info(
                "YouTube upload completed",
                project_id=state["project_id"],
                video_id=video_id,
            )

    except Exception as e:
        error_msg = f"YouTube upload failed: {str(e)}"
        logger.error(error_msg, project_id=state["project_id"])
        state["errors"].append(error_msg)

        # Handle specific errors
        if "401" in str(e) or "invalid_grant" in str(e).lower():
            # Token revoked - deactivate connection
            async with get_session_context() as session:
                stmt = select(YouTubeConnection).where(
                    YouTubeConnection.user_id == state["user_id"]
                )
                result = await session.execute(stmt)
                connection = result.scalar_one_or_none()
                if connection:
                    connection.is_active = False
                    session.add(connection)

                from uuid import UUID as UUIDType

                project = await session.get(Project, UUIDType(state["project_id"]))
                if project:
                    project.status = ProjectStatus.COMPLETED  # Revert to completed
                    project.error_message = (
                        "YouTube connection expired. Please reconnect."
                    )
                    session.add(project)

                await session.commit()

        elif "403" in str(e) or "quotaExceeded" in str(e).lower():
            # Quota exceeded - mark for retry tomorrow
            async with get_session_context() as session:
                from uuid import UUID as UUIDType

                project = await session.get(Project, UUIDType(state["project_id"]))
                if project:
                    project.status = ProjectStatus.COMPLETED
                    project.error_message = (
                        "YouTube quota exceeded. Will retry tomorrow."
                    )
                    session.add(project)
                    await session.commit()

    return state
