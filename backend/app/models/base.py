"""
Base model configuration for all SQLModel classes.
Provides common fields and utilities.
"""
from datetime import  datetime, timezone
from typing import Optional
from uuid import UUID, uuid4
from sqlmodel import Field, SQLModel


def utc_now() -> datetime:
    """Get current UTC timestamp (naive, for TIMESTAMP WITHOUT TIME ZONE)."""
    return datetime.utcnow()


class BaseUUIDModel(SQLModel):
    """
    Base model with UUID primary key and timestamps.
    
    All database models should inherit from this.
    """
    id: UUID = Field(
        default_factory=uuid4,
        primary_key=True,
        index=True,
        nullable=False
    )
    created_at: datetime = Field(
        default_factory=utc_now,
        nullable=False
    )