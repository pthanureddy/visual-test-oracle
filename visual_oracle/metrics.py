from __future__ import annotations

from statistics import mean
from typing import Any


def safe_rate(numerator: int, denominator: int) -> float:
    return numerator / denominator if denominator else 0.0


def summarize(results: list[dict[str, Any]]) -> dict[str, Any]:
    clean = [r for r in results if r["bug"] == "clean" and r["variant"] == "default"]
    mutants = [r for r in results if r["expected_verdict"] == "fail"]
    benign = [r for r in results if r["expected_verdict"] == "pass" and r["variant"] != "default"]
    healing_success = [
        r
        for r in results
        if r.get("healing_events")
        and r["actual_verdict"] == "pass"
        and any(event.get("method") != "self-heal-failed" for event in r["healing_events"])
    ]

    detected = sum(1 for r in mutants if r["actual_verdict"] == "fail")
    false_positive = sum(1 for r in clean if r["actual_verdict"] == "fail")
    benign_passed = sum(1 for r in benign if r["actual_verdict"] == "pass")

    latencies = [
        vote.get("latency_seconds", 0.0)
        for result in results
        for vote in result.get("votes", [])
    ]
    return {
        "total_cases": len(results),
        "bug_detection_rate": safe_rate(detected, len(mutants)),
        "false_positive_rate": safe_rate(false_positive, len(clean)),
        "maintenance_resilience": safe_rate(benign_passed, len(benign)),
        "self_healing_successes": len(healing_success),
        "mean_agreement_rate": mean(r["agreement_rate"] for r in results) if results else 0.0,
        "mean_latency_seconds": mean(latencies) if latencies else 0.0,
        "estimated_cost_usd": sum(
            vote.get("cost_usd", 0.0)
            for result in results
            for vote in result.get("votes", [])
        ),
    }
