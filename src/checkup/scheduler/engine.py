"""Scheduling engine — compute check-ins, medication reminders, and trend analysis."""

from __future__ import annotations

import logging
from datetime import datetime, timedelta
from typing import Any

logger = logging.getLogger(__name__)


def compute_medication_reminders(medications: list[dict]) -> list[dict[str, Any]]:
    """Given a list of medications, compute today's remaining reminder times.

    Args:
        medications: List of dicts like:
            [{"name": "Metformin", "dosage": "500mg", "times": ["08:00", "20:00"]}]

    Returns:
        List of reminder dicts with name, dosage, and scheduled_time.
    """
    now = datetime.now()
    reminders = []

    for med in medications:
        for time_str in med.get("times", []):
            hour, minute = map(int, time_str.split(":"))
            reminder_dt = now.replace(hour=hour, minute=minute, second=0, microsecond=0)

            # Only include future reminders
            if reminder_dt > now:
                reminders.append({
                    "medication_name": med["name"],
                    "dosage": med.get("dosage", ""),
                    "scheduled_time": reminder_dt,
                })

    reminders.sort(key=lambda r: r["scheduled_time"])
    return reminders


def assess_weekly_trend(health_logs: list[dict]) -> dict[str, Any]:
    """Analyze the last 7 days of health logs for trends.

    Args:
        health_logs: List of log dicts with 'risk_level' and 'timestamp' keys.

    Returns:
        Summary dict with counts and trend assessment.
    """
    if not health_logs:
        return {"trend": "no_data", "high": 0, "medium": 0, "low": 0}

    counts = {"high": 0, "medium": 0, "low": 0}
    for log in health_logs:
        level = log.get("risk_level", "low")
        counts[level] = counts.get(level, 0) + 1

    # Determine overall trend
    if counts["high"] >= 2:
        trend = "worsening"
    elif counts["high"] >= 1 or counts["medium"] >= 4:
        trend = "needs_attention"
    elif counts["medium"] >= 2:
        trend = "moderate"
    else:
        trend = "stable"

    return {
        "trend": trend,
        "high": counts["high"],
        "medium": counts["medium"],
        "low": counts["low"],
        "total_logs": len(health_logs),
    }


def compute_missed_checkin_alert(
    last_checkin_time: datetime | None,
    checkin_hour: int = 9,
    threshold_hours: int = 2,
) -> bool:
    """Determine if a missed check-in alert should be sent.

    Args:
        last_checkin_time: When the last check-in response was received.
        checkin_hour: The hour the check-in was sent (default 9 AM).
        threshold_hours: Hours after check-in before alerting.

    Returns:
        True if alert should be sent.
    """
    now = datetime.now()
    today_checkin = now.replace(hour=checkin_hour, minute=0, second=0, microsecond=0)

    # Only alert if today's check-in time has passed + threshold
    if now < today_checkin + timedelta(hours=threshold_hours):
        return False

    # Alert if no check-in today
    if last_checkin_time is None:
        return True

    return last_checkin_time.date() < now.date()
