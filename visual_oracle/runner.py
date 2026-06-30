from __future__ import annotations

import contextlib
import functools
import http.server
import json
import socket
import threading
from dataclasses import asdict
from pathlib import Path
from typing import Any
from urllib.parse import urlencode

from playwright.sync_api import sync_playwright

from .consistency import majority_vote
from .oracle_client import OracleClient, build_oracle
from .self_healing import self_heal_click
from .specs import TestSpec


@contextlib.contextmanager
def static_server(root: Path):
    class QuietHandler(http.server.SimpleHTTPRequestHandler):
        def log_message(self, format: str, *args: Any) -> None:
            return

    handler = functools.partial(QuietHandler, directory=str(root))
    with socket.socket() as sock:
        sock.bind(("127.0.0.1", 0))
        _, port = sock.getsockname()
    server = http.server.ThreadingHTTPServer(("127.0.0.1", port), handler)
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    try:
        yield f"http://127.0.0.1:{port}"
    finally:
        server.shutdown()
        thread.join(timeout=5)


def build_url(base_url: str, route: str, bug: str | None, variant: str | None) -> str:
    params = {}
    if bug and bug != "clean":
        params["bug"] = bug
    if variant and variant != "default":
        params["variant"] = variant
    query = f"?{urlencode(params)}" if params else ""
    return f"{base_url}{route}{query}"


def capture_dom_snapshot(page) -> dict[str, Any]:
    return page.evaluate(
        """() => {
          const banner = document.querySelector('#confirmation-banner');
          const btn = document.querySelector('#checkout-btn, #place-order-btn');
          const btnBox = btn ? btn.getBoundingClientRect() : null;
          const style = banner ? getComputedStyle(banner) : null;
          const bg = style ? style.backgroundColor : '';
          const success = bg.includes('18, 128, 92') || bg.includes('19, 128, 92');
          return {
            cart_count: document.querySelector('#cart-count')?.textContent?.trim(),
            total_visible: !!document.querySelector('#total-row') && getComputedStyle(document.querySelector('#total-row')).display !== 'none',
            total_price: document.querySelector('#total-price')?.textContent?.trim(),
            confirmation: {
              visible: !!banner && getComputedStyle(banner).display !== 'none',
              text: banner?.textContent?.trim() || '',
              role: success ? 'success' : (banner ? 'non-success' : 'missing'),
              background: bg
            },
            checkout_button: {
              visible: !!btn && getComputedStyle(btn).display !== 'none',
              text: btn?.textContent?.trim() || '',
              box: btnBox ? {x: btnBox.x, y: btnBox.y, width: btnBox.width, height: btnBox.height} : null
            }
          };
        }"""
    )


def run_spec_case(
    spec: TestSpec,
    app_dir: Path,
    artifact_dir: Path,
    provider: str = "heuristic",
    bug: str | None = None,
    variant: str | None = None,
    expected_verdict: str = "pass",
    k: int = 3,
) -> dict[str, Any]:
    oracle = build_oracle(provider)
    artifact_dir.mkdir(parents=True, exist_ok=True)
    case_id = f"{spec.test_id}__{bug or 'clean'}__{variant or 'default'}"

    with static_server(app_dir) as base_url:
        with sync_playwright() as playwright:
            browser = playwright.chromium.launch()
            page = browser.new_page(viewport={"width": 1280, "height": 900})
            healing_events: list[dict[str, Any]] = []
            try:
                for step in spec.steps:
                    if step.action == "goto":
                        page.goto(build_url(base_url, step.url or "/", bug, variant))
                    elif step.action == "click":
                        try:
                            page.locator(step.selector or "").click(timeout=900)
                        except Exception:
                            before_path = artifact_dir / f"{case_id}__before_heal.png"
                            page.screenshot(path=str(before_path), full_page=True)
                            snapshot = capture_dom_snapshot(page)
                            try:
                                event = self_heal_click(
                                    page,
                                    oracle,
                                    step.target_description or step.selector or "target element",
                                    before_path,
                                    snapshot,
                                )
                            except Exception as exc:
                                event = {
                                    "method": "self-heal-failed",
                                    "confidence": 0.0,
                                    "error": str(exc),
                                }
                            event["failed_selector"] = step.selector
                            healing_events.append(event)
                    elif step.action == "wait":
                        page.wait_for_timeout(step.ms or 250)
                    else:
                        raise ValueError(f"Unsupported action: {step.action}")

                screenshot_path = artifact_dir / f"{case_id}.png"
                page.screenshot(path=str(screenshot_path), full_page=True)
                dom_snapshot = capture_dom_snapshot(page)
                raw_votes = [
                    oracle.judge(spec.expected_outcome, screenshot_path, dom_snapshot).to_dict()
                    for _ in range(k)
                ]
                vote = majority_vote(raw_votes)
                return {
                    "case_id": case_id,
                    "test_id": spec.test_id,
                    "bug": bug or "clean",
                    "variant": variant or "default",
                    "provider": provider,
                    "expected_verdict": expected_verdict,
                    "actual_verdict": vote.verdict,
                    "passed_expectation": vote.verdict == expected_verdict,
                    "agreement_rate": vote.agreement_rate,
                    "confidence": vote.confidence,
                    "reasons": vote.reasons,
                    "votes": raw_votes,
                    "healing_events": healing_events,
                    "screenshot": str(screenshot_path),
                    "dom_snapshot": dom_snapshot,
                }
            finally:
                browser.close()


def write_results(path: Path, results: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(results, indent=2), encoding="utf-8")
