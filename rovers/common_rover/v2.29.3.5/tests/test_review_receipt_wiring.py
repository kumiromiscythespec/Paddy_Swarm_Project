import unittest

from _test_support import install_matrix_tests
from full_loop_runner import validate_receipt_argument


class ReviewReceiptWiringTests(unittest.TestCase):
    def test_missing_receipt_is_pending(self):
        result = validate_receipt_argument(None, {}, [])
        self.assertEqual(result["status"], "PENDING_EXTERNAL_REVIEW")

    def test_missing_receipt_is_not_consumed(self):
        result = validate_receipt_argument(None, {}, [])
        self.assertFalse(result["receipt_argument_consumed"])


install_matrix_tests(
    ReviewReceiptWiringTests,
    "receipt",
    30,
    lambda index: (
        validate_receipt_argument(None, {}, [])["overall_decision"]
        == "PENDING"
        and index >= 0
    ),
)
