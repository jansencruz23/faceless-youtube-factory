"""
Automation API endpoints for n8n and other automation tools.
Uses API key authentication instead of Clerk.
"""

from uuid import UUID
import secrets

from fastapi import APIRouter, Depends, HTTPException, Header, BackgroundTasks
from sqlalchemy.ext.asyncio import AsyncSession
from pydantic import BaseModel

from app.config import settings
from app.database import get_session
from app.crud import project_crud
from app.models import ProjectStatus, User
from app.api.v1.projects import run_pipeline_background
from app.utils.logging import get_logger
from sqlmodel import select
import hashlib

router = APIRouter()
logger = get_logger(__name__)

# Default automation user ID (created on first use)
AUTOMATION_USER_EMAIL = "automation@system.internal"


def verify_api_key(x_api_key: str = Header(..., alias="X-API-Key")) -> str:
    """Verify the automation API key."""
    if not settings.automation_api_key:
        raise HTTPException(
            status_code=503,
            detail="Automation API key not configured. Set AUTOMATION_API_KEY in .env",
        )

    if not secrets.compare_digest(x_api_key, settings.automation_api_key):
        raise HTTPException(status_code=401, detail="Invalid API key")

    return x_api_key


async def get_or_create_automation_user(session: AsyncSession) -> UUID:
    """Get or create the automation system user."""
    result = await session.execute(
        select(User).where(User.email == AUTOMATION_USER_EMAIL)
    )
    user = result.scalar_one_or_none()

    if not user:
        # Create deterministic UUID from email
        hash_bytes = hashlib.md5(AUTOMATION_USER_EMAIL.encode()).digest()
        user_id = UUID(bytes=hash_bytes)

        user = User(id=user_id, email=AUTOMATION_USER_EMAIL)
        session.add(user)
        await session.commit()
        await session.refresh(user)
        logger.info("Created automation user", user_id=str(user.id))

    return user.id


class AutoGenerateRequest(BaseModel):
    """Request body for auto-generate endpoint."""

    topic: str
    title: str | None = None
    category: str | None = None  # e.g., "psychology", "motivation", "tech"

    # Video format
    video_format: str = "vertical"  # "vertical" or "horizontal"

    # For vertical videos - background video options:
    # - None = no background video
    # - "preset:minecraft" = use preset video
    # - "preset:subway" = use preset video
    # - URL = uploaded video URL
    background_video: str | None = None

    # Background music options:
    # - None = no music
    # - "preset:lofi" = use preset music
    # - "preset:energetic" = use preset music
    # - URL = uploaded music URL
    background_music: str | None = None
    music_volume: float = 0.3  # 0.0 to 1.0

    # Image mode (for horizontal videos mainly):
    # - "per_scene" = generate image per scene
    # - "shared" = one image for multiple scenes
    # - "upload" = use uploaded background
    # - "none" = no images (vertical with video background)
    image_mode: str = "none"  # Default to none for vertical

    # Captions
    enable_captions: bool = True

    # Auto upload to YouTube
    auto_upload: bool = True


class AutoGenerateResponse(BaseModel):
    """Response from auto-generate endpoint."""

    project_id: str
    title: str
    status: str
    message: str


@router.post("/generate", response_model=AutoGenerateResponse)
async def auto_generate_video(
    request: AutoGenerateRequest,
    background_tasks: BackgroundTasks,
    session: AsyncSession = Depends(get_session),
    _api_key: str = Depends(verify_api_key),
):
    """
    Create a new project and start video generation.

    This endpoint is for automation tools like n8n.
    Requires X-API-Key header with valid AUTOMATION_API_KEY.
    """
    # Get automation user
    user_id = await get_or_create_automation_user(session)

    # Create title from topic if not provided
    title = request.title or f"Auto: {request.topic[:50]}"

    # Create project
    project = await project_crud.create(
        session=session, user_id=user_id, title=title, category=request.category
    )

    # Update status
    await project_crud.update_status(
        session=session, project_id=project.id, status=ProjectStatus.GENERATING_SCRIPT
    )

    # Process background video URL
    background_video_url = None
    if request.background_video:
        if request.background_video.startswith("preset:"):
            preset_name = request.background_video.replace("preset:", "")
            # Path relative to static_base (static/), not starting with /static
            background_video_url = f"presets/videos/{preset_name}.mp4"
        else:
            background_video_url = request.background_video

    # Process background music URL
    background_music_url = None
    if request.background_music:
        if request.background_music.startswith("preset:"):
            preset_name = request.background_music.replace("preset:", "")
            # Path relative to static_base (static/), not starting with /static
            background_music_url = f"presets/music/{preset_name}.mp3"
        else:
            background_music_url = request.background_music

    # Start pipeline in background
    background_tasks.add_task(
        run_pipeline_background,
        project_id=str(project.id),
        user_id=str(user_id),
        script_prompt=request.topic,
        auto_upload=request.auto_upload,
        video_format=request.video_format,
        image_mode=request.image_mode,
        background_video_url=background_video_url,
        background_music_url=background_music_url,
        music_volume=request.music_volume,
        enable_captions=request.enable_captions,
    )

    logger.info(
        "Auto-generated project created",
        project_id=str(project.id),
        topic=request.topic,
    )

    return AutoGenerateResponse(
        project_id=str(project.id),
        title=title,
        status="generating_script",
        message="Video generation started. Use GET /api/v1/projects/{id} to check status.",
    )


@router.get("/status/{project_id}")
async def get_project_status(
    project_id: UUID,
    session: AsyncSession = Depends(get_session),
    _api_key: str = Depends(verify_api_key),
):
    """
    Get project status for automation polling.

    Returns simplified status for n8n workflow decisions.
    """
    project = await project_crud.get_by_id(session=session, project_id=project_id)

    if not project:
        raise HTTPException(status_code=404, detail="Project not found")

    # Determine if complete
    is_complete = project.status in [
        ProjectStatus.COMPLETED,
        ProjectStatus.PUBLISHED,
        ProjectStatus.FAILED,
    ]

    return {
        "project_id": str(project.id),
        "title": project.title,
        "status": project.status.value,
        "is_complete": is_complete,
        "is_success": project.status
        in [ProjectStatus.COMPLETED, ProjectStatus.PUBLISHED],
        "youtube_url": project.youtube_url,
        "error_message": project.error_message,
    }


@router.get("/projects")
async def list_automation_projects(
    category: str | None = None,
    page: int = 1,
    page_size: int = 50,
    session: AsyncSession = Depends(get_session),
    _api_key: str = Depends(verify_api_key),
):
    """
    List all automation projects with optional category filter.

    This shows projects created by the automation system user.
    Requires X-API-Key header with valid AUTOMATION_API_KEY.
    """
    # Get automation user ID
    result = await session.execute(
        select(User).where(User.email == AUTOMATION_USER_EMAIL)
    )
    user = result.scalar_one_or_none()

    if not user:
        return {"items": [], "total": 0, "page": page, "page_size": page_size}

    # List projects for automation user
    items, total = await project_crud.list_by_user(
        session=session,
        user_id=user.id,
        page=page,
        page_size=page_size,
        category=category,
    )

    return {
        "items": [
            {
                "id": str(p.id),
                "title": p.title,
                "category": p.category,
                "status": p.status.value,
                "youtube_video_id": p.youtube_video_id,
                "youtube_url": p.youtube_url,
                "error_message": p.error_message,
                "created_at": p.created_at.isoformat(),
                "updated_at": p.updated_at.isoformat(),
            }
            for p in items
        ],
        "total": total,
        "page": page,
        "page_size": page_size,
    }


@router.get("/projects/{project_id}")
async def get_automation_project(
    project_id: UUID,
    session: AsyncSession = Depends(get_session),
    _api_key: str = Depends(verify_api_key),
):
    """
    Get automation project details.

    This allows viewing projects created by the automation system.
    Requires X-API-Key header with valid AUTOMATION_API_KEY.
    """
    # Get automation user
    result = await session.execute(
        select(User).where(User.email == AUTOMATION_USER_EMAIL)
    )
    user = result.scalar_one_or_none()

    if not user:
        raise HTTPException(status_code=404, detail="Automation user not found")

    # Get project - only if owned by automation user
    project = await project_crud.get_with_relations(
        session=session, project_id=project_id, user_id=user.id
    )

    if not project:
        raise HTTPException(status_code=404, detail="Project not found")

    # Build response
    response = {
        "id": str(project.id),
        "title": project.title,
        "category": project.category,
        "status": project.status.value,
        "youtube_video_id": project.youtube_video_id,
        "youtube_url": project.youtube_url,
        "error_message": project.error_message,
        "created_at": project.created_at.isoformat(),
        "updated_at": project.updated_at.isoformat(),
        "script": None,
        "cast": None,
        "assets": [],
    }

    # Add script if exists
    if project.scripts:
        latest_script = max(project.scripts, key=lambda s: s.version)
        scenes_data = latest_script.content.get("scenes", [])
        response["script"] = {
            "id": str(latest_script.id),
            "version": latest_script.version,
            "scenes": [
                {
                    "speaker": s.get("speaker", ""),
                    "line": s.get("line", ""),
                    "duration": s.get("duration", 3.0),
                }
                for s in scenes_data
            ],
            "created_at": latest_script.created_at.isoformat(),
        }

    # Add cast if exists
    if project.casts:
        latest_cast = max(project.casts, key=lambda c: c.created_at)
        response["cast"] = {
            "id": str(latest_cast.id),
            "assignments": latest_cast.assignments or {},
            "created_at": latest_cast.created_at.isoformat(),
        }

    # Add assets
    if project.assets:
        response["assets"] = [
            {
                "id": str(a.id),
                "type": a.asset_type.value if a.asset_type else "unknown",
                "url": a.file_path,
                "created_at": a.created_at.isoformat(),
            }
            for a in project.assets
        ]

    return response
