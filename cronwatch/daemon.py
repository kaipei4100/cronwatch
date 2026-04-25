"""Main daemon loop that ties together scheduling, checking, and notification."""

import logging
import signal
import time
from pathlib import Path
from typing import Optional

from cronwatch.checker import OverdueChecker
from cronwatch.config import AppConfig, load_config
from cronwatch.notifier import Notifier
from cronwatch.store import HeartbeatStore

logger = logging.getLogger(__name__)


class Daemon:
    """Runs the cronwatch monitoring loop."""

    def __init__(self, config: AppConfig, store: HeartbeatStore) -> None:
        self.config = config
        self.store = store
        self.notifier: Optional[Notifier] = (
            Notifier(config.smtp) if config.smtp else None
        )
        self.checker = OverdueChecker(store)
        self._running = False

    def start(self) -> None:
        """Enter the main polling loop."""
        self._running = True
        signal.signal(signal.SIGTERM, self._handle_signal)
        signal.signal(signal.SIGINT, self._handle_signal)
        logger.info("cronwatch daemon started (poll_interval=%ds)", self.config.poll_interval)
        while self._running:
            self._tick()
            time.sleep(self.config.poll_interval)
        logger.info("cronwatch daemon stopped")

    def _tick(self) -> None:
        reports = self.checker.check(self.config.jobs)
        if reports:
            logger.warning("%d overdue job(s) detected", len(reports))
            for r in reports:
                logger.warning("  %s", r)
            if self.notifier:
                self.notifier.send(reports)
        else:
            logger.debug("All jobs on schedule")

    def _handle_signal(self, signum: int, _frame: object) -> None:
        logger.info("Received signal %d, shutting down", signum)
        self._running = False


def run_daemon(config_path: Path) -> None:
    """Convenience entry-point used by the CLI."""
    cfg = load_config(config_path)
    store = HeartbeatStore(cfg.db_path)
    Daemon(cfg, store).start()
