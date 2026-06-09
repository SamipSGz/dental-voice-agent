import re
from sqlalchemy.orm import Session
from app.models.patient import Patient
from app.schemas.patient import PatientCreate, PatientUpdate


def _normalize_phone(phone: str) -> str:
    digits = re.sub(r"\D", "", phone)
    return f"+1{digits[-10:]}" if not phone.startswith("+") else phone


def get_patient(db: Session, patient_id: str) -> Patient | None:
    return db.query(Patient).filter(Patient.id == patient_id).first()


def get_patient_by_phone(db: Session, phone: str) -> Patient | None:
    normalized = _normalize_phone(phone)
    return db.query(Patient).filter(Patient.phone == normalized).first()


def get_or_create_patient(db: Session, data: PatientCreate) -> tuple[Patient, bool]:
    existing = get_patient_by_phone(db, data.phone)
    if existing:
        return existing, False
    patient = Patient(**data.model_dump())
    db.add(patient)
    db.commit()
    db.refresh(patient)
    return patient, True


def update_patient(db: Session, patient: Patient, data: PatientUpdate) -> Patient:
    for field, value in data.model_dump(exclude_none=True).items():
        setattr(patient, field, value)
    db.commit()
    db.refresh(patient)
    return patient
