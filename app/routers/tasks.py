from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from sqlalchemy.orm import selectinload

from app.database import get_db
from app.models import User, Project, ProjectMember, Task
from app.schemas import TaskCreate, TaskUpdate, TaskResponse
from app.auth import get_current_user

router = APIRouter(prefix="/api/projects/{project_id}/tasks", tags=["tasks"])


async def verify_project_access(project_id: int, db: AsyncSession, user: User) -> Project:
    """Verify user has access to project"""
    result = await db.execute(
        select(Project)
        .options(selectinload(Project.members))
        .where(Project.id == project_id)
    )
    project = result.scalar_one_or_none()
    
    if not project:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Project not found")
    
    is_member = any(m.user_id == user.id for m in project.members)
    if project.owner_id != user.id and not is_member:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Access denied")
    
    return project


async def get_task_with_access(
    task_id: int,
    project_id: int,
    db: AsyncSession,
    user: User
) -> Task:
    """Get task and verify access"""
    await verify_project_access(project_id, db, user)
    
    result = await db.execute(
        select(Task)
        .options(selectinload(Task.creator), selectinload(Task.assignee))
        .where(Task.id == task_id, Task.project_id == project_id)
    )
    task = result.scalar_one_or_none()
    
    if not task:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Task not found")
    
    return task


@router.post("/", response_model=TaskResponse, status_code=status.HTTP_201_CREATED)
async def create_task(
    project_id: int,
    task_data: TaskCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    project = await verify_project_access(project_id, db, current_user)
    
    # Validate assignee if provided
    if task_data.assignee_id:
        is_owner = project.owner_id == task_data.assignee_id
        is_member = any(m.user_id == task_data.assignee_id for m in project.members)
        if not is_owner and not is_member:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Assignee must be project owner or member"
            )
    
    task = Task(
        title=task_data.title,
        description=task_data.description,
        status=task_data.status,
        complexity=task_data.complexity,
        project_id=project_id,
        creator_id=current_user.id,
        assignee_id=task_data.assignee_id
    )
    db.add(task)
    await db.commit()
    
    result = await db.execute(
        select(Task)
        .options(selectinload(Task.creator), selectinload(Task.assignee))
        .where(Task.id == task.id)
    )
    return result.scalar_one()


@router.get("/", response_model=list[TaskResponse])
async def get_tasks(
    project_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    await verify_project_access(project_id, db, current_user)
    
    result = await db.execute(
        select(Task)
        .options(selectinload(Task.creator), selectinload(Task.assignee))
        .where(Task.project_id == project_id)
        .order_by(Task.created_at.desc())
    )
    return result.scalars().all()


@router.get("/{task_id}", response_model=TaskResponse)
async def get_task(
    project_id: int,
    task_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    return await get_task_with_access(task_id, project_id, db, current_user)


@router.put("/{task_id}", response_model=TaskResponse)
async def update_task(
    project_id: int,
    task_id: int,
    task_data: TaskUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    task = await get_task_with_access(task_id, project_id, db, current_user)
    project = await verify_project_access(project_id, db, current_user)
    
    if task_data.title is not None:
        task.title = task_data.title
    if task_data.description is not None:
        task.description = task_data.description
    if task_data.status is not None:
        task.status = task_data.status
    if task_data.complexity is not None:
        task.complexity = task_data.complexity
    
    # Check if assignee_id was explicitly provided (even if None)
    if 'assignee_id' in task_data.model_fields_set:
        if task_data.assignee_id is not None:
            # Validate assignee
            is_owner = project.owner_id == task_data.assignee_id
            is_member = any(m.user_id == task_data.assignee_id for m in project.members)
            if not is_owner and not is_member:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Assignee must be project owner or member"
                )
        task.assignee_id = task_data.assignee_id
    
    await db.commit()
    
    result = await db.execute(
        select(Task)
        .options(selectinload(Task.creator), selectinload(Task.assignee))
        .where(Task.id == task.id)
    )
    return result.scalar_one()


@router.delete("/{task_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_task(
    project_id: int,
    task_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    task = await get_task_with_access(task_id, project_id, db, current_user)
    await db.delete(task)
    await db.commit()

