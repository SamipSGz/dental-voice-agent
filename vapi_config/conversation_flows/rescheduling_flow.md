# Conversation Flow: Appointment Rescheduling

## Trigger
Patient calls wanting to move their existing appointment to a different time.

## Flow

```
Agent: "Hello! Thank you for calling Bright Smile Dental Clinic.
        How can I help you today?"

Patient: "I need to reschedule my appointment."

Agent: "Of course! May I have your name and phone number
        so I can pull up your appointment?"

Patient: [provides details]

→ TOOL: lookupPatient(phone)

[Patient found with upcoming appointment]
Agent: "I can see you have an appointment on [current date/time] for a [type].
        Is that the one you'd like to reschedule?"

Patient: "Yes"

Agent: "No problem. Do you have a new date in mind, or would you like me
        to suggest available times?"

[If patient has a date]
→ TOOL: checkAvailability(new_date)

[If flexible]
→ TOOL: getNextAvailable()

Agent: [presents available options]

Patient: [selects new time]

Agent: "To confirm — I'll move your [appointment type] from [old date]
        to [new date and time]. Shall I go ahead?"

Patient: "Yes"

→ TOOL: rescheduleAppointment(appointment_id or phone, new_datetime)

[On success]
Agent: "Done! Your appointment has been rescheduled to [new date and time].
        Your confirmation number remains [ID]. Is there anything else?"

[Patient not found / no upcoming appointments]
Agent: "I don't see any upcoming appointments under that number.
        Could you check if it might be under a different phone number,
        or would you like to book a new appointment?"
```

## Edge Cases

- **Patient has multiple appointments** → Agent asks which one to reschedule
- **New slot conflicts** → Offer alternatives immediately
- **Patient wants same-day reschedule** → Check today's remaining slots
