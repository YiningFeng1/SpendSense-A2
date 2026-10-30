"""Optional command-line runner for SpendSense.

The graphical interface is the normal way to use the project. This small file
also makes it easy to demonstrate or test the pipeline from a terminal.
"""

from __future__ import annotations

import argparse
from pathlib import Path

from .pipeline import run_pipeline


def main() -> None:
    project_root = Path(__file__).resolve().parents[1]
    parser = argparse.ArgumentParser(description="Analyse a bank CSV with SpendSense.")
    parser.add_argument("input", type=Path, help="Path to the bank CSV file")
    parser.add_argument(
        "--output",
        type=Path,
        default=project_root / "outputs",
        help="Folder for reports and charts",
    )
    parser.add_argument(
        "--rules",
        type=Path,
        default=project_root / "config" / "category_rules.json",
        help="JSON category rules file",
    )
    args = parser.parse_args()

    result = run_pipeline(args.input, args.rules, args.output)
    metrics = result.metrics
    print("SpendSense analysis complete")
    print(f"Transactions: {metrics['transactions']}")
    print(f"Income: ${metrics['income']:,.2f}")
    print(f"Expenses: ${metrics['expenses']:,.2f}")
    print(f"Uncategorised: {metrics['uncategorised']}")
    print(f"Results: {args.output.resolve()}")


if __name__ == "__main__":
    main()
