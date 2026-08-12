from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth import create_access_token, verify_password
from app.database import get_db
from app.models import Staff
from app.schemas import LoginRequest, LoginResponse

router = APIRouter(tags=["auth"])


@router.post("/login", response_model=LoginResponse)
async def login(payload: LoginRequest, db: AsyncSession = Depends(get_db)):
    # Case-insensitive match: "Nandom", "nandom", "NANDOM" all find the same
    # account, matching how usernames read on a login screen.
    result = await db.execute(select(Staff).where(func.lower(Staff.username) == payload.username.lower()))
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