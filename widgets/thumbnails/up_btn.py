from PyQt5.QtWidgets import QWidget, QFrame

from base_widgets import SvgBtn, SvgShadowed, LayoutV
from signals import gui_signals_app
from styles import Names, Themes

# class _UpBtn(SvgBtn):
#     def __init__(self, parent: QWidget):
#         super().__init__(
#             icon_name="up.svg",
#             size=45,
#             parent=parent,
#             )

#     def mouseReleaseEvent(self, event):
#         gui_signals_app.scroll_top.emit()


class UpBtn(QFrame):
    def __init__(self, parent: QWidget = None):
        super().__init__(parent)
        self.setFixedSize(44, 44)
        self.setObjectName(Names.up_btn)
        self.setStyleSheet(Themes.current)

        v_layout = LayoutV()
        self.setLayout(v_layout)

        self.svg = SvgBtn("up_new.svg", 44)
        v_layout.addWidget(self.svg)

    def mouseReleaseEvent(self, event):
        gui_signals_app.scroll_top.emit()