import sys
from PyQt6.QtWidgets import QApplication
from dashboard import Dashboard

app = QApplication(sys.argv)

window = Dashboard()
window.show()

sys.exit(app.exec())