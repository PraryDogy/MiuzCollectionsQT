from PyQt5.QtWidgets import QApplication, QCalendarWidget, QWidget, QVBoxLayout
import sys

app = QApplication(sys.argv)

window = QWidget()
layout = QVBoxLayout(window)

calendar = QCalendarWidget()
layout.addWidget(calendar)

window.show()
sys.exit(app.exec_())