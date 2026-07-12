"""Run blocking work off the Tk thread and deliver results back on it."""
import queue
import threading
from typing import Callable, Optional


class TaskRunner:
    def __init__(self, root, interval_ms: int = 80):
        self._root = root
        self._queue: queue.Queue = queue.Queue()
        self._interval = interval_ms
        self._root.after(self._interval, self._pump)

    def submit(self, fn: Callable, *, on_done: Optional[Callable] = None,
               on_error: Optional[Callable] = None,
               on_progress: Optional[Callable] = None) -> threading.Event:
        """Run fn(progress, cancel) on a daemon thread. Returns its cancel Event."""
        cancel = threading.Event()

        def progress(value):
            self._queue.put((on_progress, value))

        def run():
            try:
                result = fn(progress, cancel)
                self._queue.put((on_done, result))
            except Exception as exc:
                self._queue.put((on_error, exc))

        threading.Thread(target=run, daemon=True).start()
        return cancel

    def _pump(self):
        try:
            while True:
                callback, payload = self._queue.get_nowait()
                if callback is not None:
                    callback(payload)
        except queue.Empty:
            pass
        self._root.after(self._interval, self._pump)
