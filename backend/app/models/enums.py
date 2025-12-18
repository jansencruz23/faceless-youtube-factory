"""
Database ENUM types matching PostgreSQL definitions.
These enums are used for type safety in SQLModel classes.
"""
from enum import Enum


class ProjectStatus(str, Enum):
    """Project workflow status states."""
    DRAFT = "draft"
    GENERATING_SCRIPT ="generating_script"
    CASTING = "casting"
    GENERATING_AUDIO = "generating_audio"
    GENERATING_VIDEO = "generating_video"
    COMPLETED = "completed"
    UPLOADING_YOUTUBE = "uploading_youtube"
    PUBLISHED = "published"
    FAILED = "failed"


class AssetType(str, Enum):
    """Types of generated assets."""
    AUDIO = "audio"
    VIDEO = "video"


class PrivacyStatus(str, Enum):
    """YouTube video privacy settings."""
    PUBLIC = "public"
    PRIVATE = "private"
    UNLISTED = "unlisted"