from PyQt6.QtWidgets import QWidget, QVBoxLayout
import pyqtgraph as pg


class TempPanel(QWidget):

    def __init__(self):
        super().__init__()

        layout = QVBoxLayout()

        # =====================================
        # TEMPERATURE 1
        # =====================================
        self.temp1_plot = pg.PlotWidget(
            title="Temperature Sensor 1"
        )

        self.temp1_plot.showGrid(
            x=True,
            y=True
        )

        self.temp1_plot.setLabel(
            'left',
            'Temperature (°C)'
        )

        self.temp1_plot.setLabel(
            'bottom',
            'Samples'
        )

        self.temp1_plot.addLegend()
        self.temp1_plot.setXRange(0, 300, padding=0)

        self.temp1_curve = self.temp1_plot.plot(
            pen=pg.mkPen('r', width=2),
            name='Temp1'
        )

        # =====================================
        # TEMPERATURE 2
        # =====================================
        self.temp2_plot = pg.PlotWidget(
            title="Temperature Sensor 2"
        )

        self.temp2_plot.showGrid(
            x=True,
            y=True
        )

        self.temp2_plot.setLabel(
            'left',
            'Temperature (°C)'
        )

        self.temp2_plot.setLabel(
            'bottom',
            'Samples'
        )

        self.temp2_plot.addLegend()
        self.temp2_plot.setXRange(0, 300, padding=0)

        self.temp2_curve = self.temp2_plot.plot(
            pen=pg.mkPen('g', width=2),
            name='Temp2'
        )

        # =====================================
        # LAYOUT
        # =====================================
        layout.addWidget(
            self.temp1_plot
        )

        layout.addWidget(
            self.temp2_plot
        )

        self.setLayout(
            layout
        )