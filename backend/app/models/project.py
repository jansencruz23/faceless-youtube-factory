"""
Project model - the central entity for video generation workflows.
"""

from datetime import datetime
from typing import TYPE_CHECKING, List, Optional
from uuid import UUID

from sqlmodel import Field, Relationship, SQLModel, Column
from sqlalchemy import Enum as SAEnum

from app.models.base import BaseUUIDModel, utc_now
from app.models.enums import ProjectStatus

if TYPE_CHECKING:
    from app.models.user import User
    from app.models.script import Script
    from app.models.cast import Cast
    from app.models.asset import Asset
    from app.models.youtube_metadata import YouTubeMetadata


class ProjectBase(SQLModel):
    """Shared project properties."""
    title: str = Field(max_length=255, nullable=False)
    status: ProjectStatus = Field(
        default=ProjectStatus.DRAFT,
        sa_column=Column(
            SAEnum(ProjectStatus, name="project_status", create_type=False, values_callable=lambda x: [e.value for e in x]),
            nullable=False
        )
    )
    youtube_video_id: Optional[str] = Field(default=None, max_length=50)
    youtube_url: Optional[str] = Field(default=None, max_length=500)
    error_message: Optional[str] = Field(default=None)


class Project(ProjectBase, BaseUUIDModel, table=True):
    """
    Project database model.
    
    Table: projects
    
    Represents a video generation project with its current status
    and all related data (script, cast, assets).
    """
    __tablename__ = "projects"

    # Foreign key to user
    user_id: UUID = Field(foreign_key="users.id", nullable=False, index=True)

    # Timestamps
    updated_at: datetime = Field(
        default_factory=utc_now,
        nullable=False,
        sa_column_kwargs={"onupdate": utc_now}
    )

    # Relationships
    user: Optional["User"] = Relationship(back_populates="projects")
    scripts: List["Script"] = Relationship(back_populates="project")
    casts: List["Cast"] = Relationship(back_populates="project")
    assets: List["Asset"] = Relationship(back_populates="project")
    youtube_metadata: Optional["YouTubeMetadata"] = Relationship(
        back_populates="project",
        sa_relationship_kwargs={"uselist": False} # One-to-one
    )


class ProjectCreate(SQLModel):
    """Schema for creating a new project."""
    title: str = Field(max_length=255)
    script_prompt: str = Field(max_length=5000)
    auto_upload: bool = False


class ProjectRead(ProjectBase):
    """Schema for reading project data."""
    id: UUID
    user_id: UUID
    created_at: datetime
    updated_at: datetime


class ProjectReadWithRelations(ProjectRead):
    """Schema for reading project with all related data."""
    scripts: List["ScriptRead"] = []
    casts: List["CastRead"] = []
    assets: List["AssetRead"] = []
    youtube_metadata: Optional["YouTubeMetadataRead"] = None


# Forward reference for type hints
from app.models.script import ScriptRead
from app.models.cast import CastRead
from app.models.asset import AssetRead
from app.models.youtube_metadata import YouTubeMetadataRead

ProjectReadWithRelations.model_rebuild()