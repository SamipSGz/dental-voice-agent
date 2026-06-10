# Conversation Flow: Appointment Scheduling

## Trigger
Patient calls the clinic and wants to book a new appointment.

## Flow

```
Agent: "Hello! Thank you for calling Bright Smile Dental Clinic. I'm your appointment assistant.
        How can I help you today?"

Patient: "I'd like to book an appointment."

Agent: "I'd be happy to help you schedule an appointment. May I get your full name please?"

Patient: [provides name]

Agent: "And what's the best phone number to reach you?"

Patient: [provides phone]

→ TOOL: lookupPatient(phone) — check if returning patient

[If returning patient]
Agent: "Welcome back, [Name]! I can see your information on file."

[If new patient]
Agent: "Great, I'll get your information set up."

Agent: "What type of appointment are you looking for?
        I can schedule a checkup, cleaning, filling, consultation, or other procedure."

Patient: [states appointment type]

Agent: "Do you have a preferred date in mind, or would you like me to suggest
        the next available times?"

[If patient has a date]
→ TOOL: checkAvailability(date)

Agent: "I have the following times available on [date]:
        [reads available slots]
        Which time works best for you?"

[If patient is flexible]
→ TOOL: getNextAvailable()

Agent: "The next available appointments are:
        1. [slot 1 display]
        2. [slot 2 display]
        3. [slot 3 display]
        Which of these works for you?"

Patient: [selects time]

Agent: "Perfect! Just to confirm — I'm scheduling a [type] appointment for
        [full name] on [date and time]. Is that correct?"

Patient: "Yes"

→ TOOL: bookAppointment(all collected details)

[On success]
Agent: "You're all set! Your appointment is confirmed for [date and time].
        Your confirmation number is [ID]. We'll see you then!
        Is there anything else I can help you with?"

[On slot taken]
Agent: "I'm sorry, that slot was just taken. Let me check the next available..."
→ TOOL: getNextAvailable()
```

## Edge Cases

- **Patient unsure of appointment type** → Default to "consultation" and note concerns
- **No slots on requested date** → Offer next 3 available across upcoming days
- **Patient needs to speak to someone** → "Let me transfer you to our front desk."
- **Call drops** → Appointment is NOT saved unless `bookAppointment` tool returned success
