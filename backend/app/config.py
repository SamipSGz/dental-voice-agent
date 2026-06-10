from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8")

    app_name: str = "Dental Voice Agent API"
    environment: str = "development"
    debug: bool = False

    database_url: str = "sqlite:///./dental_appointments.db"

    vapi_api_key: str = ""
    vapi_phone_number_id: str = ""
    vapi_assistant_id: str = ""
    vapi_webhook_secret: str = ""

    api_secret_key: str = "change-me-in-production"

    sentry_dsn: str = ""

    clinic_name: str = "Bright Smile Dental Clinic"
    clinic_phone: str = "+1-800-DENTIST"
    clinic_timezone: str = "America/New_York"

    # Business hours (24h format)
    business_hours_start: int = 9
    business_hours_end: int = 17
    appointment_slot_minutes: int = 30
    max_advance_booking_days: int = 60

    human_escalation_phone: str = ""


@lru_cache
def get_settings() -> Settings:
    return Settings()
