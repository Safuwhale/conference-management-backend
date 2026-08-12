from datetime import datetime, date, time

from sqlalchemy import (
    String,
    Integer,
    Boolean,
    Numeric,
    Date,
    Time,
    ForeignKey,
    DateTime,
    UniqueConstraint,
    func,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


class Staff(Base):
    __tablename__ = "staff"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    username: Mapped[str] = mapped_column(String(50), unique=True, index=True, nullable=False)
    password_hash: Mapped[str] = mapped_column(String(255), nullable=False)
    full_name: Mapped[str | None] = mapped_column(String(100), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())


class Event(Base):
    """
    A single check-in-able session (e.g. two tracks running the same
    afternoon are two separate Event rows). Ordered by (event_date,
    start_time) wherever listed, so creation order doesn't matter.
    """
    __tablename__ = "events"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    name: Mapped[str] = mapped_column(String(150), nullable=False)
    location: Mapped[str | None] = mapped_column(String(150), nullable=True)
    event_date: Mapped[date] = mapped_column(Date, nullable=False)
    start_time: Mapped[time] = mapped_column(Time, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())


class Registrant(Base):
    __tablename__ = "registrants"

    # tag_id IS the primary key: Postgres assigns it via an atomic SERIAL
    # sequence, so two staff registering at the exact same instant can never
    # get the same number, and a failed insert never "burns" a number since
    # nothing was committed. Displayed zero-padded (001, 002...) in the UI -
    # stored as a plain int so search/sort stay simple.
    tag_id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)

    first_name: Mapped[str] = mapped_column(String(75), nullable=False)
    middle_name: Mapped[str | None] = mapped_column(String(75), nullable=True)
    last_name: Mapped[str] = mapped_column(String(75), nullable=False)

    reg_class: Mapped[str] = mapped_column(String(30), nullable=False)  # toddlers | pre_teen | teen_young_adults | guest_ministers

    phone: Mapped[str | None] = mapped_column(String(30), nullable=True, index=True)
    parent_phone: Mapped[str | None] = mapped_column(String(30), nullable=True)
    emergency_contact: Mapped[str | None] = mapped_column(String(30), nullable=True)
    address: Mapped[str | None] = mapped_column(String(255), nullable=True)
    age: Mapped[int | None] = mapped_column(Integer, nullable=True)

    camp_paid: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    camp_amount: Mapped[float | None] = mapped_column(Numeric(10, 2), nullable=True)
    conference_paid: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    conference_amount: Mapped[float | None] = mapped_column(Numeric(10, 2), nullable=True)

    registered_by_id: Mapped[int | None] = mapped_column(ForeignKey("staff.id"), nullable=True)
    registered_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    registered_by: Mapped["Staff"] = relationship()
    attendance_records: Mapped[list["Attendance"]] = relationship(back_populates="registrant")


class Attendance(Base):
    __tablename__ = "attendance"
    __table_args__ = (
        # Marking the same registrant present twice for the same event is a
        # no-op, not a duplicate row - enforced at the DB level so it's safe
        # even if two staff tap "check in" on the same person at once.
        UniqueConstraint("registrant_id", "event_id", name="uq_attendance_registrant_event"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    registrant_id: Mapped[int] = mapped_column(ForeignKey("registrants.tag_id", ondelete="CASCADE"), nullable=False)
    event_id: Mapped[int] = mapped_column(ForeignKey("events.id", ondelete="CASCADE"), nullable=False)

    marked_by_id: Mapped[int | None] = mapped_column(ForeignKey("staff.id"), nullable=True)
    marked_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    registrant: Mapped["Registrant"] = relationship(back_populates="attendance_records")
    event: Mapped["Event"] = relationship()
    marked_by: Mapped["Staff"] = relationship()
