"""Integration tests for HeartbeatStore and OverdueChecker."""

from datetime import datetime, timedelta
from pathlib import Path

import pytest

from cronwatch.checker import OverdueChecker
from cronwatch.schedule import CronJob
from cronwatch.store import HeartbeatStore


@pytest.fixture()
def store(tmp_path: Path) -> HeartbeatStore:
    return HeartbeatStore(db_path=tmp_path / "test.db")


def test_record_and_retrieve(store: HeartbeatStore) -> None:
    ts = datetime(2024, 6, 1, 10, 0, 0)
    store.record("backup", ts)
    assert store.last_seen("backup") == ts


def test_last_seen_unknown_job_returns_none(store: HeartbeatStore) -> None:
    assert store.last_seen("ghost") is None


def test_record_updates_existing(store: HeartbeatStore) -> None:
    t1 = datetime(2024, 6, 1, 10, 0, 0)
    t2 = datetime(2024, 6, 1, 11, 0, 0)
    store.record("backup", t1)
    store.record("backup", t2)
    assert store.last_seen("backup") == t2


def test_checker_reports_overdue_job(store: HeartbeatStore) -> None:
    job = CronJob(name="minutely", schedule="* * * * *", grace_seconds=30)
    checker = OverdueChecker(jobs=[job], store=store)
    # job never recorded; check well past grace
    now = datetime(2024, 1, 1, 12, 1, 45)
    reports = checker.check(now=now)
    assert len(reports) == 1
    assert reports[0].job.name == "minutely"
    assert reports[0].last_seen is None


def test_checker_no_report_when_job_seen(store: HeartbeatStore) -> None:
    job = CronJob(name="minutely", schedule="* * * * *", grace_seconds=60)
    checker = OverdueChecker(jobs=[job], store=store)
    now = datetime(2024, 1, 1, 12, 1, 10)
    # record heartbeat at the expected minute
    store.record("minutely", datetime(2024, 1, 1, 12, 1, 0))
    reports = checker.check(now=now)
    assert reports == []
