import sys
from PyQt5.QtCore import *
from PyQt5.QtGui import *
from PyQt5.QtWidgets import *
from PyQt5.Qt import QRunnable, QThreadPool, pyqtSlot

from matplotlib.backends.backend_qt5agg import FigureCanvas
from matplotlib.figure import Figure
from matplotlib.colorbar import Colorbar

import numpy as np
from numpy import sqrt, sin, cos, pi, log10

class beamspectra(QWidget):
    """ A simple app for generating beamspectra for a simple DAS beamformer. """
    def __init__(self, parent = None):
        super(beamspectra, self).__init__(parent)

        self.setWindowTitle('Beampatterns')

        self.show_axis = True
        """ Whether or not to show the axes and the colorbar of the beamspectrum."""

        self.a_min = -90
        """ The starting angle of the beamspectrum relative to the steering direction, in degrees. """

        self.a_max = 90
        """ The ending angle of the beamspectrum relative to the steering direction, in degrees. """

        a_res = 256
        """ The resolution of the beamspectrum along the angle axis. """

        self.a_axis = np.linspace(np.deg2rad(self.a_min), np.deg2rad(self.a_max), a_res)
        """ All individual angle values along the angle axis of the beamspectrum, in radians. """

        self.f_min = 0
        """ The starting frequency of the beamspectrum, in hertz. """

        self.f_max = 20_000
        """ The ending frequency of the beamspectrum, in hertz. """

        f_res = 256
        """ The resolution of the beamspectrum along the frequency axis. """

        self.f_axis = np.linspace(self.f_min, self.f_max, f_res)
        """ All individual frequency values along the frequency axis of the beamspectrum, in hertz. """

        # Layout the window.
        self.layout()

        # Draw the initial beamspectrum.
        self.draw(res=1)

    def layout(self):
        # The main layout of the entire window.
        layout = QVBoxLayout()

        self._cb = None
        """ The colorbar for the current beamspectrum, initialized to None. """

        matplot_widget = FigureCanvas(Figure())

        self._ax = matplot_widget.figure.subplots()
        """ The matplotlib plot in which to display the beamspectrum. """

        layout.addWidget(matplot_widget)
		
        # The layout for the microphone count slider.
        m_layout = QHBoxLayout()
        M_initial = 10
        self.m_label = QLabel(f'M = {M_initial}')
        m_layout.addWidget(self.m_label)

        self.m_slider = QSlider(Qt.Horizontal)
        """ The slider for controlling the number of microphones. """

        self.m_slider.setMinimum(2)
        self.m_slider.setMaximum(30)
        self.m_slider.setValue(M_initial)
        self.m_slider.valueChanged.connect(self.m_slider_update)
        self.m_slider.sliderReleased.connect(self.m_slider_update_HD)
        m_layout.addWidget(self.m_slider)
        layout.addLayout(m_layout)

        # THe layout for the distance slider.
        d_layout = QHBoxLayout()
        d_initial = 0.015
        self.d_min = 0.005
        self.d_max = 0.4
        self.d_step = 0.005
        d_res = round((self.d_max - self.d_min) / self.d_step)
        self.d_label = QLabel(f'd = {d_initial * 1000:.0f}mm')
        d_layout.addWidget(self.d_label)

        self.d_slider = QSlider(Qt.Horizontal)
        """ The slider for controlling the distance between the microphones. """

        self.d_slider.setMinimum(0)
        self.d_slider.setMaximum(d_res)
        self.d_slider.setValue(self.d_to_i(d_initial))
        self.d_slider.valueChanged.connect(self.d_slider_update)
        self.d_slider.sliderReleased.connect(self.d_slider_update_HD)
        d_layout.addWidget(self.d_slider)
        layout.addLayout(d_layout)

        # Set the completed layout as the main layout of the window.
        self.setLayout(layout)

    def m_slider_update(self):
        """ A callback for when the M slider's value changed. """
        self.m_label.setText(f'M = {self.m_slider.value()}')
        # Draw an updated beamspectrum at a default low resolution to allow for
        # smooth sliding.
        self.draw()

    def m_slider_update_HD(self):
        """ A callback for when the M slider is released. """
        self.m_label.setText(f'M = {self.m_slider.value()}')
        # Only draw an updated beamspectrum at the highest resolution when the
        # slider is finally released.
        self.draw(res=1)

    def d_slider_update(self):
        """ A callback for when the d slider's value changed. """
        self.d_label.setText(f'd = {self.d() * 1000:.0f}mm')
        # Draw an updated beamspectrum at a default low resolution to allow for
        # smooth sliding.
        self.draw()

    def d_slider_update_HD(self):
        """ A callback for when the d slider is released. """
        self.d_label.setText(f'd = {self.d() * 1000:.0f}mm')
        # Only draw an updated beamspectrum at the highest resolution when the
        # slider is finally released.
        self.draw(res=1)

    def M(self):
        """ Get the current number of microphones. """
        return self.m_slider.value()

    def d_to_i(self, d):
        """ Convert a floating point distance to an integer index for the slider. """
        return round((d - self.d_min) / self.d_step)

    def d(self):
        """ Get the current distance set between the microphones. """
        di = self.d_slider.value()
        return self.d_min + di * self.d_step

    def beam_pattern(self, M, d, v, f, a_axis):
        """ Generate the beam pattern across the angle axis for a specific frequency. """

        # Reference implementation taken from http://www.labbookpages.co.uk/audio/beamforming/delaySum.html.
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

    def beam_spectrum(self, M, d, v, f_axis, a_axis):
        """ Generate an entire beamspectrum. """
        pattern = []
        for f in np.flip(f_axis):
            pattern.append(self.beam_pattern(M, d, v, f, a_axis))
        return pattern

    def draw(self, res=4):
        """ Draw a new beamspectrum for the current settings. """
        self._ax.clear()

        if not self.show_axis:
            self._ax.axis('off')
        else:
            self._ax.set_xlabel('Angle (degrees)')
            x_res = len(self.a_axis[::res])
            self._ax.set_xticks(
                np.linspace(0, x_res - 1, 9),
                list(map(lambda x: f'{self.a_max/((x_res - 1)/2)*x+self.a_min:.1f}', np.linspace(0, x_res - 1, 9)))
            )

            self._ax.set_ylabel('Frequency (Hz)')
            y_res = len(self.f_axis[::res])
            self._ax.set_yticks(
                np.linspace(0, y_res - 1, 9),
                list(map(lambda x: f'{-(self.f_max-self.f_min)/(y_res - 1)*x+self.f_max:.0f}', np.linspace(0, y_res - 1, 9)))
            )

        spec = self.beam_spectrum(self.M(), self.d(), 343, self.f_axis[::res], self.a_axis[::res])
        im = self._ax.imshow(spec, cmap='plasma')

        if self.show_axis:
            if self._cb is not None:
                self._cb.remove()
            mini = np.min(spec)
            maxi = np.max(spec)
            self._cb = self._ax.figure.colorbar(im)
            self._cb.set_ticks(np.linspace(mini, maxi, 11))
            self._cb.set_ticklabels(list(map(lambda x: f'{(x - mini) / abs(mini - maxi)}', np.linspace(mini, maxi, 11))))

        self._ax.figure.canvas.draw()
		
if __name__ == '__main__':
    app = QApplication(sys.argv)
    ex = beamspectra()
    ex.show()
    sys.exit(app.exec_())
