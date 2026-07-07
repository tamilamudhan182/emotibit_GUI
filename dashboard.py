from PyQt6.QtWidgets import (
    QMainWindow,
    QWidget,
    QVBoxLayout,
    QTabWidget
)

import pyqtgraph as pg

from status_panel import StatusPanel
from control_panel import ControlPanel
from signal_panel import SignalPanel

from motion_panel import MotionPanel
from ppg_panel import PPGPanel
from eda_panel import EDAPanel
from temp_panel import TempPanel


class Dashboard(QMainWindow):

    def __init__(self):
        super().__init__()

        # =========================================
        # WINDOW SETTINGS
        # =========================================
        self.setWindowTitle("EmotiBit Live Dashboard")
        self.resize(1600, 1000)

        pg.setConfigOption('background', 'k')
        pg.setConfigOption('foreground', 'w')

        # =========================================
        # MAIN LAYOUT
        # =========================================
        central_widget = QWidget()
        layout = QVBoxLayout()

        # =========================================
        # TOP PANELS
        # =========================================
        self.status_panel = StatusPanel()
        self.control_panel = ControlPanel()

        # =========================================
        # SENSOR TABS
        # =========================================
        self.tabs = QTabWidget()

        self.motion_panel = MotionPanel()
        self.ppg_panel = PPGPanel()
        self.eda_panel = EDAPanel()
        self.temp_panel = TempPanel()

        # Add Tabs
        self.tabs.addTab(
            self.motion_panel,
            "Motion"
        )

        self.tabs.addTab(
            self.ppg_panel,
            "PPG"
        )

        self.tabs.addTab(
            self.eda_panel,
            "EDA"
        )

        self.tabs.addTab(
            self.temp_panel,
            "Temperature"
        )

        # =========================================
        # SIGNAL CONTROLLER
        # =========================================
        self.signal_panel = SignalPanel(self)

        # =========================================
        # BUTTON CONNECTIONS
        # =========================================

        # Device Controls
        self.control_panel.connect_button.clicked.connect(
            self.signal_panel.connect_device
        )

        self.control_panel.disconnect_button.clicked.connect(
            self.signal_panel.disconnect_device
        )

        # Stream Controls
        self.control_panel.start_button.clicked.connect(
            self.signal_panel.start_stream
        )

        self.control_panel.stop_button.clicked.connect(
            self.signal_panel.stop_stream
        )

        self.control_panel.pause_button.clicked.connect(
            self.signal_panel.pause_stream
        )

        # =========================================
        # RECORDING CONTROLS
        # =========================================

        self.control_panel.record_button.clicked.connect(
            self.signal_panel.start_recording
        )

        try:
            self.control_panel.stop_record_button.clicked.connect(
                self.signal_panel.stop_recording
            )
        except:
            pass

        self.control_panel.save_button.clicked.connect(
            self.signal_panel.save_data
        )

        # =========================================
        # FINAL LAYOUT
        # =========================================
        layout.addWidget(
            self.status_panel
        )

        layout.addWidget(
            self.control_panel
        )

        layout.addWidget(
            self.tabs
        )

        central_widget.setLayout(
            layout
        )

        self.setCentralWidget(
            central_widget
        )