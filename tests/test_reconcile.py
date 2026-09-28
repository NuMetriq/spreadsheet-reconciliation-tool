import unittest

from src.reconcile import compare_rows, index_rows, reconcile


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