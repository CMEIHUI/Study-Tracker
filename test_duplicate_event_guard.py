from report import ReportWindow


class DummyWidget:
    def __init__(self):
        self.state = None
        self.text = None

    def configure(self, **kwargs):
        if "state" in kwargs:
            self.state = kwargs["state"]
        if "text" in kwargs:
            self.text = kwargs["text"]


class DummyButton(DummyWidget):
    pass


def test_report_generation_guard_blocks_duplicate_runs():
    window = ReportWindow.__new__(ReportWindow)
    window._report_generation_in_progress = False
    window.generate_button = DummyButton()
    window.refresh_button = DummyButton()
    window.button_frame = DummyWidget()
    window.button_frame.winfo_children = lambda: []
    window.report_textbox = DummyWidget()
    window.report_textbox.delete = lambda *args, **kwargs: None
    window.report_textbox.insert = lambda *args, **kwargs: None

    window._set_report_loading_state()
    assert window.generate_button.state == "disabled"
    assert window.refresh_button.state == "disabled"

    window._reset_report_loading_state()
    assert window.generate_button.state == "normal"
    assert window.refresh_button.state == "normal"
