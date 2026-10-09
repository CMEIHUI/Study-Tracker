import os
from tkinter import filedialog

import customtkinter as ctk
from PIL import Image, ImageOps
import customtkinter as ctk


VALID_APPEARANCE_MODES = {"System", "Light", "Dark", "Custom"}


def normalize_appearance_mode(value):
    if not value:
        return "Light"
    normalized_value = str(value).strip()
    if not normalized_value:
        return "Light"
    lowered = normalized_value.lower()
    if lowered in {"light", "dark", "system"}:
        return normalized_value.capitalize() if lowered != "system" else "System"
    if lowered in {"custom background", "custom", "custombackground"}:
        return "Custom"
    return "Light"


def load_background_image(image_path, size=None):
    if not image_path or not os.path.exists(image_path):
        return None
    try:
        with Image.open(image_path) as image:
            image = ImageOps.exif_transpose(image)
            if image.mode not in {"RGBA", "RGB", "L"}:
                image = image.convert("RGBA")
            if size is None:
                size = (1600, 900)
            width, height = size
            if width <= 0 or height <= 0:
                return None
            image_width, image_height = image.size
            if image_width and image_height:
                aspect_ratio = min(width / image_width, height / image_height)
                target_width = max(1, int(image_width * aspect_ratio))
                target_height = max(1, int(image_height * aspect_ratio))
                resized_image = image.resize((target_width, target_height), Image.Resampling.LANCZOS)
            else:
                resized_image = image.resize(size, Image.Resampling.LANCZOS)
            return ctk.CTkImage(light_image=resized_image, dark_image=resized_image, size=resized_image.size)
    except Exception:
        return None


class AppearanceManager:
    _instance = None

    def __init__(self):
        self.appearance_mode = "Light"
        self.background_image_path = ""
        self.background_image_object = None
        self._observers = []
        self._photo_cache = {}
        self._last_size = None

    @classmethod
    def get_instance(cls):
        if cls._instance is None:
            cls._instance = cls()
        return cls._instance

    def register_observer(self, callback):
        if callback not in self._observers:
            self._observers.append(callback)
            try:
                callback(self.get_state(), target=None)
            except Exception:
                pass

    def unregister_observer(self, callback):
        if callback in self._observers:
            self._observers.remove(callback)

    def get_state(self):
        return {
            "appearance_mode": self.appearance_mode,
            "background_image_path": self.background_image_path,
            "background_image_object": self.background_image_object,
        }

    def _notify(self, target=None):
        for callback in list(self._observers):
            try:
                callback(self.get_state(), target=target)
            except Exception:
                continue

    def _ensure_background_photo(self, size=None):
        if self.appearance_mode != "Custom":
            self.background_image_object = None
            return None
        if not self.background_image_path or not os.path.exists(self.background_image_path):
            self.background_image_object = None
            return None
        if self.background_image_object is not None and self._last_size == size:
            return self.background_image_object
        if size is None:
            size = (1600, 900)
        cache_key = (self.background_image_path, size)
        if cache_key in self._photo_cache:
            self.background_image_object = self._photo_cache[cache_key]
            return self.background_image_object
        if self.background_image_object is not None and self._last_size == size:
            return self.background_image_object
        photo = load_background_image(self.background_image_path, size)
        if photo is not None:
            self._photo_cache[cache_key] = photo
            self.background_image_object = photo
            self._last_size = size
        else:
            self.background_image_object = None
            self._last_size = size
        return self.background_image_object

    def apply_current_state(self, target=None, settings=None):
        if settings is not None:
            self.load_settings(settings)
        if self.appearance_mode == "Custom":
            try:
                current_mode = ctk.get_appearance_mode()
            except Exception:
                current_mode = "Light"
            ctk.set_appearance_mode(current_mode)
        elif self.appearance_mode == "Light":
            ctk.set_appearance_mode("Light")
        elif self.appearance_mode == "Dark":
            ctk.set_appearance_mode("Dark")
        else:
            ctk.set_appearance_mode("System")

        if self.appearance_mode == "Custom":
            size = None
            if target is not None:
                try:
                    width = target.winfo_width()
                    height = target.winfo_height()
                    if width > 1 and height > 1:
                        size = (width, height)
                except Exception:
                    size = None
            self._ensure_background_photo(size)
        else:
            self.background_image_object = None
        self._notify(target=target)
        if target is not None and hasattr(target, "update_idletasks"):
            try:
                target.update_idletasks()
            except Exception:
                pass
        return self.get_state()

    def load_settings(self, settings_payload=None):
        if not isinstance(settings_payload, dict):
            return self.get_state()
        appearance_mode = normalize_appearance_mode(settings_payload.get("appearance_mode", "Light"))
        background_image_path = str(settings_payload.get("background_image_path") or "")
        if appearance_mode != "Custom":
            background_image_path = ""
        self.appearance_mode = appearance_mode
        self.background_image_path = background_image_path
        self.background_image_object = None
        self._last_size = None
        return self.get_state()

    def save_settings(self, settings_manager=None):
        if settings_manager is None:
            return self.get_state()
        settings_manager.update_setting("appearance_mode", self.appearance_mode)
        settings_manager.update_setting("background_image_path", self.background_image_path)
        settings_manager.save_settings()
        return self.get_state()

    def apply_light_mode(self, target=None, settings_manager=None):
        self.appearance_mode = "Light"
        self.background_image_path = ""
        self.background_image_object = None
        self._last_size = None
        self.apply_current_state(target=target)
        if settings_manager is not None:
            self.save_settings(settings_manager)
        return self.get_state()

    def apply_dark_mode(self, target=None, settings_manager=None):
        self.appearance_mode = "Dark"
        self.background_image_path = ""
        self.background_image_object = None
        self._last_size = None
        self.apply_current_state(target=target)
        if settings_manager is not None:
            self.save_settings(settings_manager)
        return self.get_state()

    def apply_custom_background(self, image_path, target=None, settings_manager=None):
        if not image_path or not os.path.exists(image_path):
            return None
        self.appearance_mode = "Custom"
        self.background_image_path = image_path
        self.background_image_object = None
        self._last_size = None
        self.apply_current_state(target=target)
        if settings_manager is not None:
            self.save_settings(settings_manager)
        return self.get_state()

    def select_background_image(self, parent=None, target=None, settings_manager=None):
        file_path = filedialog.askopenfilename(
            title="Select background image",
            parent=parent,
            filetypes=[("Image files", "*.png *.jpg *.jpeg *.bmp *.gif")],
        )
        if not file_path:
            return None
        return self.apply_custom_background(file_path, target=target, settings_manager=settings_manager)

    def remove_custom_background(self, target=None, settings_manager=None):
        self.appearance_mode = "Light"
        self.background_image_path = ""
        self.background_image_object = None
        self._last_size = None
        self.apply_current_state(target=target)
        if settings_manager is not None:
            self.save_settings(settings_manager)
        return self.get_state()

    def get_current_appearance_mode(self):
        return self.appearance_mode
