"""Parse and evaluate business constraint rules from Strategy Intake."""

from __future__ import annotations

import re
from dataclasses import dataclass

from exposureflow_api.strategy.keyword_utils import normalize_keyword

NEGATION_PREFIXES = (
    "不做",
    "排除",
    "不寫",
    "不經營",
    "不提供",
    "不承接",
    "不開發",
    "不投",
    "不要",
    "no ",
    "not ",
)

COMPOUND_SPLIT = re.compile(r"[、,，/|＋+與及和]")


@dataclass(frozen=True)
class ParsedConstraintRule:
    description: str
    match_pattern: str
    rule_type: str = "substring"
    action: str = "block"


def _unique_strings(values: list | None) -> list[str]:
    seen: set[str] = set()
    out: list[str] = []
    for raw in values or []:
        text = str(raw).strip()
        if not text:
            continue
        key = text.lower()
        if key in seen:
            continue
        seen.add(key)
        out.append(text)
    return out


def _strip_negation_prefix(text: str) -> str:
    lowered = text.lower()
    for prefix in NEGATION_PREFIXES:
        if lowered.startswith(prefix):
            return text[len(prefix) :].strip(" ：:，,。.")
    return text.strip()


def _expand_patterns(text: str) -> list[str]:
    core = _strip_negation_prefix(text)
    if not core:
        return []
    parts = [part.strip() for part in COMPOUND_SPLIT.split(core) if part.strip()]
    if not parts:
        parts = [core]
    patterns: list[str] = []
    for part in parts:
        normalized = normalize_keyword(part)
        if len(normalized) >= 2:
            patterns.append(part.strip())
        for token in part.split():
            token = token.strip()
            token_norm = normalize_keyword(token)
            if len(token_norm) >= 2 and token not in patterns:
                patterns.append(token)
    return patterns or [core]


def parse_constraint_rules(constraints: list[str] | None) -> list[ParsedConstraintRule]:
    rules: list[ParsedConstraintRule] = []
    seen: set[tuple[str, str]] = set()
    for constraint in _unique_strings(constraints):
        for pattern in _expand_patterns(constraint):
            key = (normalize_keyword(pattern), "block")
            if key in seen:
                continue
            seen.add(key)
            rules.append(
                ParsedConstraintRule(
                    description=constraint,
                    match_pattern=pattern,
                    rule_type="substring",
                    action="block",
                )
            )
    return rules


def evaluate_constraint_match(
    keyword: str | None,
    rules: list[ParsedConstraintRule],
) -> ParsedConstraintRule | None:
    normalized = normalize_keyword(keyword)
    if not normalized:
        return None
    for rule in rules:
        pattern = normalize_keyword(rule.match_pattern)
        if pattern and pattern in normalized:
            return rule
    return None


def rule_to_payload(rule: ParsedConstraintRule) -> dict:
    return {
        "description": rule.description,
        "rule_type": rule.rule_type,
        "match_pattern": rule.match_pattern,
        "action": rule.action,
    }
