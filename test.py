import sys

from PyQt6.QtWidgets import QApplication
from PyQt6.QtGui import QFontDatabase


app = QApplication(sys.argv)

fonts = sorted(QFontDatabase.families())

for font in fonts:
    print(font)

sys.exit()