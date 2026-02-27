"""Celery tasks — daily check-ins, medication reminders, caregiver alerts."""

from __future__ import annotations

import logging

from celery import Celery
from celery.schedules import crontab

from checkup.config import settings

logger = logging.getLogger(__name__)

# ── Celery app ────────────────────────────────────────────────────────

celery_app = Celery(
    "checkup",
    broker=settings.redis_url,
    backend=settings.redis_url,
)

celery_app.conf.update(
    timezone=settings.timezone,
    enable_utc=False,
    beat_schedule={
        "daily-checkin-scan": {
            "task": "checkup.scheduler.tasks.daily_checkin_scan",
            "schedule": crontab(minute="0", hour="9"),  # 9 AM IST
        },
        "missed-checkin-alert": {
            "task": "checkup.scheduler.tasks.missed_checkin_alert_scan",
            "schedule": crontab(minute="0", hour="11"),  # 11 AM IST (2h after check-in)
        },
        "medication-reminder-scan": {
            "task": "checkup.scheduler.tasks.medication_reminder_scan",
            "schedule": crontab(minute="*/30"),  # Every 30 minutes
        },
        "weekly-summary": {
            "task": "checkup.scheduler.tasks.weekly_summary",
            "schedule": crontab(minute="0", hour="20", day_of_week="0"),  # Sunday 8 PM
        },
    },
)


@celery_app.task(name="checkup.scheduler.tasks.daily_checkin_scan")
def daily_checkin_scan():
    """Send daily check-in messages to all active parents.

    Queries parent_profiles for active parents and sends a check-in
    prompt in their preferred language.
    """
    logger.info("Running daily check-in scan...")
    # TODO: Query DB for active parents, send check-in via meta_client
    # For each parent:
    #   1. Get preferred language
    #   2. Send check-in prompt (from prompts.py)
    #   3. Mark reminder as sent
    logger.info("Daily check-in scan complete")


@celery_app.task(name="checkup.scheduler.tasks.missed_checkin_alert_scan")
def missed_checkin_alert_scan():
    """Alert caregivers about parents who haven't responded to check-ins.

    Runs 2 hours after the check-in time. Queries for parents with
    no check-in response today and notifies their caregiver.
    """
    logger.info("Running missed check-in alert scan...")
    # TODO: Query for parents with no check-in today
    # For each missed parent:
    #   1. Look up caregiver phone
    #   2. Send missed check-in alert
    logger.info("Missed check-in alert scan complete")


@celery_app.task(name="checkup.scheduler.tasks.medication_reminder_scan")
def medication_reminder_scan():
    """Send medication reminders to parents whose medication time is approaching.

    Runs every 30 minutes. Sends reminders for medications due within
    the next 30 minutes.
    """
    logger.info("Running medication reminder scan...")
    # TODO: Query for parents with medications due in next 30 min
    # For each due medication:
    #   1. Send reminder in preferred language
    #   2. Log the reminder
    logger.info("Medication reminder scan complete")


@celery_app.task(name="checkup.scheduler.tasks.weekly_summary")
def weekly_summary():
    """Send weekly health summary to all caregivers.

    Compiles the last 7 days of health logs and sends a structured
    summary to each caregiver.
    """
    logger.info("Running weekly summary generation...")
    # TODO: For each active parent:
    #   1. Query last 7 days of health_logs
    #   2. Use engine.assess_weekly_trend()
    #   3. Format with WEEKLY_SUMMARY_TEMPLATE
    #   4. Send to caregiver phone
    logger.info("Weekly summary generation complete")
