import pyqtgraph as pg
from pyqtgraph.Qt import QtGui, QtWidgets, QtCore
import sys
import random
from collections import defaultdict, deque
import time

class MultiFrequencyVisualizer:
    """
    Modern real-time visualization for multi-task frequency monitoring.
    """

    def __init__(self, freq_manager, title="Task Frequencies (Hz)"):
        self.freq_manager = freq_manager

        self.app = QtWidgets.QApplication(sys.argv)
        pg.setConfigOptions(antialias=True)

        self.win = pg.GraphicsLayoutWidget(title=title)
        self.win.resize(900, 500)
        self.win.show()

        self.plot = self.win.addPlot()
        self.plot.showGrid(x=True, y=True)
        self.plot.addLegend()
        self.plot.setLabel("left", "Frequency (Hz)")
        self.plot.setLabel("bottom", "Time (s)")

        # task_name -> curve
        self.curves = {}
        self.data_buffers = defaultdict(lambda: deque(maxlen=300))
        self.time_axis = deque(maxlen=300)
        self.start_time = time.monotonic()

        self.timer = QtCore.QTimer()
        self.timer.timeout.connect(self.update_plot)
        self.timer.start(50)  # 20 FPS

    def update_plot(self):
        now = time.monotonic() - self.start_time
        self.time_axis.append(now)

        freqs = self.freq_manager.get_all_frequencies()

        for task_name, freq in freqs.items():
            if task_name not in self.curves:
                # Add a new curve
                color = pg.intColor(len(self.curves), hues=10)
                curve = self.plot.plot(
                    name=task_name,
                    pen=pg.mkPen(color, width=2)
                )
                self.curves[task_name] = curve

            self.data_buffers[task_name].append(freq)
            self.curves[task_name].setData(self.time_axis, self.data_buffers[task_name])

        QtWidgets.QApplication.processEvents()

    def run(self):
        sys.exit(self.app.exec_())
