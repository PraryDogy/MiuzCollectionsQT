import colorsys
import gc
import os
import subprocess
import sys

import cv2
import numpy as np
from PIL import Image
from PyQt5.QtCore import (QObject, QRunnable, QSize, Qt, QThreadPool, QTimer,
                          pyqtSignal)
from PyQt5.QtGui import QColor, QDropEvent, QIcon, QImage, QPixmap
from PyQt5.QtWidgets import (QApplication, QFrame, QGridLayout, QHBoxLayout,
                             QLabel, QListWidget, QListWidgetItem, QPushButton,
                             QScrollArea, QSplitter, QTextEdit, QVBoxLayout,
                             QWidget)

exts = (".jpg", ".jpeg")
gray_style = "background-color: rgba(100, 100, 100, 50);"
red_style = "background-color: rgba(137, 0, 0, 0.3);"
app_support = os.path.join(
    os.path.expanduser("~"),
    "Library",
    "Application Support",
    "GeoFinder"    
)
downloads = os.path.join(
    os.path.expanduser("~"),
    "Downloads",
    "GeoFinder"
)
search_colors = {
    "Красный": (np.array([0, 50, 20]),   np.array([10, 255, 255]),  "#FF0000"),
    "Оранжевый": (np.array([10, 50, 50]),  np.array([20, 255, 255]),  "#FFA500"),
    "Жёлтый":    (np.array([20, 50, 50]),  np.array([30, 255, 255]),  "#FFD700"),
    "Зелёный":   (np.array([40, 50, 20]),  np.array([80, 255, 255]),  "#00FF00"),
    "Голубой":   (np.array([85, 40, 40]),  np.array([99, 255, 255]),  "#00BFFF"),
    "Синий":     (np.array([75, 30, 30]),  np.array([150, 255, 255]), "#0000FF"), # старый
    # "Синий": (np.array([90, 80, 50]), np.array([130, 255, 220]), "#0000FF"), # новый варик 2
    # "Синий": (np.array([75, 30, 30]), np.array([150, 255, 200]), "#0000FF"),
    "Фиолетовый":(np.array([140, 50, 20]), np.array([160, 255, 255]), "#8A2BE2"),
}
Image.MAX_IMAGE_PIXELS = None
pool = QThreadPool()

class SaveImagesTask(QRunnable):
    
    class Sigs(QObject):
        process = pyqtSignal(tuple)
        finished_ = pyqtSignal()
        
    def __init__(self, images: list[tuple[QImage, QImage, str, str]]):
        """
        images: список словарей вида {"qimage": QImage, "dest": str}
        """
        super().__init__()
        self.sigs = SaveImagesTask.Sigs()
        self.images = images
        self.flag = True

    def cancel(self):
        self.flag = False

    def run(self):
        os.makedirs(downloads, exist_ok=True)
        for x, data in enumerate(self.images, start=1):
            if not self.flag:
                break
            try:
                self.sigs.process.emit((x, len(self.images)))
            except RuntimeError:
                ...
            src_qimage, res_qimage, src_filename, res_filename = data
            # src_qimage.save(os.path.join(downloads, src_filename))
            res_qimage.save(os.path.join(downloads, res_filename))
        subprocess.Popen(["open", downloads])
        try:
            self.sigs.finished_.emit()
        except RuntimeError:
            ...


class ColorHighlighter(QRunnable):

    class Sigs(QObject):
        process = pyqtSignal(tuple)
        finished_ = pyqtSignal(list)

    def __init__(self, files: list[str], selected_colors: dict):
        super().__init__()
        self.sigs = ColorHighlighter.Sigs()

        self.files = files
        self.selected_colors = selected_colors

        self.result = []
        self.flag = True

    def cancel(self):
        self.flag = False

    def run(self):
        for x, i in enumerate(self.files, start=1):
            if not self.flag:
                break
            try:
                count = (x, len(self.files))
                try:
                    self.sigs.process.emit(count)
                except RuntimeError:
                    ...
                src_qimage, res_qimage, filename, percent = self.highlight_colors(i)
                self.result.append((src_qimage, res_qimage, filename, percent))
            except Exception as e:
                import traceback
                print(traceback.format_exc())
                print("cv2 error", e)
        try:
            self.sigs.finished_.emit(self.result)
        except RuntimeError:
            ...

    def highlight_colors(self, file: str, min_area: int = 500) -> tuple[np.ndarray, dict]:
        img_pil = Image.open(file)
        img = np.array(img_pil)
        img_pil.close()  # <--- освобождаем память PIL
        del img_pil

        image = cv2.cvtColor(img, cv2.COLOR_RGB2BGR)
        del img  # <--- удаляем исходный массив

        hsv = cv2.cvtColor(image, cv2.COLOR_BGR2HSV)
        output = image.copy()
        filled_mask = np.zeros((image.shape[0], image.shape[1]), dtype=np.uint8)

        for color_name, (lower, upper) in self.selected_colors.items():
            mask = cv2.inRange(hsv, lower, upper)
            mask = cv2.morphologyEx(mask, cv2.MORPH_OPEN, np.ones((3, 3), np.uint8))
            output[mask > 0] = (0, 0, 255)
            filled_mask[mask > 0] = 255
            del mask  # <--- важно при больших изображениях

        percent = (cv2.countNonZero(filled_mask) / (image.shape[0] * image.shape[1])) * 100
        filename = os.path.basename(file.rstrip(os.sep))

        qimg_original = self.ndarray_to_qpimg(image)
        qimg_highlighted = self.ndarray_to_qpimg(output)

        del image, output, hsv, filled_mask  # <--- очистка
        gc.collect()  # <--- принудительный сбор мусора

        return qimg_original, qimg_highlighted, filename, str(round(percent, 2)).replace(".", ",")


    
    def ndarray_to_qpimg(self, img: np.ndarray) -> QPixmap:
        """Конвертирует BGR ndarray в QPixmap"""
        img_rgb = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
        h, w, ch = img_rgb.shape
        bytes_per_line = ch * w
        return QImage(img_rgb.data, w, h, bytes_per_line, QImage.Format_RGB888)


class ImageOpener(QRunnable):

    class Sigs(QObject):
        finished_ = pyqtSignal()

    def __init__(self, data: tuple[QImage, QImage, str, str]):
        super().__init__()
        self.sigs = ImageOpener.Sigs()
        self.data = data

    def run(self):
        try:
            self._run()
        except Exception as e:
            print("ImageOpener error", e)
        self.sigs.finished_.emit()

    def _run(self):
        src_qimage, res_qimage, src_img, res_img = self.data
        src_qimage.save(src_img)
        res_qimage.save(res_img)
        subprocess.Popen(["open", src_img, res_img])


class ImageLabel(QLabel):
    clicked = pyqtSignal()

    def __init__(self):
        super().__init__()

    def mouseReleaseEvent(self, ev):
        if ev.button() == Qt.MouseButton.LeftButton:
            self.clicked.emit()


class ProcessDialog(QWidget):
    cancel = pyqtSignal()

    def __init__(self, descr: str):
        super().__init__()
        self.setWindowModality(Qt.WindowModality.ApplicationModal)
        self.setMinimumWidth(200)
        self.setWindowTitle("Внимание")
        # --- Флаги окна: только кнопка закрытия ---
        flags = Qt.WindowType.Window | Qt.WindowType.CustomizeWindowHint
        flags |= Qt.WindowType.WindowCloseButtonHint
        self.setWindowFlags(flags)
        self.setWindowFlag(Qt.WindowType.WindowCloseButtonHint, False)

        self.v_lay = QVBoxLayout()
        self.v_lay.setContentsMargins(5, 10, 5, 10)
        self.v_lay.setSpacing(10)
        self.setLayout(self.v_lay)

        descr_label = QLabel(descr)
        self.v_lay.addWidget(descr_label, alignment=Qt.AlignmentFlag.AlignCenter)

        self.count_label = QLabel()
        self.count_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.v_lay.addWidget(self.count_label)

        self.cancel_btn = QPushButton("Отмена")
        self.cancel_btn.setFixedWidth(100)
        self.cancel_btn.clicked.connect(self.cancel.emit)
        self.v_lay.addWidget(self.cancel_btn, alignment=Qt.AlignmentFlag.AlignCenter)

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
        self.resize(450, 450)
        self.files = files

        self.filenames: list[str] = []
        self.percents: list[str] = []
        self.images: list[tuple[QImage, QImage, str, str]] = []

        self.main_layout = QVBoxLayout(self)
        self.main_layout.setContentsMargins(0, 0, 0, 10)
        self.main_layout.setSpacing(10)
        self.init_table()
        self.init_btns()
        self.setLayout(self.main_layout)

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
        btn_lay.addStretch()

        def copy_cmd():
            combined = "\n".join(
                f"{a}\t{b}" for a, b in zip(self.filenames, self.percents)
            )
            clipboard = QApplication.clipboard()
            clipboard.setText(combined)

            # Временный QLabel
            msg_label = QLabel("Результат скопирован\nВставьте в Excel", self)
            msg_label.setStyleSheet("""
                background-color: rgba(0,0,0,180);
                color: white;
                padding: 8px;
                border-radius: 5px;
            """)
            msg_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
            msg_label.setFixedSize(200, 60)
            msg_label.move(
                (self.width() - msg_label.width()) // 2,
                (self.height() - msg_label.height()) // 2
            )
            msg_label.show()

            # Скрыть через 2 секунды
            QTimer.singleShot(2000, msg_label.deleteLater)

        copy_names = QPushButton("Excel")
        copy_names.clicked.connect(copy_cmd)
        copy_names.setFixedWidth(130)
        btn_lay.addWidget(copy_names)

        save_all = QPushButton("Сохр. все фото")
        save_all.clicked.connect(self.save_task_cmd)
        save_all.setFixedWidth(130)
        btn_lay.addWidget(save_all)

        btn_lay.addStretch()
        self.main_layout.addLayout(btn_lay)  # кнопки в основной layout, под скроллом

    def init_table(self):
        scroll = QScrollArea(self)
        scroll.setWidgetResizable(True)  # содержимое растягивается
        scroll.horizontalScrollBar().setDisabled(True)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)

        # Контейнер внутри scroll
        container = QWidget()
        self.v_layout = QVBoxLayout(container)
        self.v_layout.setContentsMargins(0, 10, 0, 10)
        self.grid_layout = QGridLayout()
        self.grid_layout.setAlignment(Qt.AlignmentFlag.AlignTop)
        self.v_layout.addLayout(self.grid_layout)

        scroll.setWidget(container)
        self.main_layout.addWidget(scroll)  # добавляем scroll в основной layout

        for row, (src_qimage, res_qimage, src_filename, percent) in enumerate(self.files, start=1):
            self.filenames.append(src_filename)
            self.percents.append(str(percent))
            filename, ext = os.path.splitext(src_filename)
            res_filename = f"{filename} ({percent}){ext}"
            image_dict: tuple[QImage, QImage, str, str] = (src_qimage, res_qimage, src_filename, res_filename)
            self.images.append(image_dict)

            # === контейнер для строки ===
            row_widget = QWidget()
            row_widget.setObjectName("row_")  # одинаковое имя для всех строк
            row_layout = QHBoxLayout(row_widget)
            row_layout.setContentsMargins(5, 2, 5, 2)
            row_layout.setSpacing(10)

            # Превью
            pixmap_lbl = ImageLabel()
            pixmap_lbl.setFixedSize(68, 68)
            pixmap_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
            qicon = QIcon(QPixmap.fromImage(src_qimage))
            pixmap = qicon.pixmap(65, 65)
            pixmap_lbl.setPixmap(pixmap)
            pixmap_lbl.clicked.connect(
                lambda src_qimg=src_qimage, qimg=res_qimage, filename=src_filename:
                self.show_image(src_qimg, qimg, filename)
            )
            row_layout.addWidget(pixmap_lbl)

            # Имя файла
            name_lbl = QLabel(src_filename)
            name_lbl.setAlignment(Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter)
            name_lbl.setMinimumWidth(170)
            row_layout.addWidget(name_lbl)

            # Процент
            percent_lbl = QLabel(str(percent) + "%")
            percent_lbl.setFixedWidth(50)
            percent_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
            row_layout.addWidget(percent_lbl)

            # Кнопка сохранить
            save_btn = QLabel("Сохранить")
            save_btn.setFixedWidth(150)
            save_btn.mouseReleaseEvent = lambda e, images=[image_dict, ]: self.save_task_cmd(images)
            row_layout.addWidget(save_btn)

            # === фон через строку ===
            if row % 2 == 0:
                row_widget.setStyleSheet(f"""
                    QWidget#row_ {{
                        {gray_style}
                    }}
                """)

            self.grid_layout.addWidget(row_widget, row, 0, 1, 4)

    def save_task_cmd(self, images: list[tuple[QImage, QImage, str, str]] = None):
        if not images:
            images = self.images
        self.save_task = SaveImagesTask(images)
        self.process_win = ProcessDialog("Сохраняю изображения в папку \"Загрузки\"")
        self.process_win.adjustSize()
        self.process_win.center_to_parent(self.window())
        self.save_task.sigs.process.connect(
            lambda data: self.process_win.count_label.setText(f"{data[0]} из {data[1]}")
        )
        self.save_task.sigs.finished_.connect(
            lambda: self.process_win.deleteLater()
        )
        self.process_win.cancel.connect(
            lambda: self.save_task.cancel()
        )
        self.process_win.cancel.connect(
            lambda: self.process_win.deleteLater()
        )
        pool.start(self.save_task)
        self.process_win.show()

    def show_image(self, src_qimage: QImage, res_qimage: QImage, filename: str):

        def fin():
            try:
                self.img_open_wait.deleteLater()
            except RuntimeError:
                ...

        filename, ext = os.path.splitext(filename)
        src_img = os.path.join(app_support, f"{filename}_src.jpg")
        res_img = os.path.join(app_support, f"{filename}_res.jpg")
        for i in (src_img, res_img):
            if os.path.exists(i):
                try:
                    os.remove(i)
                except Exception as e:
                    print("show_image remove img error", e)

        self.img_open_task = ImageOpener((src_qimage, res_qimage, src_img, res_img))
        self.img_open_wait = ProcessDialog("Открываю изображения...")
        self.img_open_wait.count_label.deleteLater()
        self.img_open_task.sigs.finished_.connect(fin)
        self.img_open_wait.adjustSize()
        self.img_open_wait.center_to_parent(self)
        self.img_open_wait.cancel_btn.setDisabled(True)
        self.img_open_wait.show()
        pool.start(self.img_open_task)


class FileDropTextEdit(QTextEdit):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setAcceptDrops(True)
        self.setPlaceholderText("Вставьте пути к файлам или перетащите их сюда")
        self.paths = []

    def get_paths(self):
        return [i for i in self.toPlainText().split("\n") if i]
    
    def find_jpegs(self, urls: list[str]):
        stack = []
        jpegs = []
        for i in urls:
            if i.lower().endswith(exts):
                jpegs.append(i)
            elif os.path.isdir(i):
                stack.append(i)
        while stack:
            current_dir = stack.pop()
            for i in os.scandir(current_dir):
                if i.is_dir():
                    stack.append(i)
                elif i.name.endswith(exts):
                    jpegs.append(i.path)
        return jpegs

    def dropEvent(self, event: QDropEvent):
        if not event.mimeData().hasUrls():
            return
        new_urls = [
            url.toLocalFile().rstrip(os.sep)
            for url in event.mimeData().urls()
        ]
        new_urls = self.find_jpegs(new_urls)
        old_urls = self.get_paths()
        old_urls.extend(new_urls)
        self.setPlainText("\n".join(old_urls))
        event.acceptProposedAction()


class ColorListWidget(QListWidget):
    def mousePressEvent(self, event):
        item = self.itemAt(event.pos())
        if not item:  # клик по пустому месту
            self.clearSelection()
        super().mousePressEvent(event)


class MainWindow(QWidget):
    left_wid_w = 200

    def __init__(self):
        super().__init__()
        self.setWindowTitle("GeoFinder")
        self.resize(700, 400)
        self.selected_colors = {}

        # === Главный сплиттер ===
        splitter = QSplitter(self)
        splitter.setHandleWidth(15)
        main_layout = QHBoxLayout(self)
        main_layout.setContentsMargins(5, 5, 5, 5)
        main_layout.addWidget(splitter)

        # === Левая часть: QListWidget ===
        self.list_widget = ColorListWidget()
        splitter.addWidget(self.list_widget)

        # Добавляем элементы из search_colors в QListWidget
        for color_name, (lower, upper, hex_color) in search_colors.items():
            item = QListWidgetItem(color_name)
            item.setSizeHint(QSize(0, 28))
            item.setCheckState(Qt.Checked if color_name in self.selected_colors else Qt.Unchecked)
            item.value = (lower, upper)

            pixmap = QPixmap(12, 12)
            pixmap.fill(QColor(hex_color))
            item.setIcon(QIcon(pixmap))
            self.list_widget.addItem(item)

        self.list_widget.itemClicked.connect(self.on_color_item_changed)

        # === Правая часть: старое содержимое ===
        right_widget = QWidget()
        splitter.addWidget(right_widget)

        layout = QVBoxLayout(right_widget)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(15)

        self.text_edit = FileDropTextEdit(self)
        layout.addWidget(self.text_edit)

        btn_lay = QHBoxLayout()
        btn_lay.setSpacing(15)
        btn_lay.addStretch()

        self.start_btn = QPushButton("Старт", self)
        self.start_btn.setFixedWidth(100)
        self.start_btn.clicked.connect(self.start_cmd)
        btn_lay.addWidget(self.start_btn)
        btn_lay.addStretch()
        layout.addLayout(btn_lay)

        splitter.setSizes([self.left_wid_w, self.width() - self.left_wid_w])
        self.on_start()

    def on_start(self):
        os.makedirs(app_support, exist_ok=True)
        for i in os.scandir(app_support):
            try:
                if i.is_file():
                    os.remove(i.path)
            except Exception as e:
                print("GeoFinder MainWindow remove file error", e)    

    def on_color_item_changed(self, item: QListWidgetItem):
        if item.checkState() == Qt.Checked:
            item.setCheckState(Qt.Unchecked)
            self.selected_colors.pop(item.text(), None)
        else:
            item.setCheckState(Qt.Checked)
            self.selected_colors[item.text()] = item.value
    
    def start_cmd(self):
        files = self.text_edit.get_paths()
        files = [i for i in files if os.path.exists(i)]
        timeout = 400

        if not self.selected_colors:
            self.list_widget.setStyleSheet(red_style)
            QTimer.singleShot(timeout, lambda: self.list_widget.setStyleSheet(""))
        if not files:
            self.text_edit.setStyleSheet(red_style)
            QTimer.singleShot(timeout, lambda: self.text_edit.setStyleSheet(""))

        if not files or not self.selected_colors:
            return
        task = ColorHighlighter(files, self.selected_colors)
        text = f"Ищу цвета: {', '.join(list(self.selected_colors))}"
        self.process_win = ProcessDialog(text)
        self.process_win.adjustSize()
        self.process_win.center_to_parent(self.window())
        task.sigs.finished_.connect(
            lambda files: self.show_result(files)
        )
        task.sigs.process.connect(
            lambda data: self.process_win.count_label.setText(f"{data[0]} из {data[1]}")
        )
        self.process_win.cancel.connect(
            lambda: task.cancel()
        )
        self.process_win.cancel.connect(
            lambda: self.process_win.deleteLater()
        )
        pool.start(task)
        self.process_win.show()

    def show_result(self, files: list):
        self.process_win.deleteLater()
        self.result = ResultsDialog(files)
        self.result.center_to_parent(self.window())
        self.result.show()


if __name__ == "__main__":
    app = QApplication(sys.argv)
    w = MainWindow()
    w.show()
    sys.exit(app.exec_())
