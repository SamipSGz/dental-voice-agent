# API Design — Dental Voice Agent

## Base URL
```
https://your-domain.com/api/v1
```

## Authentication
All production endpoints require `Authorization: Bearer <token>` except the VAPI webhook which uses HMAC signature verification (`X-VAPI-Signature` header).

---

## Appointments

### Check Availability
```
GET /appointments/availability?date=YYYY-MM-DD&duration_minutes=30
```
Returns all time slots for the given date with availability flags.

### Next Available Slots
```
GET /appointments/next-available?count=3&duration_minutes=30
```
Returns the next N open slots across upcoming weekdays.

### Book Appointment
```
POST /appointments/
Content-Type: application/json

{
  "patient_id": "uuid",
  "appointment_datetime": "2025-06-15T10:00:00-05:00",
  "duration_minutes": 30,
  "appointment_type": "cleaning",
  "notes": "First visit"
}
```
Returns 201 with appointment object, or 409 if slot is taken.

### Get Appointment
```
GET /appointments/{id}
```

### Update / Reschedule
```
PATCH /appointments/{id}
Content-Type: application/json

{
  "appointment_datetime": "2025-06-20T14:00:00-05:00"
}
```

### Cancel Appointment
```
DELETE /appointments/{id}?reason=Patient+request
```

---

## Patients

### Create Patient
```
POST /patients/
Content-Type: application/json

{
  "first_name": "Jane",
  "last_name": "Doe",
  "phone": "5551234567",
  "email": "jane@example.com"
}
```

### Lookup by Phone
```
GET /patients/lookup?phone=5551234567
```

### Get Patient
```
GET /patients/{id}
```

### Patient's Appointments
```
GET /patients/{id}/appointments
```

---

## VAPI Webhook

```
POST /vapi/webhook
X-VAPI-Signature: <hmac-sha256>

{
  "message": {
    "type": "function-call",
    "call": { "id": "call-xyz" },
    "functionCall": {
      "name": "bookAppointment",
      "parameters": { ... }
    }
  }
}
```

### Supported Tool Names
| Tool | Action |
|------|--------|
| `checkAvailability` | Get slots for a date |
| `getNextAvailable` | Get next 3 open slots |
| `bookAppointment` | Create appointment + patient |
| `rescheduleAppointment` | Move appointment to new time |
| `cancelAppointment` | Cancel with optional reason |
| `lookupPatient` | Retrieve patient + upcoming appts |

---

## Outbound Calls

```
POST /api/v1/outbound/call
Content-Type: application/json

{
  "appointment_id": "uuid",
  "call_type": "reminder"
}
```
`call_type` options: `reminder`, `follow_up`, `cancellation_confirmation`

---

## Health Check

```
GET /health
→ 200 { "status": "healthy", "service": "Dental Voice Agent API" }
```

## Metrics

```
GET /metrics
→ Prometheus-format metrics
```
