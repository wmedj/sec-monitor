from __future__ import annotations

from typing import Iterable, List, Optional, Set

from sec_monitor.agent import ConservativeJudge
from sec_monitor.filtering import hard_filter
from sec_monitor.models import JudgeResult, RoutedAlert, SecEvent


def route_notification(result: JudgeResult) -> str:
    if result.importance == "high":
        return "interrupt"
    if result.importance == "medium":
        return "digest"
    return "silent"


def run_pipeline(events: Iterable[SecEvent], watchlist: Optional[Set[str]] = None) -> List[RoutedAlert]:
    judge = ConservativeJudge()
    routed: List[RoutedAlert] = []
    normalized_watchlist = {ticker.upper() for ticker in watchlist} if watchlist else None

    for event in hard_filter(events):
        if normalized_watchlist and event.ticker.upper() not in normalized_watchlist:
            continue
        judgment = judge.judge(event)
        channel = route_notification(judgment)
        routed.append(RoutedAlert(event=event, judgment=judgment, channel=channel))

    return routed
