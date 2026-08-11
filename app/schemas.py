from datetime import datetime
from enum import Enum

from pydantic import BaseModel, ConfigDict


class RegClass(str, Enum):
    baby = "baby"
    alpha = "alpha"
    youth = "youth"
    speakers_ministers = "speakers_ministers"


# ---------- Auth ----------

class LoginRequest(BaseModel):
    username: str
    password: str


class LoginResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    staff_id: int
    username: str
    full_name: str | None = None


# ---------- Registrants ----------

class RegistrantCreate(BaseModel):
    name: str
    reg_class: RegClass
    phone: str | None = None
    parent_phone: str | None = None
    emergency_contact: str | None = None
    address: str | None = None
    age: int | None = None
    camp_paid: bool = False
    camp_amount: float | None = None
    conference_paid: bool = False
    conference_amount: float | None = None
    # Which event day "today" is, so the auto-check-in on registration
    # lands on the right day (1-4). Defaults to 1 if not provided.
    today_day: int = 1


class RegistrationConfirmation(BaseModel):
    """What the desk staff sees right after a successful registration."""
    tag_id: int
    name: str
    reg_class: RegClass
    camp_paid: bool
    camp_amount: float | None
    conference_paid: bool
    conference_amount: float | None
    registered_at: datetime

    model_config = ConfigDict(from_attributes=True)


class AttendanceRecord(BaseModel):
    day: int
    marked_at: datetime
    marked_by: str | None = None

    model_config = ConfigDict(from_attributes=True)


class RegistrantSummary(BaseModel):
    """Row shape for search/lookup results."""
    tag_id: int
    name: str
    reg_class: RegClass
    phone: str | None
    camp_paid: bool
    conference_paid: bool

    model_config = ConfigDict(from_attributes=True)


class RegistrantDetail(BaseModel):
    """Full record shown on the registrant detail page."""
    tag_id: int
    name: str
    reg_class: RegClass
    phone: str | None
    parent_phone: str | None
    emergency_contact: str | None
    address: str | None
    age: int | None
    camp_paid: bool
    camp_amount: float | None
    conference_paid: bool
    conference_amount: float | None
    registered_by: str | None = None
    registered_at: datetime
    attendance: list[AttendanceRecord] = []

    model_config = ConfigDict(from_attributes=True)


# ---------- Attendance ----------

class MarkAttendanceRequest(BaseModel):
    tag_id: int
    day: int
