from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select, or_
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.database import get_db
from app.deps import get_current_staff
from app.models import Registrant, Attendance, Event, Staff
from app.schemas import (
    RegistrantCreate,
    RegistrationConfirmation,
    RegistrantSummary,
    RegistrantDetail,
    AttendanceRecord,
    PaymentUpdate,
    RegistrantListEntry,
)

router = APIRouter(prefix="/registrants", tags=["registrants"])


@router.post("", response_model=RegistrationConfirmation, status_code=status.HTTP_201_CREATED)
async def register_attendee(
    payload: RegistrantCreate,
    db: AsyncSession = Depends(get_db),
    staff: Staff = Depends(get_current_staff),
):
    event_exists = await db.execute(select(Event.id).where(Event.id == payload.event_id))
    if event_exists.scalar_one_or_none() is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Selected event not found")

    registrant = Registrant(
        first_name=payload.first_name.strip(),
        middle_name=(payload.middle_name.strip() if payload.middle_name else None),
        last_name=payload.last_name.strip(),
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

        checkin = Attendance(
            registrant_id=registrant.tag_id,
            event_id=payload.event_id,
            marked_by_id=staff.id,
        )
        db.add(checkin)
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


@router.get("", response_model=list[RegistrantListEntry])
async def list_all_registrants(db: AsyncSession = Depends(get_db), staff: Staff = Depends(get_current_staff)):
    # Full roster for the "All Members" export - every registrant,
    # independent of any single event. At this app's scale (up to ~500
    # rows) a single unfiltered select is simplest and fast; no pagination
    # needed for a dataset this size.
    result = await db.execute(select(Registrant).order_by(Registrant.first_name, Registrant.last_name))
    return result.scalars().all()


@router.get("/search", response_model=list[RegistrantSummary])
async def search_registrants(
    q: str,
    event_id: int | None = None,
    db: AsyncSession = Depends(get_db),
    staff: Staff = Depends(get_current_staff),
):
    query = select(Registrant)
    conditions = [
        Registrant.first_name.ilike(f"%{q}%"),
        Registrant.middle_name.ilike(f"%{q}%"),
        Registrant.last_name.ilike(f"%{q}%"),
        Registrant.phone.ilike(f"%{q}%"),
    ]
    if q.isdigit():
        conditions.append(Registrant.tag_id == int(q))
    query = query.where(or_(*conditions)).limit(25)

    result = await db.execute(query)
    registrants = result.scalars().all()

    checked_in_ids = set()
    if event_id is not None and registrants:
        att_result = await db.execute(
            select(Attendance.registrant_id).where(
                Attendance.event_id == event_id,
                Attendance.registrant_id.in_([r.tag_id for r in registrants]),
            )
        )
        checked_in_ids = {row[0] for row in att_result.all()}

    return [
        RegistrantSummary(
            tag_id=r.tag_id,
            first_name=r.first_name,
            middle_name=r.middle_name,
            last_name=r.last_name,
            reg_class=r.reg_class,
            phone=r.phone,
            camp_paid=r.camp_paid,
            conference_paid=r.conference_paid,
            checked_in=(r.tag_id in checked_in_ids) if event_id is not None else None,
        )
        for r in registrants
    ]


@router.get("/{tag_id}", response_model=RegistrantDetail)
async def get_registrant(tag_id: int, db: AsyncSession = Depends(get_db), staff: Staff = Depends(get_current_staff)):
    query = (
        select(Registrant)
        .where(Registrant.tag_id == tag_id)
        .options(
            selectinload(Registrant.attendance_records).selectinload(Attendance.marked_by),
            selectinload(Registrant.attendance_records).selectinload(Attendance.event),
            selectinload(Registrant.registered_by),
        )
    )
    result = await db.execute(query)
    registrant = result.scalar_one_or_none()
    if registrant is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Registrant not found")

    return RegistrantDetail(
        tag_id=registrant.tag_id,
        first_name=registrant.first_name,
        middle_name=registrant.middle_name,
        last_name=registrant.last_name,
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
                event_id=a.event.id,
                event_name=a.event.name,
                event_date=a.event.event_date,
                event_start_time=a.event.start_time,
                marked_at=a.marked_at,
                marked_by=a.marked_by.username if a.marked_by else None,
            )
            for a in registrant.attendance_records
        ],
    )


@router.patch("/{tag_id}/payment", response_model=RegistrantDetail)
async def update_payment(
    tag_id: int,
    payload: PaymentUpdate,
    db: AsyncSession = Depends(get_db),
    staff: Staff = Depends(get_current_staff),
):
    result = await db.execute(select(Registrant).where(Registrant.tag_id == tag_id))
    registrant = result.scalar_one_or_none()
    if registrant is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Registrant not found")

    updates = payload.model_dump(exclude_unset=True)
    for field, value in updates.items():
        setattr(registrant, field, value)

    await db.commit()
    return await get_registrant(tag_id, db, staff)