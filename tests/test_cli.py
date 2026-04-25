"""Tests for the CLI entry-point."""

from pathlib import Path
from unittest.mock import patch, MagicMock

import pytest

from cronwatch.cli import main, build_parser


MINIMAL_TOML = """
poll_interval = 30

[[jobs]]
name = "test_job"
schedule = "*/5 * * * *"
"""


@pytest.fixture()
def config_file(tmp_path):
    p = tmp_path / "cronwatch.toml"
    p.write_text(MINIMAL_TOML)
    return p


def test_parser_defaults():
    parser = build_parser()
    args = parser.parse_args([])
    assert args.config == "cronwatch.toml"
    assert args.verbose is False


def test_heartbeat_command(config_file):
    with patch("cronwatch.cli.HeartbeatStore") as MockStore:
        instance = MockStore.return_value
        result = main(["-c", str(config_file), "heartbeat", "test_job"])
    instance.record.assert_called_once_with("test_job")
    assert result == 0


def test_status_all_ok(config_file):
    with patch("cronwatch.cli.OverdueChecker") as MockChecker:
        MockChecker.return_value.check.return_value = []
        result = main(["-c", str(config_file), "status"])
    assert result == 0


def test_status_overdue_returns_nonzero(config_file):
    mock_report = MagicMock()
    mock_report.__str__ = lambda self: "backup is overdue"
    with patch("cronwatch.cli.OverdueChecker") as MockChecker:
        MockChecker.return_value.check.return_value = [mock_report]
        result = main(["-c", str(config_file), "status"])
    assert result == 1


def test_no_command_prints_help(config_file, capsys):
    result = main(["-c", str(config_file)])
    captured = capsys.readouterr()
    assert "usage" in captured.out.lower() or result == 0


def test_start_delegates_to_run_daemon(config_file):
    with patch("cronwatch.cli.run_daemon") as mock_run:
        main(["-c", str(config_file), "start"])
    mock_run.assert_called_once_with(config_file)
