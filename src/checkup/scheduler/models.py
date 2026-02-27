"""SQLAlchemy models for parent profiles, health logs, and reminders."""

from __future__ import annotations

from datetime import date, datetime, time
from typing import Optional

from sqlalchemy import JSON, Boolean, Date, DateTime, ForeignKey, Integer, String, Time
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship


class Base(DeclarativeBase):
    """Base class for all models."""
    pass


class ParentProfile(Base):
    """Elderly parent's health profile."""

    __tablename__ = "parent_profiles"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    parent_phone: Mapped[str] = mapped_column(String(20), unique=True, index=True)
    caregiver_phone: Mapped[str] = mapped_column(String(20), index=True)
    parent_name: Mapped[str] = mapped_column(String(100))
    age: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    known_conditions: Mapped[Optional[dict]] = mapped_column(JSON, default=list)
    medications: Mapped[Optional[dict]] = mapped_column(JSON, default=list)
    preferred_language: Mapped[str] = mapped_column(String(5), default="te")
    checkin_time: Mapped[time] = mapped_column(Time, default=time(9, 0))
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)

    # Relationships
    health_logs: Mapped[list["HealthLog"]] = relationship(back_populates="parent")
    reminders: Mapped[list["ScheduledReminder"]] = relationship(back_populates="parent")


class HealthLog(Base):
    """Log entry from a health check-in or interaction."""

    __tablename__ = "health_logs"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    parent_id: Mapped[int] = mapped_column(ForeignKey("parent_profiles.id"), index=True)
    timestamp: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    log_type: Mapped[str] = mapped_column(String(20))  # "checkin" | "medication" | "alert"
    data: Mapped[Optional[dict]] = mapped_column(JSON, default=dict)
    risk_level: Mapped[str] = mapped_column(String(10), default="low")

    # Relationships
    parent: Mapped["ParentProfile"] = relationship(back_populates="health_logs")


class ScheduledReminder(Base):
    """A scheduled reminder (check-in, medication, or appointment)."""

    __tablename__ = "scheduled_reminders"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    parent_id: Mapped[int] = mapped_column(ForeignKey("parent_profiles.id"), index=True)
    reminder_type: Mapped[str] = mapped_column(String(20))  # "checkin" | "medication" | "appointment"
    scheduled_time: Mapped[datetime] = mapped_column(DateTime)
    sent: Mapped[bool] = mapped_column(Boolean, default=False)
    acknowledged: Mapped[bool] = mapped_column(Boolean, default=False)
    message_id: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    # Relationships
    parent: Mapped["ParentProfile"] = relationship(back_populates="reminders")
