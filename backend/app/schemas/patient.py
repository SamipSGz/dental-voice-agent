import re
from datetime import datetime

from pydantic import BaseModel, field_validator


class PatientBase(BaseModel):
    first_name: str
    last_name: str
    phone: str
    email: str | None = None
    date_of_birth: str | None = None
    insurance_provider: str | None = None
    insurance_id: str | None = None
    notes: str | None = None

    @field_validator("phone")
    @classmethod
    def normalize_phone(cls, v: str) -> str:
        digits = re.sub(r"\D", "", v)
        if len(digits) < 10:
            raise ValueError("Phone number must have at least 10 digits")
        return f"+1{digits[-10:]}" if not v.startswith("+") else v


class PatientCreate(PatientBase):
    pass


class PatientUpdate(BaseModel):
    first_name: str | None = None
    last_name: str | None = None
    email: str | None = None
    date_of_birth: str | None = None
    insurance_provider: str | None = None
    insurance_id: str | None = None
    notes: str | None = None


class PatientResponse(PatientBase):
    id: str
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}
