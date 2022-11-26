import sys
from PyQt5.QtCore import *
from PyQt5.QtGui import *
from PyQt5.QtWidgets import *
from PyQt5.Qt import QRunnable, QThreadPool, pyqtSlot

from matplotlib.backends.backend_qt5agg import FigureCanvas
from matplotlib.figure import Figure

import numpy as np
from numpy import sqrt, sin, cos, pi, log10

class ThreadingService(QRunnable):

    def __init__(self, fn, *args, **kwargs):
        super().__init__()
        self.fn = fn
        self.args = args
        self.kwargs = kwargs

    @pyqtSlot()
    def run(self):
        self.fn(*self.args, **self.kwargs)

class sliderdemo(QWidget):
    def __init__(self, parent = None):
        super(sliderdemo, self).__init__(parent)

        self.pool = QThreadPool()

        a_min = -np.pi / 2
        a_max = np.pi / 2
        a_res = 256
        self.a_axis = np.linspace(a_min, a_max, a_res)

        f_min = 0
        f_max = 10_000
        f_res = 256
        self.f_axis = np.linspace(f_min, f_max, f_res)

        layout = QVBoxLayout()

        matplot_widget = FigureCanvas(Figure())
        self._ax = matplot_widget.figure.subplots()
        layout.addWidget(matplot_widget)
		
        m_layout = QHBoxLayout()
        M_initial = 10
        self.m_label = QLabel(f'M = {M_initial}')
        m_layout.addWidget(self.m_label)
        self.m_slider = QSlider(Qt.Horizontal)
        self.m_slider.setMinimum(1)
        self.m_slider.setMaximum(30)
        self.m_slider.setValue(M_initial)
        self.m_slider.valueChanged.connect(self.m_slider_update)
        self.m_slider.sliderReleased.connect(self.m_slider_update_HD)
        m_layout.addWidget(self.m_slider)
        layout.addLayout(m_layout)

        d_layout = QHBoxLayout()
        d_initial = 0.03
        self.d_min = 0.005
        self.d_max = 0.4
        self.d_step = 0.005
        d_res = round((self.d_max - self.d_min) / self.d_step)
        self.d_label = QLabel(f'd = {d_initial * 1000:.0f}mm')
        d_layout.addWidget(self.d_label)
        self.d_slider = QSlider(Qt.Horizontal)
        self.d_slider.setMinimum(0)
        self.d_slider.setMaximum(d_res)
        self.d_slider.setValue(self.d_to_i(d_initial))
        self.d_slider.valueChanged.connect(self.d_slider_update)
        self.d_slider.sliderReleased.connect(self.d_slider_update_HD)
        d_layout.addWidget(self.d_slider)

        layout.addLayout(d_layout)

        self.setLayout(layout)
        self.setWindowTitle('Beampatterns')

        self.update(res=1)

    def beam_pattern(self, M, d, v, f, a_axis):
        pattern = []
        for a in a_axis:
            realSum = 0
            imagSum = 0
            for m in range(M):
                position = m * d
                delay = position * sin(a) / v
                realSum += cos(2 * pi * f * delay)
                imagSum += sin(2 * pi * f * delay)
            output = sqrt(realSum**2 + imagSum**2) / M
            logOutput = 20 * log10(output)
            if (logOutput < -50):
                logOutput = -50
            pattern.append(logOutput)
        return pattern

    def beam_pattern_plot(self, M, d, v, f_axis, a_axis):
        pattern = []
        for f in np.flip(f_axis):
            pattern.append(self.beam_pattern(M, d, v, f, a_axis))
        return pattern

    def M(self):
        return self.m_slider.value()

    def d_to_i(self, d):
        return round((d - self.d_min) / self.d_step)

    def d(self):
        di = self.d_slider.value()
        return self.d_min + di * self.d_step

    def update(self, res=4):
        # TODO: potentially add some threading...
        #self.pool.start(ThreadingService(
        self._ax.clear()
        self._ax.axis('off')
        self._ax.imshow(
            self.beam_pattern_plot(self.M(), self.d(), 343, self.f_axis[::res], self.a_axis[::res]),
            cmap='plasma'
        )
        self._ax.figure.canvas.draw()

    def m_slider_update(self):
        self.m_label.setText(f'M = {self.m_slider.value()}')
        self.update()

    def d_slider_update(self):
        self.d_label.setText(f'd = {self.d() * 1000:.0f}mm')
        self.update()

    def m_slider_update_HD(self):
        self.m_label.setText(f'M = {self.m_slider.value()}')
        # TODO: Only this should be in a separate thread.
        self.update(res=1)

    def d_slider_update_HD(self):
        self.d_label.setText(f'd = {self.d() * 1000:.0f}mm')
        # TODO: Only this should be in a separate thread.
        self.update(res=1)
		
def main():
    app = QApplication(sys.argv)
    ex = sliderdemo()
    ex.show()
    sys.exit(app.exec_())
	
if __name__ == '__main__':
    main()
