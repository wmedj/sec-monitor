from __future__ import annotations

import json
import os
import urllib.parse
import urllib.request
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from typing import Dict, Iterable, List, Optional, Sequence, Set

from sec_monitor.models import SecEvent

SEC_TICKERS_URL = "https://www.sec.gov/files/company_tickers.json"
SEC_SUBMISSIONS_URL = "https://data.sec.gov/submissions/CIK{cik}.json"
DEFAULT_USER_AGENT = "sec-monitor-mvp/0.1 (research@example.com)"

# Fallback for common watchlist names when ticker lookup endpoint is inaccessible.
FALLBACK_CIK_BY_TICKER = {
    "BABA": ("0001577552", "Alibaba Group Holding Ltd"),
}


@dataclass(slots=True)
class CompanyRef:
    ticker: str
    cik: str
    title: str


class SecApiClient:
    def __init__(self, user_agent: Optional[str] = None) -> None:
        self.user_agent = user_agent or os.getenv("SEC_USER_AGENT", DEFAULT_USER_AGENT)

    def _get_json(self, url: str) -> Dict:
        req = urllib.request.Request(
            url,
            headers={
                "User-Agent": self.user_agent,
                "Accept": "application/json",
                "Accept-Encoding": "gzip, deflate",
            },
        )
        with urllib.request.urlopen(req, timeout=30) as response:
            return json.loads(response.read().decode("utf-8"))

    def get_company_ref(self, ticker: str) -> CompanyRef:
        normalized = ticker.upper()

        try:
            payload = self._get_json(SEC_TICKERS_URL)
            for row in payload.values():
                if row.get("ticker", "").upper() == normalized:
                    return CompanyRef(
                        ticker=row["ticker"],
                        cik=str(row["cik_str"]).zfill(10),
                        title=row["title"],
                    )
        except Exception:
            pass

        fallback = FALLBACK_CIK_BY_TICKER.get(normalized)
        if fallback:
            cik, title = fallback
            return CompanyRef(ticker=normalized, cik=cik, title=title)

        raise ValueError(f"Ticker not found in SEC company list (and no fallback mapping): {ticker}")

    def get_recent_filings(self, cik: str) -> Dict[str, List[str]]:
        url = SEC_SUBMISSIONS_URL.format(cik=cik)
        payload = self._get_json(url)
        return payload.get("filings", {}).get("recent", {})


class RealSecFetcher:
    def __init__(self, client: Optional[SecApiClient] = None) -> None:
        self.client = client or SecApiClient()

    def fetch(self, ticker: str, days: int = 30, forms: Optional[Sequence[str]] = None) -> Iterable[SecEvent]:
        company = self.client.get_company_ref(ticker)
        recent = self.client.get_recent_filings(company.cik)

        wanted_forms: Set[str] = {f.upper() for f in (forms or ("4", "8-K"))}

        forms_col = recent.get("form", [])
        filing_dates = recent.get("filingDate", [])
        primary_docs = recent.get("primaryDocument", [])
        accession_numbers = recent.get("accessionNumber", [])

        cutoff = datetime.now(timezone.utc).date() - timedelta(days=days)

        events: List[SecEvent] = []
        for idx, form in enumerate(forms_col):
            normalized_form = form.upper()
            if normalized_form not in wanted_forms:
                continue

            filing_date = self._safe_date(filing_dates, idx)
            if filing_date and filing_date < cutoff:
                continue

            accession = accession_numbers[idx] if idx < len(accession_numbers) else ""
            primary_doc = primary_docs[idx] if idx < len(primary_docs) else ""
            filing_url = self._build_filing_url(company.cik, accession, primary_doc)

            if normalized_form == "4":
                events.append(
                    SecEvent(
                        company=company.title,
                        ticker=company.ticker,
                        form_type="Form4",
                        event=f"Form 4 filed on {filing_date.isoformat() if filing_date else 'unknown date'}",
                        details=filing_url,
                        amount_usd=None,
                        is_10b5_1=None,
                        insider_role=None,
                    )
                )

            elif normalized_form == "8-K":
                events.append(
                    SecEvent(
                        company=company.title,
                        ticker=company.ticker,
                        form_type="8-K",
                        event=f"8-K filed on {filing_date.isoformat() if filing_date else 'unknown date'}",
                        details=filing_url,
                        item_code="8.01",
                    )
                )

            elif normalized_form == "6-K":
                events.append(
                    SecEvent(
                        company=company.title,
                        ticker=company.ticker,
                        form_type="8-K",
                        event=f"6-K filed on {filing_date.isoformat() if filing_date else 'unknown date'}",
                        details=filing_url,
                        item_code="8.01",
                    )
                )

        return events

    @staticmethod
    def _safe_date(values: List[str], idx: int):
        if idx >= len(values):
            return None
        try:
            return datetime.strptime(values[idx], "%Y-%m-%d").date()
        except (TypeError, ValueError):
            return None

    @staticmethod
    def _build_filing_url(cik: str, accession: str, primary_doc: str) -> str:
        if not accession or not primary_doc:
            return ""
        cleaned = accession.replace("-", "")
        doc = urllib.parse.quote(primary_doc)
        return f"https://www.sec.gov/Archives/edgar/data/{int(cik)}/{cleaned}/{doc}"
