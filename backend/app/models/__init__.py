"""
SQLModel ORM models for the application.
All models are exported here for convenient imports:
    from app.models import User, Project, Script, ...
"""
from app.models.enums import ProjectStatus, AssetType, PrivacyStatus
from app.models.base import BaseUUIDModel, utc_now
from app.models.user import User, UserCreate, UserRead
from app.models.project import (
    Project,
    ProjectCreate,
    ProjectRead,
    ProjectReadWithRelations,
)
from app.models.script import (
    Script,
    ScriptCreate,
    ScriptRead,
    ScriptContent,
    SceneContent,
)
from app.models.cast import (
    Cast,
    CastCreate,
    CastUpdate,
    CastRead,
    VoiceSettings,
)
from app.models.asset import Asset, AssetCreate, AssetRead
from app.models.youtube_connection import (
    YouTubeConnection,
    YouTubeConnectionCreate,
    YouTubeConnectionRead,
)
from app.models.youtube_metadata import (
    YouTubeMetadata,
    YouTubeMetadataCreate,
    YouTubeMetadataUpdate,
    YouTubeMetadataRead,
)

__all__ = [
    # Enums
    "ProjectStatus",
    "AssetType",
    "PrivacyStatus",
    # Base
    "BaseUUIDModel",
    "utc_now",
    # User
    "User",
    "UserCreate",
    "UserRead",
    # Project
    "Project",
    "ProjectCreate",
    "ProjectRead",
    "ProjectReadWithRelations",
    # Script
    "Script",
    "ScriptCreate",
    "ScriptRead",
    "ScriptContent",
    "SceneContent",
    # Cast
    "Cast",
    "CastCreate",
    "CastUpdate",
    "CastRead",
    "VoiceSettings",
    # Asset
    "Asset",
    "AssetCreate",
    "AssetRead",
    # YouTube Connection
    "YouTubeConnection",
    "YouTubeConnectionCreate",
    "YouTubeConnectionRead",
    # YouTube Metadata
    "YouTubeMetadata",
    "YouTubeMetadataCreate",
    "YouTubeMetadataUpdate",
    "YouTubeMetadataRead",
]