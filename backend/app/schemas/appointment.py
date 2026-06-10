from datetime import date, datetime

from pydantic import BaseModel

from app.models.appointment import AppointmentStatus, AppointmentType


class AppointmentBase(BaseModel):
    appointment_datetime: datetime
    duration_minutes: int = 30
    appointment_type: AppointmentType = AppointmentType.CHECKUP
    dentist_name: str | None = None
    notes: str | None = None


class AppointmentCreate(AppointmentBase):
    patient_id: str
    vapi_call_id: str | None = None


class AppointmentUpdate(BaseModel):
    appointment_datetime: datetime | None = None
    duration_minutes: int | None = None
    appointment_type: AppointmentType | None = None
    status: AppointmentStatus | None = None
    dentist_name: str | None = None
    notes: str | None = None
    cancellation_reason: str | None = None


class AppointmentResponse(AppointmentBase):
    id: str
    patient_id: str
    status: AppointmentStatus
    cancellation_reason: str | None = None
    vapi_call_id: str | None = None
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class AvailabilityRequest(BaseModel):
    date: date
    duration_minutes: int = 30


class TimeSlot(BaseModel):
    start_time: datetime
    end_time: datetime
    available: bool


class AvailabilityResponse(BaseModel):
    date: date
    available_slots: list[TimeSlot]
