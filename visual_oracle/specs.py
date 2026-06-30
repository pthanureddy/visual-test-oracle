from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any

import yaml


@dataclass(frozen=True)
class TestStep:
    action: str
    selector: str | None = None
    target_description: str | None = None
    url: str | None = None
    ms: int | None = None


@dataclass(frozen=True)
class TestSpec:
    test_id: str
    description: str
    expected_outcome: str
    steps: list[TestStep]
    checkpoint: str = "screenshot"


def _step_from_mapping(raw: dict[str, Any]) -> TestStep:
    action = str(raw["action"]).strip()
    return TestStep(
        action=action,
        selector=raw.get("selector"),
        target_description=raw.get("target_description"),
        url=raw.get("url"),
        ms=int(raw["ms"]) if raw.get("ms") is not None else None,
    )


def load_spec(path: Path) -> TestSpec:
    raw = yaml.safe_load(path.read_text(encoding="utf-8"))
    required = {"test_id", "description", "expected_outcome", "steps"}
    missing = required.difference(raw)
    if missing:
        raise ValueError(f"{path} is missing required fields: {sorted(missing)}")
    return TestSpec(
        test_id=str(raw["test_id"]),
        description=str(raw["description"]).strip(),
        expected_outcome=str(raw["expected_outcome"]).strip(),
        steps=[_step_from_mapping(step) for step in raw["steps"]],
        checkpoint=str(raw.get("checkpoint", "screenshot")),
    )


def load_specs(spec_dir: Path) -> list[TestSpec]:
    return [load_spec(path) for path in sorted(spec_dir.glob("*.yaml"))]
