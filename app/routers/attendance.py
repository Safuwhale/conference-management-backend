from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.dialects.postgresql import insert as pg_insert
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.deps import get_current_staff
from app.models import Attendance, Registrant, Staff
from app.schemas import MarkAttendanceRequest, AttendanceRecord

router = APIRouter(prefix="/attendance", tags=["attendance"])


@router.post("/mark", response_model=AttendanceRecord)
async def mark_attendance(
    payload: MarkAttendanceRequest,
    db: AsyncSession = Depends(get_db),
    staff: Staff = Depends(get_current_staff),
):
    if payload.day not in (1, 2, 3, 4):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="day must be 1-4")

    exists = await db.execute(select(Registrant.tag_id).where(Registrant.tag_id == payload.tag_id))
    if exists.scalar_one_or_none() is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Registrant not found")

    # ON CONFLICT DO NOTHING makes double-marking (e.g. two staff tapping
    # "present" on the same person at once) a safe no-op at the DB level,
    # rather than a race between a SELECT check and an INSERT.
    stmt = (
        pg_insert(Attendance)
        .values(registrant_id=payload.tag_id, day=payload.day, marked_by_id=staff.id)
        .on_conflict_do_nothing(constraint="uq_attendance_registrant_day")
        .returning(Attendance)
    )
    result = await db.execute(stmt)
    await db.commit()

    row = result.scalar_one_or_none()
    if row is None:
        # Already marked earlier - fetch the existing record so the staffer
        # sees who marked it and when, instead of a confusing error.
        existing = await db.execute(
            select(Attendance).where(Attendance.registrant_id == payload.tag_id, Attendance.day == payload.day)
        )
        row = existing.scalar_one()

    await db.refresh(row, attribute_names=["marked_by"])
    return AttendanceRecord(day=row.day, marked_at=row.marked_at, marked_by=row.marked_by.username if row.marked_by else None)
