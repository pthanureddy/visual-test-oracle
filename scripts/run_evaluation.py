from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from visual_oracle.mutations import BENIGN_VARIANTS, MUTATIONS
from visual_oracle.report_generator import generate_report
from visual_oracle.runner import run_spec_case, write_results
from visual_oracle.specs import load_specs


def build_cases(provider: str, include_ollama: bool) -> list[dict]:
    specs = {spec.test_id: spec for spec in load_specs(ROOT / "tests" / "specs")}
    cases: list[dict] = []
    main = specs["checkout_success_state"]
    total = specs["checkout_total_state"]
    healing = specs["selector_healing_checkout"]

    cases.append({"spec": main, "bug": "clean", "variant": "default", "expected": "pass", "provider": provider})
    cases.append({"spec": total, "bug": "clean", "variant": "default", "expected": "pass", "provider": provider})

    for mutation in MUTATIONS:
        spec = total if mutation in {"missing_total", "wrong_currency"} else main
        cases.append({"spec": spec, "bug": mutation, "variant": "default", "expected": "fail", "provider": provider})

    for variant in BENIGN_VARIANTS:
        cases.append({"spec": main, "bug": "clean", "variant": variant, "expected": "pass", "provider": provider})

    cases.append({"spec": healing, "bug": "clean", "variant": "renamed_selector", "expected": "pass", "provider": provider})

    if include_ollama:
        cases.append({"spec": main, "bug": "clean", "variant": "default", "expected": "pass", "provider": "ollama"})
        cases.append({"spec": main, "bug": "wrong_copy", "variant": "default", "expected": "fail", "provider": "ollama"})

    return cases


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--provider", default="heuristic", choices=["heuristic", "openai"])
    parser.add_argument("--include-ollama", action="store_true")
    parser.add_argument("--k", type=int, default=3)
    args = parser.parse_args()

    artifact_dir = ROOT / "artifacts" / "screenshots"
    results = []
    for case in build_cases(args.provider, args.include_ollama):
        results.append(
            run_spec_case(
                case["spec"],
                app_dir=ROOT / "app",
                artifact_dir=artifact_dir,
                provider=case["provider"],
                bug=case["bug"],
                variant=case["variant"],
                expected_verdict=case["expected"],
                k=args.k,
            )
        )

    results_path = ROOT / "artifacts" / "evaluation.json"
    write_results(results_path, results)
    summary = generate_report(results_path, ROOT / "docs")
    print(json.dumps(summary, indent=2))


if __name__ == "__main__":
    main()
