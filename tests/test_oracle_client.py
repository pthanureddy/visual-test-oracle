import pytest

from visual_oracle.oracle_client import parse_json_verdict


def test_parse_json_verdict_accepts_model_text_wrapping():
    parsed = parse_json_verdict('Here is the result: {"verdict":"pass","confidence":0.91,"reasoning":"looks correct"}')

    assert parsed["verdict"] == "pass"
    assert parsed["confidence"] == 0.91


def test_parse_json_verdict_rejects_invalid_verdict():
    with pytest.raises(ValueError):
        parse_json_verdict('{"verdict":"maybe","confidence":0.5,"reasoning":"unclear"}')
