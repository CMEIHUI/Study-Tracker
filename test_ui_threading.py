import threading

from utils import run_in_background


class DummyWidget:
    def __init__(self):
        self.callbacks = []

    def after(self, delay, callback):
        self.callbacks.append((delay, callback))
        callback()

    def winfo_exists(self):
        return True


def test_run_in_background_invokes_callback_with_result():
    widget = DummyWidget()
    completed = {}

    def target():
        return 42

    def on_done(value):
        completed["value"] = value

    thread = run_in_background(widget, target, callback=on_done)
    thread.join(timeout=2)

    assert completed["value"] == 42
    assert widget.callbacks


def test_run_in_background_skips_callback_when_widget_cannot_schedule_ui_work():
    class BrokenWidget:
        def winfo_exists(self):
            raise RuntimeError("main thread is not in main loop")

        def after(self, delay, callback):
            raise RuntimeError("main thread is not in main loop")

    widget = BrokenWidget()
    completed = {}

    def target():
        return 99

    def on_done(value):
        completed["value"] = value

    thread = run_in_background(widget, target, callback=on_done)
    thread.join(timeout=2)

    assert completed == {}
