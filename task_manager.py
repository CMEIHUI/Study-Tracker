import threading
import time
from utils import _schedule_ui_callback, handle_operation_error


class BackgroundTaskManager:
    """Central manager for background work that should be deduplicated and UI-safe."""

    def __init__(self):
        self._tasks = {}
        self._lock = threading.Lock()

    def submit_task(self, task_key, target, callback=None, error_callback=None, widget=None, *args, **kwargs):
        with self._lock:
            if task_key in self._tasks:
                return self._tasks[task_key]

            event = {
                "key": task_key,
                "running": True,
                "result": None,
                "error": None,
                "completed": False,
            }
            self._tasks[task_key] = event

        def worker():
            try:
                result = target(*args, **kwargs)
                with self._lock:
                    event["result"] = result
                    event["completed"] = True
                    event["running"] = False
                if callback is not None:
                    if widget is not None:
                        _schedule_ui_callback(widget, callback, result)
                    else:
                        callback(result)
            except Exception as error:
                with self._lock:
                    event["error"] = error
                    event["completed"] = True
                    event["running"] = False
                safe_message = handle_operation_error(
                    error,
                    context=str(task_key),
                    user_message="We couldn't complete that task right now.",
                )
                if error_callback is not None:
                    if widget is not None:
                        _schedule_ui_callback(widget, error_callback, error, safe_message)
                    else:
                        error_callback(error, safe_message)
                else:
                    if callback is not None:
                        if widget is not None:
                            _schedule_ui_callback(widget, callback, None)
                        else:
                            callback(None)
            finally:
                with self._lock:
                    self._tasks.pop(task_key, None)

        thread = threading.Thread(target=worker, daemon=True)
        thread.start()
        return event

    def is_running(self, task_key):
        with self._lock:
            event = self._tasks.get(task_key)
            return bool(event and event.get("running"))

    def get_task(self, task_key):
        with self._lock:
            return self._tasks.get(task_key)
