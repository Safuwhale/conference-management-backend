from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.dialects.postgresql import insert as pg_insert
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.deps import get_current_staff
from app.models import Attendance, Registrant, Event, Staff
from app.schemas import MarkAttendanceRequest, AttendanceRecord

router = APIRouter(prefix="/attendance", tags=["attendance"])


@router.post("/mark", response_model=AttendanceRecord)
async def mark_attendance(
    payload: MarkAttendanceRequest,
    db: AsyncSession = Depends(get_db),
    staff: Staff = Depends(get_current_staff),
):
    reg_exists = await db.execute(select(Registrant.tag_id).where(Registrant.tag_id == payload.tag_id))
    if reg_exists.scalar_one_or_none() is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Registrant not found")

    event = await db.execute(select(Event).where(Event.id == payload.event_id))
    event = event.scalar_one_or_none()
    if event is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Event not found")

    # ON CONFLICT DO NOTHING makes double check-in (e.g. two staff tapping
    # "check in" on the same person at once) a safe no-op at the DB level,
    # rather than a race between a SELECT check and an INSERT.
    stmt = (
        pg_insert(Attendance)
        .values(registrant_id=payload.tag_id, event_id=payload.event_id, marked_by_id=staff.id)
        .on_conflict_do_nothing(constraint="uq_attendance_registrant_event")
        .returning(Attendance)
    )
    result = await db.execute(stmt)
    await db.commit()

    row = result.scalar_one_or_none()
    if row is None:
        # Already checked in earlier - fetch the existing record so the
        # staffer sees who checked them in and when, instead of a confusing
        # error.
        existing = await db.execute(
            select(Attendance).where(
                Attendance.registrant_id == payload.tag_id, Attendance.event_id == payload.event_id
            )
        )
        row = existing.scalar_one()

    await db.refresh(row, attribute_names=["marked_by"])

    return AttendanceRecord(
        event_id=event.id,
        event_name=event.name,
        event_date=event.event_date,
        event_start_time=event.start_time,
        marked_at=row.marked_at,
        marked_by=row.marked_by.username if row.marked_by else None,
    )
