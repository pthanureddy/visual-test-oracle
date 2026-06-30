from visual_oracle.consistency import majority_vote


def test_majority_vote_tracks_agreement_and_confidence():
    result = majority_vote(
        [
            {"verdict": "pass", "confidence": 0.8, "reasoning": "ok"},
            {"verdict": "pass", "confidence": 0.9, "reasoning": "still ok"},
            {"verdict": "fail", "confidence": 0.7, "reasoning": "minor issue"},
        ]
    )

    assert result.verdict == "pass"
    assert result.agreement_rate == 2 / 3
    assert round(result.confidence, 2) == 0.85
