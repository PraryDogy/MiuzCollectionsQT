import gc
import os
from typing import Literal

from PyQt5.QtCore import (QEvent, QObject, QPoint, QPointF, QSize, Qt, QTimer,
                          pyqtSignal)
from PyQt5.QtGui import (QColor, QContextMenuEvent, QCursor, QIcon, QImage,
                         QKeyEvent, QMouseEvent, QPainter, QPaintEvent,
                         QPixmap, QResizeEvent, QWheelEvent)
from PyQt5.QtSvg import QSvgWidget
from PyQt5.QtWidgets import (QAction, QApplication, QFrame,
                             QGraphicsPixmapItem, QGraphicsScene,
                             QGraphicsView, QHBoxLayout, QLabel, QScrollBar,
                             QSpacerItem, QVBoxLayout, QWidget)

from cfg import Static, cfg
from system.lang import Lng
from system.main_folder import Mf
from system.shared_utils import SharedUtils
from system.tasks import OneImgLoader, UThreadPool
from system.utils import Utils

from ._base_widgets import (AppModalWindow, SvgShadowed, UHBoxLayout, UMenu,
                            USubMenu, UVBoxLayout)
from .actions import (CopyName, CopyPath, RevealInFinder, Save, SaveAs, SetFav,
                      WinInfoAction)
from .grid import Thumbnail


class ImageWidget(QGraphicsView):
    mouse_moved = pyqtSignal()

    def __init__(self, pixmap: QPixmap = None):
        super().__init__()

        self.setMouseTracking(True)
        self.setStyleSheet("background: black")
        self.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)

        self.scene_ = QGraphicsScene()
        self.setScene(self.scene_)

        self.pixmap_item: QGraphicsPixmapItem = None
        self._last_mouse_pos: QPointF = None

        if pixmap:
            self.pixmap_item = QGraphicsPixmapItem(pixmap)
            self.scene_.addItem(self.pixmap_item)
            self.resetTransform()
            self.horizontalScrollBar().setValue(0)
            self.verticalScrollBar().setValue(0)

    def zoom_in(self):
        self.scale(1.1, 1.1)

    def zoom_out(self):
        self.scale(0.9, 0.9)

    def zoom_fit(self):
        if self.pixmap_item:
            self.resetTransform()
            self.fitInView(self.pixmap_item, Qt.KeepAspectRatio)

    # ---------------------- Drag через мышь ----------------------
    def mousePressEvent(self, event: QMouseEvent):
        if event.button() == Qt.LeftButton:
            self.setCursor(Qt.ClosedHandCursor)
            self._last_mouse_pos = event.pos()
        super().mousePressEvent(event)

    def mouseMoveEvent(self, event: QMouseEvent):
        self.mouse_moved.emit()
        if self._last_mouse_pos and event.buttons() & Qt.LeftButton:
            delta = event.pos() - self._last_mouse_pos
            self._last_mouse_pos = event.pos()

            # перемещаем сцену через scrollbars
            self.horizontalScrollBar().setValue(self.horizontalScrollBar().value() - delta.x())
            self.verticalScrollBar().setValue(self.verticalScrollBar().value() - delta.y())
        super().mouseMoveEvent(event)

    def mouseReleaseEvent(self, event: QMouseEvent):
        self.setCursor(Qt.ArrowCursor)
        self._last_mouse_pos = None
        super().mouseReleaseEvent(event)

    def keyPressEvent(self, event):
        # Если это стрелки, не обрабатываем их здесь
        if event.key() in (Qt.Key_Left, Qt.Key_Right, Qt.Key_Up, Qt.Key_Down):
            event.ignore()  # передаём событие родителю
            return
        # для остальных клавиш можно оставить стандартную обработку
        super().keyPressEvent(event)

    def resizeEvent(self, event):
        super().resizeEvent(event)
        if self.pixmap_item:
            self.fitInView(self.pixmap_item, Qt.KeepAspectRatio)
    

class ZoomBtns(QFrame):
    style_ = """
        background-color: rgba(128, 128, 128, 0.40);
        border-radius: 15px;
    """
    svg_size = 45
    svg_zoom_out = "./images/zoom_out.svg"
    svg_zoom_in = "./images/zoom_in.svg"
    svg_zoom_fit = "./images/zoom_fit.svg"
    svg_zoom_close = "./images/zoom_close.svg"

    def __init__(self, parent: QWidget = None) -> None:
        super().__init__(parent)
        self.setStyleSheet(self.style_)

        h_layout = UHBoxLayout()
        self.setLayout(h_layout)

        h_layout.addSpacerItem(QSpacerItem(5, 0))

        self.zoom_out = SvgShadowed(self.svg_zoom_out, self.svg_size)
        h_layout.addWidget(self.zoom_out)
        h_layout.addSpacerItem(QSpacerItem(10, 0))

        self.zoom_in = SvgShadowed(self.svg_zoom_in, self.svg_size)
        h_layout.addWidget(self.zoom_in)
        h_layout.addSpacerItem(QSpacerItem(10, 0))

        self.zoom_fit = SvgShadowed(self.svg_zoom_fit, self.svg_size)
        h_layout.addWidget(self.zoom_fit)
        h_layout.addSpacerItem(QSpacerItem(10, 0))

        self.zoom_close = SvgShadowed(self.svg_zoom_close, self.svg_size)
        h_layout.addWidget(self.zoom_close)

        h_layout.addSpacerItem(QSpacerItem(5, 0))

        self.adjustSize()


class SwitchImageBtn(QFrame):
    style_ = f"""
        background-color: rgba(128, 128, 128, 0.40);
        border-radius: 27px;
    """
    size_ = 54  # 27px border-radius, 27 * 2 for round shape

    def __init__(self, path: str, parent: QWidget = None) -> None:
        super().__init__(parent)
        self.setFixedSize(self.size_, self.size_)
        self.setStyleSheet(self.style_)

        v_layout = UVBoxLayout()
        self.setLayout(v_layout)

        btn = SvgShadowed(path, 50)
        v_layout.addWidget(btn)


class PrevImageBtn(SwitchImageBtn):
    svg_prev = "./images/prev.svg"

    def __init__(self, parent: QWidget = None) -> None:
        super().__init__(self.svg_prev, parent)


class NextImageBtn(SwitchImageBtn):
    svg_next = "./images/next.svg"

    def __init__(self, parent: QWidget = None) -> None:
        super().__init__(self.svg_next, parent)


class WinImageView(AppModalWindow):
    switch_image_sig = pyqtSignal(str)
    no_connection = pyqtSignal()
    closed_ = pyqtSignal()
    open_win_info = pyqtSignal(list)
    copy_path = pyqtSignal(list)
    copy_name = pyqtSignal(list)
    reveal_in_finder = pyqtSignal(list)
    set_fav = pyqtSignal(tuple)
    save_files = pyqtSignal(tuple)
    open_in_app = pyqtSignal(tuple)
    
    task_count_limit = 10
    ww, hh = 700, 500
    min_w, min_h = 500, 400
    window_style = """background: black;"""

    def __init__(self, rel_path: str, path_to_wid: dict[str, Thumbnail], is_selection: bool):
        super().__init__()

        self.image_apps = {i: os.path.basename(i) for i in SharedUtils.get_apps(cfg.apps)}
        self.cached_images: dict[str, QPixmap] = {}
        self.is_selection = is_selection
        self.path_to_wid = path_to_wid
        self.rel_paths = list(path_to_wid.keys())
        self.rel_path = rel_path
        self.wid = path_to_wid.get(self.rel_path)
        self.task_count = 0

        self.setStyleSheet(self.window_style)
        self.setMinimumSize(QSize(self.min_w, self.min_h))
        self.resize(self.ww, self.hh)
        self.installEventFilter(self)

        self.mouse_move_timer = QTimer(self)
        self.mouse_move_timer.setSingleShot(True)
        self.mouse_move_timer.timeout.connect(self.hide_all_buttons)

        self.image_label = ImageWidget(QPixmap())
        self.central_layout.addWidget(self.image_label)
        self.prev_image_btn = PrevImageBtn(self.centralWidget())
        self.prev_image_btn.mouseReleaseEvent = lambda e: self.button_switch_cmd("-")

        self.next_image_btn = NextImageBtn(self.centralWidget())
        self.next_image_btn.mouseReleaseEvent = lambda e: self.button_switch_cmd("+")

        self.zoom_btns = ZoomBtns(parent=self.centralWidget())
        self.zoom_btns.zoom_in.clicked.connect(
            lambda: self.zoom_cmd("in")
        )
        self.zoom_btns.zoom_out.clicked.connect(
            lambda: self.zoom_cmd("out")
        )
        self.zoom_btns.zoom_fit.clicked.connect(
            lambda: self.zoom_cmd("fit")
        )
        self.zoom_btns.zoom_close.clicked.connect(
            lambda: self.deleteLater()
        )

        self.text_label = QLabel(self)
        self.text_label.setStyleSheet("background: black;")
        self.text_label.setAlignment(Qt.AlignmentFlag.AlignCenter)

        self.hide_all_buttons()
        QTimer.singleShot(100, self.first_load)

# SYSTEM SYSTEM SYSTEM SYSTEM SYSTEM SYSTEM SYSTEM SYSTEM SYSTEM SYSTEM SYSTEM


    def first_load(self):
        if not Mf.current.set_curr_path():
            self.no_connection.emit()
        self.load_thumb()
    
    def zoom_cmd(self, flag: str):
        actions = {
            "in": self.image_label.zoom_in,
            "out": self.image_label.zoom_out,
            "fit": self.image_label.zoom_fit,
        }
        actions[flag]()

    def restart_img_wid(self, pixmap: QPixmap):
        self.text_label.hide()
        self.image_label.hide()  # скрываем старый
        new_wid = ImageWidget(pixmap)
        new_wid.mouse_moved.connect(self.zoom_btns.show)
        self.central_layout.addWidget(new_wid)

        self.image_label.deleteLater()
        self.image_label = new_wid
        self.image_label.show()

        btns = (self.zoom_btns, self.prev_image_btn, self.next_image_btn)
        for i in btns:
            i.raise_()

    def show_text_label(self, text: str):
        self.text_label.setText(text)
        self.text_label.raise_()  # поверх остальных
        self.text_label.show()

    def load_thumb(self):
        self.set_title()
        try:
            pixmap = self.wid.img
        except Exception:
            pixmap = None
        if pixmap:
            self.restart_img_wid(pixmap)
        else:
            t = f"{os.path.basename(self.rel_path)}\n{Lng.loading[cfg.lng]}"
            self.show_text_label(t)

        if Mf.current.set_curr_path():
            self.path = Utils.get_abs_path(Mf.current.curr_path, self.rel_path)
            self.load_image()
        else:
            print("img viewer > no smb")

    def load_image(self):
        def fin(data: tuple[str, QImage]):
            self.task_count -= 1
            old_path, qimage = data
            if qimage:
                if old_path == self.path:
                    pixmap = QPixmap.fromImage(qimage)
                    self.restart_img_wid(pixmap)
            else:
                t = f"{os.path.basename(self.path)}\n{Lng.read_file_error[cfg.lng]}"
                self.show_text_label(t)

        self.task_count += 1
        img_thread = OneImgLoader(self.path, self.cached_images)
        img_thread.sigs.finished_.connect(fin)
        UThreadPool.start(img_thread)

# GUI GUI GUI GUI GUI GUI GUI GUI GUI GUI GUI GUI GUI GUI GUI GUI GUI GUI

    def hide_all_buttons(self):
        btns = (self.prev_image_btn, self.next_image_btn, self.zoom_btns)
        widget_under_cursor = QApplication.widgetAt(QCursor.pos())
        if isinstance(widget_under_cursor, QSvgWidget):
            return
        for i in btns:
            i.hide()

    def switch_image(self, offset):
        if self.task_count == self.task_count_limit:
            return

        # мы формируем актуальный список src из актуальной сетки изображений
        self.rel_paths = list(self.path_to_wid.keys())

        if self.rel_path in self.rel_paths:
            current_index = self.rel_paths.index(self.rel_path)
            new_index = current_index + offset
        else:
            new_index = 0

        if new_index == len(self.rel_paths):
            new_index = 0

        elif new_index < 0:
            new_index = len(self.rel_paths) - 1

        # 
        # сетка = Thumbnail.path_to_wid = сетка thumbnails
        # 

        # ищем новый src после или до предыдущего
        # так как мы сохранили список src сетки, то новый src будет найден
        # но не факт, что он уже есть в сетке
        try:
            rel_path = self.rel_paths[new_index]
        except IndexError as e:
            print(e)
            return

        # ищем виджет в актуальной сетке, которая могла обновиться в фоне
        new_wid = self.path_to_wid.get(rel_path)

        # если виджет не найден в сетке
        # значит сетка обновилась в фоне с новыми виджетами
        # формируем заново список src соответсвуя новой сетке
        # берем первый src из этого списка
        # и первый виджет из сетки
        if not new_wid:
            self.rel_path = self.rel_paths[0]
            self.wid = self.path_to_wid.get(self.rel_path)

        # если виджет найден, тоне факт, что список src актуален
        # то есть сетка все равно могла быть перетасована
        # формируем заново список src соответсвуя новой сетке
        # так как мы ранее выяснили, что виджет есть в новой сетке
        # то есть и src в списке src
        # поэтому берем ранее найденный src и виджет
        else:
            self.rel_path = rel_path
            self.wid = new_wid

        self.load_thumb()

        # если был выделен один виджет для просмотра, значит мы просматриваем
        # все виджеты в сетке и, по мере пролистывания изображений,
        # выделяем просматриваемый виджет
        # но если было выбрано для просмотра х число виджетов, мы не 
        # снимаем с них выделение
        if not self.is_selection:
            self.switch_image_sig.emit(self.rel_path)

    def set_title(self):
        basename = os.path.basename(os.path.dirname(self.wid.rel_path))
        filename = os.path.basename(self.wid.rel_path)
        self.setWindowTitle(f"{basename}: {filename}")

    def button_switch_cmd(self, flag: Literal["+", "-"]) -> None:
        if flag == "+":
            self.switch_image(1)
        else:
            self.switch_image(-1)
        self.image_label.setCursor(Qt.CursorShape.ArrowCursor)

    def change_fav(self, value: int):
        self.wid.set_fav(value)
        self.set_title()


# EVENTS EVENTS EVENTS EVENTS EVENTS EVENTS EVENTS EVENTS EVENTS EVENTS 

    def keyPressEvent(self, ev: QKeyEvent | None) -> None:
        if ev.key() == Qt.Key.Key_Left:
            self.switch_image(-1)

        elif ev.key() == Qt.Key.Key_Right:
            self.switch_image(1)

        elif ev.key() == Qt.Key.Key_Escape:
            if self.isFullScreen():
                self.showNormal()
                self.raise_()
            else:
                self.deleteLater()

        elif ev.key() == Qt.Key.Key_Equal:
            self.image_label.zoom_in()

        elif ev.key() == Qt.Key.Key_Minus:
            self.image_label.zoom_out()

        elif ev.key() == Qt.Key.Key_0:
            self.image_label.zoom_fit()

        elif ev.modifiers() & Qt.KeyboardModifier.ControlModifier and ev.key() == Qt.Key.Key_I:
            self.open_win_info.emit([self.rel_path])

        # return super().keyPressEvent(ev)

    def contextMenuEvent(self, ev: QContextMenuEvent | None) -> None:

        self.menu_ = UMenu(event=ev)
        rel_paths = [self.rel_path]

        # открыть в приложении
        open_menu = USubMenu(
            f"{Lng.open_in[cfg.lng]} ({len(rel_paths)})",
            self.menu_
        )

        act = QAction(Lng.open_default[cfg.lng], open_menu)
        act.triggered.connect(
            lambda: self.open_in_app.emit((rel_paths, None))
        )
        open_menu.addAction(act)
        open_menu.addSeparator()

        for app_path, basename in self.image_apps.items():
            act = QAction(basename, open_menu)
            act.triggered.connect(
                lambda _, x=app_path: self.open_in_app.emit((rel_paths, x))
            )
            open_menu.addAction(act)

        self.menu_.addMenu(open_menu)

        self.fav_action = SetFav(self.menu_, self.wid.fav_value)
        self.fav_action.triggered.connect(
            lambda: self.set_fav.emit(
                (self.wid.rel_path, not self.wid.fav_value)
            )
        )
        self.menu_.addAction(self.fav_action)

        info = WinInfoAction(self.menu_)
        info.triggered.connect(
            lambda: self.open_win_info.emit(rel_paths)
        )
        self.menu_.addAction(info)

        self.menu_.addSeparator()

        reveal = RevealInFinder(self.menu_, 1)
        reveal.triggered.connect(
            lambda: self.reveal_in_finder.emit(rel_paths)
        )
        self.menu_.addAction(reveal)

        copy_path = CopyPath(self.menu_, 1)
        copy_path.triggered.connect(
            lambda: self.copy_path.emit(rel_paths)
        )
        self.menu_.addAction(copy_path)

        copy_name = CopyName(self.menu_, 1)
        copy_name.triggered.connect(
            lambda: self.copy_name.emit(rel_paths)
        )
        self.menu_.addAction(copy_name)

        self.menu_.addSeparator()

        save = Save(self.menu_, 1)
        save.triggered.connect(
            lambda: self.save_files.emit(
                (os.path.expanduser("~/Downloads"), rel_paths)
            )
        )
        self.menu_.addAction(save)

        save_as = SaveAs(self.menu_, 1)
        save_as.triggered.connect(
            lambda: self.save_files.emit(
                (None, rel_paths)
            )
        )
        self.menu_.addAction(save_as)

        self.menu_.show_umenu()

    def resizeEvent(self, a0: QResizeEvent | None) -> None:
        vertical_center = a0.size().height() // 2 - self.next_image_btn.height() // 2
        right_window_side = a0.size().width() - self.next_image_btn.width()
        self.prev_image_btn.move(10, vertical_center)
        self.next_image_btn.move(right_window_side - 10, vertical_center)

        horizontal_center = a0.size().width() // 2 - self.zoom_btns.width() // 2
        bottom_window_side = a0.size().height() - self.zoom_btns.height()
        self.zoom_btns.move(horizontal_center, bottom_window_side - 50)

        self.ww = a0.size().width()
        self.hh = a0.size().height()

        self.text_label.resize(self.size())
        self.setFocus()

        return super().resizeEvent(a0)

    def eventFilter(self, a0: QObject | None, a1: QEvent | None) -> bool:
        if a1.type() == 129:
            self.mouse_move_timer.stop()
            self.prev_image_btn.show()
            self.next_image_btn.show()
            self.zoom_btns.show()
            self.mouse_move_timer.start(2000)
        return super().eventFilter(a0, a1)

    def leaveEvent(self, a0: QEvent | None) -> None:
        self.hide_all_buttons()
        return super().leaveEvent(a0)

    def closeEvent(self, a0):
        self.closed_.emit()
        return super().closeEvent(a0)
    
    def deleteLater(self):
        self.closed_.emit()
        return super().deleteLater()