"""CSV loading and lightweight file inspection."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

import pandas as pd


@dataclass(frozen=True)
class LoadedCsv:
    frame: pd.DataFrame
    encoding: str


def load_csv(path: str | Path) -> LoadedCsv:
    """Load a CSV using common bank-export encodings.

    ``sep=None`` lets pandas detect comma, semicolon, tab, and pipe delimiters.
    """

    source = Path(path)
    if not source.exists():
        raise FileNotFoundError(f"CSV file not found: {source}")
    if not source.is_file():
        raise ValueError(f"The selected path is not a file: {source}")
    if source.stat().st_size == 0:
        raise ValueError("The selected CSV file is empty.")

    last_error: Exception | None = None
    for encoding in ("utf-8-sig", "utf-8", "cp1252", "latin-1"):
        try:
            frame = pd.read_csv(source, sep=None, engine="python", encoding=encoding)
            if frame.columns.empty:
                raise ValueError("The CSV does not contain a header row.")
            if frame.empty:
                raise ValueError("The CSV has column names but no transaction rows.")
            return LoadedCsv(frame=frame, encoding=encoding)
        except (UnicodeDecodeError, pd.errors.ParserError, pd.errors.EmptyDataError) as error:
            last_error = error

    raise ValueError(f"Unable to read CSV: {last_error}")
