# cronwatch

Lightweight daemon that monitors cron job execution times and sends alerts on missed or slow runs.

---

## Installation

```bash
pip install cronwatch
```

Or install from source:

```bash
git clone https://github.com/youruser/cronwatch.git && cd cronwatch && pip install .
```

---

## Usage

Start the daemon by pointing it at a configuration file:

```bash
cronwatch --config /etc/cronwatch/config.yaml
```

Example `config.yaml`:

```yaml
jobs:
  - name: daily-backup
    schedule: "0 2 * * *"
    timeout: 300        # seconds before a "slow" alert fires
    grace: 60           # seconds after scheduled time before a "missed" alert fires

alerts:
  email:
    to: ops@example.com
    from: cronwatch@example.com
    smtp: smtp.example.com
```

Once running, cronwatch listens for heartbeat pings from your cron jobs:

```bash
# Add to the end of your cron script
curl -sf "http://localhost:8731/ping/daily-backup" || true
```

If a ping is not received within the configured grace period, or takes longer than the timeout, an alert is dispatched to the configured channel.

### CLI Reference

| Command | Description |
|---|---|
| `cronwatch start` | Start the daemon |
| `cronwatch stop` | Stop the daemon |
| `cronwatch status` | Show status of all monitored jobs |
| `cronwatch test-alert` | Send a test alert to verify configuration |

---

## License

MIT © 2024 cronwatch contributors