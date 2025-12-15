"""
YouTubeConnection model - stores OAuth tokens for YouTube API access.
"""
from datetime import datetime, timezone
from typing import TYPE_CHECKING, Optional
from uuid import UUID

from sqlmodel import Field, Relationship, SQLModel
from app.models.base import BaseUUIDModel, utc_now

if TYPE_CHECKING:
    from app.models.user import User


class YouTubeConnectionBase(SQLModel):
    """Shared YouTube connection properties."""
    channel_id: str = Field(max_length=100, nullable=False)
    channel_title: Optional[str] = Field(default=None, max_length=255)
    is_active: bool = Field(default=True)


class YouTubeConnection(YouTubeConnectionBase, BaseUUIDModel, table=True):
    """
    YouTubeConnection database model.
    
    Table: youtube_connections
    
    Stores encrypted OAuth tokens for YouTube upload access.
    Tokens should be encrypted at the application level before storage.
    """
    __tablename__ = "youtube_connections"

    # Foreign key to user
    user_id: UUID = Field(foreign_key="users.id", nullable=False, index=True)

    # Encrypted tokens (encrypt before storing!)
    refresh_token: str = Field(nullable=False)
    access_token: str = Field(nullable=False)
    token_expires_at: datetime = Field(nullable=False)

    # Timestamps
    updated_at: datetime = Field(
        default_factory=utc_now,
        nullable=False,
    )

    # Relationships
    user: Optional["User"] = Relationship(back_populates="youtube_connections")

    def is_token_expired(self) -> bool:
        """Check if the access token has expired."""
        return datetime.now(timezone.utc) >= self.token_expires_at

    def needs_refresh(self, buffer_minutes: int=5) -> bool:
        """
        Check if token should be refreshed.
        
        Args:
            buffer_minutes: Refresh this many minutes before expiry.
        """
        from datetime import timedelta
        buffer = timedelta(minutes=buffer_minutes)
        return datetime.now(timezone.utc) >= (self.token_expires_at - buffer)


class YouTubeConnectionCreate(SQLModel):
    """Schema for creating a new YouTube connection."""
    user_id: UUID
    channel_id: str
    channel_title: Optional[str] = None
    refresh_token: str  # Should be encrypted
    access_token: str   # Should be encrypted
    token_expires_at: datetime


class YouTubeConnectionRead(YouTubeConnectionBase):
    """
    Schema for reading YouTube connection data.
    
    Note: Tokens are intentionally excluded for security.
    """
    id: UUID
    user_id: UUID
    created_at: datetime
    updated_at: datetime