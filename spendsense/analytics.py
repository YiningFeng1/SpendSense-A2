"""Create easy-to-read summaries from categorised transactions."""

from __future__ import annotations

import pandas as pd


def build_category_summary(frame: pd.DataFrame) -> pd.DataFrame:
    """Return spending totals and percentages for each category."""

    expenses = frame.loc[frame["direction"].eq("Expense")].copy()
    expenses["spent"] = -expenses["amount_cents"].astype("int64") / 100
    summary = expenses.groupby("category", as_index=False).agg(
        transactions=("transaction_id", "count"),
        total_spent=("spent", "sum"),
    )
    total = summary["total_spent"].sum()
    summary["percentage"] = (
        summary["total_spent"].div(total).mul(100).round(1) if total else 0.0
    )
    return summary.sort_values("total_spent", ascending=False).reset_index(drop=True)


def build_monthly_summary(frame: pd.DataFrame) -> pd.DataFrame:
    """Return income, expenses, and net cash flow for each month."""

    working = frame.copy()
    working["month"] = pd.to_datetime(working["date"]).dt.to_period("M").astype(str)
    working["income"] = working["amount_cents"].where(working["amount_cents"] > 0, 0) / 100
    working["expenses"] = -working["amount_cents"].where(working["amount_cents"] < 0, 0) / 100
    summary = working.groupby("month", as_index=False)[["income", "expenses"]].sum()
    summary["net"] = summary["income"] - summary["expenses"]
    return summary


def build_merchant_summary(frame: pd.DataFrame) -> pd.DataFrame:
    """Return the largest expense merchants first."""

    expenses = frame.loc[frame["direction"].eq("Expense")].copy()
    expenses["spent"] = -expenses["amount_cents"].astype("int64") / 100
    return (
        expenses.groupby("merchant", as_index=False)
        .agg(transactions=("transaction_id", "count"), total_spent=("spent", "sum"))
        .sort_values("total_spent", ascending=False)
        .reset_index(drop=True)
    )


def headline_metrics(frame: pd.DataFrame) -> dict[str, float | int]:
    """Calculate the figures shown at the end of an analysis."""

    amounts = frame["amount_cents"].astype("int64")
    expense_total = float(-amounts[amounts < 0].sum() / 100)
    income_total = float(amounts[amounts > 0].sum() / 100)
    uncategorised = int(frame["category"].eq("Uncategorised").sum())
    return {
        "transactions": len(frame),
        "income": income_total,
        "expenses": expense_total,
        "balance_change": income_total - expense_total,
        "uncategorised": uncategorised,
    }
