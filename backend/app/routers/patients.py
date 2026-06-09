from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.database import get_db
from app.schemas.appointment import AppointmentResponse
from app.schemas.patient import PatientCreate, PatientResponse, PatientUpdate
from app.services import appointment_service, patient_service

router = APIRouter(prefix="/patients", tags=["patients"])


@router.post("/", response_model=PatientResponse, status_code=201)
def create_patient(data: PatientCreate, db: Session = Depends(get_db)):
    patient, created = patient_service.get_or_create_patient(db, data)
    if not created:
        raise HTTPException(status_code=409, detail="Patient with this phone number already exists")
    return patient


@router.get("/lookup", response_model=PatientResponse)
def lookup_patient(phone: str = Query(...), db: Session = Depends(get_db)):
    patient = patient_service.get_patient_by_phone(db, phone)
    if not patient:
        raise HTTPException(status_code=404, detail="Patient not found")
    return patient


@router.get("/{patient_id}", response_model=PatientResponse)
def get_patient(patient_id: str, db: Session = Depends(get_db)):
    patient = patient_service.get_patient(db, patient_id)
    if not patient:
        raise HTTPException(status_code=404, detail="Patient not found")
    return patient


@router.patch("/{patient_id}", response_model=PatientResponse)
def update_patient(patient_id: str, data: PatientUpdate, db: Session = Depends(get_db)):
    patient = patient_service.get_patient(db, patient_id)
    if not patient:
        raise HTTPException(status_code=404, detail="Patient not found")
    return patient_service.update_patient(db, patient, data)


@router.get("/{patient_id}/appointments", response_model=list[AppointmentResponse])
def get_patient_appointments(patient_id: str, db: Session = Depends(get_db)):
    patient = patient_service.get_patient(db, patient_id)
    if not patient:
        raise HTTPException(status_code=404, detail="Patient not found")
    return appointment_service.get_appointments_for_patient(db, patient_id)
