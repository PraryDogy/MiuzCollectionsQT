import sys

from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import (
    QApplication,
    QFrame,
    QLabel,
    QMainWindow,
    QVBoxLayout,
    QWidget,
)

from qframelesswindow import FramelessMainWindow


class MainWindow(FramelessMainWindow):
    def __init__(self):
        super().__init__()

        self.setWindowTitle("Miuz Collections")
        self.resize(1200, 800)

        # ---------------------------------------------------------
        # macOS native traffic lights:
        # 🔴 close
        # 🟡 minimize
        # 🟢 maximize
        # ---------------------------------------------------------
        if sys.platform == "darwin":
            self.setSystemTitleBarButtonVisible(True)

        # ---------------------------------------------------------
        # Центральный контейнер
        # ---------------------------------------------------------
        central = QWidget()
        central.setObjectName("CentralWidget")

        layout = QVBoxLayout(central)
        layout.setContentsMargins(24, 24, 24, 24)
        layout.setSpacing(16)

        # ---------------------------------------------------------
        # Наш кастомный верхний бар
        # ---------------------------------------------------------
        top_bar = QFrame()
        top_bar.setObjectName("TopBar")
        top_bar.setFixedHeight(44)

        top_layout = QVBoxLayout(top_bar)
        top_layout.setContentsMargins(70, 0, 20, 0)

        title = QLabel("Miuz Collections")
        title.setObjectName("WindowTitle")

        top_layout.addWidget(
            title,
            alignment=Qt.AlignmentFlag.AlignVCenter
        )

        # ---------------------------------------------------------
        # Контент
        # ---------------------------------------------------------
        content = QFrame()
        content.setObjectName("Content")

        content_layout = QVBoxLayout(content)
        content_layout.setContentsMargins(20, 20, 20, 20)

        label = QLabel("Your content")
        label.setObjectName("ContentLabel")

        content_layout.addWidget(
            label,
            alignment=Qt.AlignmentFlag.AlignCenter
        )

        # ---------------------------------------------------------
        # Добавляем всё
        # ---------------------------------------------------------
        layout.addWidget(top_bar)
        layout.addWidget(content, 1)

        self.setCentralWidget(central)

        # Важно: titleBar библиотеки должен находиться сверху,
        # чтобы native traffic lights оставались кликабельными.
        self.titleBar.raise_()

        # ---------------------------------------------------------
        # QSS
        # ---------------------------------------------------------
        self.setStyleSheet("""
            #CentralWidget {
                background: #0c1218;
            }

            #TopBar {
                background: rgba(15, 23, 31, 180);
                border: 1px solid #263440;
                border-radius: 10px;
            }

            #WindowTitle {
                color: #ffffff;
                font-size: 14px;
                font-weight: 500;
            }

            #Content {
                background: #0f171f;
                border: 1px solid #263440;
                border-radius: 10px;
            }

            #ContentLabel {
                color: #7b8792;
                font-size: 18px;
            }
        """)


if __name__ == "__main__":
    app = QApplication(sys.argv)

    app.setApplicationName("Miuz Collections")

    window = MainWindow()
    window.show()

    sys.exit(app.exec())