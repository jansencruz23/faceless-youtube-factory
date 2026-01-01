"""Project management endpoints."""

from typing import Optional
from uuid import UUID
from pathlib import Path
import shutil

from fastapi import (
    APIRouter,
    Depends,
    HTTPException,
    BackgroundTasks,
    Query,
    UploadFile,
    File,
)
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_session
from app.config import settings
from app.crud.project import project_crud
from app.schemas.project import (
    ProjectCreateRequest,
    ProjectResponse,
    ProjectListResponse,
    ProjectDetailResponse,
    ScriptResponse,
    ScriptSceneResponse,
    CastResponse,
    CastAssignmentResponse,
    AssetResponse,
)
from app.models import ProjectStatus
from app.graph import run_pipeline
from app.utils.logging import get_logger
from app.auth import ClerkUser, get_current_user

router = APIRouter()
logger = get_logger(__name__)


def get_user_uuid(clerk_user: ClerkUser) -> UUID:
    """
    Convert Clerk user ID to UUID for database operations.
    Clerk IDs are strings like 'user_2abc123', we need to create a deterministic UUID.
    """
    import hashlib

    # Create a deterministic UUID from the Clerk user ID
    hash_bytes = hashlib.md5(clerk_user.user_id.encode()).digest()
    return UUID(bytes=hash_bytes)


async def ensure_user_exists(session: AsyncSession, clerk_user: ClerkUser) -> UUID:
    """
    Ensure that a user exists in the database for the given Clerk user.
    Creates the user if they don't exist.
    Returns the user's UUID.
    """
    from app.models import User
    from sqlmodel import select

    user_id = get_user_uuid(clerk_user)

    # Check if user exists
    result = await session.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()

    if not user:
        # Create user with Clerk email or a generated one
        email = clerk_user.email or f"{clerk_user.user_id}@clerk.user"
        user = User(id=user_id, email=email)
        session.add(user)
        await session.commit()
        await session.refresh(user)
        logger.info("Created new user from Clerk", user_id=str(user_id), email=email)

    return user_id


async def run_pipeline_background(
    project_id: str,
    user_id: str,
    script_prompt: str,
    auto_upload: bool,
    image_mode: str = "per_scene",
    scenes_per_image: int = 2,
    background_image_url: str = None,
    video_format: str = "horizontal",
    background_video_url: str = None,
    background_music_url: str = None,
    music_volume: float = 0.3,
    enable_captions: bool = True,
):
    """Background task to run the generation pipeline."""
    try:
        await run_pipeline(
            project_id=project_id,
            user_id=user_id,
            script_prompt=script_prompt,
            auto_upload=auto_upload,
            youtube_metadata=None,
            image_mode=image_mode,
            scenes_per_image=scenes_per_image,
            background_image_url=background_image_url,
            video_format=video_format,
            background_video_url=background_video_url,
            background_music_url=background_music_url,
            music_volume=music_volume,
            enable_captions=enable_captions,
        )
    except Exception as e:
        logger.error(
            "Pipeline background task failed", project_id=project_id, error=str(e)
        )


@router.post("", response_model=ProjectResponse)
async def create_project(
    request: ProjectCreateRequest,
    background_tasks: BackgroundTasks,
    session: AsyncSession = Depends(get_session),
    current_user: ClerkUser = Depends(get_current_user),
):
    """Create a new project and start the generation pipeline."""
    # Ensure user exists in database (creates if not)
    user_id = await ensure_user_exists(session, current_user)

    # Create project record
    project = await project_crud.create(
        session=session, user_id=user_id, title=request.title
    )

    # Update status to generating
    await project_crud.update_status(
        session=session, project_id=project.id, status=ProjectStatus.GENERATING_SCRIPT
    )

    # Start pipeline in background
    background_tasks.add_task(
        run_pipeline_background,
        project_id=str(project.id),
        user_id=str(user_id),
        script_prompt=request.script_prompt,
        auto_upload=request.auto_upload,
        image_mode=request.image_mode,
        scenes_per_image=request.scenes_per_image,
        background_image_url=request.background_image_url,
        video_format=request.video_format,
        background_video_url=request.background_video_url,
        background_music_url=request.background_music_url,
        music_volume=request.music_volume,
        enable_captions=request.enable_captions,
    )

    logger.info("Project created", project_id=str(project.id), user_id=str(user_id))

    return ProjectResponse(
        id=project.id,
        title=project.title,
        status=project.status.value,
        youtube_video_id=project.youtube_video_id,
        youtube_url=project.youtube_url,
        error_message=project.error_message,
        created_at=project.created_at,
        updated_at=project.updated_at,
    )


@router.post("/upload-background")
async def upload_background(
    file: UploadFile = File(...),
):
    """
    Upload a custom background image for use with image_mode='upload'.

    Returns the URL path to use as background_image_url in createProject.
    """
    # Validate file type
    allowed_types = ["image/jpeg", "image/png", "image/webp"]
    if file.content_type not in allowed_types:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid file type. Allowed: {', '.join(allowed_types)}",
        )

    # Create uploads directory
    uploads_dir = Path(settings.static_dir) / "uploads"
    uploads_dir.mkdir(parents=True, exist_ok=True)

    # Generate unique filename
    import uuid

    ext = file.filename.split(".")[-1] if "." in file.filename else "png"
    filename = f"{uuid.uuid4()}.{ext}"
    file_path = uploads_dir / filename

    # Save file
    with open(file_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)

    # Return relative URL path
    url_path = f"uploads/{filename}"

    logger.info("Background image uploaded", path=url_path)

    return {"url": url_path}


@router.get("", response_model=ProjectListResponse)
async def list_projects(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    session: AsyncSession = Depends(get_session),
    current_user: ClerkUser = Depends(get_current_user),
):
    """List all projects for the current user."""
    user_id = get_user_uuid(current_user)
    items, total = await project_crud.list_by_user(
        session=session, user_id=user_id, page=page, page_size=page_size
    )

    return ProjectListResponse(
        items=[
            ProjectResponse(
                id=p.id,
                title=p.title,
                status=p.status.value,
                youtube_video_id=p.youtube_video_id,
                youtube_url=p.youtube_url,
                error_message=p.error_message,
                created_at=p.created_at,
                updated_at=p.updated_at,
            )
            for p in items
        ],
        total=total,
        page=page,
        page_size=page_size,
    )


@router.get("/preset-videos")
async def list_preset_videos():
    """
    List available preset background videos for shorts.

    Place your preset videos in: static/presets/videos/
    """
    presets_dir = Path(settings.static_dir) / "presets" / "videos"
    presets_dir.mkdir(parents=True, exist_ok=True)

    video_extensions = [".mp4", ".webm", ".mov"]
    presets = []

    for video_file in presets_dir.iterdir():
        if video_file.suffix.lower() in video_extensions:
            display_name = video_file.stem.replace("_", " ").replace("-", " ").title()
            presets.append(
                {
                    "id": video_file.stem,
                    "name": display_name,
                    "url": f"presets/videos/{video_file.name}",
                    "thumbnail": None,
                }
            )

    return {"presets": presets}


@router.get("/preset-music")
async def list_preset_music():
    """
    List available preset background music for shorts.

    Place your music files in: static/presets/music/
    """
    presets_dir = Path(settings.static_dir) / "presets" / "music"
    presets_dir.mkdir(parents=True, exist_ok=True)

    audio_extensions = [".mp3", ".wav", ".m4a", ".ogg"]
    presets = []

    for audio_file in presets_dir.iterdir():
        if audio_file.suffix.lower() in audio_extensions:
            display_name = audio_file.stem.replace("_", " ").replace("-", " ").title()
            presets.append(
                {
                    "id": audio_file.stem,
                    "name": display_name,
                    "url": f"presets/music/{audio_file.name}",
                }
            )

    return {"presets": presets}


@router.get("/{project_id}", response_model=ProjectDetailResponse)
async def get_project(
    project_id: UUID,
    session: AsyncSession = Depends(get_session),
    current_user: ClerkUser = Depends(get_current_user),
):
    """Get project details with all related data."""
    user_id = get_user_uuid(current_user)
    project = await project_crud.get_with_relations(
        session=session, project_id=project_id, user_id=user_id
    )

    if not project:
        raise HTTPException(status_code=404, detail="Project not found")

    # Build response
    response = ProjectDetailResponse(
        id=project.id,
        title=project.title,
        status=project.status.value,
        youtube_video_id=project.youtube_video_id,
        youtube_url=project.youtube_url,
        error_message=project.error_message,
        created_at=project.created_at,
        updated_at=project.updated_at,
    )

    # Add script if exists
    if project.scripts:
        latest_script = max(project.scripts, key=lambda s: s.version)
        scenes_data = latest_script.content.get("scenes", [])
        response.script = ScriptResponse(
            id=latest_script.id,
            version=latest_script.version,
            scenes=[
                ScriptSceneResponse(
                    speaker=s.get("speaker", ""),
                    line=s.get("line", ""),
                    duration=s.get("duration", 3.0),
                )
                for s in scenes_data
            ],
            created_at=latest_script.created_at,
        )

    # Add cast if exists
    if project.casts:
        latest_cast = project.casts[-1]
        response.cast = CastResponse(
            id=latest_cast.id,
            assignments={
                name: CastAssignmentResponse(
                    voice_id=settings.get("voice_id", ""),
                    pitch=settings.get("pitch", "+0Hz"),
                    rate=settings.get("rate", "+0%"),
                )
                for name, settings in latest_cast.assignments.items()
            },
            created_at=latest_cast.created_at,
        )

    # Add assets
    response.assets = [
        AssetResponse(
            id=asset.id,
            asset_type=asset.asset_type.value,
            file_path=asset.file_path,
            url=f"/static/{asset.file_path}",
            character_name=asset.character_name,
            file_size_bytes=asset.file_size_bytes,
            created_at=asset.created_at,
        )
        for asset in project.assets
    ]

    return response


@router.post("/{project_id}/regenerate-audio")
async def regenerate_audio(
    project_id: UUID,
    background_tasks: BackgroundTasks,
    session: AsyncSession = Depends(get_session),
    current_user: ClerkUser = Depends(get_current_user),
):
    """Regenerate audio with current cast settings."""
    import asyncio
    from app.graph.nodes.audio_generator import audio_generator_node
    from app.graph.nodes.video_composer import video_composer_node
    from app.models import Asset, AssetType
    from sqlmodel import delete

    user_id = get_user_uuid(current_user)
    project = await project_crud.get_with_relations(
        session=session, project_id=project_id, user_id=user_id
    )

    if not project:
        raise HTTPException(status_code=404, detail="Project not found")

    if not project.scripts or not project.casts:
        raise HTTPException(
            status_code=400,
            detail="Project needs script and cast before regenerating audio",
        )

    # Get latest script and cast - extract values before async task
    latest_script = max(project.scripts, key=lambda s: s.version)
    latest_cast = project.casts[-1]
    script_content = latest_script.content
    cast_assignments = latest_cast.assignments
    project_id_str = str(project_id)

    # Find existing image files from the file system
    # Images are saved to static/images/{project_id}/ by image_service
    from pathlib import Path

    images_dir = Path(settings.static_dir) / "images" / project_id_str
    existing_image_files = []
    if images_dir.exists():
        # Get all png files sorted by name (they're named image_0.png, image_1.png, etc.)
        png_files = sorted(images_dir.glob("*.png"))
        existing_image_files = [f"images/{project_id_str}/{f.name}" for f in png_files]

    # Build image_scene_indices based on number of scenes and images
    num_scenes = len(script_content.get("scenes", []))
    num_images = len(existing_image_files)
    if num_images > 0:
        # Calculate scenes_per_image from existing ratio
        scenes_per_image = max(1, num_scenes // num_images) if num_images > 0 else 2
        image_scene_indices = [
            min(i // scenes_per_image, num_images - 1) for i in range(num_scenes)
        ]
    else:
        scenes_per_image = 2
        image_scene_indices = []

    # Delete existing audio assets
    await session.execute(
        delete(Asset).where(
            Asset.project_id == project_id, Asset.asset_type == AssetType.AUDIO
        )
    )
    await session.commit()

    # Update status to generating_audio
    await project_crud.update_status(
        session=session, project_id=project_id, status=ProjectStatus.GENERATING_AUDIO
    )

    # Build state for audio regeneration
    async def regenerate_task():
        from app.graph.state import GraphState
        from app.database import get_session_context

        try:
            state: GraphState = {
                "project_id": project_id_str,
                "user_id": str(user_id),
                "script_prompt": "",
                "auto_upload": False,
                "scenes_per_image": scenes_per_image,
                "script_json": script_content,
                "cast_list": cast_assignments,
                "audio_files": [],
                "audio_scene_indices": [],
                "image_files": existing_image_files,
                "image_scene_indices": image_scene_indices,
                "image_prompts": [],
                "video_path": None,
                "youtube_metadata": None,
                "youtube_video_id": None,
                "errors": [],
                "retry_count": 0,
                "current_step": "regenerating_audio",
                "progress": 0.3,
            }

            # Run audio generator
            state = await audio_generator_node(state)

            # Run video composer if audio succeeded
            if state["audio_files"]:
                # Update status to generating_video
                async with get_session_context() as db_session:
                    await project_crud.update_status(
                        session=db_session,
                        project_id=UUID(project_id_str),
                        status=ProjectStatus.GENERATING_VIDEO,
                    )
                state = await video_composer_node(state)

            # Update status to completed
            async with get_session_context() as db_session:
                await project_crud.update_status(
                    session=db_session,
                    project_id=UUID(project_id_str),
                    status=ProjectStatus.COMPLETED,
                )

            logger.info(
                "Audio regeneration complete",
                project_id=project_id_str,
                audio_count=len(state["audio_files"]),
            )
        except Exception as e:
            logger.error(
                "Audio regeneration failed",
                project_id=project_id_str,
                error=str(e),
            )
            # Update status to failed
            async with get_session_context() as db_session:
                await project_crud.update_status(
                    session=db_session,
                    project_id=UUID(project_id_str),
                    status=ProjectStatus.FAILED,
                    error_message=str(e),
                )

    # Use asyncio.create_task for proper async context
    asyncio.create_task(regenerate_task())

    return {"message": "Audio regeneration started", "project_id": project_id_str}


@router.post("/{project_id}/regenerate-video")
async def regenerate_video(
    project_id: UUID,
    background_tasks: BackgroundTasks,
    session: AsyncSession = Depends(get_session),
    current_user: ClerkUser = Depends(get_current_user),
):
    """Regenerate video with existing audio."""
    from app.graph.nodes.video_composer import video_composer_node
    from app.models import Asset, AssetType
    from sqlmodel import select, delete

    user_id = get_user_uuid(current_user)
    project = await project_crud.get_by_id(
        session=session, project_id=project_id, user_id=user_id
    )

    if not project:
        raise HTTPException(status_code=404, detail="Project not found")

    # Get audio assets
    audio_assets = [a for a in project.assets if a.asset_type == AssetType.AUDIO]

    if not audio_assets:
        raise HTTPException(
            status_code=400, detail="No audio files to compose into video"
        )

    # Get script for metadata
    if not project.scripts:
        raise HTTPException(status_code=400, detail="No script found")

    latest_script = max(project.scripts, key=lambda s: s.version)

    # Delete existing video assets
    await session.execute(
        delete(Asset).where(
            Asset.project_id == project_id, Asset.asset_type == AssetType.VIDEO
        )
    )
    await session.commit()

    # Sort audio files by scene index
    audio_files = sorted(
        [a.file_path for a in audio_assets],
        key=lambda p: int(p.split("/")[-1].replace(".mp3", "")),
    )

    async def regenerate_task():
        from app.graph.state import GraphState

        state: GraphState = {
            "project_id": str(project_id),
            "user_id": str(user_id),
            "script_prompt": "",
            "auto_upload": False,
            "script_json": latest_script.content,
            "cast_list": {},
            "audio_files": audio_files,
            "video_path": None,
            "youtube_metadata": None,
            "youtube_video_id": None,
            "errors": [],
            "retry_count": 0,
            "current_step": "regenerating_video",
            "progress": 0.6,
        }

        state = await video_composer_node(state)

        logger.info(
            "Video regeneration complete",
            project_id=str(project_id),
            video_path=state.get("video_path"),
        )

    background_tasks.add_task(regenerate_task)

    return {"message": "Video regeneration started", "project_id": str(project_id)}


@router.post("/{project_id}/cancel")
async def cancel_project(
    project_id: UUID,
    session: AsyncSession = Depends(get_session),
    current_user: ClerkUser = Depends(get_current_user),
):
    """
    Cancel an in-progress project.

    Sets the project status to 'failed' with a cancellation message.
    Note: This doesn't stop a running background task immediately,
    but prevents further processing steps.
    """
    user_id = get_user_uuid(current_user)
    project = await project_crud.get_by_id(
        session=session, project_id=project_id, user_id=user_id
    )

    if not project:
        raise HTTPException(status_code=404, detail="Project not found")

    # Check if project is in a cancellable state
    cancellable_states = [
        ProjectStatus.DRAFT,
        ProjectStatus.GENERATING_SCRIPT,
        ProjectStatus.CASTING,
        ProjectStatus.GENERATING_IMAGES,
        ProjectStatus.GENERATING_AUDIO,
        ProjectStatus.GENERATING_VIDEO,
        ProjectStatus.UPLOADING_YOUTUBE,
    ]

    if project.status not in cancellable_states:
        raise HTTPException(
            status_code=400,
            detail=f"Cannot cancel project in '{project.status.value}' status",
        )

    # Update status to failed with cancellation message
    project.status = ProjectStatus.FAILED
    project.error_message = "Cancelled by user"
    session.add(project)
    await session.commit()

    logger.info("Project cancelled", project_id=str(project_id))

    return {"message": "Project cancelled", "project_id": str(project_id)}


@router.delete("/{project_id}")
async def delete_project(
    project_id: UUID,
    session: AsyncSession = Depends(get_session),
    current_user: ClerkUser = Depends(get_current_user),
):
    """
    Delete a project and all its related data.

    Removes:
    - Project record
    - Scripts, casts, assets from database
    - Generated files from filesystem
    """
    from app.models import Project, Script, Cast, Asset
    from sqlmodel import delete
    import shutil
    from pathlib import Path
    from app.config import settings

    user_id = get_user_uuid(current_user)
    project = await project_crud.get_by_id(
        session=session, project_id=project_id, user_id=user_id
    )

    if not project:
        raise HTTPException(status_code=404, detail="Project not found")

    # Don't allow deletion of in-progress projects
    in_progress_states = [
        ProjectStatus.GENERATING_SCRIPT,
        ProjectStatus.CASTING,
        ProjectStatus.GENERATING_IMAGES,
        ProjectStatus.GENERATING_AUDIO,
        ProjectStatus.GENERATING_VIDEO,
        ProjectStatus.UPLOADING_YOUTUBE,
    ]

    if project.status in in_progress_states:
        raise HTTPException(
            status_code=400,
            detail="Cannot delete project while in progress. Cancel it first.",
        )

    # Delete generated files
    static_dir = Path(settings.static_dir)

    # Delete audio files
    audio_dir = static_dir / "audio" / str(project_id)
    if audio_dir.exists():
        shutil.rmtree(audio_dir, ignore_errors=True)
        logger.info(f"Deleted audio directory: {audio_dir}")

    # Delete video files
    video_dir = static_dir / "video" / str(project_id)
    if video_dir.exists():
        shutil.rmtree(video_dir, ignore_errors=True)
        logger.info(f"Deleted video directory: {video_dir}")

    # Delete image files
    images_dir = static_dir / "images" / str(project_id)
    if images_dir.exists():
        shutil.rmtree(images_dir, ignore_errors=True)
        logger.info(f"Deleted images directory: {images_dir}")

    # Delete database records (cascading deletes handle related records)
    await session.execute(delete(Asset).where(Asset.project_id == project_id))
    await session.execute(delete(Cast).where(Cast.project_id == project_id))
    await session.execute(delete(Script).where(Script.project_id == project_id))
    await session.execute(delete(Project).where(Project.id == project_id))
    await session.commit()

    logger.info("Project deleted", project_id=str(project_id))

    return {"message": "Project deleted successfully", "project_id": str(project_id)}


@router.post("/upload-video")
async def upload_video(file: UploadFile = File(...)):
    """Upload a background video for shorts."""
    allowed_types = ["video/mp4", "video/webm", "video/quicktime"]
    if file.content_type not in allowed_types:
        raise HTTPException(status_code=400, detail="Invalid file type")

    uploads_dir = Path(settings.static_dir) / "uploads" / "videos"
    uploads_dir.mkdir(parents=True, exist_ok=True)

    import uuid

    ext = file.filename.split(".")[-1] if "." in file.filename else "mp4"
    filename = f"{uuid.uuid4()}.{ext}"
    file_path = uploads_dir / filename

    with open(file_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)

    return {"url": f"uploads/videos/{filename}"}


@router.post("/upload-music")
async def upload_music(file: UploadFile = File(...)):
    """Upload background music."""

    allowed_types = ["audio/mpeg", "audio/wav", "audio/mp3", "audio/x-wav"]
    if file.content_type not in allowed_types:
        raise HTTPException(status_code=400, detail="Invalid audio type")

    uploads_dir = Path(settings.static_dir) / "uploads" / "music"
    uploads_dir.mkdir(parents=True, exist_ok=True)

    import uuid

    ext = file.filename.split(".")[-1] if "." in file.filename else "mp3"
    filename = f"{uuid.uuid4()}.{ext}"
    file_path = uploads_dir / filename

    with open(file_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)

    return {"url": f"uploads/music/{filename}"}
