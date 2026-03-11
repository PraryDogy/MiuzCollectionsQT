from PyQt5.QtWidgets import QApplication, QCalendarWidget
from PyQt5.QtCore import QLocale
import sys

app = QApplication(sys.argv)

calendar = QCalendarWidget()
calendar.setLocale(QLocale(QLocale.Russian))  # дни недели и месяцы на русском
calendar.show()

sys.exit(app.exec_())