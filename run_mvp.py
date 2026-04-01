from __future__ import annotations

import argparse

from sec_monitor.fetcher import MockSecFetcher
from sec_monitor.pipeline import run_pipeline


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run SEC monitor MVP demo")
    parser.add_argument(
        "--ticker",
        default="BABA",
        help="Comma-separated watchlist tickers, default is BABA.",
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    watchlist = {ticker.strip().upper() for ticker in args.ticker.split(",") if ticker.strip()}

    fetcher = MockSecFetcher()
    alerts = run_pipeline(fetcher.fetch(), watchlist=watchlist)

    for alert in alerts:
        if alert.channel == "silent":
            continue
        print(
            f"[{alert.event.ticker}] {alert.event.event} | "
            f"importance={alert.judgment.importance} | "
            f"dimension={alert.judgment.dimension} | "
            f"action={alert.judgment.action} | "
            f"channel={alert.channel}"
        )


if __name__ == "__main__":
    main()
