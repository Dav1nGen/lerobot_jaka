# multi_visualizer_process.py
import multiprocessing as mp
import pyqtgraph as pg
from pyqtgraph.Qt import QtGui
import time
import numpy as np


class MultiFrequencyVisualizerProcess:
    def __init__(self, update_interval=0.1):
        self.update_interval = update_interval
        self.queue = mp.Queue()

    def start(self):
        p = mp.Process(target=self._run_gui, daemon=True)
        p.start()
        return self.queue  # 返回队列给主进程，用来发送频率数据

    def _run_gui(self):
        app = QtGui.QApplication([])

        win = pg.GraphicsLayoutWidget(show=True, title="Multi Task Frequency Monitor")
        win.resize(900, 600)
        plot = win.addPlot(title="Task Frequencies (Hz)")
        plot.showGrid(x=True, y=True)

        curves = {}  # {task_name: plot_curve}
        data_buffer = {}  # {task_name: [freq values]}

        last_update = time.time()

        timer = pg.QtCore.QTimer()
        timer.timeout.connect(
            lambda: self._update_plot(plot, curves, data_buffer)
        )
        timer.start(int(self.update_interval * 1000))

        # Queue listener
        listener = pg.QtCore.QTimer()
        listener.timeout.connect(
            lambda: self._read_queue(curves, data_buffer)
        )
        listener.start(10)

        app.exec_()

    def _read_queue(self, curves, data_buffer):
        """Read messages from main process"""
        while not self.queue.empty():
            msg = self.queue.get()
            task, freq = msg["task"], msg["freq"]

            if task not in data_buffer:
                data_buffer[task] = []
            data_buffer[task].append(freq)

            # Keep last 200 points
            if len(data_buffer[task]) > 200:
                data_buffer[task] = data_buffer[task][-200:]

    def _update_plot(self, plot, curves, data_buffer):
        """Draw curves"""
        for task, data in data_buffer.items():
            if task not in curves:
                curves[task] = plot.plot(pen=pg.mkPen(width=2), name=task)
            x = np.arange(len(data))
            curves[task].setData(x, data)
