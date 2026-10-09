import json
import os
import tkinter as tk
import urllib.error
import urllib.request
from datetime import datetime
import customtkinter as ctk

from design_system import DesignSystem
from utils import run_in_background, handle_operation_error


class AIStudyAssistantPage(ctk.CTkFrame):
    """Modern AI study assistant page with persistent chat history."""

    EXAMPLE_PROMPTS = [
        "Explain Python Loop",
        "Explain Java OOP",
        "Generate Quiz",
        "Summarize Notes",
        "Generate Study Plan",
    ]

    def __init__(self, master, database):
        super().__init__(master, corner_radius=24, fg_color="transparent")
        self.database = database
        self.design = DesignSystem()
        self._loading_after_id = None
        self._loading_dots = 0
        self.create_widgets()
        self.load_chat_history()

    def create_widgets(self):
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(1, weight=1)

        header = ctk.CTkFrame(self, fg_color="transparent")
        header.grid(row=0, column=0, sticky="ew", padx=10, pady=(10, 10))
        header.grid_columnconfigure(0, weight=1)

        self.design.create_label(
            header,
            text="🤖 AI Study Assistant",
            size="3xl",
            weight="bold",
        ).grid(row=0, column=0, sticky="w")

        self.design.create_label(
            header,
            text="Ask for explanations, quizzes, summaries, or a study plan.",
            size="base",
            text_color=self.design.get_color("text_secondary"),
        ).grid(row=1, column=0, sticky="w", pady=(4, 0))

        examples = ctk.CTkFrame(self, fg_color="transparent")
        examples.grid(row=1, column=0, sticky="ew", padx=10, pady=(0, 10))
        examples.grid_columnconfigure(0, weight=1)

        self.example_prompt_frame = ctk.CTkFrame(examples, fg_color="transparent")
        self.example_prompt_frame.pack(fill="x")

        for prompt in self.EXAMPLE_PROMPTS:
            button = self.design.create_button(
                self.example_prompt_frame,
                text=prompt,
                command=lambda prompt=prompt: self.question_entry.insert(0, prompt),
                style="secondary",
                height=34,
                corner_radius=12,
                fg_color="#eff6ff",
                text_color="#1d4ed8",
                hover_color="#E2E8F0",
            )
            button.pack(side="left", padx=(0, 8), pady=4)

        self.chat_container = ctk.CTkScrollableFrame(
            self,
            corner_radius=24,
            fg_color=self.design.get_color("surface"),
            border_width=1,
            border_color="#E2E8F0",
        )
        self.chat_container.grid(row=2, column=0, sticky="nsew", padx=10, pady=(0, 10))
        self.chat_container.grid_columnconfigure(0, weight=1)

        input_frame = ctk.CTkFrame(self, fg_color="transparent")
        input_frame.grid(row=3, column=0, sticky="ew", padx=10, pady=(0, 10))
        input_frame.grid_columnconfigure(0, weight=1)

        self.question_entry = self.design.create_entry(
            input_frame,
            placeholder="Ask your study question...",
            width=640,
            height=44,
        )
        self.question_entry.grid(row=0, column=0, sticky="ew", padx=(0, 8))
        self.question_entry.bind("<Return>", lambda event: self.ask_question())

        self.ask_button = self.design.create_button(
            input_frame,
            text="Ask",
            command=self.ask_question,
            style="primary",
            height=44,
            width=110,
            corner_radius=14,
        )
        self.ask_button.grid(row=0, column=1, sticky="e", padx=(0, 8))

        self.clear_button = self.design.create_button(
            input_frame,
            text="Clear History",
            command=self.clear_chat_history,
            style="secondary",
            height=44,
            width=140,
            corner_radius=14,
            fg_color="#f8fafc",
            text_color="#0f172a",
            hover_color="#e2e8f0",
        )
        self.clear_button.grid(row=0, column=2, sticky="e")

        self.loading_label = self.design.create_label(
            input_frame,
            text="",
            size="sm",
            text_color=self.design.get_color("text_secondary"),
        )
        self.loading_label.grid(row=1, column=0, columnspan=3, sticky="w", pady=(8, 0))

    def load_chat_history(self):
        for widget in self.chat_container.winfo_children():
            widget.destroy()

        history = self.database.get_ai_history(limit=50) if self.database else []
        if not history:
            self._show_empty_state()
            return

        for row in reversed(history):
            if len(row) >= 3:
                self._show_user_message(row[1])
                self._show_assistant_message(row[2])

    def _show_empty_state(self):
        empty = ctk.CTkFrame(self.chat_container, fg_color="transparent")
        empty.pack(fill="both", expand=True, padx=20, pady=30)
        self.design.create_label(
            empty,
            text="Your AI study chat will appear here.",
            size="lg",
            weight="bold",
            text_color=self.design.get_color("text_secondary"),
        ).pack(anchor="center")
        self.design.create_label(
            empty,
            text="Try one of the example prompts to start.",
            size="sm",
            text_color=self.design.get_color("text_secondary"),
        ).pack(anchor="center", pady=(6, 0))

    def ask_question(self):
        prompt = self.question_entry.get().strip()
        if not prompt:
            return

        self.question_entry.delete(0, tk.END)
        self._show_user_message(prompt)
        self._start_loading_animation()
        run_in_background(
            self,
            lambda: self._generate_response(prompt),
            callback=lambda response: self._display_final_response(prompt, response),
            error_callback=self._show_ai_error,
        )

    def _display_final_response(self, prompt, response_text):
        self._stop_loading_animation()
        self._show_assistant_message_streamed(response_text)
        self._persist_message(prompt, response_text)

    def _persist_message(self, prompt, response_text):
        if self.database is None:
            return
        try:
            self.database.add_ai_history(prompt, response_text)
        except Exception:
            pass

    def _start_loading_animation(self):
        self.loading_label.configure(text="Thinking...")
        self._loading_dots = 0
        if self._loading_after_id is not None:
            try:
                self.after_cancel(self._loading_after_id)
            except Exception:
                pass
        self._loading_after_id = self.after(400, self._animate_loading)

    def _animate_loading(self):
        self._loading_dots = (self._loading_dots + 1) % 4
        dots = "." * self._loading_dots
        self.loading_label.configure(text=f"Thinking{dots}")
        self._loading_after_id = self.after(400, self._animate_loading)

    def _stop_loading_animation(self):
        self.loading_label.configure(text="")
        if self._loading_after_id is not None:
            try:
                self.after_cancel(self._loading_after_id)
            except Exception:
                pass
            self._loading_after_id = None

    def _show_ai_error(self, error, safe_message=None):
        self._stop_loading_animation()
        friendly_message = safe_message or handle_operation_error(
            error,
            context="asking the AI study assistant",
            user_message="We couldn't generate a response right now.",
        )
        self._show_assistant_message(friendly_message)

    def clear_chat_history(self):
        if self.database is None:
            return
        try:
            clear_method = getattr(self.database, "clear_ai_history", None)
            if clear_method is not None:
                clear_method()
            else:
                conn = self.database.connect()
                if conn is not None:
                    conn.cursor().execute("DELETE FROM ai_history")
                    conn.commit()
                    conn.close()
        except Exception:
            try:
                conn = self.database.connect()
                if conn is not None:
                    conn.cursor().execute("DELETE FROM ai_history")
                    conn.commit()
                    conn.close()
            except Exception:
                pass
        self._clear_chat_frame()

    def _clear_chat_frame(self):
        for widget in self.chat_container.winfo_children():
            widget.destroy()
        self._show_empty_state()

    def _show_user_message(self, text, timestamp=None):
        bubble = ctk.CTkFrame(
            self.chat_container,
            corner_radius=16,
            fg_color="#E2E8F0",
            border_width=0,
        )
        bubble.pack(fill="x", padx=16, pady=8)
        self.design.create_label(
            bubble,
            text=text,
            size="base",
            weight="bold",
            text_color="#0f172a",
            wraplength=660,
            justify="left",
        ).pack(anchor="e", padx=14, pady=(12, 2))
        self.design.create_label(
            bubble,
            text=timestamp or self._current_timestamp(),
            size="xs",
            text_color="#64748b",
        ).pack(anchor="e", padx=14, pady=(0, 10))

    def _show_assistant_message(self, text, timestamp=None):
        bubble = ctk.CTkFrame(
            self.chat_container,
            corner_radius=16,
            fg_color="#f8fafc",
            border_width=1,
            border_color="#E2E8F0",
        )
        bubble.pack(fill="x", padx=16, pady=8)
        self.design.create_label(
            bubble,
            text=text,
            size="base",
            text_color="#0f172a",
            wraplength=660,
            justify="left",
        ).pack(anchor="w", padx=14, pady=(12, 2))
        self.design.create_label(
            bubble,
            text=timestamp or self._current_timestamp(),
            size="xs",
            text_color="#64748b",
        ).pack(anchor="w", padx=14, pady=(0, 10))

    def _show_assistant_message_streamed(self, text):
        bubble = ctk.CTkFrame(
            self.chat_container,
            corner_radius=16,
            fg_color="#f8fafc",
            border_width=1,
            border_color="#E2E8F0",
        )
        bubble.pack(fill="x", padx=16, pady=8)

        label = self.design.create_label(
            bubble,
            text="",
            size="base",
            text_color="#0f172a",
            wraplength=660,
            justify="left",
        )
        label.pack(anchor="w", padx=14, pady=(12, 2))

        timestamp_label = self.design.create_label(
            bubble,
            text=self._current_timestamp(),
            size="xs",
            text_color="#64748b",
        )
        timestamp_label.pack(anchor="w", padx=14, pady=(0, 10))

        self._stream_message_text(label, text, 0)

    def _stream_message_text(self, label, full_text, current_index):
        if current_index >= len(full_text):
            return
        next_index = min(len(full_text), current_index + 1)
        label.configure(text=full_text[:next_index])
        self.after(20, lambda: self._stream_message_text(label, full_text, next_index))

    def _current_timestamp(self):
        return datetime.now().strftime("%H:%M")

    def _generate_response(self, prompt):
        llm_response = self._call_openai_compatible_llm(prompt)
        if llm_response:
            return llm_response

        prompt_lower = prompt.lower()

        if "python" in prompt_lower and "loop" in prompt_lower:
            return (
                "A Python loop repeats a block of code until a condition is met.\n\n"
                "Example:\n"
                "for i in range(3):\n"
                "    print(i)\n\n"
                "Use loops when you want to automate repeated work such as scanning a list or counting totals."
            )

        if "java" in prompt_lower and "oop" in prompt_lower:
            return (
                "Java OOP centers on four main ideas: encapsulation, inheritance, polymorphism, and abstraction.\n\n"
                "A class defines a blueprint, while an object is an instance of that class.\n\n"
                "For example, a Car class can have properties like speed and methods like drive()."
            )

        if "quiz" in prompt_lower:
            return (
                "Quick Quiz\n"
                "1. What is the difference between a list and a tuple in Python?\n"
                "2. What does OOP stand for?\n"
                "3. Which study habit helps the most with retention?\n\n"
                "Answer them yourself and review your reasoning after each one."
            )

        if "summarize" in prompt_lower or "notes" in prompt_lower:
            return (
                "Summary Draft\n"
                "- Focus on the key concept first.\n"
                "- Turn each topic into one short explanation.\n"
                "- Highlight formulas, definitions, and examples.\n"
                "- Keep one sentence for why the idea matters."
            )

        if "study plan" in prompt_lower:
            return (
                "Study Plan\n"
                "1. Set a 25-minute focused session for one main topic.\n"
                "2. Review a short set of notes for 10 minutes.\n"
                "3. Take a 5-minute break.\n"
                "4. Repeat for the next subject and track your completion."
            )

        return (
            "Here is a focused study answer:\n\n"
            "- Start by identifying the main concept.\n"
            "- Write a short explanation in your own words.\n"
            "- Review one example and one practice question.\n"
            "- Retest yourself after a short break."
        )

    def _call_openai_compatible_llm(self, prompt):
        api_key = os.getenv("OPENAI_API_KEY") or os.getenv("AI_API_KEY")
        if not api_key:
            return None

        model = os.getenv("OPENAI_MODEL") or os.getenv("AI_MODEL") or "gpt-4o-mini"
        base_url = os.getenv("OPENAI_BASE_URL") or os.getenv("AI_BASE_URL") or "https://api.openai.com/v1/chat/completions"

        payload = {
            "model": model,
            "messages": [
                {
                    "role": "system",
                    "content": (
                        "You are a focused AI study assistant. Reply clearly, teach the key idea, "
                        "use concise bullet points when helpful, and keep answers practical for study."
                    ),
                },
                {"role": "user", "content": prompt},
            ],
            "temperature": 0.4,
            "stream": True,
        }

        request = urllib.request.Request(
            base_url,
            data=json.dumps(payload).encode("utf-8"),
            headers={
                "Content-Type": "application/json",
                "Authorization": f"Bearer {api_key}",
                "Accept": "text/event-stream",
            },
            method="POST",
        )

        try:
            with urllib.request.urlopen(request, timeout=30) as response:
                collected_chunks = []
                while True:
                    line = response.readline()
                    if not line:
                        break
                    decoded_line = line.decode("utf-8", errors="ignore").strip()
                    if not decoded_line:
                        continue
                    if not decoded_line.startswith("data:"):
                        continue
                    data_payload = decoded_line[5:].strip()
                    if data_payload == "[DONE]":
                        break
                    try:
                        data = json.loads(data_payload)
                    except json.JSONDecodeError:
                        continue
                    choices = data.get("choices") or []
                    if not choices:
                        continue
                    delta = choices[0].get("delta") or {}
                    content = delta.get("content") or ""
                    if not content:
                        continue
                    collected_chunks.append(str(content))
                response_text = "".join(collected_chunks).strip()
                return response_text or None
        except (urllib.error.URLError, urllib.error.HTTPError, json.JSONDecodeError, ValueError, TimeoutError):
            return None
