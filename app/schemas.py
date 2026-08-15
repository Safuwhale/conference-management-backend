from datetime import datetime
from enum import Enum

from pydantic import BaseModel, ConfigDict


class RegClass(str, Enum):
    toddlers = "toddlers"
    pre_teen = "pre_teen"
    teen_young_adults = "teen_young_adults"
    guest_ministers = "guest_ministers"


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
from datetime import datetime, date, time
from enum import Enum

from pydantic import BaseModel, ConfigDict


class RegClass(str, Enum):
    toddlers = "toddlers"
    pre_teen = "pre_teen"
    teen_young_adults = "teen_young_adults"
    guest_ministers = "guest_ministers"


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


# ---------- Events ----------

class EventCreate(BaseModel):
    name: str
    location: str | None = None
    event_date: date
    start_time: time


class EventOut(BaseModel):
    id: int
    name: str
    location: str | None
    event_date: date
    start_time: time

    model_config = ConfigDict(from_attributes=True)


# ---------- Registrants ----------

class RegistrantCreate(BaseModel):
    first_name: str
    middle_name: str | None = None
    last_name: str
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
    # Which event to auto-check-in to at the moment of registration.
    event_id: int


class RegistrationConfirmation(BaseModel):
    """What the desk staff sees right after a successful registration."""
    tag_id: int
    first_name: str
    middle_name: str | None
    last_name: str
    reg_class: RegClass
    camp_paid: bool
    camp_amount: float | None
    conference_paid: bool
    conference_amount: float | None
    registered_at: datetime

    model_config = ConfigDict(from_attributes=True)


class AttendanceRecord(BaseModel):
    event_id: int
    event_name: str
    event_date: date
    event_start_time: time
    marked_at: datetime
    marked_by: str | None = None

    model_config = ConfigDict(from_attributes=True)


class RegistrantSummary(BaseModel):
    """Row shape for search/lookup results."""
    tag_id: int
    first_name: str
    middle_name: str | None
    last_name: str
    reg_class: RegClass
    phone: str | None
    camp_paid: bool
    conference_paid: bool
    # Populated only when the search was scoped to a specific event
    # (?event_id=...) - lets the Lookup page show check-in state per card.
    checked_in: bool | None = None

    model_config = ConfigDict(from_attributes=True)


class RegistrantDetail(BaseModel):
    """Full record shown on the registrant detail page."""
    tag_id: int
    first_name: str
    middle_name: str | None
    last_name: str
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


class PaymentUpdate(BaseModel):
    """Partial update - only send the fields you're changing."""
    camp_paid: bool | None = None
    camp_amount: float | None = None
    conference_paid: bool | None = None
    conference_amount: float | None = None


# ---------- Attendance ----------

class MarkAttendanceRequest(BaseModel):
    tag_id: int
    event_id: int
    
class RosterEntry(BaseModel):
    """One row for an event's roster - a registrant plus their check-in
    details for that specific event. Used by the roster page and its
    CSV/PDF export."""
    tag_id: int
    first_name: str
    middle_name: str | None
    last_name: str
    reg_class: RegClass
    phone: str | None
    parent_phone: str | None
    emergency_contact: str | None
    age: int | None
    camp_paid: bool
    camp_amount: float | None
    conference_paid: bool
    conference_amount: float | None
    checked_in_at: datetime
    checked_in_by: str | None = None

    model_config = ConfigDict(from_attributes=True)


class RegistrantListEntry(BaseModel):
    """One row for the all-members list/export - every registrant,
    independent of any single event."""
    tag_id: int
    first_name: str
    middle_name: str | None
    last_name: str
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
    registered_at: datetime

    model_config = ConfigDict(from_attributes=True)
