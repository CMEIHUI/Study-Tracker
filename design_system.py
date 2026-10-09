import customtkinter as ctk
import tkinter as tk
from config import THEMES, CORNER_RADIUS, PADDING, FONT_FAMILY, FONT_SIZES


class DesignSystem:
    """Centralized design system for consistent UI components."""

    def __init__(self, theme="light"):
        self.theme = THEMES[theme]
        self.corner_radius = CORNER_RADIUS
        self.padding = PADDING

    def get_color(self, key):
        """Return a color value from the active theme."""
        return self.theme.get(key, "#ffffff")

    def get_font(self, size="base", weight="normal"):
        """Return a font tuple using the shared font settings."""
        size_value = FONT_SIZES.get(size, FONT_SIZES["base"])
        return (FONT_FAMILY, size_value, weight)

    def create_card(self, parent, **kwargs):
        """Create a styled card frame."""
        defaults = dict(
            corner_radius=self.corner_radius,
            fg_color=self.theme["surface"],
            border_width=1,
            border_color="#E2E8F0",
        )
        defaults.update(kwargs)
        return ctk.CTkFrame(parent, **defaults)

    def create_button(self, parent, text, command=None, style="primary", **kwargs):
        """Create a themed button."""
        defaults = dict(
            text=text,
            command=command,
            corner_radius=12,
            font=(FONT_FAMILY, 14, "bold"),
            height=42,
            fg_color=self.theme["primary"],
            hover_color="#1D4ED8",
            text_color="white",
        )

        layout_kwargs = {
            "padx",
            "pady",
            "anchor",
            "fill",
            "side",
            "expand",
            "ipadx",
            "ipady",
            "column",
            "row",
            "columnspan",
            "rowspan",
            "sticky",
            "before",
            "after",
            "in_",
        }
        filtered_kwargs = {key: value for key, value in kwargs.items() if key not in layout_kwargs}
        defaults.update(filtered_kwargs)
        return ctk.CTkButton(parent, **defaults)

    def create_label(self, parent, text, size="base", weight="normal", **kwargs):
        """Create a themed label."""
        defaults = dict(
            text=text,
            font=self.get_font(size, weight),
            text_color=self.theme["text_primary"],
        )
        defaults.update(kwargs)
        return ctk.CTkLabel(parent, **defaults)

    def create_entry(self, parent, placeholder="", **kwargs):
        """Create a themed entry field."""
        defaults = dict(
            placeholder_text=placeholder,
            corner_radius=self.corner_radius,
            font=self.get_font("base", "normal"),
            height=44,
            border_width=1,
            border_color="#E2E8F0",
            fg_color=self.theme["surface"],
        )
        defaults.update(kwargs)
        return ctk.CTkEntry(parent, **defaults)


class Tooltip:
    """Simple hover tooltip for Tk widgets using a transient Toplevel."""

    def __init__(self, widget, text, delay=500):
        self.widget = widget
        self.text = text
        self.delay = int(delay)
        self.tipwindow = None
        self.id = None
        try:
            widget.bind("<Enter>", self.schedule)
            widget.bind("<Leave>", self.hide)
            widget.bind("<ButtonPress>", self.hide)
        except Exception:
            pass

    def schedule(self, event=None):
        self.unschedule()
        try:
            self.id = self.widget.after(self.delay, self.show)
        except Exception:
            self.show()

    def unschedule(self):
        if self.id:
            try:
                self.widget.after_cancel(self.id)
            except Exception:
                pass
            self.id = None

    def show(self):
        if self.tipwindow or not self.text:
            return
        # Support callable text providers for dynamic tooltips
        try:
            display_text = self.text() if callable(self.text) else self.text
        except Exception:
            display_text = self.text
        if not display_text:
            return
        x = self.widget.winfo_rootx() + 20
        y = self.widget.winfo_rooty() + self.widget.winfo_height() + 6
        try:
            self.tipwindow = tw = tk.Toplevel(self.widget)
            tw.wm_overrideredirect(True)
            tw.wm_geometry(f"+{x}+{y}")
            lbl = ctk.CTkLabel(tw, text=display_text, fg_color="#0f172a", text_color="#ffffff", corner_radius=6)
            lbl.pack(ipadx=6, ipady=4)
        except Exception:
            self.tipwindow = None

    def hide(self, event=None):
        self.unschedule()
        if self.tipwindow:
            try:
                self.tipwindow.destroy()
            except Exception:
                pass
            self.tipwindow = None

    def update_text(self, text):
        self.text = text

    
def attach_tooltip(widget, text, delay=500):
    """Convenience helper: attach a Tooltip to a widget and return it."""
    try:
        tt = Tooltip(widget, text, delay=delay)
        return tt
    except Exception:
        return None