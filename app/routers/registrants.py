from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select, or_
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.database import get_db
from app.deps import get_current_staff
from app.models import Registrant, Attendance, Staff
from app.schemas import (
    RegistrantCreate,
    RegistrationConfirmation,
    RegistrantSummary,
    RegistrantDetail,
    AttendanceRecord,
)

router = APIRouter(prefix="/registrants", tags=["registrants"])


@router.post("", response_model=RegistrationConfirmation, status_code=status.HTTP_201_CREATED)
async def register_attendee(
    payload: RegistrantCreate,
    db: AsyncSession = Depends(get_db),
    staff: Staff = Depends(get_current_staff),
):
    registrant = Registrant(
        name=payload.name,
        reg_class=payload.reg_class.value,
        phone=payload.phone,
        parent_phone=payload.parent_phone,
        emergency_contact=payload.emergency_contact,
        address=payload.address,
        age=payload.age,
        camp_paid=payload.camp_paid,
        camp_amount=payload.camp_amount,
        conference_paid=payload.conference_paid,
        conference_amount=payload.conference_amount,
        registered_by_id=staff.id,
    )
    db.add(registrant)

    try:
        # Flush (not commit) first so tag_id is assigned by the DB sequence
        # and available for the attendance row, while staying in one
        # transaction: if anything below fails, both roll back together.
        await db.flush()

        today_attendance = Attendance(
            registrant_id=registrant.tag_id,
            day=payload.today_day,
            marked_by_id=staff.id,
        )
        db.add(today_attendance)
        await db.commit()
    except IntegrityError:
        # Nothing was actually persisted - the DB sequence still advanced
        # for next time, so no tag_id is "wasted" or reused. Safe to just
        # ask the frontend to retry the same submission.
        await db.rollback()
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Registration could not be saved, please retry.",
        )

    await db.refresh(registrant)
    return registrant


@router.get("/search", response_model=list[RegistrantSummary])
async def search_registrants(q: str, db: AsyncSession = Depends(get_db), staff: Staff = Depends(get_current_staff)):
    query = select(Registrant)
    conditions = [Registrant.name.ilike(f"%{q}%"), Registrant.phone.ilike(f"%{q}%")]
    if q.isdigit():
        conditions.append(Registrant.tag_id == int(q))
    query = query.where(or_(*conditions)).limit(25)

    result = await db.execute(query)
    return result.scalars().all()


@router.get("/{tag_id}", response_model=RegistrantDetail)
async def get_registrant(tag_id: int, db: AsyncSession = Depends(get_db), staff: Staff = Depends(get_current_staff)):
    query = (
        select(Registrant)
        .where(Registrant.tag_id == tag_id)
        .options(
            selectinload(Registrant.attendance_records).selectinload(Attendance.marked_by),
            selectinload(Registrant.registered_by),
        )
    )
    result = await db.execute(query)
    registrant = result.scalar_one_or_none()
    if registrant is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Registrant not found")

    return RegistrantDetail(
        tag_id=registrant.tag_id,
        name=registrant.name,
        reg_class=registrant.reg_class,
        phone=registrant.phone,
        parent_phone=registrant.parent_phone,
        emergency_contact=registrant.emergency_contact,
        address=registrant.address,
        age=registrant.age,
        camp_paid=registrant.camp_paid,
        camp_amount=registrant.camp_amount,
        conference_paid=registrant.conference_paid,
        conference_amount=registrant.conference_amount,
        registered_by=registrant.registered_by.username if registrant.registered_by else None,
        registered_at=registrant.registered_at,
        attendance=[
            AttendanceRecord(
                day=a.day,
                marked_at=a.marked_at,
                marked_by=a.marked_by.username if a.marked_by else None,
            )
            for a in registrant.attendance_records
        ],
    )
