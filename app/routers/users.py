from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.database import get_db
from app.models import User
from app.schemas import UserBrief
from app.auth import get_current_user

router = APIRouter(prefix="/api/users", tags=["users"])


@router.get("/search", response_model=list[UserBrief])
async def search_users(
    q: str = Query(..., min_length=1, description="Search query for username"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Search users by username (for adding members to projects)"""
    search_pattern = f"%{q}%"
    result = await db.execute(
        select(User)
        .where(User.username.ilike(search_pattern))
        .limit(10)
    )
    return result.scalars().all()

