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
        if len(digits) < 7:
            raise ValueError("Phone number must have at least 7 digits")
        if v.startswith("+"):
            return v  # already has country code
        if len(digits) == 10 and digits.startswith("98"):
            return f"+977{digits}"  # Nepal mobile numbers (98xxxxxxxx)
        if len(digits) == 10:
            return f"+1{digits}"  # US/Canada default
        return f"+{digits}"


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
