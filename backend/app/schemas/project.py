"""Project-related schemas."""

from datetime import datetime
from typing import List, Optional, Dict, Any, Literal
from uuid import UUID
from pydantic import BaseModel, Field


class ProjectCreateRequest(BaseModel):
    """Request body for creating a new project."""

    title: str = Field(..., max_length=255, min_length=1)
    category: Optional[str] = Field(
        None, max_length=100, description="Project category for organization"
    )
    script_prompt: str = Field(..., max_length=5000, min_length=10)
    auto_upload: bool = False

    # Video format
    video_format: Literal["horizontal", "vertical"] = Field(
        default="horizontal",
        description="Video format: horizontal (YouTube) or vertical (Shorts/TikTok)",
    )

    # Image generation mode
    image_mode: Literal["per_scene", "single", "upload", "none"] = Field(
        default="per_scene",
        description="Image generation mode: per_scene, single, upload (custom image), none",
    )
    scenes_per_image: int = Field(
        default=2,
        ge=1,
        le=10,
        description="Number of scenes per generated image (for per_scene mode)",
    )
    background_image_url: Optional[str] = Field(
        default=None,
        description="URL/path of uploaded background image (for image_mode='upload')",
    )

    # Shorts/vertical specific
    background_video_url: Optional[str] = Field(
        default=None,
        description="Background video URL for shorts (loops behind captions)",
    )
    background_music_url: Optional[str] = Field(
        default=None,
        description="Background music URL",
    )
    music_volume: float = Field(
        default=0.3,
        ge=0.0,
        le=1.0,
        description="Background music volume (0-1)",
    )
    enable_captions: bool = Field(
        default=True,
        description="Enable word-by-word captions for shorts",
    )


class ProjectResponse(BaseModel):
    """Basic project response."""

    id: UUID
    title: str
    category: Optional[str] = None
    status: str
    youtube_video_id: Optional[str] = None
    youtube_url: Optional[str] = None
    error_message: Optional[str] = None
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class ScriptSceneResponse(BaseModel):
    """A single scene in the script."""

    speaker: str
    line: str
    duration: float


class ScriptResponse(BaseModel):
    """Script data response."""

    id: UUID
    version: int
    scenes: List[ScriptSceneResponse]
    created_at: datetime


class CastAssignmentResponse(BaseModel):
    """Voice assignment for a character."""

    voice_id: str
    pitch: str
    rate: str


class CastResponse(BaseModel):
    """Cast data response."""

    id: UUID
    assignments: Dict[str, CastAssignmentResponse]
    created_at: datetime


class AssetResponse(BaseModel):
    """Asset data response."""

    id: UUID
    asset_type: str
    file_path: str
    url: str
    character_name: Optional[str] = None
    file_size_bytes: Optional[int] = None
    created_at: datetime


class YouTubeMetadataShortResponse(BaseModel):
    """YouTube metadata in project response."""

    title: str
    privacy_status: str
    category_id: str


class ProjectDetailResponse(ProjectResponse):
    """Detailed project response with all related data."""

    script: Optional[ScriptResponse] = None
    cast: Optional[CastResponse] = None
    assets: List[AssetResponse] = []
    youtube_metadata: Optional[YouTubeMetadataShortResponse] = None


class ProjectListResponse(BaseModel):
    """Paginated list of projects."""

    items: List[ProjectResponse]
    total: int
    page: int
    page_size: int
