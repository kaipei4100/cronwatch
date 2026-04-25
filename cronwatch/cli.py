"""Command-line interface for cronwatch."""

import argparse
import logging
import sys
from pathlib import Path

from cronwatch.daemon import run_daemon
from cronwatch.config import load_config
from cronwatch.store import HeartbeatStore


def _setup_logging(verbose: bool) -> None:
    level = logging.DEBUG if verbose else logging.INFO
    logging.basicConfig(
        format="%(asctime)s %(levelname)-8s %(name)s: %(message)s",
        datefmt="%Y-%m-%dT%H:%M:%S",
        level=level,
    )


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="cronwatch",
        description="Monitor cron job execution times and alert on missed or slow runs.",
    )
    parser.add_argument("-c", "--config", default="cronwatch.toml", metavar="FILE",
                        help="Path to TOML config file (default: cronwatch.toml)")
    parser.add_argument("-v", "--verbose", action="store_true",
                        help="Enable debug logging")

    sub = parser.add_subparsers(dest="command")

    sub.add_parser("start", help="Start the monitoring daemon")

    heartbeat = sub.add_parser("heartbeat", help="Record a heartbeat for a job")
    heartbeat.add_argument("job_name", help="Name of the cron job")

    sub.add_parser("status", help="Print current job status and exit")
    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    _setup_logging(args.verbose)

    config_path = Path(args.config)

    if args.command == "start":
        run_daemon(config_path)
    elif args.command == "heartbeat":
        cfg = load_config(config_path)
        store = HeartbeatStore(cfg.db_path)
        store.record(args.job_name)
        print(f"Heartbeat recorded for '{args.job_name}'")
    elif args.command == "status":
        from cronwatch.checker import OverdueChecker
        cfg = load_config(config_path)
        store = HeartbeatStore(cfg.db_path)
        checker = OverdueChecker(store)
        reports = checker.check(cfg.jobs)
        if reports:
            for r in reports:
                print(str(r))
            return 1
        print("All jobs on schedule.")
    else:
        parser.print_help()
    return 0


if __name__ == "__main__":
    sys.exit(main())
