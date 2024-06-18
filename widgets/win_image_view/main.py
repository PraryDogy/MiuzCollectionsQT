import os

import sqlalchemy
from PyQt5.QtCore import (QEvent, QObject, QPoint, QSize, Qt, QThread, QTimer,
                          pyqtSignal)
from PyQt5.QtGui import (QFocusEvent, QImage, QMouseEvent, QPainter, QPixmap,
                         QResizeEvent)
from PyQt5.QtWidgets import QFrame, QLabel, QSpacerItem, QWidget

from base_widgets import LayoutH, LayoutV, SvgShadowed, WinImgViewBase
from cfg import cnf
from database import Dbase, ThumbsMd
from signals import gui_signals_app
from styles import Names, Themes
from utils import MainUtils, ReadDesatImage, get_image_size

from ..image_context import ImageContext
from ..notification import Notification
from ..win_smb import WinSmb


class Manager:
    images = {}
    threads = []
    win_smb: WinSmb = None


class ImageWinUtils:

    @staticmethod
    def close_same_win():
        widgets: list[WinImgViewBase] = MainUtils.get_app().topLevelWidgets()

        for widget in widgets:
            if isinstance(widget, WinImgViewBase):

                cnf.imgview_g.update(
                    {"aw": widget.width(), "ah": widget.height()}
                    )

                widget.deleteLater()


class FSizeImgThread(QThread):
    image_loaded = pyqtSignal(dict)

    def __init__(self, image_path: str):
        super().__init__()
        self.image_path = image_path

    def run(self):
        try:
            if not os.path.exists(self.image_path):
                print("image viewer thread no connection")
                return

            if self.image_path not in Manager.images:

                img = ReadDesatImage(self.image_path)
                img = img.get_rgb_image()
                q_image = QImage(img.data, img.shape[1], img.shape[0],
                                img.shape[1] * 3, QImage.Format_RGB888)
                Manager.images[self.image_path] = q_image

            else:
                q_image = Manager.images[self.image_path]

        except Exception as e:
            print("image viewer cant open image, open with pixmap")
            print(e)

            q_image = QImage()
            q_image.load(self.image_path)
            Manager.images[self.image_path] = q_image

        pixmap = QPixmap.fromImage(q_image)

        if len(Manager.images) > 50:
            Manager.images.pop(next(iter(Manager.images)))

        self.image_loaded.emit(
            {"image": pixmap,
             "width": pixmap.width(),
             "src": self.image_path
             }
             )


class ImageWidget(QLabel):
    def __init__(self):
        super().__init__()
        self.setAlignment(Qt.AlignCenter)

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
        self.setCursor(Qt.OpenHandCursor)
        self.update()

    def zoom_out(self):
        self.scale_factor /= 1.1
        self.update()

    def zoom_reset(self):
        self.scale_factor = 1.0
        self.offset = QPoint(0, 0)
        self.setCursor(Qt.CursorShape.ArrowCursor)
        self.update()

    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            self.last_mouse_pos = event.pos()

    def mouseMoveEvent(self, event):
        if event.buttons() == Qt.LeftButton and self.scale_factor > 1.0:
            delta = event.pos() - self.last_mouse_pos
            self.offset += delta
            self.last_mouse_pos = event.pos()
            self.setCursor(Qt.CursorShape.ClosedHandCursor)
            self.update()

    def mouseReleaseEvent(self, ev: QMouseEvent | None) -> None:
        if self.scale_factor > 1.0:
            self.setCursor(Qt.CursorShape.OpenHandCursor)
        return super().mouseReleaseEvent(ev)

    def paintEvent(self, event):
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

    def resizeEvent(self, a0: QResizeEvent | None) -> None:
        self.w, self.h = self.width(), self.height()
        self.update()
        return super().resizeEvent(a0)
    

class NaviZoom(QFrame):
    def __init__(self, parent: QWidget = None) -> None:
        super().__init__(parent)

        self.setObjectName(Names.navi_zoom)
        self.setStyleSheet(Themes.current)

        h_layout = LayoutH()
        self.setLayout(h_layout)

        h_layout.addSpacerItem(QSpacerItem(10, 0))

        self.zoom_out = SvgShadowed(os.path.join("images", "zoom_out.svg"), 45)
        h_layout.addWidget(self.zoom_out)
        h_layout.addSpacerItem(QSpacerItem(20, 0))

        self.zoom_in = SvgShadowed(os.path.join("images", "zoom_in.svg"), 45)
        h_layout.addWidget(self.zoom_in)
        h_layout.addSpacerItem(QSpacerItem(20, 0))

        self.zoom_fit = SvgShadowed(os.path.join("images", "zoom_fit.svg"), 45)
        h_layout.addWidget(self.zoom_fit)

        h_layout.addSpacerItem(QSpacerItem(10, 0))

        self.adjustSize()

    def bind_btns(
            self,
            zoom_out_cmd: callable,
            zoom_in_cmd: callable,
            zoom_fit_cmd: callable
            ):

        self.zoom_out.mouseReleaseEvent = zoom_out_cmd
        self.zoom_in.mouseReleaseEvent = zoom_in_cmd
        self.zoom_fit.mouseReleaseEvent = zoom_fit_cmd


class NaviArrow(QFrame):
    def __init__(self, icon_name: str, parent: QWidget = None) -> None:
        super().__init__(parent)
        self.setObjectName(Names.navi_switch)
        self.setStyleSheet(Themes.current)
        self.setFixedSize(54, 54) # 27px border-radius, 27 * 2 for round shape

        v_layout = LayoutV()
        self.setLayout(v_layout)

        btn = SvgShadowed(os.path.join("images", icon_name), 50)
        v_layout.addWidget(btn)


class NaviArrowPrev(NaviArrow):
    def __init__(self, parent: QWidget = None) -> None:
        super().__init__("prev.svg", parent)


class NaviArrowNext(NaviArrow):
    def __init__(self, parent: QWidget = None) -> None:
        super().__init__("next.svg", parent)


class WinImageView(WinImgViewBase):
    def __init__(self, parent: QWidget, img_src: str):
        ImageWinUtils.close_same_win()
        self.img_src = img_src
        self.fsize_img_thread = None

        super().__init__(close_func=self.my_close)
        self.setMinimumSize(QSize(500, 400))
        self.my_set_title()
        self.resize(cnf.imgview_g["aw"], cnf.imgview_g["ah"])

        self.fsize_img_timer = QTimer(self)
        self.fsize_img_timer.setSingleShot(True)
        self.fsize_img_timer.timeout.connect(self.run_thread)

        self.mouse_move_timer = QTimer(self)
        self.mouse_move_timer.setSingleShot(True)
        self.mouse_move_timer.setInterval(2000)
        self.mouse_move_timer.timeout.connect(self.hide_navi_btns)
        self.installEventFilter(self)

        self.image_label = ImageWidget()
        self.content_layout.addWidget(
            self.image_label,
            )

        self.notification = Notification(self.content_wid)
        self.notification.resize(self.width() - 20, 30)
        self.notification.move(10, 2)
        gui_signals_app.noti_img_view.connect(self.notification.show_notify)

        self.navi_prev = NaviArrowPrev(self.content_wid)
        self.navi_prev.mouseReleaseEvent = lambda e: self.navi_switch_img("-")

        self.navi_next = NaviArrowNext(self.content_wid)
        self.navi_next.mouseReleaseEvent = lambda e: self.navi_switch_img("+")

        self.navi_zoom = NaviZoom(parent=self.content_wid)
        self.navi_zoom.bind_btns(
            lambda e: self.image_label.zoom_out(),
            lambda e: self.image_label.zoom_in(),
            lambda e : self.image_label.zoom_reset()
            )
        self.hide_navi_btns()

        self.setFocus()
        self.center_win(parent)
        self.load_image(interval=200)

        smb_timer = QTimer(self)
        smb_timer.setSingleShot(True)
        smb_timer.timeout.connect(self.smb_check_first)
        smb_timer.start(300)

    def smb_check_first(self):
        if not MainUtils.smb_check():
            Manager.win_smb = WinSmb(parent=self)
            Manager.win_smb.show()
            Manager.win_smb.finished.connect(self.run_thread)

    def load_image(self, interval: int = 50):
        if self.img_src not in Manager.images:
            self.my_set_title(loading=True)

            q = (sqlalchemy.select(ThumbsMd.img150)
                .filter(ThumbsMd.src == self.img_src))
            session = Dbase.get_session()

            try:
                res = session.execute(q).first()[0]

            except Exception as e:
                print(e)
                self.update_geometry()
                self.deleteLater()
                return

            finally:
                session.close()    

            pixmap = QPixmap()
            pixmap.loadFromData(res)
            self.image_label.set_image(pixmap)

        self.fsize_img_timer.start(interval)

    def move_navi_btns(self):
        navi_h = (self.height() // 2) - (self.navi_next.height() // 2)
        navi_next_w = self.width() - self.navi_next.width() - 12
        self.navi_prev.move(10, navi_h)
        self.navi_next.move(navi_next_w, navi_h)

        zoom_w = self.width() // 2 - self.navi_zoom.width() // 2
        zoom_h = self.height() - self.navi_zoom.height() - 50
        self.navi_zoom.move(zoom_w, zoom_h)

    def hide_navi_btns(self):
        for i in (self.navi_prev, self.navi_next, self.navi_zoom):
            if i.underMouse():
                return
        self.navi_zoom.hide()
        self.navi_prev.hide()
        self.navi_next.hide()

    def run_thread(self):
        self.fsize_img_thread = FSizeImgThread(self.img_src)
        self.fsize_img_thread.image_loaded.connect(self.finalize_thread)
        self.fsize_img_thread.start()
        Manager.threads.append(self.fsize_img_thread)

    def finalize_thread(self, data: dict):
        if data["width"] == 0 or data["src"] != self.img_src:
            return
        
        self.image_label.set_image(data["image"])
        self.my_set_title()
        Manager.threads.remove(self.fsize_img_thread)

    def switch_image(self, offset):
        try:
            keys = list(cnf.images.keys())
            current_index = keys.index(self.img_src)
        except Exception as e:
            print(e)
            keys = list(cnf.images.keys())
            current_index = 0

        total_images = len(cnf.images)
        new_index = (current_index + offset) % total_images
        self.img_src = keys[new_index]
        self.load_image()

    def cut_text(self, text: str) -> str:
        limit = 40
        if len(text) > limit:
            return text[:limit] + "..."
        return text

    def my_set_title(self, loading=False):
        if loading:
            self.set_title(cnf.lng.loading)
            return

        try:
            w, h = get_image_size(self.img_src)
        except Exception:
            w, h = "?", "?"
        coll = self.cut_text(MainUtils.get_coll_name(self.img_src))
        name = self.cut_text(os.path.basename(self.img_src))

        self.set_title(f"{w}x{h} - {coll} - {name}")

    def navi_switch_img(self, flag: str) -> None:
        if flag == "+":
            self.switch_image(1)
        else:
            self.switch_image(-1)
        self.setFocus()
        self.image_label.setCursor(Qt.CursorShape.ArrowCursor)

    def keyPressEvent(self, event):
        if event.key() == Qt.Key_Left:
            self.switch_image(-1)

        elif event.key() == Qt.Key_Right:
            self.switch_image(1)

        elif event.key() == Qt.Key_Escape:
            self.my_close(event)

        elif event.modifiers() & Qt.ControlModifier and event.key() == Qt.Key_Equal:
            self.image_label.zoom_in()

        elif event.modifiers() & Qt.ControlModifier and  event.key() == Qt.Key_Minus:
            self.image_label.zoom_out()

        elif event.modifiers() & Qt.ControlModifier and  event.key() == Qt.Key_0:
            self.image_label.zoom_reset()

        super().keyPressEvent(event)

    def contextMenuEvent(self, event):
        self.image_context = ImageContext(
            parent=self, img_src=self.img_src, event=event
            )
        self.image_context.show_menu()

    def focusInEvent(self, a0: QFocusEvent | None) -> None:
        self.setFocus()
        return super().focusInEvent(a0)

    def resizeEvent(self, event):
        self.move_navi_btns()
        self.notification.resize(self.width() - 20, 30)
        return super().resizeEvent(event)
    
    def eventFilter(self, a0: QObject | None, a1: QEvent | None) -> bool:
        if a1.type() == 129: # mouse move
            self.mouse_move_timer.stop()
            self.navi_prev.show()
            self.navi_next.show()
            self.navi_zoom.show()
            self.mouse_move_timer.start()
        return super().eventFilter(a0, a1)

    def leaveEvent(self, a0: QEvent | None) -> None:
        self.hide_navi_btns()
        return super().leaveEvent(a0)
    
    def update_geometry(self):
        cnf.imgview_g.update({"aw": self.width(), "ah": self.height()})

    def my_close(self, event):
        wid: QLabel = cnf.images[self.img_src]
        wid.setObjectName(Names.thumbnail_selected)
        wid.setStyleSheet(Themes.current)
        gui_signals_app.move_to_wid.emit(wid)

        timer = QTimer(parent=MainUtils.get_central_widget())
        timer.setSingleShot(True)
        timer.timeout.connect(lambda: self.after_close(wid=wid))
        timer.start(1500)

        Manager.images.clear()
        self.update_geometry()
        self.deleteLater()
        event.ignore()

    def after_close(self, wid: QLabel):
        try:
            wid.setFocus()
            wid.setObjectName(Names.thumbnail_normal)
            wid.setStyleSheet(Themes.current)
        except Exception as e:
            print(e)