import os
import tkinter as tk
import customtkinter as ctk
from tkinter import filedialog, messagebox
from PIL import Image

from database import DatabaseManager
from design_system import DesignSystem
from appearance_manager import AppearanceManager


class ProfileWindow(ctk.CTkFrame):
    """User profile page showing personal info and study statistics."""

    def __init__(self, master, database, user_id=None, **kwargs):
        super().__init__(master, corner_radius=12, **kwargs)
        self.database = database or DatabaseManager()
        self.user_id = user_id
        self.design = DesignSystem()
        self.appearance = AppearanceManager.get_instance()
        self.user_row = None
        self.profile_image = None
        self.create_widgets()
        self.load_profile()

    def create_widgets(self):
        self.grid_columnconfigure(0, weight=1)
        header = ctk.CTkFrame(self, fg_color="transparent")
        header.grid(row=0, column=0, sticky="ew", padx=20, pady=(20, 6))
        header.grid_columnconfigure(1, weight=1)

        self.avatar_label = ctk.CTkLabel(header, text="", width=120, height=120, corner_radius=60)
        self.avatar_label.grid(row=0, column=0, rowspan=2, sticky="w")

        self.username_label = ctk.CTkLabel(header, text="Username", font=("Arial", 18, "bold"))
        self.username_label.grid(row=0, column=1, sticky="w", padx=12)

        self.edit_button = self.design.create_button(header, text="Edit Profile", command=self.enable_edit)
        self.edit_button.grid(row=0, column=2, sticky="e", padx=8)

        self.info_frame = ctk.CTkFrame(self, fg_color="transparent")
        self.info_frame.grid(row=1, column=0, sticky="nsew", padx=20, pady=8)
        self.info_frame.grid_columnconfigure(1, weight=1)

        # Labels
        labels = [
            ("Full name", "full_name"),
            ("Email", "email"),
            ("Account created", "created_at"),
            ("Last login", "last_login"),
        ]
        self.entries = {}
        for i, (label_text, key) in enumerate(labels):
            ctk.CTkLabel(self.info_frame, text=label_text).grid(row=i, column=0, sticky="w", pady=6)
            ent = ctk.CTkLabel(self.info_frame, text="", anchor="w")
            ent.grid(row=i, column=1, sticky="ew", padx=8)
            self.entries[key] = ent

        # Stats
        stats_frame = ctk.CTkFrame(self, fg_color="transparent")
        stats_frame.grid(row=2, column=0, sticky="nsew", padx=20, pady=(8, 20))
        for i in range(4):
            stats_frame.grid_columnconfigure(i, weight=1)

        self.stats_labels = {}
        stats = [
            ("Total study hours", "study_hours"),
            ("Completed tasks", "completed_tasks"),
            ("Current streak", "streak"),
            ("Total subjects", "subjects"),
        ]
        for i, (label_text, key) in enumerate(stats):
            frame = ctk.CTkFrame(stats_frame, width=140, height=90)
            frame.grid(row=0, column=i, padx=4, pady=4, sticky="nsew")
            frame.grid_propagate(False)
            ctk.CTkLabel(frame, text=label_text, font=("Arial", 10)).pack(pady=(8, 2))
            val = ctk.CTkLabel(frame, text="0", font=("Arial", 14, "bold"))
            val.pack(pady=(0, 8))
            self.stats_labels[key] = val

        # Recent activity
        ctk.CTkLabel(self, text="Recent study activity", font=("Arial", 14, "bold")).grid(row=3, column=0, sticky="w", padx=20)
        self.recent_container = ctk.CTkScrollableFrame(self)
        self.recent_container.grid(row=4, column=0, sticky="nsew", padx=20, pady=(8,20))
        self.recent_container.grid_columnconfigure(0, weight=1)

    def load_profile(self):
        if not self.user_id:
            # Cannot load profile without user id
            return
        row = self.database.get_user_by_id(self.user_id)
        if not row:
            return
        # Expected columns: id, username, email, password, full_name, profile_picture, created_at, last_login
        self.user_row = row
        username = row[1]
        email = row[2]
        full_name = row[4] if len(row) > 4 else ""
        profile_picture = row[5] if len(row) > 5 else ""
        created_at = row[6] if len(row) > 6 else ""
        last_login = row[7] if len(row) > 7 else ""

        self.username_label.configure(text=username)
        self.entries["full_name"].configure(text=full_name)
        self.entries["email"].configure(text=email)
        self.entries["created_at"].configure(text=created_at)
        self.entries["last_login"].configure(text=last_login)

        # Load avatar
        if profile_picture and os.path.exists(profile_picture):
            try:
                img = Image.open(profile_picture)
                img = img.resize((120, 120))
                self.profile_image = ctk.CTkImage(light_image=img, dark_image=img, size=(120, 120))
                self.avatar_label.configure(image=self.profile_image, text="")
            except Exception:
                self.avatar_label.configure(text="No Image")
        else:
            self.avatar_label.configure(text="No Image")

        # Load stats
        self.stats_labels["study_hours"].configure(text=str(self.database.get_total_study_hours()))
        self.stats_labels["completed_tasks"].configure(text=str(self.database.total_completed_tasks()))
        self.stats_labels["subjects"].configure(text=str(self.database.total_subjects()))
        # streak
        try:
            streak = self.database.get_current_study_streak()
        except Exception:
            streak = 0
        self.stats_labels["streak"].configure(text=str(streak))

        # Recent activity
        for w in self.recent_container.winfo_children():
            w.destroy()
        sessions = self.database.get_all_study_sessions()
        for s in sessions[:5]:
            duration_hours = round(s[2] / 60, 2) if s[2] else 0
            text = f"{s[1]} • {duration_hours}h • {s[3]}"
            ctk.CTkLabel(self.recent_container, text=text).pack(anchor="w", pady=4, padx=6)

    def enable_edit(self):
        # Open a small edit form overlay
        self.edit_win = ctk.CTkToplevel(self)
        self.edit_win.title("Edit Profile")
        self.edit_win.geometry("480x320")
        frame = ctk.CTkFrame(self.edit_win)
        frame.pack(fill="both", expand=True, padx=20, pady=20)

        ctk.CTkLabel(frame, text="Full name").pack(anchor="w")
        full_entry = ctk.CTkEntry(frame, width=400)
        full_entry.pack(pady=6)
        full_entry.insert(0, self.entries["full_name"].cget("text"))

        ctk.CTkLabel(frame, text="Email").pack(anchor="w")
        email_entry = ctk.CTkEntry(frame, width=400)
        email_entry.pack(pady=6)
        email_entry.insert(0, self.entries["email"].cget("text"))

        def choose_image():
            path = filedialog.askopenfilename(filetypes=[("Images", "*.png;*.jpg;*.jpeg;*.gif")])
            if path:
                image_path_entry.delete(0, "end")
                image_path_entry.insert(0, path)

        ctk.CTkLabel(frame, text="Profile picture").pack(anchor="w")
        image_path_entry = ctk.CTkEntry(frame, width=320)
        image_path_entry.pack(side="left", pady=6)
        choose_btn = self.design.create_button(frame, text="Choose", command=choose_image)
        choose_btn.pack(side="left", padx=8)

        def save():
            full = full_entry.get().strip()
            email = email_entry.get().strip()
            pic = image_path_entry.get().strip() or None
            try:
                ok = self.database.update_profile(self.user_id, full_name=full, email=email, profile_picture=pic)
                if ok:
                    messagebox.showinfo("Saved", "Profile updated.")
                    self.edit_win.destroy()
                    self.load_profile()
                else:
                    messagebox.showerror("Error", "Unable to save profile.")
            except Exception as e:
                messagebox.showerror("Error", str(e))

        save_btn = self.design.create_button(frame, text="Save", command=save)
        save_btn.pack(pady=12)
