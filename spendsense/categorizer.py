"""Editable regex-based spending classifier."""

from __future__ import annotations

import json
from pathlib import Path
import re

import pandas as pd


def load_rules(path: str | Path) -> list[dict]:
    """Load and validate editable category rules from JSON."""

    source = Path(path)
    if not source.exists():
        raise FileNotFoundError(f"Rules file not found: {source}")

    try:
        with source.open("r", encoding="utf-8") as stream:
            document = json.load(stream)
    except json.JSONDecodeError as error:
        raise ValueError(f"The rules file is not valid JSON: {error}") from error

    rules = document.get("rules", [])
    if not isinstance(rules, list):
        raise ValueError("category_rules.json must contain a rules list.")

    seen_ids: set[str] = set()
    for rule in rules:
        if not isinstance(rule, dict):
            raise ValueError("Every category rule must be a JSON object.")
        rule_id = str(rule.get("id", "")).strip()
        if not rule_id:
            raise ValueError("Every category rule needs an id.")
        if rule_id in seen_ids:
            raise ValueError(f"Rule id '{rule_id}' is repeated.")
        seen_ids.add(rule_id)

    return sorted(rules, key=lambda rule: int(rule.get("priority", 0)), reverse=True)


def categorise_transactions(frame: pd.DataFrame, rules: list[dict]) -> pd.DataFrame:
    """Apply the first matching rule and retain its ID for explainability."""

    result = frame.copy()
    result["category"] = "Uncategorised"
    result["matched_rule_id"] = ""

    income = result["direction"].eq("Income")
    result.loc[income, "category"] = "Income"
    result.loc[income, "matched_rule_id"] = "system_income"

    # Search both forms. The original text can contain useful bank information,
    # while the cleaned merchant name is easier to match with simple rules.
    search_text = (
        result["original_description"].fillna("").astype(str)
        + " "
        + result["merchant"].fillna("").astype(str)
    )
    for rule in rules:
        rule_id = str(rule.get("id", "")).strip()
        category = str(rule.get("category", "")).strip()
        patterns = rule.get("patterns", [])
        if not rule_id or not category or not patterns:
            continue
        if not isinstance(patterns, list) or not all(isinstance(item, str) for item in patterns):
            raise ValueError(f"Rule '{rule_id}' patterns must be a list of text values.")

        try:
            combined = "|".join(f"(?:{pattern})" for pattern in patterns)
            matches = search_text.str.contains(combined, case=False, regex=True, na=False)
        except re.error as error:
            raise ValueError(f"Invalid regex in rule '{rule_id}': {error}") from error

        available = result["category"].eq("Uncategorised")
        selected = matches & available
        result.loc[selected, "category"] = category
        result.loc[selected, "matched_rule_id"] = rule_id

    result["is_manual_override"] = False
    return result
