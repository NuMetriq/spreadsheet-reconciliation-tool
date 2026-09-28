import csv
from pathlib import Path


def read_csv(file_path: Path) -> list[dict[str, str]]:
    with file_path.open(newline="", encoding="utf-8-sig") as file:
        reader = csv.DictReader(file)
        return list(reader)


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

    for row in rows:
        key = row[key_column]

        if key in indexed_rows:
            raise ValueError(f"Duplicate key found: {key}")

        indexed_rows[key] = row

    return indexed_rows


if __name__ == "__main__":
    project_root = Path(__file__).resolve().parent.parent

    source_path = project_root / "data" / "source.csv"
    target_path = project_root / "data" / "target.csv"

    source_rows = read_csv(source_path)
    target_rows = read_csv(target_path)

    source_index = index_rows(source_rows, "invoice_id")
    target_index = index_rows(target_rows, "invoice_id")

    source_ids = set(source_index)
    target_ids = set(target_index)

    shared_ids = source_ids & target_ids
    source_only_ids = source_ids - target_ids
    target_only_ids = target_ids - source_ids

    print("IDs in both files:", sorted(shared_ids))
    print("IDs only in source:", sorted(source_only_ids))
    print("IDs only in target:", sorted(target_only_ids))

    comparison_columns = ["customer", "amount"]

    for invoice_id in sorted(shared_ids):
        source_row = source_index[invoice_id]
        target_row = target_index[invoice_id]

        differences = compare_rows(
            source_row,
            target_row,
            comparison_columns,
        )

        if differences:
            print(f"\nChanged: {invoice_id}")

            for column, values in differences.items():
                source_value, target_value = values
                print(f"  {column}: {source_value} -> {target_value}")
        else:
            print(f"\nMatched: {invoice_id}")