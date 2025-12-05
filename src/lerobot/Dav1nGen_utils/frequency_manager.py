import time
from collections import deque, defaultdict


class FrequencyManager:
    """
    Multi-task frequency manager.
    
    Usage:
        fm = FrequencyManager(window=2.0)
        fm.tick("vision")
        fm.tick("motor")
        f = fm.get_frequency("vision")
    """

    def __init__(self, window: float = 2.0):
        self.window = window
        self.timestamps = defaultdict(lambda: deque())

    def tick(self, task_name: str):
        """Record one execution of the task."""
        now = time.perf_counter()
        ts = self.timestamps[task_name]
        ts.append(now)

        # Remove old timestamps
        cutoff = now - self.window
        while ts and ts[0] < cutoff:
            ts.popleft()
            

    def get_frequency(self, task_name: str) -> float:
        """Return current frequency (Hz)."""
        ts = self.timestamps.get(task_name, None)
        if not ts or len(ts) < 2:
            return 0.0
        duration = ts[-1] - ts[0]
        if duration <= 0:
            return 0.0
        return (len(ts) - 1) / duration

    def get_all_frequencies(self) -> dict:
        """Return frequency dict: {task_name: freq}"""
        return {name: self.get_frequency(name) for name in self.timestamps}

