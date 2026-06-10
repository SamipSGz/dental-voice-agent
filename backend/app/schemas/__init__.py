from app.schemas.appointment import (
    AppointmentCreate,
    AppointmentResponse,
    AppointmentUpdate,
    AvailabilityRequest,
    AvailabilityResponse,
)
from app.schemas.patient import PatientCreate, PatientResponse, PatientUpdate

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
