"""Core tests for the complete SpendSense pipeline."""

from pathlib import Path
import tempfile
import unittest

import pandas as pd

from spendsense.analytics import build_category_summary
from spendsense.categorizer import categorise_transactions, load_rules
from spendsense.cleaning import clean_transactions
from spendsense.loader import load_csv
from spendsense.pipeline import run_pipeline


ROOT = Path(__file__).resolve().parents[1]
SAMPLE = ROOT / "data" / "sample" / "anonymous_transactions.csv"
RULES = ROOT / "config" / "category_rules.json"


class SpendSensePipelineTests(unittest.TestCase):
    def test_sample_file_cleans_and_categorises(self) -> None:
        loaded = load_csv(SAMPLE)
        cleaned, rejected = clean_transactions(loaded.frame)
        categorised = categorise_transactions(cleaned, load_rules(RULES))

        self.assertEqual(len(cleaned), 12)
        self.assertTrue(rejected.empty)
        self.assertIn("Groceries", set(categorised["category"]))
        self.assertIn("Income", set(categorised["category"]))
        self.assertIn("Education", set(categorised["category"]))
        self.assertNotIn("Uncategorised", set(categorised["category"]))

    def test_category_summary_uses_positive_spending_values(self) -> None:
        loaded = load_csv(SAMPLE)
        cleaned, _ = clean_transactions(loaded.frame)
        categorised = categorise_transactions(cleaned, load_rules(RULES))
        summary = build_category_summary(categorised)

        self.assertGreater(summary["total_spent"].sum(), 0)

    def test_pipeline_exports_expected_files(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            result = run_pipeline(SAMPLE, RULES, directory)
            self.assertEqual(result.metrics["transactions"], 12)
            self.assertTrue(all(path.exists() for path in result.output_files.values()))
            self.assertIn("dashboard", result.output_files)
            self.assertGreater(result.output_files["dashboard"].stat().st_size, 1000)

    def test_separate_debit_and_credit_columns(self) -> None:
        source = pd.DataFrame(
            {
                "Date": ["29/10/2026", "30/10/2026"],
                "Details": ["COLES", "PART TIME PAY"],
                "Debit": ["12.50", ""],
                "Credit": ["", "300.00"],
            }
        )
        cleaned, rejected = clean_transactions(source)

        self.assertTrue(rejected.empty)
        self.assertEqual(cleaned["amount_cents"].tolist(), [-1250, 30000])

    def test_invalid_rows_are_rejected_with_a_reason(self) -> None:
        source = pd.DataFrame(
            {
                "Date": ["not a date", "29/10/2026"],
                "Description": ["COLES", ""],
                "Amount": ["-20.00", "bad amount"],
            }
        )
        cleaned, rejected = clean_transactions(source)

        self.assertTrue(cleaned.empty)
        self.assertEqual(len(rejected), 2)
        self.assertIn("invalid date", rejected.loc[0, "rejection_reason"])
        self.assertIn("missing description", rejected.loc[1, "rejection_reason"])


if __name__ == "__main__":
    unittest.main()
