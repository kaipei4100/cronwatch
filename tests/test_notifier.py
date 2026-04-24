"""Tests for cronwatch.notifier."""

from __future__ import annotations

import smtplib
from unittest.mock import MagicMock, patch

import pytest

from cronwatch.checker import OverdueReport
from cronwatch.notifier import Notifier, SMTPConfig
from cronwatch.schedule import CronJob


@pytest.fixture()
def smtp_cfg() -> SMTPConfig:
    return SMTPConfig(host="localhost", port=1025, use_tls=False)


@pytest.fixture()
def notifier(smtp_cfg: SMTPConfig) -> Notifier:
    return Notifier(smtp=smtp_cfg, sender="cronwatch@example.com", recipients=["ops@example.com"])


@pytest.fixture()
def sample_report() -> OverdueReport:
    job = CronJob(name="backup", cron_expr="0 2 * * *", grace_seconds=300)
    return OverdueReport(job=job, seconds_overdue=600)


def test_send_calls_smtp(notifier: Notifier, sample_report: OverdueReport) -> None:
    mock_conn = MagicMock()
    with patch("smtplib.SMTP", return_value=mock_conn.__enter__.return_value) as mock_smtp:
        mock_smtp.return_value.__enter__ = lambda s: mock_conn
        mock_smtp.return_value.__exit__ = MagicMock(return_value=False)
        notifier.send([sample_report])
        mock_smtp.assert_called_once_with("localhost", 1025)


def test_send_no_reports_skips_smtp(notifier: Notifier) -> None:
    with patch("smtplib.SMTP") as mock_smtp:
        notifier.send([])
        mock_smtp.assert_not_called()


def test_send_no_recipients_skips_smtp(smtp_cfg: SMTPConfig, sample_report: OverdueReport) -> None:
    n = Notifier(smtp=smtp_cfg, sender="cronwatch@example.com", recipients=[])
    with patch("smtplib.SMTP") as mock_smtp:
        n.send([sample_report])
        mock_smtp.assert_not_called()


def test_smtp_error_is_propagated(notifier: Notifier, sample_report: OverdueReport) -> None:
    with patch("smtplib.SMTP") as mock_smtp:
        mock_smtp.return_value.__enter__ = MagicMock(side_effect=smtplib.SMTPException("conn error"))
        mock_smtp.return_value.__exit__ = MagicMock(return_value=False)
        with pytest.raises(smtplib.SMTPException):
            notifier.send([sample_report])


def test_message_subject_contains_count(notifier: Notifier, sample_report: OverdueReport) -> None:
    msg = notifier._build_message([sample_report, sample_report])
    assert "2" in msg["Subject"]
    assert "overdue" in msg["Subject"]


def test_message_body_contains_job_name(notifier: Notifier, sample_report: OverdueReport) -> None:
    msg = notifier._build_message([sample_report])
    assert "backup" in msg.get_content()
