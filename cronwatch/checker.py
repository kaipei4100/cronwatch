"""Overdue-job checker that ties together schedule definitions and the store."""

from dataclasses import dataclass
from datetime import datetime
from typing import Optional

from cronwatch.schedule import CronJob
from cronwatch.store import HeartbeatStore


@dataclass
class OverdueReport:
    job: CronJob
    expected_at: datetime
    last_seen: Optional[datetime]
    now: datetime

    @property
    def seconds_overdue(self) -> float:
        deadline = self.expected_at.timestamp() + self.job.grace_seconds
        return max(0.0, self.now.timestamp() - deadline)

    def __str__(self) -> str:
        last = self.last_seen.isoformat() if self.last_seen else "never"
        return (
            f"[OVERDUE] {self.job.name}: expected at {self.expected_at.isoformat()}, "
            f"last seen {last}, overdue by {self.seconds_overdue:.0f}s"
        )


class OverdueChecker:
    """Check a list of CronJob definitions against the heartbeat store."""

    def __init__(self, jobs: list[CronJob], store: HeartbeatStore) -> None:
        self.jobs = jobs
        self.store = store

    def check(self, now: Optional[datetime] = None) -> list[OverdueReport]:
        """Return OverdueReport for every job that is currently overdue."""
        now = now or datetime.utcnow()
        reports: list[OverdueReport] = []
        for job in self.jobs:
            last_seen = self.store.last_seen(job.name)
            if job.is_overdue(last_seen, now):
                reports.append(
                    OverdueReport(
                        job=job,
                        expected_at=job.previous_run(now),
                        last_seen=last_seen,
                        now=now,
                    )
                )
        return reports
