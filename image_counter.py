import os
import sys

import cv2
import numpy as np
from PyQt5.QtCore import QObject, QRunnable, QThreadPool, pyqtSignal
from PyQt5.QtWidgets import (QApplication, QDialog, QHBoxLayout, QPushButton,
                             QTextEdit, QVBoxLayout, QWidget)


class ColorHighlighter(QRunnable):

    class Sigs(QObject):
        finished_ = pyqtSignal(list)

    # словарь цветов для поиска: ключ — название, значение — (lower HSV, upper HSV)
    search_colors = {
        # "blue": (np.array([85, 40, 40]), np.array([160, 255, 255])),
        "blue": (np.array([100, 80, 80]), np.array([140, 255, 255])),
        # можно добавлять другие цвета, например:
        # "red": (np.array([0, 100, 100]), np.array([10, 255, 255]))
    }

    def __init__(self, files: list[str]):
        super().__init__()
        self.files = files
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
        print(f"start read: {self.files.index(file) + 1} from {len(self.files)}")
        image = cv2.imread(file)
        hsv = cv2.cvtColor(image, cv2.COLOR_BGR2HSV)
        output = image.copy()

        for color_name, (lower, upper) in self.search_colors.items():
            mask = cv2.inRange(hsv, lower, upper)
            contours, _ = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

            filled_mask = np.zeros_like(mask)
            for cnt in contours:
                if cv2.contourArea(cnt) >= min_area:
                    cv2.drawContours(output, [cnt], -1, (0, 0, 255), cv2.FILLED)  # красная заливка
                    cv2.drawContours(filled_mask, [cnt], -1, 255, cv2.FILLED)

            percent = (cv2.countNonZero(filled_mask) / (image.shape[0] * image.shape[1])) * 100
            # percent_dict[color_name] = round(percent, 2)

        return round(percent, 2), output


class ResultsDialog(QWidget):
    def __init__(self, files: list, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Результаты")
        self.resize(600, 400)

        layout = QHBoxLayout(self)

        # Первый QTextEdit с именами файлов
        self.files_edit = QTextEdit(self)
        self.files_edit.setReadOnly(True)
        self.files_edit.setPlainText("\n".join(f[0] for f in files))  # filename
        layout.addWidget(self.files_edit)

        # Второй QTextEdit с процентами
        self.percent_edit = QTextEdit(self)
        self.percent_edit.setReadOnly(True)
        self.percent_edit.setPlainText("\n".join(str(f[1]) for f in files))  # percent
        layout.addWidget(self.percent_edit)


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


class MainWindow(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("File Drop Example")
        self.resize(400, 300)

        layout = QVBoxLayout(self)

        self.text_edit = FileDropTextEdit(self)
        layout.addWidget(self.text_edit)

        self.start_btn = QPushButton("Старт", self)
        self.start_btn.clicked.connect(self.cmd)
        layout.addWidget(self.start_btn)

    
    def cmd(self):
        self.start_btn.setDisabled(True)
        files = self.text_edit.toPlainText().split("\n")
        task = ColorHighlighter(files)
        task.sigs.finished_.connect(self.finished)
        task.run()

    def finished(self, files: list):
        self.start_btn.setDisabled(False)
        self.result = ResultsDialog(files)
        self.result.show()
        # for filename, percent, array_img in files:
        #     print(filename, percent)


if __name__ == "__main__":
    app = QApplication(sys.argv)
    w = MainWindow()
    w.show()
    sys.exit(app.exec_())
