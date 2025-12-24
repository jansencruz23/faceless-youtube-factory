"""YouTube integration endpoints."""

from datetime import datetime, timezone, timedelta
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, BackgroundTasks
from fastapi.responses import RedirectResponse
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_session
from app.crud.project import project_crud
from app.crud.youtube import youtube_crud
from app.schemas.youtube import (
    YouTubeAuthUrlResponse,
    YouTubeConnectionResponse,
    YouTubeMetadataRequest,
    YouTubeMetadataResponse,
    YouTubeUploadRequest,
)
from app.services.youtube_service import youtube_service
from app.services.groq_service import groq_service
from app.services.encryption_service import encryption_service
from app.models import ProjectStatus
from app.config import settings
from app.utils.logging import get_logger

router = APIRouter()
logger = get_logger(__name__)

DEFAULT_USER_ID = UUID("00000000-0000-0000-0000-000000000001")


@router.get("/auth-url", response_model=YouTubeAuthUrlResponse)
async def get_auth_url():
    """
    Generate OAuth authorization URL for YouTube.

    Frontend should redirect user to this URL to initiate OAuth flow.
    """
    auth_url, state = youtube_service.get_auth_url()

    return YouTubeAuthUrlResponse(auth_url=auth_url, state=state)


@router.get("/callback")
async def youtube_callback(
    code: str = Query(...),
    state: str = Query(None),
    session: AsyncSession = Depends(get_session),
):
    """
    Handle OAuth callback from Google.

    Exchanges authorization code for tokens and saves connection.
    Redirects to frontend dashboard on success.
    """
    try:
        # Exchange code for tokens
        token_data = await youtube_service.exchange_code(code)

        # Get channel info
        channel_info = await youtube_service.get_channel_info(token_data["token"])

        # Save connection
        await youtube_crud.create_connection(
            session=session,
            user_id=DEFAULT_USER_ID,
            channel_id=channel_info["channel_id"],
            channel_title=channel_info["title"],
            access_token=token_data["token"],
            refresh_token=token_data["refresh_token"],
            expires_at=datetime.utcnow()
            + timedelta(seconds=settings.youtube_token_expires_in),
        )

        logger.info(
            "YouTube connected",
            channel_id=channel_info["channel_id"],
            channel_title=channel_info["title"],
        )

        # Redirect to frontend
        return RedirectResponse(
            url=f"{settings.frontend_url}/youtube/callback?youtube_connected=true"
        )

    except Exception as e:
        logger.error("YouTube OAuth callback failed", error=str(e))
        return RedirectResponse(
            url=f"{settings.frontend_url}/youtube/callback?youtube_error={str(e)}"
        )


@router.get("/connection", response_model=YouTubeConnectionResponse)
async def get_connection_status(session: AsyncSession = Depends(get_session)):
    """Check if user has an active YouTube connection."""
    connection = await youtube_crud.get_connection(
        session=session, user_id=DEFAULT_USER_ID
    )

    if connection:
        return YouTubeConnectionResponse(
            connected=True,
            channel_id=connection.channel_id,
            channel_title=connection.channel_title,
        )

    return YouTubeConnectionResponse(connected=False)


@router.delete("/disconnect")
async def disconnect_youtube(session: AsyncSession = Depends(get_session)):
    """Disconnect YouTube account."""
    success = await youtube_crud.deactivate_connection(
        session=session, user_id=DEFAULT_USER_ID
    )

    if not success:
        raise HTTPException(
            status_code=404, detail="No active YouTube connection found"
        )

    logger.info("YouTube disconnected", user_id=str(DEFAULT_USER_ID))

    return {"message": "YouTube disconnected successfully"}


@router.post(
    "/projects/{project_id}/generate-metadata", response_model=YouTubeMetadataResponse
)
async def generate_metadata(
    project_id: UUID,
    request: YouTubeMetadataRequest,
    session: AsyncSession = Depends(get_session),
):
    """
    Generate SEO-optimized YouTube metadata using AI.

    Uses the project's script content to generate title, description, and tags.
    """
    project = await project_crud.get_with_relations(
        session=session, project_id=project_id, user_id=DEFAULT_USER_ID
    )

    if not project:
        raise HTTPException(status_code=404, detail="Project not found")

    if not project.scripts:
        raise HTTPException(
            status_code=400, detail="Project has no script to generate metadata from"
        )

    # Get latest script content
    latest_script = max(project.scripts, key=lambda s: s.version)
    script_content = latest_script.content

    # Generate metadata
    metadata = await groq_service.generate_metadata(
        script_content=script_content, context=request.video_context
    )

    # Save to database
    await youtube_crud.save_metadata(
        session=session,
        project_id=project_id,
        title=metadata["title"],
        description=metadata["description"],
        tags=metadata["tags"],
        category_id=metadata["category_id"],
        privacy_status="private",
    )

    return YouTubeMetadataResponse(
        title=metadata["title"],
        description=metadata["description"],
        tags=metadata["tags"],
        category_id=metadata["category_id"],
    )


@router.post("/projects/{project_id}/upload-to-youtube")
async def upload_to_youtube(
    project_id: UUID,
    request: YouTubeUploadRequest,
    background_tasks: BackgroundTasks,
    session: AsyncSession = Depends(get_session),
):
    """
    Upload completed video to YouTube.

    Prerequisites:
    - Project status must be "completed"
    - User must have an active YouTube connection
    """
    # Get project
    project = await project_crud.get_with_relations(
        session=session, project_id=project_id, user_id=DEFAULT_USER_ID
    )

    if not project:
        raise HTTPException(status_code=404, detail="Project not found")

    if project.status != ProjectStatus.COMPLETED:
        raise HTTPException(
            status_code=400,
            detail=f"Project must be completed to upload. Current status: {project.status.value}",
        )

    # Check YouTube connection
    connection = await youtube_crud.get_connection(
        session=session, user_id=DEFAULT_USER_ID
    )

    if not connection:
        raise HTTPException(
            status_code=400,
            detail="No YouTube connection. Please connect your YouTube account first.",
        )

    # Find video asset
    video_asset = next(
        (a for a in project.assets if a.asset_type.value == "video"), None
    )

    if not video_asset:
        raise HTTPException(
            status_code=400, detail="No video file found for this project"
        )

    # Save metadata
    await youtube_crud.save_metadata(
        session=session,
        project_id=project_id,
        title=request.title,
        description=request.description,
        tags=request.tags,
        category_id=request.category_id,
        privacy_status=request.privacy_status.value,
    )

    # Update project status
    await project_crud.update_status(
        session=session, project_id=project_id, status=ProjectStatus.UPLOADING_YOUTUBE
    )

    # Get video file path
    video_path = video_asset.file_path

    # Decrypt access token
    from app.services.encryption_service import encryption_service

    access_token = encryption_service.decrypt(connection.access_token)

    # Prepare metadata for YouTube API
    youtube_metadata = {
        "snippet": {
            "title": request.title,
            "description": request.description,
            "tags": request.tags,
            "categoryId": request.category_id,
        },
        "status": {
            "privacyStatus": request.privacy_status.value,
        },
    }

    # Add background task to upload
    background_tasks.add_task(
        upload_video_background,
        project_id=str(project_id),
        video_path=f"static/{video_path}",
        access_token=access_token,
        metadata=youtube_metadata,
    )

    logger.info("YouTube upload initiated", project_id=str(project_id))

    return {
        "status": "uploading_youtube",
        "message": "Upload started",
        "project_id": str(project_id),
    }


async def upload_video_background(
    project_id: str,
    video_path: str,
    access_token: str,
    metadata: dict,
):
    """Background task to upload video to YouTube."""
    from app.database import get_session_context
    from app.models import Project
    from uuid import UUID as UUIDType
    from pathlib import Path

    try:
        logger.info(
            "Starting YouTube upload", project_id=project_id, video_path=video_path
        )

        # Upload to YouTube
        video_id = await youtube_service.upload_video(
            access_token=access_token,
            file_path=video_path,
            metadata=metadata,
        )

        # Update project with YouTube info
        async with get_session_context() as session:
            project = await session.get(Project, UUIDType(project_id))
            if project:
                project.youtube_video_id = video_id
                project.youtube_url = f"https://youtube.com/watch?v={video_id}"
                project.status = ProjectStatus.PUBLISHED
                session.add(project)
                await session.commit()

        logger.info(
            "YouTube upload completed", project_id=project_id, video_id=video_id
        )

    except Exception as e:
        logger.error("YouTube upload failed", project_id=project_id, error=str(e))

        # Update project with error
        async with get_session_context() as session:
            project = await session.get(Project, UUIDType(project_id))
            if project:
                project.status = ProjectStatus.COMPLETED
                project.error_message = f"YouTube upload failed: {str(e)}"
                session.add(project)
                await session.commit()
