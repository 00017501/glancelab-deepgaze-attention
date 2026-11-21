"""Reading and writing the CSV tables, and the Markdown table helper."""

import csv
from pathlib import Path

from pydantic import BaseModel

# Decimal places in the CSVs; enough to reproduce the Markdown tables exactly.
CSV_DECIMALS = 4


def format_cell(value: object, decimals: int = 1, missing: str = "") -> str:
    """Format a table cell: floats to `decimals` places, `None` as `missing`."""
    if value is None:
        return missing
    return f"{value:.{decimals}f}" if isinstance(value, float) else str(value)


def write_csv(path: Path, rows: list[BaseModel], model: type[BaseModel]) -> None:
    """Write rows as CSV with the model's fields as columns, floats rounded and `None` left empty."""
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as file:
        writer = csv.DictWriter(file, fieldnames=list(model.model_fields))
        writer.writeheader()
        for row in rows:
            writer.writerow(
                {
                    field: round(value, CSV_DECIMALS) if isinstance(value, float) else ("" if value is None else value)
                    for field, value in row.model_dump(mode="json").items()
                }
            )


def read_csv[RowModel: BaseModel](path: Path, model: type[RowModel]) -> list[RowModel]:
    """Read a CSV written by `write_csv` back into its row model; empty cells become `None`."""
    with path.open(newline="", encoding="utf-8") as file:
        return [
            model.model_validate({field: (None if value == "" else value) for field, value in row.items()})
            for row in csv.DictReader(file)
        ]


def md_table(headers: list[str], rows: list[list[str]]) -> str:
    """Return a Markdown table."""
    lines = ["| " + " | ".join(headers) + " |", "|" + "---|" * len(headers)]
    lines += ["| " + " | ".join(row) + " |" for row in rows]
    return "\n".join(lines)
