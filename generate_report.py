from __future__ import annotations

import argparse
from datetime import datetime, timezone
from pathlib import Path

from sec_monitor.pipeline import run_pipeline
from sec_monitor.sec_fetcher import RealSecFetcher


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Generate SEC monitor report from real SEC data")
    parser.add_argument("--ticker", default="BABA", help="Single ticker to monitor, default BABA")
    parser.add_argument("--days", type=int, default=30, help="Lookback days, default 30")
    parser.add_argument(
        "--forms",
        default="4,8-K,6-K",
        help="Comma-separated SEC forms to pull from submissions feed, default 4,8-K,6-K",
    )
    parser.add_argument(
        "--out",
        default="reports/latest_report.md",
        help="Output markdown report path",
    )
    return parser.parse_args()


def _header(ticker: str, days: int, forms: list[str]) -> list[str]:
    now = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")
    return [
        f"# SEC Monitor Report - {ticker.upper()}",
        "",
        f"Generated: {now}",
        f"Lookback window: last {days} days",
        f"Forms: {', '.join(forms)}",
    ]


def render_report(ticker: str, days: int, forms: list[str]) -> str:
    fetcher = RealSecFetcher()

    try:
        events = list(fetcher.fetch(ticker=ticker, days=days, forms=forms))
    except Exception as exc:  # network/proxy restrictions are common in CI/sandbox
        lines = _header(ticker=ticker, days=days, forms=forms)
        lines.extend(
            [
                "",
                "## Status",
                "- Failed to fetch real SEC data in current runtime environment.",
                f"- Error: `{type(exc).__name__}: {exc}`",
                "",
                "## Next step",
                "- Re-run where sec.gov is reachable, with `SEC_USER_AGENT` set to your app/email.",
            ]
        )
        return "\n".join(lines) + "\n"

    alerts = run_pipeline(events, watchlist={ticker})
    lines = _header(ticker=ticker, days=days, forms=forms)
    lines.extend(
        [
            f"Fetched events: {len(events)}",
            f"Routed alerts: {len(alerts)}",
            "",
            "## Alerts",
        ]
    )

    if not alerts:
        lines.append("- No qualifying events in this window.")
        return "\n".join(lines) + "\n"

    for alert in alerts:
        lines.extend(
            [
                f"- **{alert.event.form_type}** | {alert.event.event}",
                f"  - company: {alert.event.company}",
                f"  - ticker: {alert.event.ticker}",
                f"  - importance: {alert.judgment.importance}",
                f"  - dimension: {alert.judgment.dimension}",
                f"  - action: {alert.judgment.action}",
                f"  - route: {alert.channel}",
                f"  - reason: {alert.judgment.reason}",
                f"  - filing_link: {alert.event.details or 'N/A'}",
            ]
        )

    return "\n".join(lines) + "\n"


def main() -> None:
    args = parse_args()
    forms = [item.strip().upper() for item in args.forms.split(",") if item.strip()]
    report_text = render_report(ticker=args.ticker, days=args.days, forms=forms)
    out_path = Path(args.out)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(report_text, encoding="utf-8")
    print(f"Report written to {out_path}")


if __name__ == "__main__":
    main()
