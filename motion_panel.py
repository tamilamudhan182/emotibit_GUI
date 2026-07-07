from PyQt6.QtWidgets import QWidget, QGridLayout
import pyqtgraph as pg
import numpy as np


class MotionPanel(QWidget):

    def __init__(self):
        super().__init__()

        layout = QGridLayout()

        # Accelerometer plot
        self.accel_plot = pg.PlotWidget(title="Accelerometer")
        self.accel_plot.addLegend()
        self.accel_plot.showGrid(x=True, y=True)
        # pyrefly: ignore [bad-keyword-argument]
        self.accel_plot.setXRange(0, 300, padding=0)

        # Gyroscope plot
        self.gyro_plot = pg.PlotWidget(title="Gyroscope")
        self.gyro_plot.addLegend()
        self.gyro_plot.showGrid(x=True, y=True)
        # pyrefly: ignore [bad-keyword-argument]
        self.gyro_plot.setXRange(0, 300, padding=0)

        layout.addWidget(self.accel_plot, 0, 0)
        layout.addWidget(self.gyro_plot, 0, 1)

        self.setLayout(layout)

        # Accelerometer curves
        self.acc_x_curve = self.accel_plot.plot(
            pen='c',
            name='Accel X'
        )

        self.acc_y_curve = self.accel_plot.plot(
            pen='y',
            name='Accel Y'
        )

        self.acc_z_curve = self.accel_plot.plot(
            pen='g',
            name='Accel Z'
        )

        # Gyroscope curves
        self.gyro_x_curve = self.gyro_plot.plot(
            pen='r',
            name='Gyro X'
        )

        self.gyro_y_curve = self.gyro_plot.plot(
            pen='m',
            name='Gyro Y'
        )

        self.gyro_z_curve = self.gyro_plot.plot(
            pen='w',
            name='Gyro Z'
        )

        # Motion regions pool (10 regions)
        self.motion_regions = []
        for _ in range(10):
            region = pg.LinearRegionItem(
                values=[0, 0],
                brush=pg.mkBrush(255, 69, 0, 45),  # Semi-transparent red-orange
                pen=pg.mkPen(color=(255, 69, 0, 100), width=1.5),
                movable=False
            )
            region.setVisible(False)
            self.accel_plot.addItem(region)
            self.motion_regions.append(region)

        # Motion label TextItem
        self.motion_label = pg.TextItem(
            text="",
            color=(255, 69, 0),
            anchor=(0.5, 0),
            fill=(30, 30, 30, 200),
            border=pg.mkPen(255, 69, 0, 180)
        )
        font = self.motion_label.textItem.font()
        font.setPointSize(14)
        font.setBold(True)
        self.motion_label.setFont(font)
        self.motion_label.setVisible(False)
        self.accel_plot.addItem(self.motion_label)

    def update_motion_regions(self, is_moving):
        starts = []
        ends = []
        if len(is_moving) > 0:
            diff = np.diff(is_moving.astype(int))
            starts = np.where(diff == 1)[0] + 1
            ends = np.where(diff == -1)[0] + 1

            if is_moving[0]:
                starts = np.insert(starts, 0, 0)
            if is_moving[-1]:
                ends = np.append(ends, len(is_moving))

        # Position and display the required number of regions
        for idx, region in enumerate(self.motion_regions):
            if idx < len(starts):
                region.setRegion([starts[idx], ends[idx]])
                region.setVisible(True)
            else:
                region.setVisible(False)

        # Display the real-time "MOVING" badge at the top-center if hand is moving
        if len(is_moving) > 0 and is_moving[-1]:
            self.motion_label.setText("⚠️ MOVING")
            self.motion_label.setVisible(True)
            view_box = self.accel_plot.getViewBox()
            y_range = view_box.viewRange()[1]
            ymax = y_range[1]
            ymin = y_range[0]
            self.motion_label.setPos(len(is_moving) / 2, ymax - (ymax - ymin) * 0.12)
        else:
            self.motion_label.setText("")
            self.motion_label.setVisible(False)