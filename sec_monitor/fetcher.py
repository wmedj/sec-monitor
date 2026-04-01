from __future__ import annotations

from typing import Iterable

from sec_monitor.models import SecEvent


class MockSecFetcher:
    """MVP fetcher placeholder. Replace with SEC API ingestion."""

    def fetch(self) -> Iterable[SecEvent]:
        return [
            SecEvent(
                company="Alibaba Group",
                ticker="BABA",
                form_type="8-K",
                event="Major partnership disclosure",
                details="Company filed Item 1.01 regarding a material strategic agreement.",
                item_code="1.01",
            ),
            SecEvent(
                company="Alibaba Group",
                ticker="BABA",
                form_type="Form4",
                event="Director sold $900k shares",
                details="Open market discretionary sale not under 10b5-1.",
                amount_usd=900_000,
                is_10b5_1=False,
                insider_role="Director",
            ),
            SecEvent(
                company="Qifu Technology",
                ticker="QFIN",
                form_type="Form4",
                event="CEO sold $3M shares",
                details="Open market sale not filed under 10b5-1 plan.",
                amount_usd=3_000_000,
                is_10b5_1=False,
                insider_role="CEO",
            ),
            SecEvent(
                company="Noise Corp",
                ticker="NOS",
                form_type="8-K",
                event="Minor disclosure",
                details="Unrelated filing outside monitored items.",
                item_code="3.01",
            ),
        ]
