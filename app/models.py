from datetime import datetime, date

from sqlalchemy import (
    String,
    Integer,
    Boolean,
    Numeric,
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


class Registrant(Base):
    __tablename__ = "registrants"

    # tag_id IS the primary key: Postgres assigns it via an atomic SERIAL
    # sequence, so two staff registering at the exact same instant can never
    # get the same number, and a failed insert never "burns" a number since
    # nothing was committed.
    tag_id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)

    name: Mapped[str] = mapped_column(String(150), nullable=False)
    reg_class: Mapped[str] = mapped_column(String(30), nullable=False)  # baby | alpha | youth | speakers_ministers

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
    attendance_records: Mapped[list["Attendance"]] = relationship(
        back_populates="registrant", order_by="Attendance.day"
    )


class Attendance(Base):
    __tablename__ = "attendance"
    __table_args__ = (
        # Marking the same registrant present twice on the same day is a
        # no-op, not a duplicate row - enforced at the DB level so it's safe
        # even if two staff tap "mark present" on the same person at once.
        UniqueConstraint("registrant_id", "day", name="uq_attendance_registrant_day"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    registrant_id: Mapped[int] = mapped_column(ForeignKey("registrants.tag_id", ondelete="CASCADE"), nullable=False)
    day: Mapped[int] = mapped_column(Integer, nullable=False)  # 1-4

    marked_by_id: Mapped[int | None] = mapped_column(ForeignKey("staff.id"), nullable=True)
    marked_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    registrant: Mapped["Registrant"] = relationship(back_populates="attendance_records")
    marked_by: Mapped["Staff"] = relationship()
