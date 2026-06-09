from datetime import datetime, date, timedelta, time
from zoneinfo import ZoneInfo
from sqlalchemy.orm import Session
from sqlalchemy import and_, or_

from app.models.appointment import Appointment, AppointmentStatus
from app.models.patient import Patient
from app.schemas.appointment import AppointmentCreate, AppointmentUpdate, AvailabilityResponse, TimeSlot
from app.config import get_settings

settings = get_settings()


def get_appointment(db: Session, appointment_id: str) -> Appointment | None:
    return db.query(Appointment).filter(Appointment.id == appointment_id).first()


def get_appointments_for_patient(db: Session, patient_id: str) -> list[Appointment]:
    return (
        db.query(Appointment)
        .filter(
            Appointment.patient_id == patient_id,
            Appointment.status.in_([AppointmentStatus.SCHEDULED, AppointmentStatus.CONFIRMED]),
        )
        .order_by(Appointment.appointment_datetime)
        .all()
    )


def get_available_slots(db: Session, target_date: date, duration_minutes: int = 30) -> AvailabilityResponse:
    tz = ZoneInfo(settings.clinic_timezone)
    slots: list[TimeSlot] = []

    start_dt = datetime.combine(target_date, time(settings.business_hours_start, 0), tzinfo=tz)
    end_dt = datetime.combine(target_date, time(settings.business_hours_end, 0), tzinfo=tz)

    existing = (
        db.query(Appointment)
        .filter(
            and_(
                Appointment.appointment_datetime >= start_dt,
                Appointment.appointment_datetime < end_dt,
                Appointment.status.in_([AppointmentStatus.SCHEDULED, AppointmentStatus.CONFIRMED]),
            )
        )
        .all()
    )

    booked_ranges = [
        (a.appointment_datetime, a.appointment_datetime + timedelta(minutes=a.duration_minutes))
        for a in existing
    ]

    current = start_dt
    while current + timedelta(minutes=duration_minutes) <= end_dt:
        slot_end = current + timedelta(minutes=duration_minutes)
        occupied = any(
            not (slot_end <= b_start or current >= b_end)
            for b_start, b_end in booked_ranges
        )
        slots.append(TimeSlot(start_time=current, end_time=slot_end, available=not occupied))
        current += timedelta(minutes=duration_minutes)

    return AvailabilityResponse(date=target_date, available_slots=slots)


def is_slot_available(db: Session, appointment_datetime: datetime, duration_minutes: int, exclude_id: str | None = None) -> bool:
    slot_end = appointment_datetime + timedelta(minutes=duration_minutes)

    # Fetch active appointments for the day and check overlap in Python
    # (avoids SQLAlchemy timedelta-column arithmetic incompatibilities across DB backends)
    day_start = appointment_datetime.replace(hour=0, minute=0, second=0, microsecond=0)
    day_end = appointment_datetime.replace(hour=23, minute=59, second=59)

    query = db.query(Appointment).filter(
        Appointment.status.in_([AppointmentStatus.SCHEDULED, AppointmentStatus.CONFIRMED]),
        Appointment.appointment_datetime >= day_start,
        Appointment.appointment_datetime <= day_end,
    )
    if exclude_id:
        query = query.filter(Appointment.id != exclude_id)

    # SQLite returns naive datetimes; strip tzinfo for portable comparison
    def _naive(dt: datetime) -> datetime:
        return dt.replace(tzinfo=None) if dt.tzinfo else dt

    naive_start = _naive(appointment_datetime)
    naive_end = _naive(slot_end)

    for appt in query.all():
        appt_start = _naive(appt.appointment_datetime)
        appt_end = appt_start + timedelta(minutes=appt.duration_minutes)
        if not (naive_end <= appt_start or naive_start >= appt_end):
            return False
    return True


def create_appointment(db: Session, data: AppointmentCreate) -> Appointment:
    appointment = Appointment(**data.model_dump())
    db.add(appointment)
    db.commit()
    db.refresh(appointment)
    return appointment


def update_appointment(db: Session, appointment: Appointment, data: AppointmentUpdate) -> Appointment:
    for field, value in data.model_dump(exclude_none=True).items():
        setattr(appointment, field, value)
    db.commit()
    db.refresh(appointment)
    return appointment


def cancel_appointment(db: Session, appointment: Appointment, reason: str | None = None) -> Appointment:
    appointment.status = AppointmentStatus.CANCELLED
    appointment.cancellation_reason = reason
    db.commit()
    db.refresh(appointment)
    return appointment


def find_next_available_slots(db: Session, num_slots: int = 3, duration_minutes: int = 30) -> list[datetime]:
    tz = ZoneInfo(settings.clinic_timezone)
    now = datetime.now(tz)
    results: list[datetime] = []
    check_date = now.date()
    max_days = settings.max_advance_booking_days

    for _ in range(max_days):
        if check_date.weekday() >= 5:  # skip weekends
            check_date += timedelta(days=1)
            continue

        availability = get_available_slots(db, check_date, duration_minutes)
        for slot in availability.available_slots:
            if slot.available and slot.start_time > now:
                results.append(slot.start_time)
                if len(results) >= num_slots:
                    return results

        check_date += timedelta(days=1)

    return results
