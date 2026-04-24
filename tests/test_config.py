"""Tests for cronwatch.config — config loading from TOML."""
from __future__ import annotations

import textwrap
from pathlib import Path

import pytest

from cronwatch.config import AppConfig, load_config


@pytest.fixture()
def config_file(tmp_path: Path) -> Path:
    content = textwrap.dedent("""\
        db_path = "test.db"
        check_interval_seconds = 30

        [[jobs]]
        name = "daily-backup"
        expression = "0 2 * * *"
        grace_seconds = 600

        [[jobs]]
        name = "hourly-sync"
        expression = "0 * * * *"

        [smtp]
        host = "smtp.example.com"
        port = 587
        username = "user@example.com"
        password = "secret"
        sender = "alerts@example.com"
        recipients = ["ops@example.com", "dev@example.com"]
        use_tls = true
    """)
    p = tmp_path / "cronwatch.toml"
    p.write_text(content)
    return p


def test_load_returns_app_config(config_file: Path) -> None:
    cfg = load_config(config_file)
    assert isinstance(cfg, AppConfig)


def test_jobs_are_parsed(config_file: Path) -> None:
    cfg = load_config(config_file)
    assert len(cfg.jobs) == 2
    names = {j.name for j in cfg.jobs}
    assert names == {"daily-backup", "hourly-sync"}


def test_job_grace_seconds_default(config_file: Path) -> None:
    cfg = load_config(config_file)
    hourly = next(j for j in cfg.jobs if j.name == "hourly-sync")
    assert hourly.grace_seconds == 300  # default


def test_job_grace_seconds_explicit(config_file: Path) -> None:
    cfg = load_config(config_file)
    backup = next(j for j in cfg.jobs if j.name == "daily-backup")
    assert backup.grace_seconds == 600


def test_smtp_is_parsed(config_file: Path) -> None:
    cfg = load_config(config_file)
    assert cfg.smtp is not None
    assert cfg.smtp.host == "smtp.example.com"
    assert cfg.smtp.recipients == ["ops@example.com", "dev@example.com"]


def test_top_level_settings(config_file: Path) -> None:
    cfg = load_config(config_file)
    assert cfg.db_path == "test.db"
    assert cfg.check_interval_seconds == 30


def test_missing_file_raises(tmp_path: Path) -> None:
    with pytest.raises(FileNotFoundError):
        load_config(tmp_path / "nonexistent.toml")


def test_no_smtp_section(tmp_path: Path) -> None:
    p = tmp_path / "minimal.toml"
    p.write_text('[[jobs]]\nname = "j"\nexpression = "* * * * *"\n')
    cfg = load_config(p)
    assert cfg.smtp is None
