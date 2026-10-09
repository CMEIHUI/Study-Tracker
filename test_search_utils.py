import unittest

from search_utils import filter_search_results


class SearchUtilsTests(unittest.TestCase):
    def test_filters_tasks_by_keyword_and_status(self):
        records = [
            (1, "Math", "Algebra revision", "Review formulas", "High", "2025-01-01", "Pending"),
            (2, "Math", "Geometry worksheet", "Solve proofs", "Low", "2025-01-02", "Completed"),
        ]

        results = filter_search_results(
            records,
            keyword="algebra",
            entity_type="Tasks",
            status_filter="Pending",
            priority_filter="All",
            sort_mode="Name",
        )

        self.assertEqual(len(results), 1)
        self.assertEqual(results[0][2], "Algebra revision")

    def test_searches_subjects_by_keyword(self):
        records = [
            (1, "Biology", "#22c55e"),
            (2, "History", "#3b82f6"),
        ]

        results = filter_search_results(
            records,
            keyword="bio",
            entity_type="Subjects",
            status_filter="All",
            priority_filter="All",
            sort_mode="Name",
        )

        self.assertEqual(len(results), 1)
        self.assertEqual(results[0][1], "Biology")


if __name__ == "__main__":
    unittest.main()
