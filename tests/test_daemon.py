"""Tests for the Daemon class."""

import time
from datetime import datetime, timezone
from unittest.mock import MagicMock, patch

import pytest

from cronwatch.checker import OverdueReport
from cronwatch.config import AppConfig
from cronwatch.daemon import Daemon
from cronwatch.schedule import CronJob


@pytest.fixture()
def app_config(tmp_path):
    job = CronJob(name="backup", schedule="* * * * *", grace_seconds=60)
    return AppConfig(
        jobs=[job],
        db_path=str(tmp_path / "hb.db"),
        poll_interval=5,
        smtp=None,
    )


@pytest.fixture()
def mock_store():
    store = MagicMock()
    store.last_seen.return_value = None
    return store


def test_tick_no_reports_skips_notifier(app_config, mock_store):
    daemon = Daemon(app_config, mock_store)
    daemon.notifier = MagicMock()
    with patch.object(daemon.checker, "check", return_value=[]):
        daemon._tick()
    daemon.notifier.send.assert_not_called()


def test_tick_with_reports_calls_notifier(app_config, mock_store):
    report = OverdueReport(
        job=app_config.jobs[0],
        last_seen=None,
        checked_at=datetime.now(timezone.utc),
    )
    daemon = Daemon(app_config, mock_store)
    daemon.notifier = MagicMock()
    with patch.object(daemon.checker, "check", return_value=[report]):
        daemon._tick()
    daemon.notifier.send.assert_called_once_with([report])


def test_tick_no_notifier_configured_does_not_raise(app_config, mock_store):
    report = OverdueReport(
        job=app_config.jobs[0],
        last_seen=None,
        checked_at=datetime.now(timezone.utc),
    )
    daemon = Daemon(app_config, mock_store)
    assert daemon.notifier is None
    with patch.object(daemon.checker, "check", return_value=[report]):
        daemon._tick()  # should not raise


def test_handle_signal_stops_loop(app_config, mock_store):
    daemon = Daemon(app_config, mock_store)
    daemon._running = True
    daemon._handle_signal(15, None)
    assert daemon._running is False
