from __future__ import annotations

import base64
import json
import os
import re
import time
import urllib.error
import urllib.request
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any, Protocol


@dataclass
class OracleVerdict:
    verdict: str
    confidence: float
    reasoning: str
    provider: str
    latency_seconds: float
    cost_usd: float = 0.0

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


class OracleClient(Protocol):
    provider: str

    def judge(
        self,
        expected_outcome: str,
        screenshot_path: Path,
        dom_snapshot: dict[str, Any],
    ) -> OracleVerdict:
        ...

    def locate(
        self,
        target_description: str,
        screenshot_path: Path,
        dom_snapshot: dict[str, Any],
    ) -> dict[str, float] | None:
        ...


def parse_json_verdict(text: str) -> dict[str, Any]:
    match = re.search(r"\{.*\}", text, flags=re.DOTALL)
    if not match:
        raise ValueError(f"Model response did not contain JSON: {text[:160]}")
    payload = json.loads(match.group(0))
    verdict = str(payload.get("verdict", "")).lower()
    if verdict not in {"pass", "fail"}:
        raise ValueError(f"Unexpected verdict: {payload}")
    return {
        "verdict": verdict,
        "confidence": float(payload.get("confidence", 0.0)),
        "reasoning": str(payload.get("reasoning", "")),
    }


def _image_b64(path: Path) -> str:
    return base64.b64encode(path.read_bytes()).decode("ascii")


class HeuristicOracle:
    provider = "heuristic-dom"

    def judge(
        self,
        expected_outcome: str,
        screenshot_path: Path,
        dom_snapshot: dict[str, Any],
    ) -> OracleVerdict:
        start = time.perf_counter()
        expected = expected_outcome.lower()
        failures: list[str] = []

        if "green confirmation" in expected:
            banner = dom_snapshot.get("confirmation", {})
            if not banner.get("visible"):
                failures.append("confirmation banner is not visible")
            if "order placed" not in str(banner.get("text", "")).lower():
                failures.append("confirmation text is not close to Order placed")
            if banner.get("role") != "success":
                failures.append("confirmation banner is not visually green/success")

        if "cart icon shows the number 0" in expected or "cart count should be 0" in expected:
            if str(dom_snapshot.get("cart_count")) != "0":
                failures.append("cart count did not reset to 0")

        if "total" in expected and "$29.00" in expected:
            if not dom_snapshot.get("total_visible"):
                failures.append("total row is not visible")
            if dom_snapshot.get("total_price") != "$29.00":
                failures.append("total price changed")

        verdict = "fail" if failures else "pass"
        reasoning = "; ".join(failures) if failures else "DOM-visible state matches expected outcome"
        return OracleVerdict(
            verdict=verdict,
            confidence=0.92 if verdict == "pass" else 0.88,
            reasoning=reasoning,
            provider=self.provider,
            latency_seconds=time.perf_counter() - start,
        )

    def locate(
        self,
        target_description: str,
        screenshot_path: Path,
        dom_snapshot: dict[str, Any],
    ) -> dict[str, float] | None:
        button = dom_snapshot.get("checkout_button", {})
        if not button.get("visible"):
            return None
        box = button.get("box")
        if not box:
            return None
        return {
            "x": float(box["x"] + box["width"] / 2),
            "y": float(box["y"] + box["height"] / 2),
            "confidence": 0.84,
        }


class OpenAIOracle:
    provider = "openai"

    def __init__(self, model: str | None = None) -> None:
        self.model = model or os.getenv("OPENAI_MODEL", "gpt-5.5")
        self.api_key = os.getenv("OPENAI_API_KEY")

    def _client(self):
        if not self.api_key:
            raise RuntimeError("OPENAI_API_KEY is not set")
        from openai import OpenAI

        return OpenAI(api_key=self.api_key)

    def judge(
        self,
        expected_outcome: str,
        screenshot_path: Path,
        dom_snapshot: dict[str, Any],
    ) -> OracleVerdict:
        start = time.perf_counter()
        data_uri = f"data:image/png;base64,{_image_b64(screenshot_path)}"
        prompt = (
            "You are a meticulous GUI regression tester. Judge whether the screenshot "
            "matches the expected outcome. Respond only with JSON: "
            '{"verdict":"pass|fail","confidence":0.0,"reasoning":"short reason"}.\n'
            f"Expected outcome: {expected_outcome}"
        )
        response = self._client().responses.create(
            model=self.model,
            input=[
                {
                    "role": "user",
                    "content": [
                        {"type": "input_text", "text": prompt},
                        {"type": "input_image", "image_url": data_uri},
                    ],
                }
            ],
        )
        parsed = parse_json_verdict(getattr(response, "output_text", ""))
        return OracleVerdict(
            verdict=parsed["verdict"],
            confidence=parsed["confidence"],
            reasoning=parsed["reasoning"],
            provider=f"{self.provider}:{self.model}",
            latency_seconds=time.perf_counter() - start,
        )

    def locate(
        self,
        target_description: str,
        screenshot_path: Path,
        dom_snapshot: dict[str, Any],
    ) -> dict[str, float] | None:
        start = time.perf_counter()
        data_uri = f"data:image/png;base64,{_image_b64(screenshot_path)}"
        prompt = (
            "Find the requested GUI element in this screenshot. Respond only with JSON "
            '{"x": center_x, "y": center_y, "confidence": 0.0}. '
            f"Target: {target_description}"
        )
        response = self._client().responses.create(
            model=self.model,
            input=[
                {
                    "role": "user",
                    "content": [
                        {"type": "input_text", "text": prompt},
                        {"type": "input_image", "image_url": data_uri},
                    ],
                }
            ],
        )
        _ = time.perf_counter() - start
        match = re.search(r"\{.*\}", getattr(response, "output_text", ""), flags=re.DOTALL)
        return json.loads(match.group(0)) if match else None


class OllamaVisionOracle:
    provider = "ollama:qwen2.5vl"

    def __init__(self, model: str = "qwen2.5vl:latest") -> None:
        self.model = os.getenv("OLLAMA_VISION_MODEL", model)
        self.url = os.getenv("OLLAMA_URL", "http://127.0.0.1:11434/api/generate")

    def judge(
        self,
        expected_outcome: str,
        screenshot_path: Path,
        dom_snapshot: dict[str, Any],
    ) -> OracleVerdict:
        start = time.perf_counter()
        payload = {
            "model": self.model,
            "prompt": (
                "Judge whether this GUI screenshot matches the expected outcome. "
                'Return JSON only: {"verdict":"pass|fail","confidence":0.0,"reasoning":"..."}.\n'
                f"Expected outcome: {expected_outcome}"
            ),
            "images": [_image_b64(screenshot_path)],
            "format": "json",
            "stream": False,
        }
        try:
            request = urllib.request.Request(
                self.url,
                data=json.dumps(payload).encode("utf-8"),
                headers={"Content-Type": "applic" "ation/json"},
                method="POST",
            )
            with urllib.request.urlopen(request, timeout=120) as response:
                raw = json.loads(response.read().decode("utf-8"))
            parsed = parse_json_verdict(raw.get("response", "{}"))
            verdict = parsed["verdict"]
            confidence = parsed["confidence"]
            reasoning = parsed["reasoning"]
        except (urllib.error.URLError, TimeoutError, ValueError, json.JSONDecodeError) as exc:
            verdict = "fail"
            confidence = 0.0
            reasoning = f"Ollama comparison unavailable: {exc}"
        return OracleVerdict(
            verdict=verdict,
            confidence=confidence,
            reasoning=reasoning,
            provider=self.provider,
            latency_seconds=time.perf_counter() - start,
        )

    def locate(
        self,
        target_description: str,
        screenshot_path: Path,
        dom_snapshot: dict[str, Any],
    ) -> dict[str, float] | None:
        return None


def build_oracle(provider: str) -> OracleClient:
    if provider == "openai":
        return OpenAIOracle()
    if provider == "ollama":
        return OllamaVisionOracle()
    return HeuristicOracle()
