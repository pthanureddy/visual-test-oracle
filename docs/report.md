# Visual Test Oracle Report

## Summary Metrics

- Bug detection rate: 90.00%
- False positive rate: 0.00%
- Maintenance resilience: 100.00%
- Mean agreement rate: 100.00%
- Self-healing successes: 1

## Case Results

| Case | Expected | Actual | Agreement |
|---|---:|---:|---:|
| `checkout_success_state__clean__default` | pass | pass | 1.00 |
| `checkout_total_state__clean__default` | pass | pass | 1.00 |
| `checkout_success_state__hidden_checkout__default` | fail | fail | 1.00 |
| `checkout_success_state__disabled_button__default` | fail | fail | 1.00 |
| `checkout_success_state__wrong_color__default` | fail | fail | 1.00 |
| `checkout_success_state__wrong_copy__default` | fail | fail | 1.00 |
| `checkout_success_state__cart_not_reset__default` | fail | fail | 1.00 |
| `checkout_total_state__missing_total__default` | fail | fail | 1.00 |
| `checkout_total_state__wrong_currency__default` | fail | fail | 1.00 |
| `checkout_success_state__layout_shift__default` | fail | pass | 1.00 |
| `checkout_success_state__missing_confirmation__default` | fail | fail | 1.00 |
| `checkout_success_state__extra_error__default` | fail | fail | 1.00 |
| `checkout_success_state__clean__benign_copy` | pass | pass | 1.00 |
| `selector_healing_checkout__clean__renamed_selector` | pass | pass | 1.00 |

## Related Work

This prototype is designed around GUI-based testing, test oracle construction, web element localization, and evaluation of non-deterministic AI systems.