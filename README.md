# SpendSense

SpendSense is a beginner-friendly Python application that turns a bank CSV
export into a clear summary of income and spending. It cleans transaction
data, applies editable category rules, creates summary tables and charts, and
exports the results without changing the original CSV.

## Main features

- Desktop interface built with Tkinter
- CSV preview before analysis
- Support for common CSV encodings and delimiters
- Automatic recognition of common bank column names
- Cleaning for dates, descriptions, and money values
- Editable regular-expression category rules
- Category, month, and merchant summaries
- Uncategorised transaction and rejected-row reports
- PNG dashboard showing category and monthly spending
- Command-line runner for testing or demonstrations

## Requirements

- Python 3.9 or newer
- pandas
- matplotlib
- Tkinter, which is included with most Python installations

Install the external libraries:

```bash
python3 -m pip install -r requirements.txt
```

## Run the graphical interface

From this folder, run:

```bash
python3 main.py
```

Then:

1. Click **Select CSV**.
2. Choose `data/sample/anonymous_transactions.csv` for a safe demonstration.
3. Choose an output folder or keep the default.
4. Click **Start analysis**.
5. Use **View dashboard** or **Open results folder**.

The interface first shows the raw CSV preview. After the analysis, the table
changes to the cleaned and categorised transactions.

## Optional command-line use

```bash
python3 -m spendsense.cli data/sample/anonymous_transactions.csv
```

Choose another output location with:

```bash
python3 -m spendsense.cli data/sample/anonymous_transactions.csv --output my_results
```

## Supported CSV columns

SpendSense needs:

- one date column, such as `Date`, `Transaction Date`, or `Posted Date`
- one description column, such as `Description`, `Details`, or `Merchant`
- either one signed `Amount` column, or separate `Debit` and `Credit` columns

Expenses should normally be negative in a single Amount column. Separate Debit
and Credit columns may use positive values. Money values such as `$1,200.50`,
`(20.00)`, and `20.00 DR` are also supported.

## Category rules

Rules are stored in `config/category_rules.json`. Each rule contains:

- `id`: a unique rule name
- `category`: the category shown in reports
- `priority`: larger numbers run first
- `patterns`: keywords or regular expressions to search for

Example:

```json
{
  "id": "groceries",
  "category": "Groceries",
  "priority": 110,
  "patterns": ["\\bCOLES\\b", "\\bWOOLWORTHS\\b", "\\bALDI\\b"]
}
```

The first matching rule wins. Positive transactions are automatically treated
as income. Transactions that match no rule are marked `Uncategorised`, making
it easy to identify rules that should be added later.

## Output files

The selected output folder contains:

- `cleaned_transactions.csv`
- `category_summary.csv`
- `monthly_summary.csv`
- `merchant_summary.csv`
- `uncategorised_transactions.csv`
- `rejected_rows.csv`
- `analysis_summary.txt`
- `spending_dashboard.png`

## Project structure

```text
SpendSense/
├── main.py
├── requirements.txt
├── VIDEO_SCRIPT.md
├── config/category_rules.json
├── data/sample/anonymous_transactions.csv
├── outputs/
├── spendsense/
│   ├── loader.py
│   ├── cleaning.py
│   ├── categorizer.py
│   ├── analytics.py
│   ├── charting.py
│   ├── exporter.py
│   ├── pipeline.py
│   ├── cli.py
│   └── ui.py
└── tests/test_pipeline.py
```

Each module has one main responsibility. `pipeline.py` calls the modules in
order, while `ui.py` provides the desktop interface.

## Run the tests

```bash
python3 -m unittest discover -s tests -v
```

## Privacy

Never upload a real bank export to GitHub. The `data/raw/` folder is ignored by
Git, and the included sample file is fictional. Screenshots and demonstrations
should also use anonymised data.

## Current scope

The project deliberately supports one CSV at a time and uses transparent,
hand-written rules rather than machine learning. This keeps every category
decision understandable and makes the project achievable within the course
timeframe.
