"""Cron schedule parsing and next-run calculation."""

from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional

try:
    from croniter import croniter
except ImportError as exc:  # pragma: no cover
    raise ImportError("croniter is required: pip install croniter") from exc


@dataclass
class CronJob:
    """Represents a monitored cron job definition."""

    name: str
    schedule: str  # standard 5-field cron expression
    timeout_seconds: int = 300  # alert if job hasn't run within this window
    grace_seconds: int = 60    # allow this many seconds past expected start
    tags: list[str] = field(default_factory=list)

    def __post_init__(self) -> None:
        if not croniter.is_valid(self.schedule):
            raise ValueError(f"Invalid cron expression for job '{self.name}': {self.schedule!r}")

    def next_run(self, after: Optional[datetime] = None) -> datetime:
        """Return the next scheduled datetime after *after* (default: now)."""
        base = after or datetime.utcnow()
        return croniter(self.schedule, base).get_next(datetime)

    def previous_run(self, before: Optional[datetime] = None) -> datetime:
        """Return the most recent scheduled datetime before *before* (default: now)."""
        base = before or datetime.utcnow()
        return croniter(self.schedule, base).get_prev(datetime)

    def is_overdue(self, last_seen: Optional[datetime], now: Optional[datetime] = None) -> bool:
        """Return True when the job is past its grace window and hasn't been seen."""
        now = now or datetime.utcnow()
        expected = self.previous_run(now)
        deadline = expected.timestamp() + self.grace_seconds
        if last_seen is not None and last_seen.timestamp() >= expected.timestamp():
            return False
        return now.timestamp() > deadline
