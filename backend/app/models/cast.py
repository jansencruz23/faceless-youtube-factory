"""
Cast model - stores voice casting assignments as JSONB.
"""
from datetime import datetime
from typing import TYPE_CHECKING, Any, Dict, Optional
from uuid import UUID

from sqlmodel import Field, Relationship, SQLModel, Column
from sqlalchemy import JSON

from app.models.base import BaseUUIDModel

if TYPE_CHECKING:
    from app.models.project import Project


class VoiceSettings(SQLModel):
    """
    Voice settings for a single character.
    
    Structure: {"voice_id": "string", "pitch": "string", "rate": "string"}
    """
    voice_id: str = Field(description="edge-tts voice identifier")
    pitch: str = Field(default="+0Hz", description="Pitch adjustment, e.g., '+5Hz', '-10Hz'")
    rate: str = Field(default="+0%", description="Rate adjustment, e.g., '+10%', '-20%'")


class CastBase(SQLModel):
    """Shared cost properties."""
    pass


class Cast(CastBase, BaseUUIDModel, table=True):
    """
    Cast database model.
    
    Table: casts
    
    Stores character-to-voice mappings for the project.
    The assignments column is JSONB for flexible structure.
    
    Example assignments:
    {
        "Narrator": {"voice_id": "en-US-AriaNeural", "pitch": "+0Hz", "rate": "+0%"},
        "Host": {"voice_id": "en-US-GuyNeural", "pitch": "-5Hz", "rate": "+10%"}
    }
    """
    __tablename__ = "casts"

    # Foreign key to project
    project_id: UUID = Field(foreign_key="projects.id", nullable=False, index=True)

    # JSONB assignments column
    assignments: Dict[str, Any] = Field(
        default_factory=dict,
        sa_column=Column(JSON, nullable=False)
    )

    # Relationships
    project: Optional["Project"] = Relationship(back_populates="casts")

    def get_voice_settings(self, character: str) -> Optional[VoiceSettings]:
        """Get voice settings for a specific character."""
        settings = self.assignments.get(character)
        if settings:
            return VoiceSettings(**settings)
        return None

    def get_all_characters(self) -> List[str]:
        """Get list of all characters in the cast."""
        return list(self.assignments.keys())

    
class CastCreate(SQLModel):
    """Schema for creating a new cast."""
    project_id: UUID
    assignments: Dict[str, Dict[str, str]]


class CastUpdate(SQLModel):
    """Schema for updating cast assignments."""
    assignments: Dict[str, Dict[str, str]]


class CastRead(CastBase):
    """Schema for reading cast data."""
    id: UUID
    project_id: UUID
    assignments: Dict[str, Any]
    created_at: datetime