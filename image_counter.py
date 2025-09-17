import os
import sys

import cv2
import numpy as np
from PyQt5.QtCore import QObject, QRunnable, Qt, QThreadPool, pyqtSignal
from PyQt5.QtWidgets import (QAction, QApplication, QDialog, QGridLayout,
                             QHBoxLayout, QLabel, QMenu, QPushButton,
                             QTextEdit, QVBoxLayout, QWidget)


class ColorHighlighter(QRunnable):

    class Sigs(QObject):
        finished_ = pyqtSignal(list)

    def __init__(self, files: list[str], selected_colors: dict):
        super().__init__()
        self.files = files
        self.selected_colors = selected_colors
        self.sigs = ColorHighlighter.Sigs()

    def run(self):
        result = [
            (os.path.basename(i.rstrip(os.sep)), *self.highlight_colors(i))
            for i in self.files
        ]

        self.sigs.finished_.emit(result)

    def highlight_colors(self, file: str, min_area: int = 500) -> tuple[np.ndarray, dict]:
        """
        Закрашивает области для всех цветов из search_colors.
        Возвращает изображение и словарь с процентом площади каждого цвета.
        """
        image = cv2.imread(file)
        hsv = cv2.cvtColor(image, cv2.COLOR_BGR2HSV)
        output = image.copy()
        filled_mask = np.zeros((image.shape[0], image.shape[1]), dtype=np.uint8)

        for color_name, (lower, upper) in self.selected_colors.items():
            mask = cv2.inRange(hsv, lower, upper)
            contours, _ = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
            for cnt in contours:
                if cv2.contourArea(cnt) >= min_area:
                    cv2.drawContours(output, [cnt], -1, (0, 0, 255), cv2.FILLED)
                    cv2.drawContours(filled_mask, [cnt], -1, 255, cv2.FILLED)

        percent = (cv2.countNonZero(filled_mask) / (image.shape[0] * image.shape[1])) * 100

        return round(percent, 2), output


class ResultsDialog(QDialog):
    def __init__(self, files: list, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Результаты")
        self.setModal(True)
        self.resize(800, 400)

        layout = QVBoxLayout(self)
        grid = QGridLayout()
        layout.addLayout(grid)

        # Заголовки
        grid.addWidget(QTextEdit("Файл"), 0, 0)
        grid.addWidget(QTextEdit("Процент"), 0, 1)
        grid.addWidget(QTextEdit("Действие"), 0, 2)

        # Первый "столбец" — файлы
        self.files_edit = QTextEdit()
        self.files_edit.setReadOnly(True)
        self.files_edit.setFrameStyle(0)
        self.files_edit.setText("\n".join(f[0] for f in files))
        grid.addWidget(self.files_edit, 1, 0)

        # Второй "столбец" — проценты
        self.percent_edit = QTextEdit()
        self.percent_edit.setReadOnly(True)
        self.percent_edit.setFrameStyle(0)
        self.percent_edit.setText("\n".join(str(f[1]) for f in files))
        grid.addWidget(self.percent_edit, 1, 1)

    def show_image(self, img, name: str):
        if img is None:
            return
        cv2.imshow(name, img)
        cv2.waitKey(0)
        cv2.destroyWindow(name)


class FileDropTextEdit(QTextEdit):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setAcceptDrops(True)
        self.setPlaceholderText("Вставьте пути к файлам\nили перетащите их сюда")

    def dragEnterEvent(self, event):
        if event.mimeData().hasUrls():
            event.acceptProposedAction()
        else:
            super().dragEnterEvent(event)

    def dropEvent(self, event):
        if event.mimeData().hasUrls():
            paths = []
            for url in event.mimeData().urls():
                paths.append(url.toLocalFile())
            # форматируем: один путь на строку
            current_text = self.toPlainText().strip()
            if current_text:
                current_text += "\n"
            current_text += "\n".join(paths)
            self.setPlainText(current_text)
            event.acceptProposedAction()
        else:
            super().dropEvent(event)


class ColorAction(QAction):
    def __init__(self, parent, text):
        super().__init__(parent=parent, text=text)
        self.value: tuple[np.array, np.array]
        self.color_name: str


class MainWindow(QWidget):
    search_colors = {
        "Синий": (np.array([100, 80, 80]), np.array([140, 255, 255])),
        "Жёлтый": (np.array([20, 100, 100]), np.array([30, 255, 255])),
    }

    def __init__(self):
        super().__init__()
        self.setWindowTitle("File Drop Example")
        self.resize(400, 300)
        self.selected_colors = {}

        layout = QVBoxLayout(self)

        self.color_btn = QPushButton("цвета")
        self.color_btn.setFixedWidth(100)
        self.color_btn.clicked.connect(self.show_menu)
        layout.addWidget(self.color_btn, alignment=Qt.AlignmentFlag.AlignCenter)

        self.color_menu = QMenu(parent=self.color_btn)
        self.color_menu.setMinimumWidth(150)
        for color_name, value in self.search_colors.items():
            act = ColorAction(self.color_menu, color_name)
            act.setCheckable(True)
            act.value = value
            act.color_name = color_name
            act.triggered.connect(lambda e, act=act: self.color_action(act))
            if act.color_name in self.selected_colors:
                act.setChecked(True)
            self.color_menu.addAction(act)

        self.text_edit = FileDropTextEdit(self)
        layout.addWidget(self.text_edit)

        self.start_btn = QPushButton("Старт", self)
        self.start_btn.setFixedWidth(100)
        self.start_btn.clicked.connect(self.cmd)
        layout.addWidget(self.start_btn, alignment=Qt.AlignmentFlag.AlignCenter)

    def color_action(self, action: ColorAction):
        if action.color_name in self.selected_colors:
            self.selected_colors.pop(action.color_name)
            action.setChecked(False)
        else:
            self.selected_colors[action.color_name] = action.value
            action.setChecked(True)

    def show_menu(self):
        self.color_menu.exec_(self.color_btn.mapToGlobal(self.color_btn.rect().bottomLeft()))
    
    def cmd(self):
        files = self.text_edit.toPlainText().split("\n")
        if not files or not self.selected_colors:
            return
        self.start_btn.setDisabled(True)
        task = ColorHighlighter(files, self.selected_colors)
        task.sigs.finished_.connect(self.finished)
        task.run()

    def finished(self, files: list):
        self.start_btn.setDisabled(False)
        self.result = ResultsDialog(files)
        self.result.show()


if __name__ == "__main__":
    app = QApplication(sys.argv)
    w = MainWindow()
    w.show()
    sys.exit(app.exec_())
