from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, or_, update
from sqlalchemy.orm import selectinload

from app.database import get_db
from app.models import User, Project, ProjectMember, Task
from app.schemas import (
    ProjectCreate,
    ProjectUpdate,
    ProjectResponse,
    ProjectListResponse,
    AddMemberRequest,
    ProjectMemberResponse,
)
from app.auth import get_current_user

router = APIRouter(prefix="/api/projects", tags=["projects"])


async def get_project_with_access(
    project_id: int, db: AsyncSession, user: User, owner_only: bool = False
) -> Project:
    """Get project and verify user access"""
    result = await db.execute(
        select(Project)
        .options(
            selectinload(Project.owner),
            selectinload(Project.members).selectinload(ProjectMember.user),
        )
        .where(Project.id == project_id)
    )
    project = result.scalar_one_or_none()

    if not project:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Project not found"
        )

    if owner_only:
        if project.owner_id != user.id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Only owner can perform this action",
            )
    else:
        # Check if user is owner or member
        is_member = any(m.user_id == user.id for m in project.members)
        if project.owner_id != user.id and not is_member:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN, detail="Access denied"
            )

    return project


@router.post("/", response_model=ProjectResponse, status_code=status.HTTP_201_CREATED)
async def create_project(
    project_data: ProjectCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    project = Project(
        name=project_data.name,
        description=project_data.description,
        owner_id=current_user.id,
    )
    db.add(project)
    await db.commit()

    # Reload with relationships
    result = await db.execute(
        select(Project)
        .options(
            selectinload(Project.owner),
            selectinload(Project.members).selectinload(ProjectMember.user),
        )
        .where(Project.id == project.id)
    )
    return result.scalar_one()


@router.get("/", response_model=list[ProjectListResponse])
async def get_projects(
    db: AsyncSession = Depends(get_db), current_user: User = Depends(get_current_user)
):
    """Get all projects where user is owner or member"""
    result = await db.execute(
        select(Project)
        .options(selectinload(Project.owner), selectinload(Project.members))
        .where(
            or_(
                Project.owner_id == current_user.id,
                Project.members.any(ProjectMember.user_id == current_user.id),
            )
        )
        .order_by(Project.updated_at.desc())
    )
    return result.scalars().all()


@router.get("/{project_id}", response_model=ProjectResponse)
async def get_project(
    project_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return await get_project_with_access(project_id, db, current_user)


@router.put("/{project_id}", response_model=ProjectResponse)
async def update_project(
    project_id: int,
    project_data: ProjectUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    project = await get_project_with_access(
        project_id, db, current_user, owner_only=True
    )

    if project_data.name is not None:
        project.name = project_data.name
    if project_data.description is not None:
        project.description = project_data.description

    await db.commit()
    await db.refresh(project)
    return project


@router.delete("/{project_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_project(
    project_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    project = await get_project_with_access(
        project_id, db, current_user, owner_only=True
    )
    await db.delete(project)
    await db.commit()


# Member management
@router.post(
    "/{project_id}/members",
    response_model=ProjectMemberResponse,
    status_code=status.HTTP_201_CREATED,
)
async def add_member(
    project_id: int,
    member_data: AddMemberRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    project = await get_project_with_access(
        project_id, db, current_user, owner_only=True
    )

    # Check if user exists
    result = await db.execute(select(User).where(User.id == member_data.user_id))
    user = result.scalar_one_or_none()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="User not found"
        )

    # Check if user is already a member
    if any(m.user_id == member_data.user_id for m in project.members):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="User is already a member"
        )

    # Check if user is the owner
    if project.owner_id == member_data.user_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Owner cannot be added as member",
        )

    member = ProjectMember(project_id=project_id, user_id=member_data.user_id)
    db.add(member)
    await db.commit()

    result = await db.execute(
        select(ProjectMember)
        .options(selectinload(ProjectMember.user))
        .where(ProjectMember.id == member.id)
    )
    return result.scalar_one()


@router.delete(
    "/{project_id}/members/{user_id}", status_code=status.HTTP_204_NO_CONTENT
)
async def remove_member(
    project_id: int,
    user_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    project = await get_project_with_access(
        project_id, db, current_user, owner_only=True
    )

    result = await db.execute(
        select(ProjectMember).where(
            ProjectMember.project_id == project_id, ProjectMember.user_id == user_id
        )
    )
    member = result.scalar_one_or_none()

    if not member:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Member not found"
        )

    # Unassign all tasks assigned to this user in this project
    await db.execute(
        update(Task)
        .where(Task.project_id == project_id, Task.assignee_id == user_id)
        .values(assignee_id=None)
    )

    await db.delete(member)
    await db.commit()


@router.get("/{project_id}/members", response_model=list[ProjectMemberResponse])
async def get_members(
    project_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    project = await get_project_with_access(project_id, db, current_user)
    return project.members
