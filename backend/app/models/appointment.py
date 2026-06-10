import random
import string
from datetime import datetime
from enum import Enum as PyEnum

from sqlalchemy import DateTime, Enum, ForeignKey, String, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


def _short_id() -> str:
    """Generate a short 8-char alphanumeric ID that's easy to read aloud (e.g. APT-X7K2M9)."""
    chars = string.ascii_uppercase + string.digits
    # Remove visually confusing chars: O/0, I/1, S/5
    chars = chars.translate(str.maketrans("", "", "O0I1S5"))
    return "APT-" + "".join(random.choices(chars, k=6))


class AppointmentStatus(str, PyEnum):
    SCHEDULED = "scheduled"
    CONFIRMED = "confirmed"
    CANCELLED = "cancelled"
    COMPLETED = "completed"
    NO_SHOW = "no_show"


class AppointmentType(str, PyEnum):
    CHECKUP = "checkup"
    CLEANING = "cleaning"
    FILLING = "filling"
    ROOT_CANAL = "root_canal"
    EXTRACTION = "extraction"
    WHITENING = "whitening"
    CONSULTATION = "consultation"
    EMERGENCY = "emergency"
    OTHER = "other"


class Appointment(Base):
    __tablename__ = "appointments"

    id: Mapped[str] = mapped_column(String(20), primary_key=True, default=_short_id)
    patient_id: Mapped[str] = mapped_column(String(36), ForeignKey("patients.id"), index=True)

    appointment_datetime: Mapped[datetime] = mapped_column(DateTime, index=True)
    duration_minutes: Mapped[int] = mapped_column(default=30)
    appointment_type: Mapped[AppointmentType] = mapped_column(
        Enum(AppointmentType), default=AppointmentType.CHECKUP
    )
    status: Mapped[AppointmentStatus] = mapped_column(
        Enum(AppointmentStatus), default=AppointmentStatus.SCHEDULED, index=True
    )

    dentist_name: Mapped[str | None] = mapped_column(String(100), nullable=True)
    notes: Mapped[str | None] = mapped_column(String(1000), nullable=True)
    cancellation_reason: Mapped[str | None] = mapped_column(String(500), nullable=True)

    # VAPI call tracking
    vapi_call_id: Mapped[str | None] = mapped_column(String(100), nullable=True, index=True)

    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now(), onupdate=func.now())

    patient: Mapped["Patient"] = relationship("Patient", back_populates="appointments")
