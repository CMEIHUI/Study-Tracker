from utils import set_loading_state


class DummyWidget:
    def __init__(self):
        self.state = None
        self.text = None

    def configure(self, **kwargs):
        if "state" in kwargs:
            self.state = kwargs["state"]
        if "text" in kwargs:
            self.text = kwargs["text"]


def test_set_loading_state_disables_button_and_updates_text():
    label = DummyWidget()
    button = DummyWidget()

    set_loading_state(label, button, "Generating AI analysis...", loading=True)

    assert label.text == "Generating AI analysis..."
    assert button.state == "disabled"

    set_loading_state(label, button, "Ready", loading=False)

    assert label.text == "Ready"
    assert button.state == "normal"
