"""Project CRUD operations."""
from typing import List, Optional, Tuple
from uuid import UUID

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models import Project, Script, Cast, Asset, YouTubeMetadata, ProjectStatus


class ProjectCRUD:
    """CRUD operations for projects."""

    async def create(
        self,
        session: AsyncSession,
        user_id: UUID,
        title: str,
    ) -> Project:
        """Create a new project."""
        project = Project(
            user_id=user_id,
            title=title,
            status=ProjectStatus.DRAFT
        )
        session.add(project)
        await session.commit()
        await session.refresh(project)
        return project

    async def get_by_id(
        self,
        session: AsyncSession,
        project_id: UUID,
        user_id: Optional[UUID]=None
    ) -> Optional[Project]:
        """Get project by ID with optional user filter."""
        stmt = select(Project).where(Project.id == project_id)
        if user_id:
            stmt = stmt.where(Project.user_id == user_id)
        result = await session.execute(stmt)
        return result.scalar_one_or_none()

    async def get_with_relations(
        self,
        session: AsyncSession,
        project_id: UUID,
        user_id: Optional[UUID]=None
    ) -> Optional[Project]:
        """Get project with all related data."""
        stmt = (
            select(Project)
            .options(
                selectinload(Project.scripts),
                selectinload(Project.casts),
                selectinload(Project.assets),
                selectinload(Project.youtube_metadata),
            )
            .where(Project.id == project_id)
        )
        if user_id:
            stmt = stmt.where(Project.user_id == user_id)
        result = await session.execute(stmt)
        return result.scalar_one_or_none()
        
    async def list_by_user(
        self,
        session: AsyncSession,
        user_id: UUID,
        page: int=1,
        page_size: int=20
    ) -> Tuple[List[Project], int]:
        """List projects for a user with pagination."""
        # Count total
        count_stmt = select(func.count(Project.id)).where(
            Project.user_id == user_id
        )
        total_result = await session.execute(count_stmt)
        total = total_result.scalar() or 0

        # Get items
        offset = (page - 1) * page_size
        stmt = (
            select(Project)
            .where(Project.user_id == user_id)
            .order_by(Project.created_at.desc())
            .offset(offset)
            .limit(page_size)
        )
        result = await session.execute(stmt)
        items = list(result.scalars().all())

        return items, total

    async def update_status(
        self,
        session: AsyncSession,
        project_id: UUID,
        status: ProjectStatus,
        error_message: Optional[str]=None
    ) -> Optional[Project]:
        """Update project status."""
        project = await session.get(Project, project_id)
        if project:
            project.status = status
            if error_message:
                project.error_message = error_message
            await session.commit()
            await session.refresh(project)
        return project

    async def get_latest_script(
        self,
        session: AsyncSession,
        project_id: UUID
    ) -> Optional[Script]:
        """Get the latest script version for a project."""
        stmt = (
            select(Script)
            .where(Script.project_id == project_id)
            .order_by(Script.version.desc())
            .limit(1)
        )
        result = await session.execute(stmt)
        return result.scalar_one_or_none()

    async def get_latest_cast(
        self,
        session: AsyncSession,
        project_id: UUID
    ) -> Optional[Cast]:
        """Get the latest cast for a project."""
        stmt = (
            select(Cast)
            .where(Cast.project_id == project_id)
            .order_by(Cast.created_at.desc())
            .limit(1)
        )
        result = await session.execute(stmt)
        return result.scalar_one_or_none()


project_crud = ProjectCRUD()