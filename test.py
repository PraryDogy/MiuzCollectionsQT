from PyQt6.QtWidgets import QApplication
from widgets._base_widgets import UPushButton, TransparentWidget, UMainWidget, QHBoxLayout
from PyQt6.QtSvgWidgets import QSvgWidget
from PyQt6.QtCore import Qt


class TestWindow(UMainWidget):
    def __init__(self, parent = None):
        super().__init__(parent)
        self.set_always_on_top()
        self.set_close_only()

        h_widget = TransparentWidget()
        self.central_layout.addWidget(h_widget)

        h_lay = QHBoxLayout(h_widget)
        h_lay.setContentsMargins(0, 0, 0, 0)
        h_lay.setSpacing(0)

        svg = QSvgWidget()
        svg.setFixedHeight(28)
        svg.setFixedWidth(28)
        svg.load("./icons/common/stop.svg")
        h_lay.addWidget(svg)

        btn = UPushButton("Stop")
        btn.setFixedHeight(28)
        h_lay.addWidget(btn)

        self._apply_system_theme()

    def _apply_system_theme(cls):
        from system.themes import ThemeChanger
        ThemeChanger.init()
        return

        app: QApplication = QApplication.instance()
        with open("./themes/dark.qss", "r", encoding="utf-8") as f:
            app.setStyleSheet(f.read())



app = QApplication([])
main_win = TestWindow()
main_win.show()
app.exec()