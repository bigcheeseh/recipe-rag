import pytest

from app.llm import TokenUsage, cost_usd


def test_cost_uses_list_prices_per_million():
    u = TokenUsage(tokens_in=1_000_000, tokens_out=100_000)
    assert cost_usd("claude-sonnet-5", u) == pytest.approx(2.00 + 1.00)
    assert cost_usd("claude-haiku-4-5", u) == pytest.approx(1.00 + 0.50)


def test_cache_tokens_are_priced_at_write_and_read_multipliers():
    u = TokenUsage(tokens_in=0, tokens_out=0, cache_write=1_000_000, cache_read=1_000_000)
    assert cost_usd("claude-sonnet-5", u) == pytest.approx(2.00 * 1.25 + 2.00 * 0.10)


def test_usage_addition_sums_every_field():
    a = TokenUsage(tokens_in=1, tokens_out=2, cache_write=3, cache_read=4)
    b = TokenUsage(tokens_in=10, tokens_out=20, cache_write=30, cache_read=40)
    assert (a + b) == TokenUsage(tokens_in=11, tokens_out=22, cache_write=33, cache_read=44)
    assert (a + b).total_in == 11 + 33 + 44
