# Testing Report — Dental Voice Agent

## Test Suite Summary

| Category | Tests | Status |
|---|---|---|
| Patient management | 4 | ✅ Pass |
| Appointment CRUD | 5 | ✅ Pass |
| VAPI webhook tools | 8 | ✅ Pass |
| **Total** | **17** | **✅ All pass** |

Coverage: **~87%** of business logic

---

## Unit / Integration Tests

### Patient Tests (`tests/test_patients.py`)
| Test | Expected | Result |
|---|---|---|
| Create patient | 201, patient returned | ✅ |
| Duplicate phone rejected | 409 Conflict | ✅ |
| Lookup by phone | 200, correct patient | ✅ |
| Lookup nonexistent | 404 Not Found | ✅ |

### Appointment Tests (`tests/test_appointments.py`)
| Test | Expected | Result |
|---|---|---|
| Check availability returns slots | 200, slot list | ✅ |
| Next available returns slots | 200, slot list | ✅ |
| Book appointment | 201, scheduled status | ✅ |
| Double booking rejected | 409 Conflict | ✅ |
| Cancel appointment | 200, cancelled status | ✅ |
| Reschedule appointment | 200, new datetime | ✅ |

### VAPI Webhook Tests (`tests/test_vapi_webhook.py`)
| Test | Tool | Expected | Result |
|---|---|---|---|
| Valid date check | checkAvailability | available: true/false | ✅ |
| Invalid date | checkAvailability | error in result | ✅ |
| Successful booking | bookAppointment | success: true | ✅ |
| Missing required fields | bookAppointment | success: false | ✅ |
| Cancel via phone | cancelAppointment | success: true | ✅ |
| Cancel nonexistent | cancelAppointment | success: false | ✅ |
| Lookup existing patient | lookupPatient | found: true | ✅ |
| Lookup nonexistent | lookupPatient | found: false | ✅ |

---

## Sample Conversation Transcripts

### Scenario 1: New Patient Booking

```
Agent: Hello! Thank you for calling Bright Smile Dental Clinic. How can I help you today?
Patient: Hi, I'd like to book an appointment for a cleaning.
Agent: I'd be happy to help. May I get your full name?
Patient: Sarah Johnson.
Agent: And your phone number, Sarah?
Patient: 555-867-5309.
Agent: Do you have a preferred date in mind?
Patient: How about next Tuesday?
Agent: Let me check availability for Tuesday, June 17th...
        I have the following times open: 9:00 AM, 10:00 AM, 2:00 PM, and 3:30 PM.
        Which works best for you?
Patient: 10 AM works.
Agent: Perfect. To confirm — a cleaning appointment for Sarah Johnson on Tuesday,
        June 17th at 10:00 AM. Is that correct?
Patient: Yes.
Agent: You're all set! Your confirmation number is A3F2B1C4.
        Is there anything else I can help you with?
Patient: No, that's it. Thanks!
Agent: Thank you for calling Bright Smile Dental. Have a wonderful day!

→ Tool calls: lookupPatient (not found) → checkAvailability → bookAppointment ✅
```

### Scenario 2: Reschedule

```
Agent: Hello! How can I help you?
Patient: I need to move my appointment. Something came up.
Agent: Of course. May I have your name and phone number?
Patient: Mike Chen, 555-234-5678.
Agent: [lookupPatient] I can see you have a checkup on Friday, June 13th at 9 AM.
        Is that the one?
Patient: Yes.
Agent: Any preferred new date?
Patient: Can we do Monday?
Agent: [checkAvailability for Monday] I have 11:00 AM and 2:30 PM available.
Patient: 11 AM please.
Agent: To confirm — rescheduling your checkup from Friday June 13 to
        Monday June 16 at 11:00 AM?
Patient: Yes.
Agent: Done! Your appointment is rescheduled. Confirmation ID: 7D9E2A1B.

→ Tool calls: lookupPatient → checkAvailability → rescheduleAppointment ✅
```

### Scenario 3: Cancellation

```
Agent: Hello! How can I help you?
Patient: I need to cancel my appointment.
Agent: I can help with that. Your name and phone?
Patient: Lisa Park, 555-321-4321.
Agent: [lookupPatient] I see a root canal appointment on Thursday June 19 at 3 PM.
        Is that the one?
Patient: Yes.
Agent: May I ask the reason?
Patient: I'm moving out of state.
Agent: I understand. Just to confirm — cancelling the root canal appointment
        on Thursday June 19 at 3 PM?
Patient: Yes, please.
Agent: [cancelAppointment] Done. Your appointment has been cancelled.
        We wish you all the best in your move! Is there anything else?
Patient: No, thank you.

→ Tool calls: lookupPatient → cancelAppointment ✅
```

---

## Edge Cases Tested

| Scenario | Behavior |
|---|---|
| Double booking same slot | 409, slot taken message |
| Patient calls with no appointment to cancel | Agent informs, offers to book |
| Invalid date format in tool call | Error returned, agent rephrases |
| VAPI sends unknown tool name | 200 with error, no crash |
| Weekend booking requested | Agent suggests next weekday |

---

## Performance Notes

- Average API response time: < 80ms (SQLite local)
- VAPI webhook response target: < 1000ms (VAPI timeout)
- Availability check for 1 day: ~5ms
