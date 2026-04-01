from __future__ import annotations

import json
from dataclasses import asdict

from sec_monitor.models import JudgeResult, SecEvent


SYSTEM_PROMPT = (
    "You are an extremely conservative investment filter. "
    "Default to low + ignore. Only escalate if long-term shareholder value could be affected."
)


class ConservativeJudge:
    """MVP judgment layer.

    In production, replace `judge` internals with a Claude API call that returns
    the same strict JSON schema.
    """

    def build_payload(self, event: SecEvent) -> str:
        payload = {
            "company": event.company,
            "type": event.form_type,
            "event": event.event,
            "details": event.details,
        }
        return json.dumps(payload, ensure_ascii=False)

    def judge(self, event: SecEvent) -> JudgeResult:
        # Deterministic fallback for MVP behavior.
        if event.form_type == "Form4" and event.amount_usd is None:
            return JudgeResult(
                importance="medium",
                dimension="leakage",
                reason="Real Form 4 detected; transaction size unavailable in MVP parser.",
                action="watch",
            )

        if event.form_type == "Form4" and (event.amount_usd or 0) >= 2_000_000:
            return JudgeResult(
                importance="high",
                dimension="leakage",
                reason="Large discretionary insider sale may indicate value leakage risk.",
                action="investigate",
            )

        if event.form_type == "8-K" and event.item_code in {"1.01", "5.02", "8.01"}:
            return JudgeResult(
                importance="medium",
                dimension="none",
                reason="Potentially material corporate change worth monitoring.",
                action="watch",
            )

        return JudgeResult(
            importance="low",
            dimension="none",
            reason="No clear long-term shareholder value impact.",
            action="ignore",
        )

    def to_json(self, result: JudgeResult) -> str:
        return json.dumps(asdict(result), ensure_ascii=False)
