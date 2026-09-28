import unittest

from src.reconcile import compare_rows


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