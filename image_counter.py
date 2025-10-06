import os
import sys
from pathlib import Path

import cv2
import numpy as np
from PIL import Image
from PyQt5.QtCore import QObject, QRunnable, Qt, QThreadPool, pyqtSignal
from PyQt5.QtGui import QDropEvent, QImage, QPixmap
from PyQt5.QtWidgets import (QAction, QApplication, QDialog, QGridLayout,
                             QHBoxLayout, QLabel, QMenu, QPushButton,
                             QScrollArea, QTextEdit, QVBoxLayout, QWidget)

Image.MAX_IMAGE_PIXELS = None


class SaveImagesTask(QRunnable):
    
    class Sigs(QObject):
        process = pyqtSignal(tuple)
        finished_ = pyqtSignal()
        
    def __init__(self, images: list[dict]):
        """
        images: список словарей вида {"qimage": QImage, "dest": str}
        """
        super().__init__()
        self.images = images
        self.sigs = SaveImagesTask.Sigs()

    def run(self):
        for x, item in enumerate(self.images, start=1):
            qimage = item["qimage"]
            filepath = item["dest"]
            if isinstance(qimage, QImage) and filepath:
                data = (x, len(self.images))
                self.sigs.process.emit(data)
                qimage.save(filepath)


class ColorHighlighter(QRunnable):

    class Sigs(QObject):
        process = pyqtSignal(tuple)
        finished_ = pyqtSignal(list)

    def __init__(self, files: list[str], selected_colors: dict):
        super().__init__()
        self.files = files
        self.selected_colors = selected_colors
        self.sigs = ColorHighlighter.Sigs()
        self.result = []

    def run(self):
        for x, i in enumerate(self.files, start=1):
            try:
                count = (x, len(self.files))
                self.sigs.process.emit(count)
                qimage, filename, percent = self.highlight_colors(i)
                self.result.append((qimage, filename, percent))
            except Exception as e:
                print("cv2 error", e)

        self.sigs.finished_.emit(self.result)

    def highlight_colors(self, file: str, min_area: int = 500) -> tuple[np.ndarray, dict]:
        """
        Закрашивает найденные области красным цветом.
        Возвращает изображение и словарь с процентом площади.
        """
        img_pil = Image.open(file)
        img = np.array(img_pil)
        image = cv2.cvtColor(img, cv2.COLOR_RGB2BGR)
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
        filename = os.path.basename(file.rstrip(os.sep))
        return (self.ndarray_to_qpimg(output), filename, round(percent, 2))

    
    def ndarray_to_qpimg(self, img: np.ndarray) -> QPixmap:
        """Конвертирует BGR ndarray в QPixmap"""
        img_rgb = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
        h, w, ch = img_rgb.shape
        bytes_per_line = ch * w
        qt_img = QImage(img_rgb.data, w, h, bytes_per_line, QImage.Format_RGB888)
        return qt_img



class ImgLabel(QLabel):
    clicked = pyqtSignal()

    def __init__(self):
        super().__init__()
        self._original_pixmap = None

    def setPixmap(self, pixmap: QPixmap):
        self._original_pixmap = pixmap
        super().setPixmap(pixmap)

    def mouseReleaseEvent(self, ev):
        if ev.button() == Qt.MouseButton.LeftButton:
            self.clicked.emit()

    def resizeEvent(self, ev):
        if self._original_pixmap:
            scaled = self._original_pixmap.scaled(
                self.width(), self.height(), Qt.KeepAspectRatio, Qt.SmoothTransformation
            )
            super().setPixmap(scaled)
        super().resizeEvent(ev)

    def keyPressEvent(self, ev):
        if ev.key() == Qt.Key.Key_Escape:
            self.deleteLater()
        return super().keyPressEvent(ev)


class ProcessDialog(QWidget):
    cancel = pyqtSignal()

    def __init__(self):
        super().__init__()
        self.setWindowModality(Qt.WindowModality.ApplicationModal)
        self.v_lay = QVBoxLayout()
        self.setLayout(self.v_lay)

        self.text_label = QLabel()
        self.text_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.v_lay.addWidget(self.text_label)

        self.cancel_btn = QPushButton("Отмена")
        self.cancel_btn.clicked.connect(self.cancel.emit)
        self.v_lay.addWidget(self.cancel_btn)

    def center_to_parent(self, parent: QWidget):
        try:
            geo = self.geometry()
            geo.moveCenter(parent.geometry().center())
            self.setGeometry(geo)
        except Exception as e:
            print("base widgets, u main window, center error", e)


class ResultsDialog(QWidget):
    def __init__(self, files: list, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Результаты")
        self.setWindowModality(Qt.WindowModality.ApplicationModal)
        self.downloads = os.path.join(os.path.expanduser("~"), "Downloads")
        self.files = files
        self.filenames = []
        self.names = []
        self.percents = []
        self.images = {}
        self.init_table()
        self.init_btns()
        self.adjustSize()

    def center_to_parent(self, parent: QWidget):
        try:
            geo = self.geometry()
            geo.moveCenter(parent.geometry().center())
            self.setGeometry(geo)
        except Exception as e:
            print("base widgets, u main window, center error", e)

    def init_btns(self):
        btn_lay = QHBoxLayout()
        btn_lay.setSpacing(15)
        self.v_layout.addLayout(btn_lay)

        btn_lay.addStretch()

        def copy_cmd(values: list):
            text = "\n".join(values)
            clipboard = QApplication.clipboard()
            clipboard.setText(text)

        copy_names = QPushButton("Копир. имена")
        copy_names.clicked.connect(lambda: copy_cmd(self.filenames))
        copy_names.setFixedWidth(120)
        btn_lay.addWidget(copy_names)

        copy_values = QPushButton("Копир. резул.")
        copy_values.clicked.connect(lambda: copy_cmd(self.percents))
        copy_values.setFixedWidth(120)
        btn_lay.addWidget(copy_values)

        btn_lay.addStretch()

    def init_table(self):
        # Создаём область прокрутки
        scroll = QScrollArea(self)
        scroll.setWidgetResizable(True)  # чтобы содержимое растягивалось

        # Контейнер внутри scroll
        container = QWidget()
        self.v_layout = QVBoxLayout(container)
        self.grid_layout = QGridLayout()
        self.grid_layout.setAlignment(Qt.AlignmentFlag.AlignTop)
        self.v_layout.addLayout(self.grid_layout)

        scroll.setWidget(container)  # добавляем контейнер в scroll
        main_layout = QVBoxLayout(self)  # основной layout для окна
        main_layout.addWidget(scroll)
        self.setLayout(main_layout)

        # Заголовки
        headers = ["Превью", "Файл", "Процент", "Действия"]
        for col, text in enumerate(headers):
            lbl = QLabel(f"<b>{text}</b>")
            lbl.setAlignment(Qt.AlignCenter)
            self.grid_layout.addWidget(lbl, 0, col, alignment=Qt.AlignmentFlag.AlignCenter)

        # Строки
        for row, (qimg, filename, percent) in enumerate(self.files, start=1):
            self.filenames.append(filename)
            self.percents.append(str(percent))

            # Превью
            pixmap_lbl = ImgLabel()
            if qimg is not None:
                pixmap = QPixmap.fromImage(qimg)
                pixmap = pixmap.scaled(100, 100, Qt.AspectRatioMode.KeepAspectRatio)
                pixmap_lbl.setPixmap(pixmap)
                pixmap_lbl.clicked.connect(
                    lambda q=qimg, f=filename, p=percent: self.show_image(q, f, p)
                )
            self.grid_layout.addWidget(pixmap_lbl, row, 0, alignment=Qt.AlignmentFlag.AlignCenter)

            # Имя файла
            name_lbl = QLabel(filename)
            name_lbl.setTextInteractionFlags(Qt.TextSelectableByMouse)
            self.grid_layout.addWidget(name_lbl, row, 1, alignment=Qt.AlignmentFlag.AlignCenter)

            # Процент
            percent_lbl = QLabel(str(percent))
            percent_lbl.setTextInteractionFlags(Qt.TextSelectableByMouse)
            self.grid_layout.addWidget(percent_lbl, row, 2, alignment=Qt.AlignmentFlag.AlignCenter)

            save_btn = QPushButton("Сохранить")
            save_btn.clicked.connect(
                lambda q=qimg, f=filename, p=percent: self.single_save(q, f, p)
            )
            self.grid_layout.addWidget(save_btn, row, 3, alignment=Qt.AlignmentFlag.AlignCenter)

    def single_save(self, qimg, file, percent):
        filename, ext = os.path.splitext(file)
        dest = f"{self.downloads}/{filename} ({percent}){ext}"
        images = [
            {"qimage": qimg, "dest": dest},
        ]
        self.save_task = SaveImagesTask(images)
        
    def show_image(self, qimage, filename, percent):
        self.img_win = ImgLabel()
        self.img_win.setWindowModality(Qt.WindowModality.ApplicationModal)
        self.img_win.setWindowTitle(f"{filename}: {percent}%")
        pixmap = QPixmap.fromImage(qimage).scaled(500, 500, Qt.AspectRatioMode.KeepAspectRatio)
        self.img_win.setPixmap(pixmap)
        self.img_win.show()
        self.img_win.raise_()


class FileDropTextEdit(QTextEdit):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setAcceptDrops(True)
        self.setPlaceholderText("Вставьте пути к файлам\nили перетащите их сюда")
        self.paths = []

    def get_paths(self):
        return [
            i
            for i in self.toPlainText().split("\n")
            if i
        ]

    def dragEnterEvent(self, event):
        if event.mimeData().hasUrls():
            event.acceptProposedAction()
        else:
            super().dragEnterEvent(event)

    def dropEvent(self, event: QDropEvent):
        if not event.mimeData().hasUrls():
            return
        new_urls = [
            url.toLocalFile().rstrip(os.sep)
            for url in event.mimeData().urls()
        ]
        old_urls = self.get_paths()
        old_urls.extend(new_urls)
        self.setPlainText("\n".join(old_urls))
        event.acceptProposedAction()


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
        self.pool = QThreadPool()
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
        files = self.text_edit.get_paths()
        if not files or not self.selected_colors:
            return
        self.start_btn.setDisabled(True)

        task = ColorHighlighter(files, self.selected_colors)
        task.sigs.finished_.connect(self.finished)

        self.process_win = ProcessDialog()
        self.process_win.adjustSize()
        self.process_win.center_to_parent(self.window())
        task.sigs.process.connect(
            lambda data: self.process_win.text_label.setText(f"{data[0]} из {data[1]}")
        )
        self.pool.start(task)
        self.process_win.show()

    def finished(self, files: list):
        self.process_win.deleteLater()
        self.start_btn.setDisabled(False)
        self.result = ResultsDialog(files)
        self.result.center_to_parent(self.window())
        self.result.show()


if __name__ == "__main__":
    app = QApplication(sys.argv)
    w = MainWindow()
    w.show()
    sys.exit(app.exec_())
