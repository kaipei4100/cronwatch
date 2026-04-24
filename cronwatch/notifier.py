"""Alert notifier for overdue cron job reports."""

from __future__ import annotations

import logging
import smtplib
from dataclasses import dataclass, field
from email.message import EmailMessage
from typing import List, Optional

from cronwatch.checker import OverdueReport

logger = logging.getLogger(__name__)


@dataclass
class SMTPConfig:
    host: str
    port: int = 587
    username: Optional[str] = None
    password: Optional[str] = None
    use_tls: bool = True


@dataclass
class Notifier:
    """Sends e-mail alerts for overdue cron jobs."""

    smtp: SMTPConfig
    sender: str
    recipients: List[str] = field(default_factory=list)

    def _build_message(self, reports: List[OverdueReport]) -> EmailMessage:
        msg = EmailMessage()
        msg["From"] = self.sender
        msg["To"] = ", ".join(self.recipients)
        msg["Subject"] = f"[cronwatch] {len(reports)} overdue job(s) detected"

        lines = ["The following cron jobs are overdue:\n"]
        for report in reports:
            lines.append(f"  • {report}")
        lines.append("\n-- cronwatch")
        msg.set_content("\n".join(lines))
        return msg

    def send(self, reports: List[OverdueReport]) -> None:
        """Send an alert email for the given overdue reports.

        Does nothing if *reports* is empty or *recipients* is empty.
        """
        if not reports:
            logger.debug("No overdue reports; skipping notification.")
            return
        if not self.recipients:
            logger.warning("Notifier has no recipients configured; skipping.")
            return

        msg = self._build_message(reports)
        try:
            with smtplib.SMTP(self.smtp.host, self.smtp.port) as conn:
                if self.smtp.use_tls:
                    conn.starttls()
                if self.smtp.username and self.smtp.password:
                    conn.login(self.smtp.username, self.smtp.password)
                conn.send_message(msg)
            logger.info("Alert sent to %s for %d report(s).", self.recipients, len(reports))
        except smtplib.SMTPException as exc:
            logger.error("Failed to send alert: %s", exc)
            raise
