from pathlib import Path

from visual_oracle.specs import load_specs


def test_load_specs_includes_required_locator_metadata():
    specs = load_specs(Path("tests/specs"))

    assert {spec.test_id for spec in specs} >= {
        "checkout_success_state",
        "checkout_total_state",
        "selector_healing_checkout",
    }
    click_steps = [step for spec in specs for step in spec.steps if step.action == "click"]
    assert all(step.selector for step in click_steps)
    assert all(step.target_description for step in click_steps)
