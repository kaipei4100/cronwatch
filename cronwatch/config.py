"""Configuration loader for cronwatch.

Supports TOML config files describing monitored cron jobs and SMTP settings.
"""
from __future__ import annotations

import tomllib
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from cronwatch.notifier import SMTPConfig
from cronwatch.schedule import CronJob


@dataclass
class AppConfig:
    jobs: list[CronJob] = field(default_factory=list)
    smtp: SMTPConfig | None = None
    db_path: str = "cronwatch.db"
    check_interval_seconds: int = 60


def _parse_smtp(raw: dict[str, Any]) -> SMTPConfig:
    return SMTPConfig(
        host=raw["host"],
        port=int(raw.get("port", 587)),
        username=raw["username"],
        password=raw["password"],
        sender=raw["sender"],
        recipients=list(raw["recipients"]),
        use_tls=bool(raw.get("use_tls", True)),
    )


def _parse_job(raw: dict[str, Any]) -> CronJob:
    return CronJob(
        name=raw["name"],
        expression=raw["expression"],
        grace_seconds=int(raw.get("grace_seconds", 300)),
    )


def load_config(path: str | Path) -> AppConfig:
    """Load and validate an AppConfig from a TOML file."""
    path = Path(path)
    if not path.exists():
        raise FileNotFoundError(f"Config file not found: {path}")

    with path.open("rb") as fh:
        raw = tomllib.load(fh)

    jobs = [_parse_job(j) for j in raw.get("jobs", [])]

    smtp: SMTPConfig | None = None
    if "smtp" in raw:
        smtp = _parse_smtp(raw["smtp"])

    return AppConfig(
        jobs=jobs,
        smtp=smtp,
        db_path=str(raw.get("db_path", "cronwatch.db")),
        check_interval_seconds=int(raw.get("check_interval_seconds", 60)),
    )
