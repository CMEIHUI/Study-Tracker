import unittest

from utils import ValidationError, validate_date_string, validate_required_field


class UtilsErrorHandlingTests(unittest.TestCase):
    def test_validate_required_field_rejects_blank_values(self):
        with self.assertRaises(ValidationError):
            validate_required_field("   ", "Task title")

    def test_validate_date_string_rejects_invalid_format(self):
        with self.assertRaises(ValidationError):
            validate_date_string("2026/07/20", "Deadline")

    def test_validate_date_string_accepts_valid_format(self):
        self.assertEqual(validate_date_string("2026-07-20", "Deadline"), "2026-07-20")


if __name__ == "__main__":
    unittest.main()
