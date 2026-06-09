from app.schemas.patient import PatientCreate, PatientUpdate, PatientResponse
from app.schemas.appointment import (
    AppointmentCreate,
    AppointmentUpdate,
    AppointmentResponse,
    AvailabilityRequest,
    AvailabilityResponse,
)

__all__ = [
    "PatientCreate",
    "PatientUpdate",
    "PatientResponse",
    "AppointmentCreate",
    "AppointmentUpdate",
    "AppointmentResponse",
    "AvailabilityRequest",
    "AvailabilityResponse",
]
