"""
Tests for VAPI webhook tool-call handling.
Simulates the JSON payloads VAPI sends for each tool invocation.
"""
import json
from datetime import datetime, timedelta
from zoneinfo import ZoneInfo

TZ = ZoneInfo("America/New_York")


def _future_iso(days: int = 3, hour: int = 10) -> str:
    dt = datetime.now(TZ).replace(hour=hour, minute=0, second=0, microsecond=0) + timedelta(days=days)
    while dt.weekday() >= 5:
        dt += timedelta(days=1)
    return dt.isoformat()


def _webhook_payload(fn_name: str, params: dict) -> dict:
    return {
        "message": {
            "type": "function-call",
            "call": {"id": "test-call-123"},
            "functionCall": {"name": fn_name, "parameters": params},
        }
    }


class TestCheckAvailability:
    def test_valid_date(self, client):
        from datetime import date, timedelta
        future = (date.today() + timedelta(days=2)).isoformat()
        resp = client.post("/vapi/webhook", json=_webhook_payload("checkAvailability", {"date": future}))
        assert resp.status_code == 200
        result = json.loads(resp.json()["result"])
        assert "available" in result

    def test_invalid_date_returns_error(self, client):
        resp = client.post("/vapi/webhook", json=_webhook_payload("checkAvailability", {"date": "not-a-date"}))
        assert resp.status_code == 200
        result = json.loads(resp.json()["result"])
        assert "error" in result


class TestBookAppointment:
    def test_successful_booking(self, client):
        resp = client.post(
            "/vapi/webhook",
            json=_webhook_payload(
                "bookAppointment",
                {
                    "patient_first_name": "John",
                    "patient_last_name": "Smith",
                    "patient_phone": "5559876543",
                    "appointment_datetime": _future_iso(days=4, hour=10),
                    "appointment_type": "cleaning",
                },
            ),
        )
        assert resp.status_code == 200
        result = json.loads(resp.json()["result"])
        assert result["success"] is True
        assert "confirmation" in result

    def test_missing_required_fields(self, client):
        resp = client.post(
            "/vapi/webhook",
            json=_webhook_payload("bookAppointment", {"patient_first_name": "John"}),
        )
        assert resp.status_code == 200
        result = json.loads(resp.json()["result"])
        assert result["success"] is False


class TestCancelAppointment:
    def test_cancel_via_phone(self, client):
        # book first
        client.post(
            "/vapi/webhook",
            json=_webhook_payload(
                "bookAppointment",
                {
                    "patient_first_name": "Alice",
                    "patient_last_name": "Brown",
                    "patient_phone": "5550001111",
                    "appointment_datetime": _future_iso(days=5, hour=14),
                },
            ),
        )
        resp = client.post(
            "/vapi/webhook",
            json=_webhook_payload("cancelAppointment", {"patient_phone": "+15550001111", "reason": "Test cancel"}),
        )
        assert resp.status_code == 200
        result = json.loads(resp.json()["result"])
        assert result["success"] is True

    def test_cancel_nonexistent_returns_error(self, client):
        resp = client.post(
            "/vapi/webhook",
            json=_webhook_payload("cancelAppointment", {"appointment_id": "nonexistent-id"}),
        )
        result = json.loads(resp.json()["result"])
        assert result["success"] is False


class TestLookupPatient:
    def test_lookup_existing_patient(self, client):
        client.post("/api/v1/patients/", json={"first_name": "Bob", "last_name": "Lee", "phone": "5552223333"})
        resp = client.post(
            "/vapi/webhook",
            json=_webhook_payload("lookupPatient", {"phone": "+15552223333"}),
        )
        result = json.loads(resp.json()["result"])
        assert result["found"] is True

    def test_lookup_nonexistent(self, client):
        resp = client.post(
            "/vapi/webhook",
            json=_webhook_payload("lookupPatient", {"phone": "+19999999999"}),
        )
        result = json.loads(resp.json()["result"])
        assert result["found"] is False
