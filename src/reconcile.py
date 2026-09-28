import csv
import argparse
from pathlib import Path


def read_csv(
    file_path: Path,
    required_columns: list[str] | None = None,
) -> list[dict[str, str]]:
    with file_path.open(newline="", encoding="utf-8-sig") as file:
        reader = csv.DictReader(file)
        headers = reader.fieldnames

        if not headers:
            raise ValueError(f"{file_path}: missing header row")

        if len(headers) != len(set(headers)):
            raise ValueError(f"{file_path}: duplicate column names")

        if required_columns is not None:
            missing_columns = [
                column
                for column in required_columns
                if column not in headers
            ]

            if missing_columns:
                missing_names = ", ".join(missing_columns)
                raise ValueError(
                    f"{file_path}: missing required columns: {missing_names}"
                )

        rows = []

        for row_number, row in enumerate(reader, start=1):
            if None in row:
                raise ValueError(
                    f"{file_path}: data row {row_number} has extra fields"
                )

            if any(value is None for value in row.values()):
                raise ValueError(
                    f"{file_path}: data row {row_number} has missing fields"
                )

            rows.append(row)

        return rows


def compare_rows(
    source_row: dict[str, str],
    target_row: dict[str, str],
    columns: list[str],
) -> dict[str, tuple[str, str]]:
    differences = {}

    for column in columns:
        source_value = source_row[column]
        target_value = target_row[column]

        if source_value != target_value:
            differences[column] = (source_value, target_value)

    return differences

def index_rows(
    rows: list[dict[str, str]],
    key_column: str,
) -> dict[str, dict[str, str]]:
    indexed_rows = {}

    for row_number, row in enumerate(rows, start=1):
        if key_column not in row:
            raise ValueError(
                f"Data row {row_number}: missing key column '{key_column}'"
            )

        key = row[key_column]

        if key is None or not key.strip():
            raise ValueError(
                f"Data row {row_number}: blank key in '{key_column}'"
            )

        if key in indexed_rows:
            raise ValueError(f"Duplicate key found: {key}")

        indexed_rows[key] = row

    return indexed_rows


def reconcile(
    source_rows: list[dict[str, str]],
    target_rows: list[dict[str, str]],
    key_column: str,
    comparison_columns: list[str],
) -> list[dict[str, str]]:
    source_index = index_rows(source_rows, key_column)
    target_index = index_rows(target_rows, key_column)

    all_ids = set(source_index) | set(target_index)
    results = []

    for record_id in sorted(all_ids):
        if record_id not in target_index:
            results.append({
                "record_id": record_id,
                "status": "source_only",
                "column": "",
                "source_value": "",
                "target_value": "",
            })
        elif record_id not in source_index:
            results.append({
                "record_id": record_id,
                "status": "target_only",
                "column": "",
                "source_value": "",
                "target_value": "",
            })
        else:
            differences = compare_rows(
                source_index[record_id],
                target_index[record_id],
                comparison_columns,
            )

            if differences:
                for column, values in differences.items():
                    source_value, target_value = values

                    results.append({
                        "record_id": record_id,
                        "status": "changed",
                        "column": column,
                        "source_value": source_value,
                        "target_value": target_value,
                    })
            else:
                results.append({
                    "record_id": record_id,
                    "status": "matched",
                    "column": "",
                    "source_value": "",
                    "target_value": "",
                })

    return results


def write_report(
    results: list[dict[str, str]],
    output_path: Path,
) -> None:
    fieldnames = [
        "record_id",
        "status",
        "column",
        "source_value",
        "target_value",
    ]

    output_path.parent.mkdir(parents=True, exist_ok=True)

    with output_path.open(
        "w",
        newline="",
        encoding="utf-8-sig",
    ) as file:
        writer = csv.DictWriter(file, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(results)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Compare two CSV files and export a reconciliation report."
    )

    parser.add_argument("--source", type=Path, required=True)
    parser.add_argument("--target", type=Path, required=True)
    parser.add_argument("--key", required=True)
    parser.add_argument("--columns", nargs="+", required=True)
    parser.add_argument("--output", type=Path, required=True)

    args = parser.parse_args()

    source_path = args.source.resolve()
    target_path = args.target.resolve()
    output_path = args.output.resolve()

    if output_path in (source_path, target_path):
        parser.error("Output path must differ from both input paths.")

    required_columns = [args.key] + args.columns

    try:
        source_rows = read_csv(args.source, required_columns)
        target_rows = read_csv(args.target, required_columns)

        results = reconcile(
            source_rows,
            target_rows,
            key_column=args.key,
            comparison_columns=args.columns,
        )

        write_report(results, args.output)

    except (ValueError, OSError, csv.Error) as error:
        parser.exit(status=1, message=f"Error: {error}\n")

    print(f"Report saved to: {args.output}")