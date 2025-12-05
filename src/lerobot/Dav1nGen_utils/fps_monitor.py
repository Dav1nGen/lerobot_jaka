import time
import multiprocessing as mp
from collections import deque, defaultdict
import random

import numpy as np
import pyqtgraph as pg
from pyqtgraph.Qt import QtWidgets, QtCore

# Sentinel value to signal the end of plotting
_STOP_SIGNAL = object()


class _Plotter:
    """
    This class runs in a separate process and handles the plotting GUI.
    It's designed to handle multiple named data series dynamically.
    It should not be instantiated directly by the user.
    """

    def __init__(self, data_queue: mp.Queue, history_size: int,
                 smoothing_window: int):
        self.data_queue = data_queue
        self.history_size = history_size
        self.smoothing_window = smoothing_window

        # Data storage, now dictionaries to hold multiple series
        self.data = defaultdict(
            lambda: {
                "timestamps": deque(maxlen=self.history_size),
                "fps_raw": deque(maxlen=self.history_size),
                "fps_smoothed": deque(maxlen=self.history_size)
            })

        # PyQt App
        self.app = QtWidgets.QApplication([])
        self.win = pg.GraphicsLayoutWidget(show=True, title="FPS Monitor")
        self.win.resize(1000, 500)
        self.win.setWindowTitle('Real-time Multi-Function FPS Monitor')
        pg.setConfigOptions(antialias=True)

        # Main Plot
        self.plot = self.win.addPlot(title="Frame Rate Monitor")
        self.plot.setLabel('left', 'FPS')
        self.plot.setLabel('bottom', 'Time (s)')
        self.plot.showGrid(x=True, y=True)
        self.plot.addLegend()

        # Curves container
        self.curves = {}
        # Use a predefined list of colors for consistency
        self._colors = [(255, 50, 50), (50, 255, 50), (50, 50, 255),
                        (255, 255, 50), (255, 50, 255), (50, 255, 255),
                        (255, 128, 50), (128, 50, 255), (50, 255, 128)]
        self._next_color_index = 0
        self._start_time = None

    def _get_or_create_curves(self, name):
        """Creates plot curves for a new named series if they don't exist."""
        if name not in self.curves:
            # Get a deterministic color from the predefined list
            color_tuple = self._colors[self._next_color_index %
                                       len(self._colors)]
            self._next_color_index += 1

            color = pg.mkColor(color_tuple)
            raw_pen = pg.mkPen(color=color,
                               width=1,
                               style=QtCore.Qt.PenStyle.DotLine)
            smooth_pen = pg.mkPen(color=color, width=2)

            self.curves[name] = {
                "raw":
                self.plot.plot(pen=raw_pen, name=f"{name} (Raw)"),
                "smoothed":
                self.plot.plot(pen=smooth_pen, name=f"{name} (Smoothed)")
            }

    def _update(self):
        """
        Called by a QTimer to fetch new data from the queue and update plots.
        """
        if self._start_time is None:
            self._start_time = time.monotonic()

        while not self.data_queue.empty():
            item = self.data_queue.get_nowait()
            if item is _STOP_SIGNAL:
                self.app.quit()
                return

            name, timestamp, fps = item
            self._get_or_create_curves(name)

            series = self.data[name]
            series["timestamps"].append(timestamp)
            series["fps_raw"].append(fps)

            # Update smoothed FPS for this series
            if len(series["fps_raw"]) >= self.smoothing_window:
                smoothed_val = np.mean(
                    list(series["fps_raw"])[-self.smoothing_window:])
                series["fps_smoothed"].append(smoothed_val)

        # Update all plots
        for name, series in self.data.items():
            if not series["timestamps"]:
                continue

            # Use timestamps relative to the first-ever data point for this series
            x_data = np.array(list(
                series["timestamps"])) - series["timestamps"][0]

            curves = self.curves[name]
            curves["raw"].setData(x=x_data, y=list(series["fps_raw"]))

            if series["fps_smoothed"]:
                smoothed_x_offset = min(len(x_data), len(
                    series["fps_raw"])) - len(series["fps_smoothed"])
                if len(x_data) > smoothed_x_offset:
                    curves["smoothed"].setData(x=x_data[smoothed_x_offset:],
                                               y=list(series["fps_smoothed"]))

        # Auto-adjust Y range
        self.plot.enableAutoRange('y', True)

    def run(self):
        """Starts the plotter's event loop."""
        self.timer = QtCore.QTimer()
        self.timer.setInterval(30)  # Update plot at ~33 FPS
        self.timer.timeout.connect(self._update)
        self.timer.start()
        self.app.exec_()


def _launch_plotter(data_queue: mp.Queue, history_size: int,
                    smoothing_window: int):
    """Target function for the plotter process."""
    plotter = _Plotter(data_queue, history_size, smoothing_window)
    plotter.run()


class FPSMonitor:
    """
    A utility to monitor the frame rate of multiple named loops in real-time.
    Designed to be used as a singleton/global instance.

    Usage:
        # In your main script
        monitor = FPSMonitor()

        def loop_function1():
            monitor.tick("loop1")

        def loop_function2():
            monitor.tick("loop2")
        
        # In your main loop
        loop_function1()
        loop_function2()

        # At the end
        monitor.stop()
    """

    def __init__(self,
                 history_size: int = 1000,
                 smoothing_window: int = 30,
                 fps_calc_window: int = 60):
        self.data_queue = mp.Queue()
        self.plot_process = mp.Process(target=_launch_plotter,
                                       args=(self.data_queue, history_size,
                                             smoothing_window),
                                       daemon=True)
        self._timestamps = defaultdict(lambda: deque(maxlen=fps_calc_window))
        self.plot_process.start()

    def tick(self, name: str):
        """
        Call this method once per frame in your loop, giving it a unique name.

        Args:
            name (str): The unique identifier for the loop being monitored.
        """
        now = time.monotonic()
        self._timestamps[name].append(now)

        timestamps = self._timestamps[name]
        if len(timestamps) > 1:
            elapsed = timestamps[-1] - timestamps[0]
            if elapsed > 0:
                fps = (len(timestamps) - 1) / elapsed
                self.data_queue.put((name, now, fps))

    def stop(self):
        """Stops the monitoring and closes the plot window."""
        if self.plot_process.is_alive():
            self.data_queue.put(_STOP_SIGNAL)
            self.plot_process.join(timeout=2)
            if self.plot_process.is_alive():
                self.plot_process.terminate()

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.stop()
