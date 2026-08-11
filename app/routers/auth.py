from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth import create_access_token, verify_password
from app.database import get_db
from app.models import Staff
from app.schemas import LoginRequest, LoginResponse

router = APIRouter(tags=["auth"])


@router.post("/login", response_model=LoginResponse)
async def login(payload: LoginRequest, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Staff).where(Staff.username == payload.username))
    staff = result.scalar_one_or_none()

    if staff is None or not verify_password(payload.password, staff.password_hash):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Incorrect username or password")

    token = create_access_token(staff.id, staff.username)
    return LoginResponse(
        access_token=token,
        staff_id=staff.id,
        username=staff.username,
        full_name=staff.full_name,
    )
