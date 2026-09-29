# Spreadsheet Reconciliation Tool

A Python command-line tool for comparing CSV and XLSX files by a shared record ID.

Identify matching records, changed fields, and records present in only one file. Export the results to a CSV report and view record counts in the terminal.

## Current features

- Match records by a configurable key column, regardless of row order.
- Compare selected columns.
- Optionally compare numeric columns using exact decimal values.
- Preserve original field values in difference reports.
- Export results to CSV.
- Summarize matched, changed, source-only, and target-only records.
- Validate required headers, duplicate headers, row structure, and record IDs.
- Display readable errors for expected file and validation problems.

Supports CSV-to-CSV, XLSX-to-XLSX, and mixed CSV-to-XLSX comparisons. Reports are exported as CSV.

## Requirements

- Python 3.11 or newer
- openpyxl 3.1.5, installed using requirements.txt

## Setup

Clone the repository:

```powershell
git clone https://github.com/NuMetriq/spreadsheet-reconciliation-tool.git
cd spreadsheet-reconciliation-tool
```

Create and activate a virtual environment on Windows PowerShell:

```powershell
py -3.11 -m venv .venv
.\.venv\Scripts\Activate.ps1
```

Install dependencies:

```powershell
python -m pip install -r requirements.txt
```

Run the following commands from the repository's top folder.

## Example usage

The repository includes sample files in `data/`.

Compare customer names as text and amounts as decimal numbers:

```powershell
python src/reconcile.py --source data/source.csv --target data/target.csv --key invoice_id --columns customer amount --numeric-columns amount --output reports/reconciliation.csv
```

Expected summary:

```text
Matched records: 1
Changed records: 1
Source-only records: 1
Target-only records: 1
```

The report is written to `reports/reconciliation.csv`.

For usage instructions:

```powershell
python src/reconcile.py --help
```

## Arguments

| Argument | Purpose |
|---|---|
| `--source` | Source CSV or XLSX path; required |
| `--target` | Target CSV or XLSX path; required |
| `--key` | Unique record ID column; required |
| `--columns` | One or more columns to compare; required |
| `--numeric-columns` | Optional columns to compare as decimal numbers |
| `--output` | Report destination; required |

Numeric columns must also appear in `--columns`. Omit `--numeric-columns` to compare all selected fields as text.

Relative paths are resolved from the terminal's current folder. Quote paths containing spaces.

## Report format

| Field | Meaning |
|---|---|
| `record_id` | Value from the selected key column |
| `status` | `matched`, `changed`, `source_only`, or `target_only` |
| `column` | Changed column name |
| `source_value` | Original source value |
| `target_value` | Original target value |

Changed records produce one report row per changed field. Other statuses produce one row per record, with the field-detail columns left empty.

The terminal summary counts unique records per status, so a record with several changed fields is counted once.

## Comparison rules and limitations

- Both files must contain the key column and all selected comparison columns.
- IDs must be nonblank and unique within each file.
- IDs and text fields are case-sensitive; surrounding whitespace is preserved.
- Numeric comparison treats `150.00` and `150.0` as equal.
- Numeric comparison uses exact equality, with no tolerance or rounding.
- Blank values, currency symbols, thousands separators, and nonfinite values are rejected when parsed as numbers.
- Numeric values are currently parsed only for records whose IDs appear in both files.
- CSV files must use UTF-8 encoding; a UTF-8 byte-order marker is supported.
- Both input files are loaded into memory.
- An existing report at the output path is replaced on a successful run.
- A rejected run may leave a report from an earlier run in place.
- XLSX input reads the first worksheet and requires nonblank, unique text headers in row 1.
- Completely blank Excel rows are skipped; blank cells become empty strings.
- Formula cells and Excel error cells are rejected.
- Excel values are read without their display formatting. Store IDs as text when leading zeros matter.
- Legacy `.xls` files are not supported.

## Tests

```powershell
python -m unittest discover -s tests -v
```

Tests cover CSV validation, record indexing, field comparison, decimal parsing, reconciliation, and summary counts.

## Planned improvements

- Selectable Excel worksheets
- Configurable numeric tolerances
- A simple user interface

## License

MIT. See `LICENSE`.