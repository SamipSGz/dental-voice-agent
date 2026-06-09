from datetime import date
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.database import get_db
from app.schemas.appointment import (
    AppointmentCreate,
    AppointmentResponse,
    AppointmentUpdate,
    AvailabilityResponse,
)
from app.services import appointment_service

router = APIRouter(prefix="/appointments", tags=["appointments"])


@router.get("/availability", response_model=AvailabilityResponse)
def check_availability(
    date: date = Query(..., description="Date to check (YYYY-MM-DD)"),
    duration_minutes: int = Query(30, ge=15, le=120),
    db: Session = Depends(get_db),
):
    return appointment_service.get_available_slots(db, date, duration_minutes)


@router.get("/next-available")
def next_available(
    count: int = Query(3, ge=1, le=10),
    duration_minutes: int = Query(30, ge=15, le=120),
    db: Session = Depends(get_db),
):
    slots = appointment_service.find_next_available_slots(db, count, duration_minutes)
    return {"slots": [{"datetime": s.isoformat(), "display": s.strftime("%A, %B %d at %I:%M %p")} for s in slots]}


@router.post("/", response_model=AppointmentResponse, status_code=201)
def create_appointment(data: AppointmentCreate, db: Session = Depends(get_db)):
    if not appointment_service.is_slot_available(db, data.appointment_datetime, data.duration_minutes):
        raise HTTPException(status_code=409, detail="Time slot is not available")
    return appointment_service.create_appointment(db, data)


@router.get("/{appointment_id}", response_model=AppointmentResponse)
def get_appointment(appointment_id: str, db: Session = Depends(get_db)):
    appointment = appointment_service.get_appointment(db, appointment_id)
    if not appointment:
        raise HTTPException(status_code=404, detail="Appointment not found")
    return appointment


@router.patch("/{appointment_id}", response_model=AppointmentResponse)
def update_appointment(appointment_id: str, data: AppointmentUpdate, db: Session = Depends(get_db)):
    appointment = appointment_service.get_appointment(db, appointment_id)
    if not appointment:
        raise HTTPException(status_code=404, detail="Appointment not found")
    if data.appointment_datetime:
        if not appointment_service.is_slot_available(
            db, data.appointment_datetime, appointment.duration_minutes, exclude_id=appointment_id
        ):
            raise HTTPException(status_code=409, detail="Time slot is not available")
    return appointment_service.update_appointment(db, appointment, data)


@router.delete("/{appointment_id}", response_model=AppointmentResponse)
def cancel_appointment(
    appointment_id: str,
    reason: str | None = Query(None),
    db: Session = Depends(get_db),
):
    appointment = appointment_service.get_appointment(db, appointment_id)
    if not appointment:
        raise HTTPException(status_code=404, detail="Appointment not found")
    return appointment_service.cancel_appointment(db, appointment, reason)
