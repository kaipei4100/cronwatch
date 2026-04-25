"""Tests for the WebhookNotifier."""

from __future__ import annotations

import json
from unittest.mock import MagicMock, patch

import pytest

from cronwatch.checker import OverdueReport
from cronwatch.webhook import WebhookConfig, WebhookNotifier


@pytest.fixture()
def cfg() -> WebhookConfig:
    return WebhookConfig(
        url="https://hooks.example.com/test",
        timeout=5,
        secret="tok3n",
    )


@pytest.fixture()
def notifier(cfg: WebhookConfig) -> WebhookNotifier:
    return WebhookNotifier(cfg)


@pytest.fixture()
def sample_reports() -> list[OverdueReport]:
    return [
        OverdueReport(job_name="daily-backup", seconds_overdue=900),
        OverdueReport(job_name="hourly-sync", seconds_overdue=300),
    ]


def test_send_no_reports_skips_urlopen(notifier: WebhookNotifier) -> None:
    with patch("urllib.request.urlopen") as mock_open:
        notifier.send([])
        mock_open.assert_not_called()


def test_send_calls_urlopen_with_post(notifier: WebhookNotifier, sample_reports: list) -> None:
    mock_resp = MagicMock()
    mock_resp.__enter__ = lambda s: s
    mock_resp.__exit__ = MagicMock(return_value=False)
    mock_resp.status = 200
    with patch("urllib.request.urlopen", return_value=mock_resp) as mock_open:
        notifier.send(sample_reports)
        mock_open.assert_called_once()
        req = mock_open.call_args[0][0]
        assert req.method == "POST"
        assert req.full_url == "https://hooks.example.com/test"


def test_send_payload_contains_all_jobs(notifier: WebhookNotifier, sample_reports: list) -> None:
    mock_resp = MagicMock()
    mock_resp.__enter__ = lambda s: s
    mock_resp.__exit__ = MagicMock(return_value=False)
    mock_resp.status = 200
    with patch("urllib.request.urlopen", return_value=mock_resp):
        notifier.send(sample_reports)

    payload = json.loads(notifier._build_payload(sample_reports))
    job_names = [a["job"] for a in payload["alerts"]]
    assert "daily-backup" in job_names
    assert "hourly-sync" in job_names


def test_send_includes_secret_header(notifier: WebhookNotifier, sample_reports: list) -> None:
    mock_resp = MagicMock()
    mock_resp.__enter__ = lambda s: s
    mock_resp.__exit__ = MagicMock(return_value=False)
    mock_resp.status = 200
    with patch("urllib.request.urlopen", return_value=mock_resp) as mock_open:
        notifier.send(sample_reports)
        req = mock_open.call_args[0][0]
        assert req.get_header("X-cronwatch-secret") == "tok3n"


def test_send_handles_http_error_gracefully(notifier: WebhookNotifier, sample_reports: list) -> None:
    import urllib.error
    with patch("urllib.request.urlopen", side_effect=urllib.error.HTTPError(
        url="", code=500, msg="Server Error", hdrs=None, fp=None
    )):
        notifier.send(sample_reports)  # should not raise


def test_send_handles_url_error_gracefully(notifier: WebhookNotifier, sample_reports: list) -> None:
    import urllib.error
    with patch("urllib.request.urlopen", side_effect=urllib.error.URLError("connection refused")):
        notifier.send(sample_reports)  # should not raise
