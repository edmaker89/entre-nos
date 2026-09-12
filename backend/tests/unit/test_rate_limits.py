"""AUTH-RESET-01 AC6: opaque rate-limit keys."""

from app.domain.rate_limits import opaque_key


def test_opaque_key_is_stable_and_fixed_length():
    first = opaque_key("person@example.com", "secret")
    assert first == opaque_key("person@example.com", "secret")
    assert len(first) == 64


def test_opaque_key_changes_with_value_or_secret():
    baseline = opaque_key("person@example.com", "secret")
    assert opaque_key("other@example.com", "secret") != baseline
    assert opaque_key("person@example.com", "other-secret") != baseline


def test_opaque_key_does_not_contain_source_value():
    source = "192.0.2.44"
    assert source not in opaque_key(source, "secret")
