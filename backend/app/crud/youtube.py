"""YouTube-related CRUD operations."""
from datetime import datetime, timezone
from typing import Optional
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import YouTubeConnection, YouTubeMetadata
from app.services.encryption_service import encryption_service


class YouTubeCRUD:
    """CRUD operations for YouTube data."""

    async def get_connection(
        self,
        session: AsyncSession,
        user_id: UUID
    ) -> Optional[YouTubeConnection]:
        """Get active YouTube connection for user."""
        stmt = select(YouTubeConnection).where(
            YouTubeConnection.user_id == user_id,
            YouTubeConnection.is_active == True
        )
        result = await session.execute(stmt)
        return result.scalar_one_or_none()

    async def create_connection(
        self,
        session: AsyncSession,
        user_id: UUID,
        channel_id: str,
        channel_title: str,
        access_token: str,
        refresh_token: str,
        expires_at: datetime
    ) -> YouTubeConnection:
        """Create a new YouTube connection with encrypted tokens."""
        # Deactivate any existing connections
        stmt = select(YouTubeConnection).where(
            YouTubeConnection.user_id == user_id
        )
        result = await session.execute(stmt)
        existing = result.scalars().all()
        for conn in existing:
            conn.is_active = False
            session.add(conn)

        # Create new connection with encrypted tokens
        connection = YouTubeConnection(
            user_id=user_id,
            channel_id=channel_id,
            channel_title=channel_title,
            access_token=encryption_service.encrypt(access_token),
            refresh_token=encryption_service.encrypt(refresh_token),
            token_expires_at=expires_at,
            is_active=True
        )
        session.add(connection)
        await session.commit()
        await session.refresh(connection)
        return connection

    async def update_tokens(
        self,
        session: AsyncSession,
        connection_id: UUID,
        access_token: str,
        expires_at: datetime
    ) -> YouTubeConnection:
        """Update connection with refreshed tokens."""
        connection = await session.get(YouTubeConnection, connection_id)
        if connection:
            connection.access_token = encryption_service.encrypt(access_token)
            connection.token_expires_at = expires_at
            session.add(connection)
            await session.commit()
            await session.refresh(connection)
        return connection

    async def deactivate_connection(
        self,
        session: AsyncSession,
        user_id: UUID
    ) -> bool:
        """Deactivate user's YouTube connection."""
        stmt = select(YouTubeConnection).where(
            YouTubeConnection.user_id == user_id,
            YouTubeConnection.is_active == True
        )
        result = await session.execute(stmt)
        connection = result.scalar_one_or_none()
        if connection:
            connection.is_active = False
            session.add(connection)
            await session.commit()
            return True
        return False

    async def get_metadata(
        self,
        session: AsyncSession,
        project_id: UUID
    ) -> Optional[YouTubeMetadata]:
        """Get YouTube metadata for a project."""
        stmt = select(YouTubeMetadata).where(
            YouTubeMetadata.project_id == project_id
        )
        result = await session.execute(stmt)
        return result.scalar_one_or_none()

    async def save_metadata(
        self,
        session: AsyncSession,
        project_id: UUID,
        title: str,
        description: str,
        tags: list,
        category_id: str,
        privacy_status: str
    ) -> YouTubeMetadata:
        """Create or update YouTube metadata for a project."""
        # Check for existing
        existing = await self.get_metadata(session, project_id)

        if existing:
            existing.title = title
            existing.description = description
            existing.tags = tags
            existing.category_id = category_id
            existing.privacy_status = privacy_status
            session.add(existing)
            await session.commit()
            await session.refresh(existing)
            return existing

        # Create new
        metadata = YouTubeMetadata(
            project_id=project_id,
            title=title,
            description=description,
            tags=tags,
            category_id=category_id,
            privacy_status=privacy_status
        )
        session.add(metadata)
        await session.commit()
        await session.refresh(metadata)
        return metadata


youtube_crud = YouTubeCRUD()