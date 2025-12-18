"""
Asset model - tracks generated audio and video files.
"""
from datetime import datetime
from typing import TYPE_CHECKING, Optional
from uuid import UUID

from sqlmodel import Field, Relationship, SQLModel, Column
from sqlalchemy import Enum as SAEnum

from app.models.base import BaseUUIDModel
from app.models.enums import AssetType

if TYPE_CHECKING:
    from app.models.project import Project


class AssetBase(SQLModel):
    """Shared asset properties."""
    asset_type: AssetType = Field(
        sa_column=Column(
            SAEnum(AssetType, name="asset_type", create_type=False, values_callable=lambda x: [e.value for e in x]),
            nullable=False
        )
    )
    file_path: str = Field(max_length=500, nullable=False)
    character_name: Optional[str] = Field(default=None, max_length=255)
    file_size_bytes: Optional[int] = Field(default=None, ge=0)


class Asset(AssetBase, BaseUUIDModel, table=True):
    """
    Asset database model.
    
    Table: assets
    
    Tracks all generated files (audio clips, final video).
    File paths are relative to the static/ directory.
    """
    __tablename__ = "assets"

    # Foreign key to project
    project_id: UUID = Field(foreign_key="projects.id", nullable=False, index=True)

    # Relationships
    project: Optional["Project"] = Relationship(back_populates="assets")

    @property
    def url(self) -> str:
        """Get the URL for serving this asset."""
        return f"/static/{self.file_path}"


class AssetCreate(SQLModel):
    """Schema for creating a new asset."""
    project_id: UUID
    asset_type: AssetType
    file_path: str
    character_name: Optional[str] = None
    file_size_bytes: Optional[str] = None


class AssetRead(AssetBase):
    """Schema for reading asset data."""
    id: UUID
    project_id: UUID
    created_at: datetime

    @property
    def url(self) -> str:
        """Get the URL for serving this asset."""
        return f"/static/{self.file_path}"