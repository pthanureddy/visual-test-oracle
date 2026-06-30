from pathlib import Path

import pytest

from visual_oracle.runner import static_server


@pytest.mark.e2e
def test_baseline_checkout_exact_assertions(page):
    with static_server(Path("app")) as base_url:
        page.goto(base_url)
        page.locator("#checkout-btn").click()
        page.locator("#confirmation-banner").wait_for()
        assert page.locator("#confirmation-banner").inner_text() == "Order placed"
        assert page.locator("#cart-count").inner_text() == "0"


@pytest.mark.e2e
def test_baseline_selector_breaks_on_benign_selector_rename(page):
    with static_server(Path("app")) as base_url:
        page.goto(f"{base_url}?variant=renamed_selector")
        with pytest.raises(Exception):
            page.locator("#checkout-btn").click(timeout=500)
