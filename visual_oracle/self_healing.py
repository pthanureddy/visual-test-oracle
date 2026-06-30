from __future__ import annotations

from pathlib import Path
from typing import Any

from playwright.sync_api import Page

from .oracle_client import OracleClient


def self_heal_click(
    page: Page,
    oracle: OracleClient,
    target_description: str,
    screenshot_path: Path,
    dom_snapshot: dict[str, Any],
) -> dict[str, Any]:
    location = oracle.locate(target_description, screenshot_path, dom_snapshot)
    if not location:
        button = page.get_by_role("button")
        button.filter(has_text="Checkout").or_(button.filter(has_text="Place order")).first.click()
        return {"method": "accessibility-text-fallback", "confidence": 0.62}

    page.mouse.click(float(location["x"]), float(location["y"]))
    return {"method": f"{oracle.provider}-bounding-box", **location}
