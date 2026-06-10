"""
VAPI webhook router — handles function/tool call events from VAPI voice agents.

VAPI sends a POST to /vapi/webhook for every call event. We handle:
  - function-call: tool invocations from the assistant during a conversation
  - end-of-call-report: final call summary for logging
"""
import hashlib
import hmac
import json
from datetime import datetime
from zoneinfo import ZoneInfo

import structlog
from fastapi import APIRouter, Depends, Header, HTTPException, Request
from sqlalchemy.orm import Session

from app.config import get_settings
from app.database import get_db
from app.models.appointment import AppointmentStatus, AppointmentType
from app.schemas.appointment import AppointmentCreate, AppointmentUpdate
from app.schemas.patient import PatientCreate
from app.services import appointment_service, patient_service

logger = structlog.get_logger()
router = APIRouter(prefix="/vapi", tags=["vapi"])
settings = get_settings()


def _verify_signature(body: bytes, signature: str | None) -> None:
    if not settings.vapi_webhook_secret:
        return
    if not signature:
        raise HTTPException(status_code=401, detail="Missing signature")
    expected = hmac.new(settings.vapi_webhook_secret.encode(), body, hashlib.sha256).hexdigest()
    if not hmac.compare_digest(expected, signature):
        raise HTTPException(status_code=401, detail="Invalid signature")


# ---------------------------------------------------------------------------
# Tool handlers
# ---------------------------------------------------------------------------


def _handle_check_availability(args: dict, db: Session) -> dict:
    try:
        target_date = datetime.strptime(args["date"], "%Y-%m-%d").date()
    except (KeyError, ValueError):
        return {"error": "Invalid or missing date. Use YYYY-MM-DD format."}

    duration = int(args.get("duration_minutes", 30))
    availability = appointment_service.get_available_slots(db, target_date, duration)
    available = [
        {"time": s.start_time.strftime("%I:%M %p"), "datetime": s.start_time.isoformat()}
        for s in availability.available_slots
        if s.available
    ]
    if not available:
        return {"available": False, "message": f"No slots available on {target_date.strftime('%B %d, %Y')}."}
    return {"available": True, "date": str(target_date), "slots": available[:8]}


def _handle_get_next_available(args: dict, db: Session) -> dict:
    duration = int(args.get("duration_minutes", 30))
    slots = appointment_service.find_next_available_slots(db, num_slots=3, duration_minutes=duration)
    if not slots:
        return {"slots": [], "message": "No available slots in the next 60 days."}
    formatted = [
        {
            "datetime": s.isoformat(),
            "display": s.strftime("%A, %B %d at %I:%M %p"),
        }
        for s in slots
    ]
    return {"slots": formatted}


def _handle_book_appointment(args: dict, db: Session, call_id: str) -> dict:
    required = ["patient_phone", "patient_first_name", "patient_last_name", "appointment_datetime"]
    if missing := [f for f in required if not args.get(f)]:
        return {"success": False, "error": f"Missing required fields: {', '.join(missing)}"}

    patient, _ = patient_service.get_or_create_patient(
        db,
        PatientCreate(
            first_name=args["patient_first_name"],
            last_name=args["patient_last_name"],
            phone=args["patient_phone"],
            email=args.get("patient_email"),
            insurance_provider=args.get("insurance_provider"),
            insurance_id=args.get("insurance_id"),
        ),
    )

    try:
        appt_dt = datetime.fromisoformat(args["appointment_datetime"])
        if appt_dt.tzinfo is None:
            appt_dt = appt_dt.replace(tzinfo=ZoneInfo(settings.clinic_timezone))
    except ValueError:
        return {"success": False, "error": "Invalid datetime format. Use ISO 8601."}

    duration = int(args.get("duration_minutes", 30))
    if not appointment_service.is_slot_available(db, appt_dt, duration):
        return {"success": False, "error": "That time slot is no longer available. Please choose another."}

    appt_type_str = args.get("appointment_type", "checkup").lower().replace(" ", "_")
    try:
        appt_type = AppointmentType(appt_type_str)
    except ValueError:
        appt_type = AppointmentType.OTHER

    appointment = appointment_service.create_appointment(
        db,
        AppointmentCreate(
            patient_id=patient.id,
            appointment_datetime=appt_dt,
            duration_minutes=duration,
            appointment_type=appt_type,
            dentist_name=args.get("dentist_name"),
            notes=args.get("notes"),
            vapi_call_id=call_id,
        ),
    )

    logger.info("appointment_booked", appointment_id=appointment.id, patient_id=patient.id)
    return {
        "success": True,
        "appointment_id": appointment.id,
        "confirmation": (
            f"Appointment confirmed for {patient.full_name} on "
            f"{appt_dt.strftime('%A, %B %d at %I:%M %p')}. "
            f"Confirmation ID: {appointment.id[:8].upper()}"
        ),
    }


def _handle_reschedule_appointment(args: dict, db: Session) -> dict:
    appointment_id = args.get("appointment_id")
    phone = args.get("patient_phone")

    appointment = None
    if appointment_id:
        appointment = appointment_service.get_appointment(db, appointment_id)
    elif phone:
        patient = patient_service.get_patient_by_phone(db, phone)
        if patient:
            appts = appointment_service.get_appointments_for_patient(db, patient.id)
            appointment = appts[0] if appts else None

    if not appointment:
        return {"success": False, "error": "No active appointment found. Please provide appointment ID or phone number."}

    if appointment.status == AppointmentStatus.CANCELLED:
        return {"success": False, "error": "This appointment has already been cancelled."}

    try:
        new_dt = datetime.fromisoformat(args["new_datetime"])
        if new_dt.tzinfo is None:
            new_dt = new_dt.replace(tzinfo=ZoneInfo(settings.clinic_timezone))
    except (KeyError, ValueError):
        return {"success": False, "error": "Invalid or missing new_datetime. Use ISO 8601 format."}

    if not appointment_service.is_slot_available(db, new_dt, appointment.duration_minutes, exclude_id=appointment.id):
        return {"success": False, "error": "That time slot is not available. Please choose another."}

    updated = appointment_service.update_appointment(
        db, appointment, AppointmentUpdate(appointment_datetime=new_dt)
    )
    return {
        "success": True,
        "appointment_id": updated.id,
        "confirmation": (
            f"Appointment rescheduled to {new_dt.strftime('%A, %B %d at %I:%M %p')}. "
            f"Confirmation ID: {updated.id[:8].upper()}"
        ),
    }


def _handle_cancel_appointment(args: dict, db: Session) -> dict:
    appointment_id = args.get("appointment_id")
    phone = args.get("patient_phone")

    appointment = None
    if appointment_id:
        appointment = appointment_service.get_appointment(db, appointment_id)
    elif phone:
        patient = patient_service.get_patient_by_phone(db, phone)
        if patient:
            appts = appointment_service.get_appointments_for_patient(db, patient.id)
            appointment = appts[0] if appts else None

    if not appointment:
        return {"success": False, "error": "No active appointment found."}

    if appointment.status == AppointmentStatus.CANCELLED:
        return {"success": False, "error": "This appointment is already cancelled."}

    reason = args.get("reason", "Cancelled by patient via phone")
    appointment_service.cancel_appointment(db, appointment, reason)
    logger.info("appointment_cancelled", appointment_id=appointment.id)
    return {
        "success": True,
        "message": (
            f"Appointment on {appointment.appointment_datetime.strftime('%B %d at %I:%M %p')} "
            "has been successfully cancelled."
        ),
    }


def _handle_lookup_patient(args: dict, db: Session) -> dict:
    phone = args.get("phone")
    if not phone:
        return {"found": False, "error": "Phone number required"}

    patient = patient_service.get_patient_by_phone(db, phone)
    if not patient:
        return {"found": False, "message": "No patient record found for this phone number."}

    upcoming = appointment_service.get_appointments_for_patient(db, patient.id)
    return {
        "found": True,
        "patient": {
            "id": patient.id,
            "name": patient.full_name,
            "phone": patient.phone,
        },
        "upcoming_appointments": [
            {
                "id": a.id,
                "datetime": a.appointment_datetime.isoformat(),
                "display": a.appointment_datetime.strftime("%A, %B %d at %I:%M %p"),
                "type": a.appointment_type.value,
                "status": a.status.value,
            }
            for a in upcoming
        ],
    }


def _dispatch_tool(fn_name: str, fn_args: dict, call_id: str, db) -> dict:
    handler = TOOL_HANDLERS.get(fn_name)
    if not handler:
        logger.warning("unknown_tool", tool=fn_name)
        return {"result": json.dumps({"error": f"Unknown tool: {fn_name}"})}
    if fn_name == "bookAppointment":
        result = handler(fn_args, db, call_id)
    else:
        result = handler(fn_args, db)
    return {"result": json.dumps(result)}


TOOL_HANDLERS = {
    "checkAvailability": _handle_check_availability,
    "getNextAvailable": _handle_get_next_available,
    "bookAppointment": _handle_book_appointment,
    "rescheduleAppointment": _handle_reschedule_appointment,
    "cancelAppointment": _handle_cancel_appointment,
    "lookupPatient": _handle_lookup_patient,
}


# ---------------------------------------------------------------------------
# Webhook endpoint
# ---------------------------------------------------------------------------


@router.post("/webhook")
async def vapi_webhook(
    request: Request,
    x_vapi_signature: str | None = Header(default=None),
    db: Session = Depends(get_db),
):
    body = await request.body()
    _verify_signature(body, x_vapi_signature)

    payload = json.loads(body)
    event_type = payload.get("message", {}).get("type")
    call_id = payload.get("message", {}).get("call", {}).get("id", "")

    logger.info("vapi_event", event_type=event_type, call_id=call_id, payload=payload)

    if event_type == "function-call":
        fn_call = payload["message"]["functionCall"]
        fn_name = fn_call["name"]
        fn_args = fn_call.get("parameters", {})
        return _dispatch_tool(fn_name, fn_args, call_id, db)

    # Newer VAPI format: tools with individual server.url receive tool-calls events
    if event_type == "tool-calls":
        tool_list = payload["message"].get("toolCallList", [])
        results = []
        for tool_call in tool_list:
            fn_name = tool_call["function"]["name"]
            raw_args = tool_call["function"].get("arguments", "{}")
            fn_args = json.loads(raw_args) if isinstance(raw_args, str) else raw_args
            tool_result = _dispatch_tool(fn_name, fn_args, call_id, db)
            results.append({
                "toolCallId": tool_call["id"],
                "result": tool_result.get("result", json.dumps({"error": "no result"})),
            })
        return {"results": results}

    if event_type == "end-of-call-report":
        report = payload.get("message", {})
        logger.info(
            "call_ended",
            call_id=call_id,
            duration=report.get("durationSeconds"),
            ended_reason=report.get("endedReason"),
        )
        return {"status": "logged"}

    # status-update and other events — acknowledge without action
    return {"status": "ok"}
