import tempfile
import unittest
from pathlib import Path

from src.reconcile import compare_rows, index_rows, read_csv, reconcile


class TestCompareRows(unittest.TestCase):
    def test_identical_rows_have_no_differences(self):
        source = {"customer": "Acme Supply", "amount": "150.00"}
        target = {"customer": "Acme Supply", "amount": "150.00"}

        result = compare_rows(source, target, ["customer", "amount"])

        self.assertEqual(result, {})

    def test_changed_amount_returns_both_values(self):
        source = {"customer": "Acme Supply", "amount": "150.00"}
        target = {"customer": "Acme Supply", "amount": "175.00"}

        result = compare_rows(source, target, ["customer", "amount"])

        self.assertEqual(result, {"amount": ("150.00", "175.00")})

    def test_unselected_columns_are_ignored(self):
        source = {"customer": "Acme Supply", "amount": "150.00"}
        target = {"customer": "Acme Supply", "amount": "175.00"}

        result = compare_rows(source, target, ["customer"])

        self.assertEqual(result, {})


class TestReconcile(unittest.TestCase):
    def test_matches_by_id_when_rows_are_reordered(self):
        source = [
            {"id": "A", "amount": "10.00"},
            {"id": "B", "amount": "20.00"},
        ]
        target = [
            {"id": "B", "amount": "25.00"},
            {"id": "A", "amount": "10.00"},
        ]

        result = reconcile(source, target, "id", ["amount"])

        self.assertEqual(result, [
            {
                "record_id": "A",
                "status": "matched",
                "column": "",
                "source_value": "",
                "target_value": "",
            },
            {
                "record_id": "B",
                "status": "changed",
                "column": "amount",
                "source_value": "20.00",
                "target_value": "25.00",
            },
        ])

    def test_reports_records_missing_from_either_file(self):
        source = [{"id": "A", "amount": "10.00"}]
        target = [{"id": "B", "amount": "20.00"}]

        result = reconcile(source, target, "id", ["amount"])

        self.assertEqual(result, [
            {
                "record_id": "A",
                "status": "source_only",
                "column": "",
                "source_value": "",
                "target_value": "",
            },
            {
                "record_id": "B",
                "status": "target_only",
                "column": "",
                "source_value": "",
                "target_value": "",
            },
        ])


class TestIndexRows(unittest.TestCase):
    def test_rejects_missing_key_column(self):
        rows = [{"amount": "10.00"}]

        with self.assertRaisesRegex(ValueError, "missing key column"):
            index_rows(rows, "id")

    def test_rejects_blank_key(self):
        rows = [{"id": "   ", "amount": "10.00"}]

        with self.assertRaisesRegex(ValueError, "blank key"):
            index_rows(rows, "id")

    def test_rejects_duplicate_keys(self):
        rows = [
            {"id": "A", "amount": "10.00"},
            {"id": "A", "amount": "20.00"},
        ]

        with self.assertRaisesRegex(ValueError, "Duplicate key"):
            index_rows(rows, "id")


class TestReadCsv(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp_dir.cleanup)
        self.csv_path = Path(self.temp_dir.name) / "input.csv"

    def test_reads_valid_csv(self):
        self.csv_path.write_text(
            "id,amount\nA,10.00\n",
            encoding="utf-8",
        )

        result = read_csv(self.csv_path, ["id", "amount"])

        self.assertEqual(result, [{"id": "A", "amount": "10.00"}])

    def test_rejects_missing_column_with_no_data_rows(self):
        self.csv_path.write_text(
            "id,customer\n",
            encoding="utf-8",
        )

        with self.assertRaisesRegex(
            ValueError, "missing required columns: amount"
        ):
            read_csv(self.csv_path, ["id", "amount"])

    def test_rejects_duplicate_headers(self):
        self.csv_path.write_text(
            "id,amount,amount\nA,10.00,20.00\n",
            encoding="utf-8",
        )

        with self.assertRaisesRegex(ValueError, "duplicate column names"):
            read_csv(self.csv_path)

    def test_rejects_empty_file(self):
        self.csv_path.write_text("", encoding="utf-8")

        with self.assertRaisesRegex(ValueError, "missing header row"):
            read_csv(self.csv_path)

    def test_rejects_extra_fields(self):
        self.csv_path.write_text(
            "id,amount\nA,10.00,unexpected\n",
            encoding="utf-8",
        )

        with self.assertRaisesRegex(ValueError, "data row 1 has extra fields"):
            read_csv(self.csv_path)

    def test_rejects_missing_fields(self):
        self.csv_path.write_text(
            "id,amount\nA\n",
            encoding="utf-8",
        )

        with self.assertRaisesRegex(ValueError, "data row 1 has missing fields"):
            read_csv(self.csv_path)