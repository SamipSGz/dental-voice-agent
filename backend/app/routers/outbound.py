"""Outbound call management — trigger reminder or follow-up calls via VAPI."""
import httpx
import structlog
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.config import get_settings
from app.database import get_db
from app.services import appointment_service

logger = structlog.get_logger()
router = APIRouter(prefix="/outbound", tags=["outbound"])
settings = get_settings()

VAPI_BASE = "https://api.vapi.ai"


class OutboundCallRequest(BaseModel):
    appointment_id: str
    call_type: str = "reminder"  # reminder | follow_up | cancellation_confirmation


@router.post("/call")
async def trigger_outbound_call(data: OutboundCallRequest, db: Session = Depends(get_db)):
    # Outbound REST calls require the private key
    private_key = settings.vapi_private_key or settings.vapi_api_key
    if not private_key or not settings.vapi_phone_number_id or not settings.vapi_assistant_id:
        raise HTTPException(status_code=503, detail="VAPI not configured")

    appointment = appointment_service.get_appointment(db, data.appointment_id)
    if not appointment:
        raise HTTPException(status_code=404, detail="Appointment not found")

    patient = appointment.patient
    payload = {
        "phoneNumberId": settings.vapi_phone_number_id,
        "assistantId": settings.vapi_assistant_id,
        "customer": {"number": patient.phone, "name": patient.full_name},
        "assistantOverrides": {
            "variableValues": {
                "patientName": patient.full_name,
                "appointmentDate": appointment.appointment_datetime.strftime("%A, %B %d at %I:%M %p"),
                "appointmentType": appointment.appointment_type.value.replace("_", " ").title(),
                "callType": data.call_type,
                "appointmentId": appointment.id,
                "clinicName": settings.clinic_name,
                "clinicPhone": settings.clinic_phone,
            }
        },
    }

    async with httpx.AsyncClient() as client:
        response = await client.post(
            f"{VAPI_BASE}/call/phone",
            headers={"Authorization": f"Bearer {private_key}"},
            json=payload,
        )

    if response.status_code not in (200, 201):
        logger.error("vapi_outbound_failed", status=response.status_code, body=response.text)
        raise HTTPException(status_code=502, detail="Failed to initiate outbound call")

    call_data = response.json()
    logger.info("outbound_call_initiated", call_id=call_data.get("id"), appointment_id=data.appointment_id)
    return {"call_id": call_data.get("id"), "status": "initiated"}
