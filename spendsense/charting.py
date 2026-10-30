"""Create the SpendSense chart dashboard.

Matplotlib uses the non-interactive ``Agg`` backend so chart creation works
even when the program is run without opening the desktop interface.
"""

from __future__ import annotations

import os
from pathlib import Path
import tempfile

# Some school or managed computers do not allow programs to write to the home
# folder. A temporary Matplotlib settings folder avoids a warning in that case.
os.environ.setdefault(
    "MPLCONFIGDIR", str(Path(tempfile.gettempdir()) / "spendsense-matplotlib")
)

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import pandas as pd


GREEN = "#274C3A"
LIGHT_GREEN = "#8EAA80"
ORANGE = "#D86A48"
CREAM = "#F4F2EA"


def create_dashboard(
    category_summary: pd.DataFrame,
    monthly_summary: pd.DataFrame,
    output_directory: str | Path,
) -> Path:
    """Save one PNG containing the category and monthly spending charts."""

    output = Path(output_directory)
    output.mkdir(parents=True, exist_ok=True)
    chart_path = output / "spending_dashboard.png"

    figure, axes = plt.subplots(1, 2, figsize=(13, 5.8))
    figure.patch.set_facecolor(CREAM)
    figure.suptitle("SpendSense Summary", fontsize=20, fontweight="bold", color=GREEN)

    category_axis, monthly_axis = axes
    for axis in axes:
        axis.set_facecolor("white")
        axis.spines[["top", "right"]].set_visible(False)
        axis.grid(axis="y", alpha=0.18)

    if category_summary.empty:
        category_axis.text(0.5, 0.5, "No expense data", ha="center", va="center")
        category_axis.set_axis_off()
    else:
        category_data = category_summary.sort_values("total_spent", ascending=True)
        category_axis.barh(
            category_data["category"],
            category_data["total_spent"],
            color=LIGHT_GREEN,
        )
        category_axis.set_title("Spending by category", color=GREEN, fontweight="bold")
        category_axis.set_xlabel("Amount spent ($)")
        for position, amount in enumerate(category_data["total_spent"]):
            category_axis.text(amount, position, f"  ${amount:,.2f}", va="center", fontsize=9)

    if monthly_summary.empty:
        monthly_axis.text(0.5, 0.5, "No monthly data", ha="center", va="center")
        monthly_axis.set_axis_off()
    else:
        positions = list(range(len(monthly_summary)))
        width = 0.36
        monthly_axis.bar(
            [value - width / 2 for value in positions],
            monthly_summary["income"],
            width,
            label="Income",
            color=LIGHT_GREEN,
        )
        monthly_axis.bar(
            [value + width / 2 for value in positions],
            monthly_summary["expenses"],
            width,
            label="Expenses",
            color=ORANGE,
        )
        monthly_axis.set_xticks(positions, monthly_summary["month"], rotation=30, ha="right")
        monthly_axis.set_title("Monthly income and expenses", color=GREEN, fontweight="bold")
        monthly_axis.set_ylabel("Amount ($)")
        monthly_axis.legend(frameon=False)

    figure.tight_layout(rect=(0, 0, 1, 0.92))
    figure.savefig(chart_path, dpi=150, bbox_inches="tight", facecolor=figure.get_facecolor())
    plt.close(figure)
    return chart_path
