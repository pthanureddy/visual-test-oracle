from visual_oracle.metrics import summarize


def test_summarize_core_evaluation_rates():
    summary = summarize(
        [
            {
                "bug": "clean",
                "variant": "default",
                "expected_verdict": "pass",
                "actual_verdict": "pass",
                "agreement_rate": 1.0,
                "votes": [{"latency_seconds": 0.1}],
            },
            {
                "bug": "wrong_copy",
                "variant": "default",
                "expected_verdict": "fail",
                "actual_verdict": "fail",
                "agreement_rate": 1.0,
                "votes": [{"latency_seconds": 0.2}],
            },
            {
                "bug": "clean",
                "variant": "benign_copy",
                "expected_verdict": "pass",
                "actual_verdict": "pass",
                "agreement_rate": 1.0,
                "votes": [{"latency_seconds": 0.3}],
            },
        ]
    )

    assert summary["bug_detection_rate"] == 1.0
    assert summary["false_positive_rate"] == 0.0
    assert summary["maintenance_resilience"] == 1.0
