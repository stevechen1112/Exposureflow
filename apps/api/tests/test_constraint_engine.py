"""Tests for business constraint rule parsing and matching."""

from exposureflow_api.strategy.constraint_engine import (
    evaluate_constraint_match,
    parse_constraint_rules,
)


def test_parse_constraint_rules_strips_negation_prefix() -> None:
    rules = parse_constraint_rules(["不做 B2B 批發", "不做全台服務"])
    patterns = {rule.match_pattern for rule in rules}
    assert "B2B 批發" in patterns or "B2B" in patterns
    assert "全台服務" in patterns


def test_evaluate_constraint_match_blocks_keyword() -> None:
    rules = parse_constraint_rules(["不做 B2B 批發"])
    hit = evaluate_constraint_match("B2B 紗窗批發合作", rules)
    assert hit is not None
    assert hit.action == "block"


def test_evaluate_constraint_match_ignores_unrelated_keyword() -> None:
    rules = parse_constraint_rules(["不做 B2B 批發"])
    hit = evaluate_constraint_match("台中紗窗維修", rules)
    assert hit is None
