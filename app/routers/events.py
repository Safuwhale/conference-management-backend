from fastapi import APIRouter, Depends
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.deps import get_current_staff
from app.models import Event, Staff
from app.schemas import EventCreate, EventOut

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
