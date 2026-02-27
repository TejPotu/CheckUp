"""Tests for the scheduling engine."""

from datetime import datetime, timedelta

from checkup.scheduler.engine import (
    assess_weekly_trend,
    compute_medication_reminders,
    compute_missed_checkin_alert,
)


class TestMedicationReminders:
    """Tests for compute_medication_reminders()."""

    def test_future_reminders_only(self):
        """Should only return reminders for future times."""
        meds = [{"name": "Metformin", "dosage": "500mg", "times": ["23:59"]}]
        reminders = compute_medication_reminders(meds)
        # 23:59 should almost always be in the future unless test runs at 23:59
        if datetime.now().hour < 23:
            assert len(reminders) >= 1
            assert reminders[0]["medication_name"] == "Metformin"

    def test_empty_medications(self):
        """Should return empty list for no medications."""
        assert compute_medication_reminders([]) == []

    def test_multiple_medications(self):
        """Should handle multiple medications with multiple times."""
        meds = [
            {"name": "Med A", "dosage": "100mg", "times": ["23:58"]},
            {"name": "Med B", "dosage": "200mg", "times": ["23:59"]},
        ]
        reminders = compute_medication_reminders(meds)
        if datetime.now().hour < 23:
            assert len(reminders) == 2


class TestWeeklyTrend:
    """Tests for assess_weekly_trend()."""

    def test_stable_trend(self):
        """All low risk should be stable."""
        logs = [{"risk_level": "low"} for _ in range(7)]
        result = assess_weekly_trend(logs)
        assert result["trend"] == "stable"
        assert result["low"] == 7

    def test_worsening_trend(self):
        """Two or more high-risk days should be worsening."""
        logs = [
            {"risk_level": "high"},
            {"risk_level": "high"},
            {"risk_level": "low"},
        ]
        result = assess_weekly_trend(logs)
        assert result["trend"] == "worsening"

    def test_needs_attention(self):
        """One high or 4+ medium should need attention."""
        logs = [{"risk_level": "high"}] + [{"risk_level": "low"} for _ in range(6)]
        result = assess_weekly_trend(logs)
        assert result["trend"] == "needs_attention"

    def test_no_data(self):
        """Empty logs should return no_data."""
        result = assess_weekly_trend([])
        assert result["trend"] == "no_data"


class TestMissedCheckin:
    """Tests for compute_missed_checkin_alert()."""

    def test_no_checkin_today(self):
        """Should alert if no check-in recorded today and threshold passed."""
        yesterday = datetime.now() - timedelta(days=1)
        # Force the check by using a checkin_hour that has passed
        result = compute_missed_checkin_alert(
            last_checkin_time=yesterday,
            checkin_hour=0,  # midnight, already passed
            threshold_hours=0,
        )
        assert result is True

    def test_checkin_received_today(self):
        """Should not alert if check-in was received today."""
        now = datetime.now()
        result = compute_missed_checkin_alert(
            last_checkin_time=now,
            checkin_hour=0,
            threshold_hours=0,
        )
        assert result is False

    def test_no_previous_checkin(self):
        """Should alert if no check-in ever recorded and threshold passed."""
        result = compute_missed_checkin_alert(
            last_checkin_time=None,
            checkin_hour=0,
            threshold_hours=0,
        )
        assert result is True
