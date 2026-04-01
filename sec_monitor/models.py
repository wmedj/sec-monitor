from __future__ import annotations

from dataclasses import dataclass
from typing import Literal, Optional

FormType = Literal["Form4", "8-K"]
Importance = Literal["low", "medium", "high"]
Dimension = Literal["leakage", "distribution", "pricing_power", "none"]
Action = Literal["ignore", "watch", "investigate"]


@dataclass(slots=True)
class SecEvent:
    company: str
    ticker: str
    form_type: FormType
    event: str
    details: str

    # Form 4 fields
    amount_usd: Optional[float] = None
    is_10b5_1: Optional[bool] = None
    insider_role: Optional[str] = None

    # 8-K fields
    item_code: Optional[str] = None


@dataclass(slots=True)
class JudgeResult:
    importance: Importance
    dimension: Dimension
    reason: str
    action: Action


@dataclass(slots=True)
class RoutedAlert:
    event: SecEvent
    judgment: JudgeResult
    channel: Literal["interrupt", "digest", "silent"]
