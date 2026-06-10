from datetime import date, datetime, timedelta
from zoneinfo import ZoneInfo

TZ = ZoneInfo("America/New_York")


def _future_dt(days: int = 1, hour: int = 10) -> str:
    dt = datetime.now(TZ).replace(hour=hour, minute=0, second=0, microsecond=0) + timedelta(days=days)
    # ensure weekday
    while dt.weekday() >= 5:
        dt += timedelta(days=1)
    return dt.isoformat()


def _create_patient(client):
    return client.post(
        "/api/v1/patients/",
        json={
            "first_name": "Jane",
            "last_name": "Doe",
            "phone": "5551234567",
        },
    )


class TestAvailability:
    def test_check_availability_returns_slots(self, client):
        tomorrow = (date.today() + timedelta(days=1)).isoformat()
        resp = client.get(f"/api/v1/appointments/availability?date={tomorrow}")
        assert resp.status_code == 200
        data = resp.json()
        assert "available_slots" in data
        assert len(data["available_slots"]) > 0

    def test_next_available_returns_slots(self, client):
        resp = client.get("/api/v1/appointments/next-available")
        assert resp.status_code == 200
        assert isinstance(resp.json()["slots"], list)


class TestAppointmentCRUD:
    def test_book_appointment(self, client):
        patient_resp = _create_patient(client)
        assert patient_resp.status_code == 201
        patient_id = patient_resp.json()["id"]

        resp = client.post(
            "/api/v1/appointments/",
            json={
                "patient_id": patient_id,
                "appointment_datetime": _future_dt(days=3, hour=10),
                "duration_minutes": 30,
                "appointment_type": "checkup",
            },
        )
        assert resp.status_code == 201
        data = resp.json()
        assert data["status"] == "scheduled"
        assert data["patient_id"] == patient_id

    def test_double_booking_rejected(self, client):
        patient_resp = _create_patient(client)
        patient_id = patient_resp.json()["id"]
        dt = _future_dt(days=4, hour=11)

        first = client.post(
            "/api/v1/appointments/",
            json={"patient_id": patient_id, "appointment_datetime": dt, "duration_minutes": 30},
        )
        assert first.status_code == 201

        second = client.post(
            "/api/v1/appointments/",
            json={"patient_id": patient_id, "appointment_datetime": dt, "duration_minutes": 30},
        )
        assert second.status_code == 409

    def test_cancel_appointment(self, client):
        patient_resp = _create_patient(client)
        patient_id = patient_resp.json()["id"]

        appt = client.post(
            "/api/v1/appointments/",
            json={"patient_id": patient_id, "appointment_datetime": _future_dt(days=5, hour=14), "duration_minutes": 30},
        )
        appt_id = appt.json()["id"]

        cancel = client.delete(f"/api/v1/appointments/{appt_id}?reason=Patient+request")
        assert cancel.status_code == 200
        assert cancel.json()["status"] == "cancelled"

    def test_reschedule_appointment(self, client):
        patient_resp = _create_patient(client)
        patient_id = patient_resp.json()["id"]

        appt = client.post(
            "/api/v1/appointments/",
            json={"patient_id": patient_id, "appointment_datetime": _future_dt(days=6, hour=9), "duration_minutes": 30},
        )
        appt_id = appt.json()["id"]

        update = client.patch(
            f"/api/v1/appointments/{appt_id}",
            json={"appointment_datetime": _future_dt(days=7, hour=10)},
        )
        assert update.status_code == 200
        assert update.json()["id"] == appt_id
