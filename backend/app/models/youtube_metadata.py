"""
YouTubeMetadata model - stores video upload configuration.
"""
from datetime import datetime
from typing import TYPE_CHECKING, Any, Dict, List, Optional
from uuid import UUID

from sqlmodel import Field, Relationship, SQLModel, Column
from sqlalchemy import JSON, Enum as SAEnum

from app.models.base import BaseUUIDModel
from app.models.enums import PrivacyStatus

if TYPE_CHECKING:
    from app.models.project import Project


class YouTubeMetadataBase(SQLModel):
    """Shared YouTube metadata properties."""
    title: str = Field(max_length=100, nullable=False)
    description: Optional[str] = Field(default=None)
    category_id: str = Field(default="22", max_length=10)  # 22 = People & Blogs
    privacy_status: PrivacyStatus = Field(
        default=PrivacyStatus.PRIVATE,
        sa_column=Column(
            SAEnum(PrivacyStatus, name="privacy_status", create_type=False),
            nullable=False,
        )
    )


class YouTubeMetadata(YouTubeMetadataBase, BaseUUIDModel, table=True):
    """
    YouTubeMetadata database model.
    
    Table: youtube_metadata
    
    Stores the YouTube upload configuration for a project.
    Tags are stored as JSONB array.
    """
    __tablename__ = "youtube_metadata"
    
    # Foreign key to project (one-to-one relationship)
    project_id: UUID = Field(
        foreign_key="projects.id", 
        nullable=False, 
        index=True,
        unique=True  # One metadata per project
    )

    # JSONB tags column
    tags: List[str] = Field(
        default_factory=list,
        sa_column=Column(JSON, nullable=False, default=[])
    )

    # Relationships
    project: Optional["Project"] = Relationship(back_populates="youtube_metadata")

    def to_youtube_body(self) -> Dict[str, Any]:
        """
        Convert to YouTube API video insert body format.
        
        Returns dict ready for YouTube API upload.
        """
        return {
            "snippet": {
                "title": self.title,
                "description": self.description or "",
                "tags": self.tags,
                "categoryId": self.category_id,
            },
            "status": {
                "privacyStatus": self.privacy_status.value,
                "selfDeclaredMadeForKids": False,
            }
        }


class YouTubeMetadataCreate(SQLModel):
    """Schema for creating YouTube metadata."""
    project_id: UUID
    title: str = Field(max_length=100)
    description: Optional[str] = None
    tags: List[str] = []
    category_id: str = "22"
    privacy_status: PrivacyStatus = PrivacyStatus.PRIVATE


class YouTubeMetadataUpdate(SQLModel):
    """Schema for updating YouTube metadata."""
    title: Optional[str] = Field(default=None, max_length=100)
    description: Optional[str] = None
    tags: Optional[List[str]] = None
    category_id: Optional[str] = None
    privacy_status: Optional[PrivacyStatus] = None


class YouTubeMetadataRead(YouTubeMetadataBase):
    """Schema for reading YouTube metadata."""
    id: UUID
    project_id: UUID
    tags: List[str]
    created_at: datetime