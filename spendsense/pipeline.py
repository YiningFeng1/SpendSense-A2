"""Connect each small SpendSense step into one complete analysis."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

import pandas as pd

from .analytics import (
    build_category_summary,
    build_merchant_summary,
    build_monthly_summary,
    headline_metrics,
)
from .categorizer import categorise_transactions, load_rules
from .charting import create_dashboard
from .cleaning import clean_transactions
from .exporter import export_results
from .loader import load_csv


@dataclass(frozen=True)
class PipelineResult:
    metrics: dict[str, float | int]
    output_files: dict[str, Path]
    rejected_rows: int
    transactions: pd.DataFrame
    category_summary: pd.DataFrame
    monthly_summary: pd.DataFrame


def run_pipeline(
    csv_path: str | Path,
    rules_path: str | Path,
    output_directory: str | Path,
) -> PipelineResult:
    """Run import, cleaning, classification, summaries, charts, and export."""

    loaded = load_csv(csv_path)
    cleaned, rejected = clean_transactions(loaded.frame)
    if cleaned.empty:
        raise ValueError("No valid transactions remain after cleaning the CSV.")

    categorised = categorise_transactions(cleaned, load_rules(rules_path))
    category_summary = build_category_summary(categorised)
    monthly_summary = build_monthly_summary(categorised)
    merchant_summary = build_merchant_summary(categorised)
    metrics = headline_metrics(categorised)
    output_files = export_results(
        categorised,
        rejected,
        category_summary,
        monthly_summary,
        merchant_summary,
        metrics,
        output_directory,
    )
    output_files["dashboard"] = create_dashboard(
        category_summary, monthly_summary, output_directory
    )
    return PipelineResult(
        metrics=metrics,
        output_files=output_files,
        rejected_rows=len(rejected),
        transactions=categorised,
        category_summary=category_summary,
        monthly_summary=monthly_summary,
    )
