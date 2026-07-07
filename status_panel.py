from PyQt6.QtWidgets import QWidget, QLabel, QHBoxLayout


class StatusPanel(QWidget):

    def __init__(self):
        super().__init__()

        layout = QHBoxLayout()

        self.connection_label = QLabel(
            "Connection : 🔴 Disconnected"
        )

        self.streaming_label = QLabel(
            "Streaming : ⚪ Idle"
        )

        self.recording_label = QLabel(
            "Recording : ⚪ Not Recording"
        )

        self.quality_label = QLabel(
            "Signal Quality: ⚪ N/A"
        )

        layout.addWidget(self.connection_label)
        layout.addWidget(self.streaming_label)
        layout.addWidget(self.recording_label)
        layout.addWidget(self.quality_label)

        self.setLayout(layout)