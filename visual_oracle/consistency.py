from __future__ import annotations

from collections import Counter
from dataclasses import dataclass
from statistics import mean


@dataclass(frozen=True)
class VoteResult:
    verdict: str
    agreement_rate: float
    confidence: float
    reasons: list[str]


def majority_vote(verdicts: list[dict]) -> VoteResult:
    if not verdicts:
        raise ValueError("majority_vote requires at least one verdict")

    normalized = [
        {
            "verdict": str(v.get("verdict", "fail")).lower(),
            "confidence": float(v.get("confidence", 0.0)),
            "reasoning": str(v.get("reasoning", "")),
        }
        for v in verdicts
    ]
    counts = Counter(v["verdict"] for v in normalized)
    verdict, winner_count = counts.most_common(1)[0]
    matching = [v for v in normalized if v["verdict"] == verdict]
    return VoteResult(
        verdict=verdict,
        agreement_rate=winner_count / len(normalized),
        confidence=mean(v["confidence"] for v in matching),
        reasons=[v["reasoning"] for v in normalized if v["reasoning"]],
    )
