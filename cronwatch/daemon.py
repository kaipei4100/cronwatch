"""Cronwatch daemon — periodically checks for overdue jobs and fires alerts."""

from __future__ import annotations

import logging
import signal
import time
from typing import Optional

from cronwatch.checker import OverdueChecker
from cronwatch.config import AppConfig
from cronwatch.notifier import Notifier
from cronwatch.store import HeartbeatStore
from cronwatch.webhook import WebhookNotifier

log = logging.getLogger(__name__)


class Daemon:
    def __init__(
        self,
        cfg: AppConfig,
        store: HeartbeatStore,
        notifier: Optional[Notifier] = None,
        webhook: Optional[WebhookNotifier] = None,
    ) -> None:
        self._cfg = cfg
        self._store = store
        self._notifier = notifier
        self._webhook = webhook
        self._running = False

    def start(self) -> None:
        log.info("Cronwatch daemon starting (interval=%ds).", self._cfg.check_interval)
        self._running = True
        signal.signal(signal.SIGTERM, self._handle_signal)
        signal.signal(signal.SIGINT, self._handle_signal)
        while self._running:
            self._tick()
            time.sleep(self._cfg.check_interval)

    def _tick(self) -> None:
        checker = OverdueChecker(self._cfg.jobs, self._store)
        reports = checker.check_all()
        if not reports:
            log.debug("All jobs on time.")
            return
        for r in reports:
            log.warning("%s", r)
        if self._notifier:
            self._notifier.send(reports)
        if self._webhook:
            self._webhook.send(reports)

    def _handle_signal(self, signum: int, _frame: object) -> None:
        log.info("Signal %d received — stopping.", signum)
        self._running = False

    def stop(self) -> None:
        self._running = False
