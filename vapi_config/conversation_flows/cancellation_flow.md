# Conversation Flow: Appointment Cancellation

## Trigger
Patient calls to cancel an existing appointment.

## Flow

```
Agent: "Hello! Thank you for calling Bright Smile Dental Clinic.
        How can I help you today?"

Patient: "I need to cancel my appointment."

Agent: "I'm sorry to hear that. Let me help you with that.
        Could I get your name and phone number?"

Patient: [provides details]

→ TOOL: lookupPatient(phone)

[Appointment found]
Agent: "I see you have a [type] appointment on [date and time].
        Is that the one you'd like to cancel?"

Patient: "Yes"

Agent: "May I ask the reason for the cancellation?
        [pause] And would you like to reschedule for another time?"

[If patient wants to reschedule instead]
→ Branch to rescheduling flow

[If confirming cancellation]
Agent: "Just to confirm — you'd like to cancel the [type] appointment
        on [date and time]. Is that correct?"

Patient: "Yes"

→ TOOL: cancelAppointment(appointment_id or phone, reason)

[On success]
Agent: "Your appointment has been successfully cancelled.
        If you'd like to book again in the future, please don't hesitate to call.
        Is there anything else I can help you with?"

[No appointment found]
Agent: "I don't see any upcoming appointments under that phone number.
        Could it be under a different number, or has it possibly already been cancelled?"
```

## Edge Cases

- **Patient unsure of which appointment** → Read back all upcoming appointments
- **Cancellation within 24 hours** → Note the policy verbally: "Please be aware of our 24-hour cancellation policy."
- **Patient wants to cancel and rebook** → Confirm cancellation first, then flow into scheduling
