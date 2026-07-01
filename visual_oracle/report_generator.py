from __future__ import annotations

import html
import json
from pathlib import Path
from typing import Any

from jinja2 import Template

from .metrics import summarize


REPORT_TEMPLATE = """<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>Visual Test Oracle Report</title>
  <style>
    :root { font-family: Inter, ui-sans-serif, system-ui, sans-serif; color: #172033; background: #f6f7f9; }
    body { margin: 0; }
    main { width: min(1120px, calc(100% - 32px)); margin: 0 auto; padding: 32px 0 56px; }
    header { margin-bottom: 28px; }
    h1 { font-size: clamp(2.4rem, 5vw, 4.6rem); line-height: 1; margin: 0 0 12px; letter-spacing: 0; }
    h2 { margin-top: 34px; }
    p, li { color: #4b5870; line-height: 1.65; }
    a { color: #1d4ed8; font-weight: 700; }
    .metrics { display: grid; grid-template-columns: repeat(auto-fit, minmax(190px, 1fr)); gap: 12px; }
    .metric, .card { background: #fff; border: 1px solid #d9dee8; border-radius: 8px; padding: 16px; }
    .metric strong { display: block; font-size: 2rem; color: #172033; }
    table { width: 100%; border-collapse: collapse; background: #fff; border: 1px solid #d9dee8; border-radius: 8px; overflow: hidden; }
    th, td { padding: 10px 12px; border-bottom: 1px solid #edf0f4; text-align: left; font-size: 0.92rem; }
    th { background: #eef2f7; color: #263244; }
    .pass { color: #0f766e; font-weight: 800; }
    .fail { color: #b42318; font-weight: 800; }
    .gallery { display: grid; grid-template-columns: repeat(auto-fit, minmax(260px, 1fr)); gap: 12px; }
    .gallery img { width: 100%; border: 1px solid #d9dee8; border-radius: 8px; background: #fff; }
    code { background: #eef2f7; padding: 2px 5px; border-radius: 5px; }
  </style>
</head>
<body>
<main>
  <header>
    <p><strong>Engineering case study</strong> - GUI regression testing with multimodal oracles</p>
    <h1>Visual Test Oracle</h1>
    <p>This report evaluates a screenshot-based GUI test oracle with k-run voting, controlled UI mutants, benign UI changes, and self-healing locator fallback.</p>
    <p><a href="case-study.pdf">Formal PDF case study</a> | <a href="case-study.md">Markdown case study</a></p>
  </header>

  <section class="metrics">
    <div class="metric"><span>Bug detection</span><strong>{{ "%.0f"|format(summary.bug_detection_rate * 100) }}%</strong></div>
    <div class="metric"><span>False positives</span><strong>{{ "%.0f"|format(summary.false_positive_rate * 100) }}%</strong></div>
    <div class="metric"><span>Maintenance resilience</span><strong>{{ "%.0f"|format(summary.maintenance_resilience * 100) }}%</strong></div>
    <div class="metric"><span>Mean agreement</span><strong>{{ "%.0f"|format(summary.mean_agreement_rate * 100) }}%</strong></div>
  </section>

  <h2>Method</h2>
  <div class="card">
    <p>YAML test specs drive a Playwright runner. At each checkpoint the runner captures a screenshot and asks an oracle whether the UI matches the natural-language expected outcome. The oracle is run three times per checkpoint and majority vote is used as the final verdict. CI uses a deterministic DOM-backed oracle; OpenAI and Ollama adapters can be enabled for model-backed runs.</p>
  </div>

  <h2>Results</h2>
  <table>
    <thead><tr><th>Case</th><th>Expected</th><th>Actual</th><th>Agreement</th><th>Healing</th><th>Reason</th></tr></thead>
    <tbody>
    {% for r in results %}
      <tr>
        <td><code>{{ r.case_id }}</code></td>
        <td>{{ r.expected_verdict }}</td>
        <td class="{{ r.actual_verdict }}">{{ r.actual_verdict }}</td>
        <td>{{ "%.0f"|format(r.agreement_rate * 100) }}%</td>
        <td>{{ r.healing_events|length }}</td>
        <td>{{ (r.reasons[0] if r.reasons else "") }}</td>
      </tr>
    {% endfor %}
    </tbody>
  </table>

  <h2>Evidence</h2>
  <div class="card">
    <p>Short demo sequence:</p>
    <img src="assets/demo.gif" alt="Animated demo of the visual oracle flow" style="width: min(720px, 100%); border-radius: 8px; border: 1px solid #d9dee8;">
  </div>
  <div class="gallery">
    {% for image in images[:6] %}
      <figure>
        <img src="{{ image.href }}" alt="{{ image.label }}">
        <figcaption>{{ image.label }}</figcaption>
      </figure>
    {% endfor %}
  </div>

  <h2>Limitations and Next Steps</h2>
  <ul>
    <li>The committed CI path avoids API spending; OpenAI-backed runs require <code>OPENAI_API_KEY</code>.</li>
    <li>The local vision comparison uses Ollama <code>qwen2.5vl:latest</code> when installed and is intentionally bounded to a small subset on CPU-only machines.</li>
    <li>The self-healing locator path records when it falls back from a failed CSS selector to model or accessibility-guided clicking.</li>
  </ul>
</main>
</body>
</html>
"""


def generate_report(results_path: Path, docs_dir: Path) -> dict[str, Any]:
    results = json.loads(results_path.read_text(encoding="utf-8"))
    summary = summarize(results)
    docs_dir.mkdir(parents=True, exist_ok=True)
    assets_dir = docs_dir / "assets"
    assets_dir.mkdir(exist_ok=True)

    images = []
    for result in results:
        src = Path(result["screenshot"])
        if src.exists():
            dest = assets_dir / src.name
            dest.write_bytes(src.read_bytes())
            images.append({"href": f"assets/{html.escape(dest.name)}", "label": result["case_id"]})

    html_text = Template(REPORT_TEMPLATE).render(results=results, summary=summary, images=images)
    (docs_dir / "index.html").write_text(html_text, encoding="utf-8")
    (docs_dir / "report.md").write_text(markdown_report(summary, results), encoding="utf-8")
    return summary


def markdown_report(summary: dict[str, Any], results: list[dict[str, Any]]) -> str:
    rows = [
        "| Case | Expected | Actual | Agreement |",
        "|---|---:|---:|---:|",
    ]
    for result in results:
        rows.append(
            f"| `{result['case_id']}` | {result['expected_verdict']} | {result['actual_verdict']} | {result['agreement_rate']:.2f} |"
        )
    return "\n".join(
        [
            "# Visual Test Oracle Report",
            "",
            "## Summary Metrics",
            "",
            f"- Bug detection rate: {summary['bug_detection_rate']:.2%}",
            f"- False positive rate: {summary['false_positive_rate']:.2%}",
            f"- Maintenance resilience: {summary['maintenance_resilience']:.2%}",
            f"- Mean agreement rate: {summary['mean_agreement_rate']:.2%}",
            f"- Self-healing successes: {summary['self_healing_successes']}",
            "",
            "## Case Results",
            "",
            *rows,
            "",
            "## Related Work",
            "",
            "This prototype is designed around GUI-based testing, test oracle construction, web element localization, and evaluation of non-deterministic AI systems.",
        ]
    )
