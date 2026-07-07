from PyQt6.QtWidgets import (
    QWidget,
    QPushButton,
    QHBoxLayout
)


class ControlPanel(QWidget):

    def __init__(self):
        super().__init__()

        layout = QHBoxLayout()

        # ==================================
        # Device Buttons
        # ==================================
        self.connect_button = QPushButton("Connect")
        self.disconnect_button = QPushButton("Disconnect")

        # ==================================
        # Streaming Buttons
        # ==================================
        self.start_button = QPushButton("Start")
        self.stop_button = QPushButton("Stop")
        self.pause_button = QPushButton("Pause")

        # ==================================
        # Recording Buttons
        # ==================================
        self.record_button = QPushButton("Start Record")

        self.stop_record_button = QPushButton(
            "Stop Record"
        )

        self.save_button = QPushButton(
            "Save CSV"
        )

        # ==================================
        # Add Widgets
        # ==================================
        layout.addWidget(self.connect_button)

        layout.addWidget(self.disconnect_button)

        layout.addWidget(self.start_button)

        layout.addWidget(self.stop_button)

        layout.addWidget(self.pause_button)

        layout.addWidget(self.record_button)

        layout.addWidget(self.stop_record_button)

        layout.addWidget(self.save_button)

        self.setLayout(layout)