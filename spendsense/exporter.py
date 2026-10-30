"""Write analysis results to an output directory."""

from __future__ import annotations

from pathlib import Path

import pandas as pd


def export_results(
    transactions: pd.DataFrame,
    rejected: pd.DataFrame,
    category_summary: pd.DataFrame,
    monthly_summary: pd.DataFrame,
    merchant_summary: pd.DataFrame,
    metrics: dict[str, float | int],
    output_directory: str | Path,
) -> dict[str, Path]:
    """Export all tables and a short human-readable summary."""

    output = Path(output_directory)
    output.mkdir(parents=True, exist_ok=True)

    paths = {
        "transactions": output / "cleaned_transactions.csv",
        "categories": output / "category_summary.csv",
        "monthly": output / "monthly_summary.csv",
        "merchants": output / "merchant_summary.csv",
        "uncategorised": output / "uncategorised_transactions.csv",
        "rejected": output / "rejected_rows.csv",
        "summary": output / "analysis_summary.txt",
    }

    transactions.to_csv(paths["transactions"], index=False)
    category_summary.to_csv(paths["categories"], index=False)
    monthly_summary.to_csv(paths["monthly"], index=False)
    merchant_summary.to_csv(paths["merchants"], index=False)
    transactions.loc[transactions["category"].eq("Uncategorised")].to_csv(
        paths["uncategorised"], index=False
    )
    rejected.to_csv(paths["rejected"], index=False)

    summary_text = (
        "SpendSense Analysis Summary\n"
        "===========================\n"
        f"Transactions analysed: {metrics['transactions']}\n"
        f"Total income: ${metrics['income']:,.2f}\n"
        f"Total expenses: ${metrics['expenses']:,.2f}\n"
        f"Balance change: ${metrics['balance_change']:,.2f}\n"
        f"Uncategorised transactions: {metrics['uncategorised']}\n"
        f"Rejected rows: {len(rejected)}\n"
    )
    paths["summary"].write_text(summary_text, encoding="utf-8")
    return paths
