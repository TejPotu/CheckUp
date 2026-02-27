"""Bilingual prompt templates for Telugu and English."""

from __future__ import annotations

# ── Daily Check-In Prompts ────────────────────────────────────────────

DAILY_CHECKIN_TE = (
    "🙏 నమస్కారం! ఈరోజు మీరు ఎలా ఉన్నారు?\n\n"
    "మీకు ఏమైనా నొప్పులు, అలసట, లేదా ఏదైనా సమస్య ఉంటే చెప్పండి. "
    "మీ ఆరోగ్యం మాకు ముఖ్యం. ❤️"
)

DAILY_CHECKIN_EN = (
    "🙏 Hello! How are you feeling today?\n\n"
    "Please let me know if you have any pain, tiredness, or any issues. "
    "Your health matters to us. ❤️"
)

# ── Medication Reminder Prompts ───────────────────────────────────────

MEDICATION_REMINDER_TE = (
    "💊 మందుల సమయం!\n\n"
    "{medication_name} ({dosage}) తీసుకునే టైమ్ అయింది.\n"
    "దయచేసి మీ మందు తీసుకోండి. తీసుకున్నాక 'తీసుకున్నాను' అని చెప్పండి. 🙏"
)

MEDICATION_REMINDER_EN = (
    "💊 Medication time!\n\n"
    "It's time to take {medication_name} ({dosage}).\n"
    "Please take your medicine and reply 'done' when you've taken it. 🙏"
)

# ── Missed Check-In Alert (for caregiver) ─────────────────────────────

MISSED_CHECKIN_ALERT = (
    "⚠️ {parent_name} has not responded to today's health check-in.\n\n"
    "The check-in was sent at {checkin_time}. It's been {hours_elapsed} hours.\n"
    "Please check on them when you can."
)

# ── Weekly Summary (for caregiver) ────────────────────────────────────

WEEKLY_SUMMARY_TEMPLATE = (
    "📊 Weekly Health Summary for {parent_name}\n"
    "━━━━━━━━━━━━━━━━━━━━━━━━\n\n"
    "📅 Period: {start_date} – {end_date}\n\n"
    "✅ Check-ins completed: {checkins_completed}/7\n"
    "💊 Medications confirmed: {meds_confirmed}/{meds_total}\n"
    "🔴 High-risk days: {high_risk_days}\n"
    "🟡 Medium-risk days: {medium_risk_days}\n"
    "🟢 Low-risk days: {low_risk_days}\n\n"
    "{notes}"
)

# ── Medical Disclaimer ────────────────────────────────────────────────

DISCLAIMER_TE = (
    "⚠️ ఇది సాధారణ ఆరోగ్య సమాచారం మాత్రమే, వైద్య సలహా కాదు. "
    "దయచేసి మీ డాక్టర్‌ను సంప్రదించండి."
)

DISCLAIMER_EN = (
    "⚠️ This is general health information, not medical advice. "
    "Please consult your doctor for personalized guidance."
)


def get_checkin_prompt(lang: str) -> str:
    """Return the daily check-in prompt in the given language."""
    return DAILY_CHECKIN_TE if lang == "te" else DAILY_CHECKIN_EN


def get_medication_reminder(lang: str, medication_name: str, dosage: str) -> str:
    """Return a medication reminder in the given language."""
    template = MEDICATION_REMINDER_TE if lang == "te" else MEDICATION_REMINDER_EN
    return template.format(medication_name=medication_name, dosage=dosage)


def get_disclaimer(lang: str) -> str:
    """Return the medical disclaimer in the given language."""
    return DISCLAIMER_TE if lang == "te" else DISCLAIMER_EN
