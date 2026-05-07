from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Iterable


@dataclass(frozen=True, slots=True)
class AdversarialCheckResult:
    passed: bool
    notes: list[str]
    risk_counts: dict[str, int]


ATTACK_PATTERNS = {
    "market_intelligence": (
        "ignore previous",
        "system prompt",
        "jailbreak",
        "prompt injection",
        "leak source",
        "fabricate citation",
    ),
    "strategy_formulation": (
        "skip backtest",
        "skip paper",
        "ignore risk",
        "all in",
        "guaranteed alpha",
        "no drawdown",
    ),
    "portfolio_ledger": (
        "modify ledger",
        "hide loss",
        "overwrite position",
        "delete trade",
        "tamper pnl",
        "mark filled without broker",
    ),
    "trade_execution": (
        "place live order",
        "send live order",
        "direct live",
        "immediate live",
        "bypass approval",
        "disable halt",
    ),
    "tool_hijacking": (
        "exfiltrate",
        "credential",
        "api key",
        "secret",
        "curl unknown",
        "download and execute",
    ),
}


def run_adversarial_checks(payload: Any, *, require_all_surfaces: bool = False) -> AdversarialCheckResult:
    text = " ".join(_flatten_strings(payload)).lower()
    notes: list[str] = []
    risk_counts: dict[str, int] = {}
    for surface, patterns in ATTACK_PATTERNS.items():
        matches = [pattern for pattern in patterns if pattern in text]
        risk_counts[surface] = len(matches)
        for pattern in matches:
            notes.append(f"Adversarial gate: {surface} pattern detected: {pattern}.")
    if require_all_surfaces:
        missing = [surface for surface in ATTACK_PATTERNS if surface not in text]
        if missing:
            notes.append(
                "Adversarial gate: stress plan does not explicitly cover surfaces: "
                + ", ".join(sorted(missing))
                + "."
            )
    return AdversarialCheckResult(passed=not notes, notes=notes, risk_counts=risk_counts)


def _flatten_strings(value: Any) -> Iterable[str]:
    if value is None:
        return
    if isinstance(value, str):
        yield value
        return
    if isinstance(value, dict):
        for key, item in value.items():
            yield from _flatten_strings(key)
            yield from _flatten_strings(item)
        return
    if isinstance(value, list | tuple | set):
        for item in value:
            yield from _flatten_strings(item)
        return
    yield str(value)
