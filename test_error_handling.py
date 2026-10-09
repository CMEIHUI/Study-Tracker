import unittest

from utils import ValidationError, handle_operation_error


class ErrorHandlingTests(unittest.TestCase):
    def test_handle_operation_error_logs_and_returns_user_message(self):
        with self.assertLogs("study_tracker", level="ERROR") as captured:
            result = handle_operation_error(
                ValueError("database unavailable"),
                context="loading analytics",
                user_message="We couldn't load analytics right now.",
            )

        self.assertEqual(result, "We couldn't load analytics right now.")
        self.assertTrue(any("loading analytics" in message for message in captured.output))

    def test_handle_operation_error_uses_validation_message(self):
        with self.assertLogs("study_tracker", level="ERROR") as captured:
            result = handle_operation_error(
                ValidationError("Deadline must use YYYY-MM-DD format."),
                context="validating task input",
                user_message="Please review the information and try again.",
            )

        self.assertEqual(result, "Please review the information and try again.")
        self.assertTrue(any("validating task input" in message for message in captured.output))


if __name__ == "__main__":
    unittest.main()
