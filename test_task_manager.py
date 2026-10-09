import time
import unittest

from task_manager import BackgroundTaskManager


class TaskManagerTests(unittest.TestCase):
    def test_duplicate_tasks_are_not_scheduled_twice(self):
        manager = BackgroundTaskManager()
        calls = []

        def target():
            calls.append("run")
            time.sleep(0.05)
            return "done"

        first_handle = manager.submit_task(
            "analytics",
            target=target,
            callback=lambda result: calls.append(result),
        )
        second_handle = manager.submit_task(
            "analytics",
            target=target,
            callback=lambda result: calls.append(result),
        )

        self.assertIs(first_handle, second_handle)
        time.sleep(0.2)
        self.assertEqual(calls.count("run"), 1)

    def test_error_callback_is_invoked_for_failures(self):
        manager = BackgroundTaskManager()
        errors = []

        def target():
            raise RuntimeError("boom")

        manager.submit_task(
            "report",
            target=target,
            error_callback=lambda error, safe_message: errors.append((error, safe_message)),
        )

        time.sleep(0.2)
        self.assertTrue(errors)
        self.assertEqual(errors[0][0].args[0], "boom")


if __name__ == "__main__":
    unittest.main()
