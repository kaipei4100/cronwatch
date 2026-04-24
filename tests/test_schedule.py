"""Unit tests for cronwatch.schedule."""

from datetime import datetime, timedelta

import pytest

from cronwatch.schedule import CronJob


EVERY_MINUTE = "* * * * *"
HOURLY = "0 * * * *"


def test_invalid_expression_raises() -> None:
    with pytest.raises(ValueError, match="Invalid cron expression"):
        CronJob(name="bad", schedule="not-a-cron")


def test_next_run_is_in_the_future() -> None:
    job = CronJob(name="j", schedule=EVERY_MINUTE)
    now = datetime(2024, 1, 1, 12, 0, 0)
    nxt = job.next_run(after=now)
    assert nxt > now


def test_previous_run_is_in_the_past() -> None:
    job = CronJob(name="j", schedule=EVERY_MINUTE)
    now = datetime(2024, 1, 1, 12, 5, 30)
    prev = job.previous_run(before=now)
    assert prev < now


def test_not_overdue_when_recently_seen() -> None:
    job = CronJob(name="j", schedule=EVERY_MINUTE, grace_seconds=60)
    now = datetime(2024, 1, 1, 12, 1, 10)
    # previous run was at 12:01:00; last_seen also at 12:01:00 → not overdue
    last_seen = datetime(2024, 1, 1, 12, 1, 0)
    assert not job.is_overdue(last_seen, now)


def test_overdue_when_never_seen_and_past_grace() -> None:
    job = CronJob(name="j", schedule=EVERY_MINUTE, grace_seconds=30)
    # previous run was at 12:00:00; now is 12:00:31 → past grace, never seen
    now = datetime(2024, 1, 1, 12, 0, 31)
    assert job.is_overdue(last_seen=None, now=now)


def test_not_overdue_within_grace_window() -> None:
    job = CronJob(name="j", schedule=EVERY_MINUTE, grace_seconds=60)
    # previous run was at 12:00:00; now is 12:00:45 → still inside grace
    now = datetime(2024, 1, 1, 12, 0, 45)
    assert not job.is_overdue(last_seen=None, now=now)
