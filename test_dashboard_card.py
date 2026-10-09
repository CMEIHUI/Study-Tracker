import unittest
import customtkinter as ctk

from dashboard import DashboardCard


def _has_tkinter_support():
    try:
        import tkinter as _tkinter
        root = _tkinter.Tk()
        root.withdraw()
        root.destroy()
        return True
    except Exception:
        return False


class DashboardCardTests(unittest.TestCase):
    def test_dashboard_card_initializes_and_shows_value(self):
        if not _has_tkinter_support():
            self.skipTest("Tkinter/Tcl not available in this environment")

        root = ctk.CTk()
        root.withdraw()
        try:
            card = DashboardCard(root, "Subjects", "0")
            self.assertEqual(card.value_label.cget("text"), "0")
        finally:
            root.destroy()


if __name__ == "__main__":
    unittest.main()
