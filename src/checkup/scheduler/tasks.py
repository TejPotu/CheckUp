"""Celery tasks — daily check-ins, medication reminders, caregiver alerts."""

from __future__ import annotations

import asyncio
import logging
from datetime import datetime, timedelta

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


# ── Async helpers ─────────────────────────────────────────────────────

async def _daily_checkin_scan_async() -> None:
    from sqlalchemy import select
    from checkup.db.session import async_session
    from checkup.scheduler.models import ParentProfile
    from checkup.language.prompts import get_checkin_prompt
    from checkup.messaging.meta_client import meta_client

    async with async_session() as session:
        result = await session.execute(
            select(ParentProfile).where(ParentProfile.is_active == True)  # noqa: E712
        )
        parents = result.scalars().all()

    for parent in parents:
        prompt = get_checkin_prompt(parent.preferred_language)
        try:
            await meta_client.send_text(parent.parent_phone, prompt)
            logger.info("Sent daily check-in to %s", parent.parent_phone)
        except Exception as e:
            logger.error("Failed to send check-in to %s: %s", parent.parent_phone, e)


async def _missed_checkin_alert_scan_async() -> None:
    from sqlalchemy import select
    from checkup.db.session import async_session
    from checkup.scheduler.models import ParentProfile, HealthLog
    from checkup.scheduler.engine import compute_missed_checkin_alert
    from checkup.language.prompts import MISSED_CHECKIN_ALERT
    from checkup.messaging.meta_client import meta_client

    now = datetime.now()

    async with async_session() as session:
        result = await session.execute(
            select(ParentProfile).where(ParentProfile.is_active == True)  # noqa: E712
        )
        parents = result.scalars().all()

        for parent in parents:
            log_result = await session.execute(
                select(HealthLog)
                .where(HealthLog.parent_id == parent.id)
                .where(HealthLog.log_type == "checkin")
                .order_by(HealthLog.timestamp.desc())
                .limit(1)
            )
            latest_log = log_result.scalar_one_or_none()
            last_checkin_time = latest_log.timestamp if latest_log else None

            should_alert = compute_missed_checkin_alert(
                last_checkin_time=last_checkin_time,
                checkin_hour=parent.checkin_time.hour,
            )

            if should_alert and parent.caregiver_phone:
                checkin_dt = now.replace(
                    hour=parent.checkin_time.hour, minute=0, second=0, microsecond=0
                )
                hours_elapsed = max(0, int((now - checkin_dt).total_seconds() / 3600))
                message = MISSED_CHECKIN_ALERT.format(
                    parent_name=parent.parent_name,
                    checkin_time=parent.checkin_time.strftime("%I:%M %p"),
                    hours_elapsed=hours_elapsed,
                )
                try:
                    await meta_client.send_text(parent.caregiver_phone, message)
                    logger.info("Sent missed check-in alert for %s", parent.parent_name)
                except Exception as e:
                    logger.error("Failed to send missed alert for %s: %s", parent.parent_name, e)


async def _medication_reminder_scan_async() -> None:
    from sqlalchemy import select
    from checkup.db.session import async_session
    from checkup.scheduler.models import ParentProfile
    from checkup.scheduler.engine import compute_medication_reminders
    from checkup.language.prompts import get_medication_reminder
    from checkup.messaging.meta_client import meta_client

    now = datetime.now()
    window_end = now + timedelta(minutes=30)

    async with async_session() as session:
        result = await session.execute(
            select(ParentProfile).where(ParentProfile.is_active == True)  # noqa: E712
        )
        parents = result.scalars().all()

    for parent in parents:
        if not parent.medications:
            continue

        reminders = compute_medication_reminders(parent.medications)
        due = [r for r in reminders if now <= r["scheduled_time"] <= window_end]

        for reminder in due:
            msg = get_medication_reminder(
                lang=parent.preferred_language,
                medication_name=reminder["medication_name"],
                dosage=reminder["dosage"],
            )
            try:
                await meta_client.send_text(parent.parent_phone, msg)
                logger.info(
                    "Sent medication reminder (%s) to %s",
                    reminder["medication_name"],
                    parent.parent_phone,
                )
            except Exception as e:
                logger.error("Failed to send reminder to %s: %s", parent.parent_phone, e)


async def _weekly_summary_async() -> None:
    from sqlalchemy import select
    from checkup.db.session import async_session
    from checkup.scheduler.models import ParentProfile, HealthLog
    from checkup.scheduler.engine import assess_weekly_trend
    from checkup.language.prompts import WEEKLY_SUMMARY_TEMPLATE
    from checkup.messaging.meta_client import meta_client

    now = datetime.now()
    week_ago = now - timedelta(days=7)

    _trend_notes = {
        "stable": "✅ Everything looks stable this week. Keep it up!",
        "moderate": "🟡 Some days need attention. Please monitor closely.",
        "needs_attention": "🟠 Multiple concerning days this week. Consider a doctor visit.",
        "worsening": "🔴 Health trend is worsening. Please consult a doctor soon.",
        "no_data": "No check-in data was recorded this week.",
    }

    async with async_session() as session:
        result = await session.execute(
            select(ParentProfile).where(ParentProfile.is_active == True)  # noqa: E712
        )
        parents = result.scalars().all()

        for parent in parents:
            if not parent.caregiver_phone:
                continue

            logs_result = await session.execute(
                select(HealthLog)
                .where(HealthLog.parent_id == parent.id)
                .where(HealthLog.timestamp >= week_ago)
                .order_by(HealthLog.timestamp)
            )
            logs = logs_result.scalars().all()

            logs_dicts = [{"risk_level": log.risk_level, "timestamp": log.timestamp} for log in logs]
            trend = assess_weekly_trend(logs_dicts)
            checkin_count = sum(1 for log in logs if log.log_type == "checkin")

            summary = WEEKLY_SUMMARY_TEMPLATE.format(
                parent_name=parent.parent_name,
                start_date=week_ago.strftime("%b %d"),
                end_date=now.strftime("%b %d"),
                checkins_completed=checkin_count,
                meds_confirmed="—",
                meds_total="—",
                high_risk_days=trend["high"],
                medium_risk_days=trend["medium"],
                low_risk_days=trend["low"],
                notes=_trend_notes.get(trend["trend"], ""),
            )

            try:
                await meta_client.send_text(parent.caregiver_phone, summary)
                logger.info("Sent weekly summary for %s", parent.parent_name)
            except Exception as e:
                logger.error("Failed to send weekly summary for %s: %s", parent.parent_name, e)


# ── Celery tasks ──────────────────────────────────────────────────────

@celery_app.task(name="checkup.scheduler.tasks.daily_checkin_scan")
def daily_checkin_scan():
    """Send daily check-in messages to all active parents."""
    logger.info("Running daily check-in scan...")
    asyncio.run(_daily_checkin_scan_async())
    logger.info("Daily check-in scan complete")


@celery_app.task(name="checkup.scheduler.tasks.missed_checkin_alert_scan")
def missed_checkin_alert_scan():
    """Alert caregivers about parents who haven't responded to check-ins."""
    logger.info("Running missed check-in alert scan...")
    asyncio.run(_missed_checkin_alert_scan_async())
    logger.info("Missed check-in alert scan complete")


@celery_app.task(name="checkup.scheduler.tasks.medication_reminder_scan")
def medication_reminder_scan():
    """Send medication reminders to parents whose medication time is approaching."""
    logger.info("Running medication reminder scan...")
    asyncio.run(_medication_reminder_scan_async())
    logger.info("Medication reminder scan complete")


@celery_app.task(name="checkup.scheduler.tasks.weekly_summary")
def weekly_summary():
    """Send weekly health summary to all caregivers."""
    logger.info("Running weekly summary generation...")
    asyncio.run(_weekly_summary_async())
    logger.info("Weekly summary generation complete")
