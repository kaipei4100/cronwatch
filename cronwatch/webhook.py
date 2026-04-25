"""Webhook notifier for cronwatch — sends overdue reports via HTTP POST."""

from __future__ import annotations

import json
import logging
import urllib.error
import urllib.request
from dataclasses import dataclass, field
from typing import List, Optional

from cronwatch.checker import OverdueReport

log = logging.getLogger(__name__)


@dataclass
class WebhookConfig:
    url: str
    timeout: int = 10
    headers: dict = field(default_factory=dict)
    secret: Optional[str] = None


class WebhookNotifier:
    """Send overdue-job reports to an HTTP webhook endpoint."""

    def __init__(self, cfg: WebhookConfig) -> None:
        self._cfg = cfg

    def _build_payload(self, reports: List[OverdueReport]) -> bytes:
        items = [
            {
                "job": r.job_name,
                "seconds_overdue": r.seconds_overdue,
                "summary": str(r),
            }
            for r in reports
        ]
        return json.dumps({"alerts": items}).encode("utf-8")

    def send(self, reports: List[OverdueReport]) -> None:
        if not reports:
            log.debug("No overdue reports — skipping webhook.")
            return

        payload = self._build_payload(reports)
        headers = {"Content-Type": "application/json", **self._cfg.headers}
        if self._cfg.secret:
            headers["X-Cronwatch-Secret"] = self._cfg.secret

        req = urllib.request.Request(
            self._cfg.url,
            data=payload,
            headers=headers,
            method="POST",
        )
        try:
            with urllib.request.urlopen(req, timeout=self._cfg.timeout) as resp:
                log.info("Webhook delivered — HTTP %s", resp.status)
        except urllib.error.HTTPError as exc:
            log.error("Webhook HTTP error: %s %s", exc.code, exc.reason)
        except urllib.error.URLError as exc:
            log.error("Webhook URL error: %s", exc.reason)
