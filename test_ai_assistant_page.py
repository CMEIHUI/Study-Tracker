import unittest
import customtkinter as ctk

try:
    import tkinter as _tkinter
    _test_root = _tkinter.Tk()
    _test_root.destroy()
    GUI_AVAILABLE = True
except Exception:
    GUI_AVAILABLE = False

from ai_assistant import AIStudyAssistantPage


class AIStudyAssistantPageTests(unittest.TestCase):
    def setUp(self):
        if not GUI_AVAILABLE:
            self.skipTest("Tkinter/Tcl not available in this environment")
        self.root = ctk.CTk()
        self.root.withdraw()

    def tearDown(self):
        try:
            self.root.destroy()
        except Exception:
            pass

    def test_assistant_page_can_clear_chat_history(self):
        class StubDatabase:
            def __init__(self):
                self._history = []

            def add_ai_history(self, query_text, response_text):
                self._history.append((1, query_text, response_text, "2026-08-02"))
                return True

            def get_ai_history(self, limit=50):
                return list(self._history[-limit:])

            def clear_ai_history(self):
                self._history.clear()
                return True

        db = StubDatabase()
        page = AIStudyAssistantPage(self.root, db)
        page._persist_message("Explain Python Loop", "A loop repeats code.")
        page.clear_chat_history()
        self.assertEqual(db.get_ai_history(limit=50), [])


if __name__ == "__main__":
    unittest.main()
