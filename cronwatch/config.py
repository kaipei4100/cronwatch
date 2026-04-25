"""Configuration loading for cronwatch."""

from __future__ import annotations

import tomllib
from dataclasses import dataclass, field
from pathlib import Path
from typing import List, Optional

from cronwatch.schedule import CronJob
from cronwatch.notifier import SMTPConfig
from cronwatch.webhook import WebhookConfig


@dataclass
class AppConfig:
    jobs: List[CronJob]
    smtp: Optional[SMTPConfig] = None
    webhook: Optional[WebhookConfig] = None
    check_interval: int = 60
    db_path: str = "cronwatch.db"


def _parse_smtp(section: dict) -> SMTPConfig:
    return SMTPConfig(
        host=section["host"],
        port=int(section.get("port", 587)),
        username=section.get("username", ""),
        password=section.get("password", ""),
        from_addr=section["from"],
        to_addrs=section["to"] if isinstance(section["to"], list) else [section["to"]],
        use_tls=bool(section.get("use_tls", True)),
    )


def _parse_webhook(section: dict) -> WebhookConfig:
    return WebhookConfig(
        url=section["url"],
        timeout=int(section.get("timeout", 10)),
        headers=dict(section.get("headers", {})),
        secret=section.get("secret"),
    )


def _parse_job(name: str, section: dict) -> CronJob:
    return CronJob(
        name=name,
        expression=section["schedule"],
        grace_seconds=int(section.get("grace_seconds", 300)),
    )


def load_config(path: str | Path) -> AppConfig:
    with open(path, "rb") as fh:
        raw = tomllib.load(fh)

    jobs = [
        _parse_job(name, section)
        for name, section in raw.get("jobs", {}).items()
    ]

    smtp = _parse_smtp(raw["smtp"]) if "smtp" in raw else None
    webhook = _parse_webhook(raw["webhook"]) if "webhook" in raw else None

    return AppConfig(
        jobs=jobs,
        smtp=smtp,
        webhook=webhook,
        check_interval=int(raw.get("check_interval", 60)),
        db_path=str(raw.get("db_path", "cronwatch.db")),
    )
