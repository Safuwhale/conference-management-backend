from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.database import get_db
from app.deps import get_current_staff
from app.models import Event, Attendance, Registrant, Staff
from app.schemas import EventCreate, EventOut, RosterEntry

router = APIRouter(prefix="/events", tags=["events"])


@router.post("", response_model=EventOut, status_code=201)
async def create_event(
    payload: EventCreate,
    db: AsyncSession = Depends(get_db),
    staff: Staff = Depends(get_current_staff),
):
    event = Event(
        name=payload.name,
        location=payload.location,
        event_date=payload.event_date,
        start_time=payload.start_time,
    )
    db.add(event)
    await db.commit()
    await db.refresh(event)
    return event


@router.get("", response_model=list[EventOut])
async def list_events(db: AsyncSession = Depends(get_db), staff: Staff = Depends(get_current_staff)):
    # Ordered by date then time, so two events on the same day sort by
    # start time, and creation order never matters.
    result = await db.execute(select(Event).order_by(Event.event_date, Event.start_time))
    return result.scalars().all()


@router.get("/{event_id}/attendees", response_model=list[RosterEntry])
async def list_event_attendees(
    event_id: int,
    db: AsyncSession = Depends(get_db),
    staff: Staff = Depends(get_current_staff),
):
    event_exists = await db.execute(select(Event.id).where(Event.id == event_id))
    if event_exists.scalar_one_or_none() is None:
        raise HTTPException(status_code=404, detail="Event not found")

    # One JOIN query, not N+1: pulls every attendance row for this event
    # plus its registrant and marked_by staff member in a single round trip.
    # Backed by the index on attendance.event_id, so this stays an index
    # scan rather than a full table scan even as attendance grows.
    stmt = (
        select(Attendance)
        .join(Registrant, Attendance.registrant_id == Registrant.tag_id)
        .where(Attendance.event_id == event_id)
        .options(selectinload(Attendance.registrant), selectinload(Attendance.marked_by))
        .order_by(Registrant.first_name, Registrant.last_name)
    )
    result = await db.execute(stmt)
    rows = result.scalars().all()

    return [
        RosterEntry(
            tag_id=a.registrant.tag_id,
            first_name=a.registrant.first_name,
            middle_name=a.registrant.middle_name,
            last_name=a.registrant.last_name,
            reg_class=a.registrant.reg_class,
            phone=a.registrant.phone,
            parent_phone=a.registrant.parent_phone,
            emergency_contact=a.registrant.emergency_contact,
            age=a.registrant.age,
            camp_paid=a.registrant.camp_paid,
            camp_amount=a.registrant.camp_amount,
            conference_paid=a.registrant.conference_paid,
            conference_amount=a.registrant.conference_amount,
            checked_in_at=a.marked_at,
            checked_in_by=a.marked_by.username if a.marked_by else None,
        )
        for a in rows
    ]