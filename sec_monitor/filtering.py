from __future__ import annotations

from typing import Iterable, Iterator

from sec_monitor.models import SecEvent

FORM4_MIN_AMOUNT = 500_000
FORM4_ALLOWED_ROLES = {"CEO", "CFO", "Director"}
FORM8K_ALLOWED_ITEMS = {"1.01", "2.02", "5.02", "8.01"}


def hard_filter(events: Iterable[SecEvent]) -> Iterator[SecEvent]:
    """Rule layer to remove the majority of noise before LLM judgment."""
    for event in events:
        if event.form_type == "Form4":
            # For real SEC feed MVP, many Form 4 details are unknown until XML parsing is added.
            if event.amount_usd is None and event.is_10b5_1 is None and event.insider_role is None:
                yield event
                continue

            if event.is_10b5_1:
                continue
            if (event.amount_usd or 0) < FORM4_MIN_AMOUNT:
                continue
            if (event.insider_role or "") not in FORM4_ALLOWED_ROLES:
                continue
            yield event
            continue

        if event.form_type == "8-K":
            if (event.item_code or "") not in FORM8K_ALLOWED_ITEMS:
                continue
            yield event
