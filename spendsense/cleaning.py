"""Convert bank-specific columns into a small standard transaction table."""

from __future__ import annotations

import re

import pandas as pd


COLUMN_ALIASES = {
    "date": ("date", "transaction_date", "posted_date", "value_date"),
    "description": (
        "description",
        "details",
        "transaction_details",
        "narrative",
        "merchant",
    ),
    "amount": ("amount", "transaction_amount", "value"),
    "debit": ("debit", "withdrawal", "money_out"),
    "credit": ("credit", "deposit", "money_in"),
}


def normalise_header(value: object) -> str:
    text = re.sub(r"[^a-z0-9]+", "_", str(value).strip().lower())
    return text.strip("_")


def _find_column(columns: list[str], logical_name: str) -> str | None:
    for alias in COLUMN_ALIASES[logical_name]:
        if alias in columns:
            return alias
    return None


def _money_to_number(series: pd.Series) -> pd.Series:
    """Convert common money formats such as '$1,200.50' and '12.00 DR'."""

    text = series.fillna("").astype(str).str.strip().str.upper()
    negative_value = text.str.match(r"^\(.*\)$") | text.str.endswith("DR")
    cleaned = text.str.replace(r"\b(?:CR|DR)\b", "", regex=True)
    cleaned = cleaned.str.replace(r"[$,\s()]", "", regex=True)
    values = pd.to_numeric(cleaned, errors="coerce")
    values.loc[negative_value & values.notna()] = -values.loc[negative_value & values.notna()].abs()
    return values


def _merchant_name(description: object) -> str:
    text = re.sub(r"\s+", " ", str(description).upper()).strip()
    text = re.sub(r"\b(VISA|DEBIT|CARD|PURCHASE)\b", "", text)
    return re.sub(r"\s+", " ", text).strip()


def clean_transactions(frame: pd.DataFrame) -> tuple[pd.DataFrame, pd.DataFrame]:
    """Return cleaned transactions and rejected rows.

    Supported inputs currently need a date and description plus either one amount
    column or separate debit and credit columns.
    """

    working = frame.copy()
    working.columns = [normalise_header(column) for column in working.columns]
    columns = list(working.columns)

    if len(columns) != len(set(columns)):
        raise ValueError("Two or more CSV columns become the same after cleaning their names.")

    date_column = _find_column(columns, "date")
    description_column = _find_column(columns, "description")
    amount_column = _find_column(columns, "amount")
    debit_column = _find_column(columns, "debit")
    credit_column = _find_column(columns, "credit")

    if not date_column or not description_column:
        raise ValueError("The CSV needs date and description columns.")
    if not amount_column and not (debit_column or credit_column):
        raise ValueError("The CSV needs an amount column, or debit/credit columns.")

    result = pd.DataFrame(index=working.index)
    # ``format="mixed"`` keeps ISO dates unambiguous while still accepting
    # common Australian day-first values such as 31/10/2026.
    result["date"] = pd.to_datetime(
        working[date_column], errors="coerce", format="mixed", dayfirst=True
    )
    result["original_description"] = working[description_column].fillna("").astype(str).str.strip()

    if amount_column:
        amount = _money_to_number(working[amount_column])
    else:
        # Separate debit and credit columns normally contain positive values.
        # abs() also handles exports that already put a minus sign on debits.
        debit = _money_to_number(working[debit_column]).abs() if debit_column else 0
        credit = _money_to_number(working[credit_column]).abs() if credit_column else 0
        amount = credit.fillna(0) - debit.fillna(0)

    result["amount_cents"] = (amount * 100).round().astype("Int64")
    result["merchant"] = result["original_description"].map(_merchant_name)
    result["direction"] = amount.map(lambda value: "Income" if pd.notna(value) and value >= 0 else "Expense")

    invalid = (
        result["date"].isna()
        | result["amount_cents"].isna()
        | result["original_description"].eq("")
    )
    rejected = working.loc[invalid].copy()
    reasons = []
    for row_index in rejected.index:
        row_reasons = []
        if pd.isna(result.loc[row_index, "date"]):
            row_reasons.append("invalid date")
        if pd.isna(result.loc[row_index, "amount_cents"]):
            row_reasons.append("invalid amount")
        if result.loc[row_index, "original_description"] == "":
            row_reasons.append("missing description")
        reasons.append(", ".join(row_reasons))
    rejected.insert(0, "rejection_reason", reasons)

    cleaned = result.loc[~invalid].copy().reset_index(drop=True)
    cleaned.insert(0, "transaction_id", [f"TX-{number:05d}" for number in range(1, len(cleaned) + 1)])
    cleaned["date"] = cleaned["date"].dt.date
    return cleaned, rejected.reset_index(drop=True)
