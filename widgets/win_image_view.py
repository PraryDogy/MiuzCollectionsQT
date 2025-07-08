import gc
import os
from typing import Literal

from PyQt5.QtCore import QEvent, QObject, QPoint, QSize, Qt, QTimer, pyqtSignal
from PyQt5.QtGui import (QContextMenuEvent, QKeyEvent, QMouseEvent, QPainter,
                         QPaintEvent, QPixmap, QPixmapCache, QResizeEvent)
from PyQt5.QtWidgets import QFrame, QLabel, QSpacerItem, QWidget

from cfg import Static
from system.lang import Lang
from system.main_folder import MainFolder
from system.tasks import LoadImage, LoadThumb
from system.utils import MainUtils, UThreadPool

from ._base_widgets import (SvgShadowed, UHBoxLayout, UMenu, UVBoxLayout,
                            WinChild)
from .actions import (CopyName, CopyPath, FavActionDb, ShowInFinder, Save,
                      WinInfoAction)
from .win_info import WinInfo
from .win_warn import WinWarn
from .grid import Thumbnail


class ImageWidget(QLabel):
    def __init__(self):
        super().__init__()
        self.setAlignment(Qt.AlignmentFlag.AlignCenter)

        self.current_pixmap: QPixmap = None
        self.scale_factor: float = 1.0
        self.offset = QPoint(0, 0)
        self.w, self.h = 0, 0

    def set_image(self, pixmap: QPixmap):
        self.current_pixmap = pixmap
        self.scale_factor = 1.0
        self.offset = QPoint(0, 0)
        self.setCursor(Qt.CursorShape.ArrowCursor)
        self.w, self.h = self.width(), self.height()

        self.current_pixmap.scaled(
            self.w, self.h, 
            Qt.AspectRatioMode.KeepAspectRatio,
            Qt.TransformationMode.SmoothTransformation
            )
        self.update()

    def zoom_in(self):
        self.scale_factor *= 1.1
        self.setCursor(Qt.CursorShape.OpenHandCursor)
        self.update()

    def zoom_out(self):
        self.scale_factor /= 1.1
        self.update()

    def zoom_reset(self):
        self.scale_factor = 1.0
        self.offset = QPoint(0, 0)
        self.setCursor(Qt.CursorShape.ArrowCursor)
        self.update()

    def mousePressEvent(self, ev: QMouseEvent | None) -> None:
        if ev.button() == Qt.MouseButton.LeftButton:
            self.last_mouse_pos = ev.pos()
        return super().mousePressEvent(ev)

    def mouseMoveEvent(self, ev: QMouseEvent | None) -> None:
        if ev.buttons() == Qt.MouseButton.LeftButton and self.scale_factor > 1.0:
            delta = ev.pos() - self.last_mouse_pos
            self.offset += delta
            self.last_mouse_pos = ev.pos()
            self.setCursor(Qt.CursorShape.ClosedHandCursor)
            self.update()
        return super().mouseMoveEvent(ev)

    def mouseReleaseEvent(self, ev: QMouseEvent | None) -> None:
        if self.scale_factor > 1.0:
            self.setCursor(Qt.CursorShape.OpenHandCursor)
        return super().mouseReleaseEvent(ev)

    def paintEvent(self, a0: QPaintEvent | None) -> None:
        if self.current_pixmap is not None:
            painter = QPainter(self)
            scaled_pixmap = self.current_pixmap.scaled(
                int(self.w * self.scale_factor),
                int(self.h * self.scale_factor),
                Qt.AspectRatioMode.KeepAspectRatio,
                Qt.TransformationMode.SmoothTransformation
                )

            offset = self.offset + QPoint(
                int((self.width() - scaled_pixmap.width()) / 2),
                int((self.height() - scaled_pixmap.height()) / 2)
                )
            painter.drawPixmap(offset, scaled_pixmap)
        return super().paintEvent(a0)

    def resizeEvent(self, a0: QResizeEvent | None) -> None:
        self.w, self.h = self.width(), self.height()
        self.update()
        return super().resizeEvent(a0)
    

class ZoomBtns(QFrame):
    style_ = """
        background-color: rgba(128, 128, 128, 0.40);
        border-radius: 15px;
    """
    size_ = 45
    zoom_out_svg = os.path.join(Static.INNER_IMAGES, "zoom_out.svg")
    zoom_in_svg = os.path.join(Static.INNER_IMAGES, "zoom_in.svg")
    zoom_fit_svg = os.path.join(Static.INNER_IMAGES, "zoom_fit.svg")
    zoom_close_svg = os.path.join(Static.INNER_IMAGES, "zoom_close.svg")

    def __init__(self, parent: QWidget = None) -> None:
        super().__init__(parent)
        self.setStyleSheet(self.style_)

        h_layout = UHBoxLayout()
        self.setLayout(h_layout)

        h_layout.addSpacerItem(QSpacerItem(5, 0))

        self.zoom_out = SvgShadowed(self.zoom_out_svg, self.size_)
        h_layout.addWidget(self.zoom_out)
        h_layout.addSpacerItem(QSpacerItem(10, 0))

        self.zoom_in = SvgShadowed(self.zoom_in_svg, self.size_)
        h_layout.addWidget(self.zoom_in)
        h_layout.addSpacerItem(QSpacerItem(10, 0))

        self.zoom_fit = SvgShadowed(self.zoom_fit_svg, self.size_)
        h_layout.addWidget(self.zoom_fit)
        h_layout.addSpacerItem(QSpacerItem(10, 0))

        self.zoom_close = SvgShadowed(self.zoom_close_svg, self.size_)
        h_layout.addWidget(self.zoom_close)

        h_layout.addSpacerItem(QSpacerItem(5, 0))

        self.adjustSize()


class SwitchImageBtn(QFrame):
    style_ = """
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
    svg_ = os.path.join(Static.INNER_IMAGES, "prev.svg")

    def __init__(self, parent: QWidget = None) -> None:
        super().__init__(self.svg_, parent)


class NextImageBtn(SwitchImageBtn):
    svg_ = os.path.join(Static.INNER_IMAGES, "next.svg")

    def __init__(self, parent: QWidget = None) -> None:
        super().__init__(self.svg_, parent)


class WinImageView(WinChild):
    task_count_limit = 10
    switch_image_sig = pyqtSignal(object)
    closed_ = pyqtSignal()
    ww, hh = 700, 500
    min_w, min_h = 500, 400
    style_ = """
        background: black;
    """

    def __init__(self, rel_img_path: str, path_to_wid: dict[str, Thumbnail], is_selection: bool):
        super().__init__()

        self.cached_images: dict[str, QPixmap] = {}
        self.is_selection = is_selection
        self.path_to_wid = path_to_wid
        self.rel_img_path_list = list(path_to_wid.keys())
        self.rel_img_path = rel_img_path
        self.wid = path_to_wid.get(self.rel_img_path)
        self.task_count = 0

        self.setStyleSheet(self.style_)
        self.setMinimumSize(QSize(self.min_w, self.min_h))
        self.resize(self.ww, self.hh)
        self.installEventFilter(self)

        self.mouse_move_timer = QTimer(self)
        self.mouse_move_timer.setSingleShot(True)
        self.mouse_move_timer.timeout.connect(self.hide_all_buttons)

        self.image_label = ImageWidget()
        self.central_layout.addWidget(self.image_label)
        self.prev_image_btn = PrevImageBtn(self.centralWidget())
        self.prev_image_btn.mouseReleaseEvent = lambda e: self.button_switch_cmd("-")

        self.next_image_btn = NextImageBtn(self.centralWidget())
        self.next_image_btn.mouseReleaseEvent = lambda e: self.button_switch_cmd("+")

        self.zoom_btns = ZoomBtns(parent=self.centralWidget())
        self.zoom_btns.zoom_in.mouseReleaseEvent = (
            lambda e: self.image_label.zoom_in()
        )
        self.zoom_btns.zoom_out.mouseReleaseEvent = (
            lambda e: self.image_label.zoom_out()
        )
        self.zoom_btns.zoom_fit.mouseReleaseEvent = (
            lambda e: self.image_label.zoom_reset()
        )
        self.zoom_btns.zoom_close.mouseReleaseEvent = lambda e: self.deleteLater()

        self.hide_all_buttons()
        QTimer.singleShot(100, self.first_load)

# SYSTEM SYSTEM SYSTEM SYSTEM SYSTEM SYSTEM SYSTEM SYSTEM SYSTEM SYSTEM SYSTEM


    def first_load(self):
        main_folder_path = MainFolder.current.is_available()
        if not main_folder_path:
            self.open_smb_win()

        self.load_thumb()

    def load_thumb(self):
        self.setFocus()
        self.img_viewer_title()
        task = LoadThumb(self.rel_img_path)
        task.signals_.finished_.connect(self.load_thumb_fin)
        UThreadPool.start(task)

    def load_thumb_fin(self, data: tuple[str, QPixmap]):
        rel_img_path, pixmap = data
        self.image_label.set_image(pixmap)
        main_folder_path = MainFolder.current.is_available()
        if main_folder_path:
            self.img_path = MainUtils.get_abs_path(main_folder_path, self.rel_img_path)
            self.load_image()
        else:
            print("img viewer > no smb")

    def load_image(self):
        self.task_count += 1
        cmd_ = lambda data: self.load_image_fin(data, self.img_path)
        img_thread = LoadImage(self.img_path, self.cached_images)
        img_thread.signals_.finished_.connect(cmd_)
        UThreadPool.start(img_thread)

    def load_image_fin(self, data: tuple[str, QPixmap], current_img_path: str):
        old_img_path, pixmap = data
        self.task_count -= 1
        if pixmap.width() == 0 or old_img_path != current_img_path:
            return
        elif isinstance(pixmap, QPixmap):
            try:
                self.image_label.set_image(pixmap)
            except RuntimeError:
                ...

# GUI GUI GUI GUI GUI GUI GUI GUI GUI GUI GUI GUI GUI GUI GUI GUI GUI GUI

    def hide_all_buttons(self):
        for i in (self.prev_image_btn, self.next_image_btn, self.zoom_btns):
            if i.underMouse():
                return
        self.zoom_btns.hide()
        self.prev_image_btn.hide()
        self.next_image_btn.hide()

    def switch_image(self, offset):
        if self.task_count == WinImageView.task_count_limit:
            return

        # мы формируем актуальный список src из актуальной сетки изображений
        self.rel_img_path_list = list(self.path_to_wid.keys())

        if self.rel_img_path in self.rel_img_path_list:
            current_index = self.rel_img_path_list.index(self.rel_img_path)
            new_index = current_index + offset
        else:
            new_index = 0

        if new_index == len(self.rel_img_path_list):
            new_index = 0

        elif new_index < 0:
            new_index = len(self.rel_img_path_list) - 1

        # 
        # сетка = Thumbnail.path_to_wid = сетка thumbnails
        # 

        # ищем новый src после или до предыдущего
        # так как мы сохранили список src сетки, то новый src будет найден
        # но не факт, что он уже есть в сетке
        try:
            rel_img_path = self.rel_img_path_list[new_index]
        except IndexError as e:
            print(e)
            return

        # ищем виджет в актуальной сетке, которая могла обновиться в фоне
        new_wid = self.path_to_wid.get(rel_img_path)

        # если виджет не найден в сетке
        # значит сетка обновилась в фоне с новыми виджетами
        # формируем заново список src соответсвуя новой сетке
        # берем первый src из этого списка
        # и первый виджет из сетки
        if not new_wid:
            self.rel_img_path = self.rel_img_path_list[0]
            self.wid = self.path_to_wid.get(self.rel_img_path)

        # если виджет найден, тоне факт, что список src актуален
        # то есть сетка все равно могла быть перетасована
        # формируем заново список src соответсвуя новой сетке
        # так как мы ранее выяснили, что виджет есть в новой сетке
        # то есть и src в списке src
        # поэтому берем ранее найденный src и виджет
        else:
            self.rel_img_path = rel_img_path
            self.wid = new_wid

        self.load_thumb()

        # если был выделен один виджет для просмотра, значит мы просматриваем
        # все виджеты в сетке и, по мере пролистывания изображений,
        # выделяем просматриваемый виджет
        # но если было выбрано для просмотра х число виджетов, мы не 
        # снимаем с них выделение
        if not self.is_selection:
            self.switch_image_sig.emit(self.rel_img_path)

    def img_viewer_title(self):
        self.setWindowTitle(f"{self.wid.collection}: {self.wid.name}")

    def button_switch_cmd(self, flag: Literal["+", "-"]) -> None:
        if flag == "+":
            self.switch_image(1)
        else:
            self.switch_image(-1)
        self.image_label.setCursor(Qt.CursorShape.ArrowCursor)

    def change_fav(self, value: int):
        self.wid.change_fav(value)
        self.img_viewer_title()

    def open_info_win_delayed(self):
        self.win_info.adjustSize()
        self.win_info.center_relative_parent(self)
        self.win_info.show()

    def open_smb_win(self):
        self.win_warn = WinWarn(Lang.no_connection, Lang.no_connection_descr)
        self.win_warn.adjustSize()
        self.win_warn.center_relative_parent(self)
        self.win_warn.show()

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
            self.image_label.zoom_reset()

        elif ev.modifiers() & Qt.KeyboardModifier.ControlModifier and ev.key() == Qt.Key.Key_I:
            main_folder_path = MainFolder.current.is_available()
            if main_folder_path:
                img_path = MainUtils.get_abs_path(main_folder_path, self.rel_img_path)
                img_path_list = [img_path]
                self.win_info = WinInfo(img_path_list)
                self.win_info.finished_.connect(self.open_info_win_delayed)
            else:
                self.open_smb_win()

        return super().keyPressEvent(ev)

    def contextMenuEvent(self, ev: QContextMenuEvent | None) -> None:

        self.menu_ = UMenu(event=ev)
        rel_img_path_list = [self.rel_img_path]

        info = WinInfoAction(self.menu_, self, rel_img_path_list)
        self.menu_.addAction(info)

        self.fav_action = FavActionDb(self.menu_, self.rel_img_path, self.wid.fav_value)
        self.fav_action.finished_.connect(self.change_fav)
        self.menu_.addAction(self.fav_action)

        self.menu_.addSeparator()

        copy = CopyPath(self.menu_, self, [self.rel_img_path])
        self.menu_.addAction(copy)

        copy_name = CopyName(self.menu_, self, [self.rel_img_path])
        self.menu_.addAction(copy_name)

        reveal = ShowInFinder(self.menu_, self, [self.rel_img_path])
        self.menu_.addAction(reveal)

        save_as = Save(self.menu_, self, [self.rel_img_path], True)
        self.menu_.addAction(save_as)

        save = Save(self.menu_, self, [self.rel_img_path], False)
        self.menu_.addAction(save)

        self.menu_.show_()

    def resizeEvent(self, a0: QResizeEvent | None) -> None:
        vertical_center = a0.size().height() // 2 - self.next_image_btn.height() // 2
        right_window_side = a0.size().width() - self.next_image_btn.width()
        self.prev_image_btn.move(10, vertical_center)
        self.next_image_btn.move(right_window_side - 10, vertical_center)

        horizontal_center = a0.size().width() // 2 - self.zoom_btns.width() // 2
        bottom_window_side = a0.size().height() - self.zoom_btns.height()
        self.zoom_btns.move(horizontal_center, bottom_window_side - 50)

        WinImageView.ww = a0.size().width()
        WinImageView.hh = a0.size().height()

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
        self.cached_images.clear()
        QPixmapCache.clear()
        gc.collect()
        self.closed_.emit()
        return super().closeEvent(a0)
    
    def deleteLater(self):
        self.cached_images.clear()
        QPixmapCache.clear()
        gc.collect()
        self.closed_.emit()
        return super().deleteLater()