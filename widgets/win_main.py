import os
import subprocess
from collections import defaultdict

from PyQt5.QtCore import Qt, QTimer
from PyQt5.QtGui import QCloseEvent, QIcon, QKeyEvent
from PyQt5.QtWidgets import (QDesktopWidget, QFileDialog, QFrame, QLabel,
                             QPushButton, QSplitter, QVBoxLayout, QWidget)
from typing_extensions import Literal

from cfg import Cfg, Dynamic, Static
from system.filters import Filters
from system.items import (Buffer, OnStartItem, SettingsItem,
                          SingleDirScanerItem, WatchDogItem)
from system.lang import Lng
from system.main_folder import Mf
from system.multiprocess import (DirWatcher, FilesRemover, OnStartTask,
                                 ProcessWorker, UpdateThumb)
from system.scaner import AllDirScaner, SingleDirScaner
from system.servers import Servers
from system.shared_utils import ImgUtils
from system.tasks import FavManager, MfDataCleaner, UThreadPool, Utils

from ._base_widgets import NotifyWid, UHBoxLayout, UMainWindow, UVBoxLayout
from .bar_bottom import BarBottom
from .bar_macos import BarMacos
from .bar_path import PathBar
from .bar_top import BarTop
from .grid import Grid
from .menu_left import MenuLeft
from .win_copy_files import WinCopyFiles
from .win_dates import WinDates
from .win_filters import WinFilters
from .win_image_view import WinImageView
from .win_info import WinInfo
from .win_servers import ServersWin
from .win_settings import WinSettings
from .win_upload import UploadWin
from .win_warn import ConfirmWindow


class TestWid(QFrame):
    def __init__(self, parent=None):
        super().__init__(parent=parent)
        self.setFixedSize(100, 100)
        self.setStyleSheet("background: black;")

        v_layout = QVBoxLayout()
        self.setLayout(v_layout)

        btn = QPushButton('test btn')
        v_layout.addWidget(btn)
        btn.clicked.connect(self.reload)

    def reload(self):
        ...


class USep(QFrame):
    def __init__(self):
        super().__init__()
        self.setStyleSheet("background: rgba(0, 0, 0, 0.2)")
        self.setFixedHeight(1)


class WinMain(UMainWindow):
    min_w = 750
    left_side_width = 250
    warning_svg = "./images/warning.svg"

    def __init__(self, argv: list[Literal["noscan", ""]]):
        super().__init__()
        self.resize(Static.ww, Static.hh)
        self.setMinimumWidth(self.min_w)
        self.setWindowTitle(f"{Static.app_name}")

        self.setWindowIcon(QIcon("./images/icon.png"))
        self.setWindowIconText(f"{Static.app_name} {Static.app_ver}")

        self.setAcceptDrops(True)
        self.setMenuBar(BarMacos())

        self.scaner_data: defaultdict[Mf, list[str]] = defaultdict(list)

        h_wid_main = QWidget()
        h_lay_main = UHBoxLayout()
        h_lay_main.setContentsMargins(5, 0, 5, 5)
        h_wid_main.setLayout(h_lay_main)
        self.central_layout.addWidget(h_wid_main)

        # Создаем QSplitter
        self.splitter = QSplitter(Qt.Orientation.Horizontal)
        self.splitter.setHandleWidth(14)

        # Левый виджет (MenuLeft)
        self.left_menu = MenuLeft()
        self.left_menu.no_connection.connect(
            lambda mf: self.open_win_smb(self.grid, mf)
        )
        self.left_menu.reload_thumbnails.connect(
            lambda: self.grid.reload_thumbnails()
        )
        self.left_menu.reload_thumbnails.connect(
            lambda: self.path_bar_update(Dynamic.current_dir)
        )
        self.left_menu.mf_edit.connect(
            lambda settings_item: self.open_settings_win(settings_item)
        )
        self.left_menu.mf_new.connect(
            lambda settings_item: self.open_settings_win(settings_item)
        )
        self.splitter.addWidget(self.left_menu)

        # Правый виджет
        right_wid = QWidget()
        self.splitter.addWidget(right_wid)
        right_lay = UVBoxLayout()
        right_lay.setContentsMargins(0, 0, 0, 0)
        right_wid.setLayout(right_lay)

        # Добавляем элементы в правую панель
        self.bar_top = BarTop()
        self.bar_top.open_dates_win.connect(
            lambda: self.open_dates_win()
        )
        self.bar_top.reload_thumbnails.connect(
            lambda: self.grid.reload_thumbnails()
            )
        self.bar_top.open_settings_win.connect(
            lambda settings_item: self.open_settings_win(settings_item)
        )
        self.bar_top.open_filters_win.connect(
            lambda: self.open_filters_win()
        )
        right_lay.addWidget(self.bar_top)

        sep_upper = USep()
        right_lay.addWidget(sep_upper)

        self.grid = Grid()
        self.grid.restart_scaner.connect(
            lambda: self.restart_scaner_task()
        )
        self.grid.remove_files.connect(
            lambda rel_paths: self.remove_files(self, Mf.current_mf, rel_paths, ))
        self.grid.no_connection.connect(
            lambda: self.open_win_smb(self.grid, Mf.current_mf)
        )
        self.grid.open_img_view.connect(
            lambda: self.open_view_win()
        )
        self.grid.save_files.connect(
            lambda data: self.save_files(self.grid, Mf.current_mf, data)
        )
        self.grid.open_info_win.connect(
            lambda rel_paths: self.open_info_win(self.grid, Mf.current_mf, rel_paths)
        )
        self.grid.copy_path.connect(
            lambda rel_paths: self.copy_path(self.grid, Mf.current_mf, rel_paths)
        )
        self.grid.copy_name.connect(
            lambda rel_paths: self.copy_name(self.grid, Mf.current_mf, rel_paths)
        )
        self.grid.reveal_in_finder.connect(
            lambda rel_paths: self.reveal_in_finder(self.grid, Mf.current_mf, rel_paths)
        )
        self.grid.set_fav.connect(
            self.set_fav
        )
        self.grid.open_in_app.connect(
            lambda data: self.open_in_app(self.grid, Mf.current_mf, data))
        self.grid.paste_files.connect(
            lambda: self.paste_files(self.grid,  Mf.current_mf)
        )
        self.grid.set_clipboard.connect(
            lambda data: self.set_buffer(self.grid, Mf.current_mf, data)
        )
        self.grid.setup_mf.connect(
            self.open_settings_win
        )
        self.grid.go_to_widget.connect(
            lambda rel_path: self.go_to_widget(rel_path)
        )
        self.grid.path_bar_update.connect(
            lambda rel_path: self.path_bar_update(rel_path)
        )
        self.grid.update_thumb.connect(
            lambda rel_path: self.start_update_thumb(
                self.grid, Mf.current_mf, rel_path
            )
        )
        right_lay.addWidget(self.grid)

        sep_bottom = USep()
        right_lay.addWidget(sep_bottom)

        self.bar_path = PathBar()
        self.path_bar_update("")
        right_lay.addWidget(self.bar_path)
        wid = self.splitter.widget(1)
        QTimer.singleShot(
            100,
            lambda: self.bar_path.setMaximumWidth(wid.width())
        )

        sep_bottom = USep()
        right_lay.addWidget(sep_bottom)

        self.bar_bottom = BarBottom()
        self.bar_bottom.progress_bar.setText(Lng.loading[Cfg.lng])
        self.bar_bottom.resize_thumbnails.connect(lambda: self.grid.resize_thumbnails())
        right_lay.addWidget(self.bar_bottom)

        # Добавляем splitter в основной layout
        h_lay_main.addWidget(self.splitter)

        self.splitter.setStretchFactor(0, 0)
        self.splitter.setStretchFactor(1, 1)
        self.splitter.setSizes([
            self.left_side_width,
            self.width() - self.left_side_width
        ])

        self.grid.setFocus()
        self.on_start(argv)

        self.start_wachdog()

    @staticmethod
    def with_conn(fn):
        def wrapper(self: "WinMain", parent: QWidget, mf: Mf, *args, **kwargs):
            avaiable_mf_path = mf.get_avaiable_mf_path()
            if avaiable_mf_path:
                mf.set_mf_current_path(avaiable_mf_path)
                return fn(self, parent, mf, *args, **kwargs)
            else:
                self.open_win_smb(parent, mf)
        return wrapper
    
    def path_bar_update(self, path: str):
        dir = f"/{Mf.current_mf.mf_alias}{path}"
        self.bar_path.update(dir)
    
    def on_start(self, argv: list[Literal["noscan", ""]], ms = 300):

        def poll_task(tsk: ProcessWorker, tmr: QTimer):
            if not tsk.is_alive():
                tsk.terminate_join()
                if argv[-1] != "noscan":
                    self.start_scaner_task()
            else:
                tmr.start(ms)

        self.grid.reload_thumbnails()

        on_start_item = OnStartItem(Mf.mf_list)
        tsk = ProcessWorker(target=OnStartTask.start, args=(on_start_item, ))
        tmr = QTimer(self)
        tmr.setSingleShot(True)
        tmr.timeout.connect(lambda: poll_task(tsk, tmr))

        tsk.start()
        tmr.start(ms)
    
    def go_to_widget(self, rel_path: str):
        dirname = os.path.dirname(rel_path)
        Dynamic.current_dir = dirname
        self.left_menu.tree_wid.expand_to_path(dirname)
        self.left_menu.setCurrentIndex(1)
        self.grid.go_to_url = rel_path
        self.grid.reload_thumbnails()
    
    def open_filters_win(self):

        def on_closed():
            if not any((
                Dynamic.filters_enabled,
                Dynamic.filter_favs,
                *Dynamic.filters_enabled,
            )):
                self.bar_top.filters_btn.set_normal_style()

        self.bar_top.filters_btn.set_solid_style()
        self.filters_win = WinFilters()
        self.filters_win.closed_.connect(on_closed)
        self.filters_win.reload_thumbnails.connect(
            self.grid.reload_thumbnails
        )
        self.filters_win.center_to_parent(self.window())
        self.filters_win.show()

    def open_win_smb(self, parent: QWidget, mf: Mf):
        try:
            self.noti_wid.deleteLater()
        except (AttributeError, RuntimeError) as e:
            print(e)

        alias = mf.mf_alias
        self.noti_wid = NotifyWid(
            parent,
            f"{alias}: {Lng.no_connection_full[Cfg.lng].lower()}",
            self.warning_svg,
            ms=3000
            )
        self.noti_wid._show()

    @with_conn
    def start_update_thumb(self, parent: QWidget, mf: Mf, rel_thumb_path: str):

        def poll_task():
            q = self.update_thumb_task.proc_q
            if not q.empty():
                img_array = q.get()
                if img_array is not None:
                    wid = self.grid.path_to_wid.get(rel_thumb_path)
                    wid.img = Utils.pixmap_from_array(img_array)
                    wid.setup()
            if not self.update_thumb_task.is_alive():
                print("remove task")
                self.update_thumb_task.terminate_join()
            else:
                QTimer.singleShot(300, poll_task)
                print("repoll task")

        self.update_thumb_task = ProcessWorker(
            target=UpdateThumb.start,
            args=(Mf.current_mf, rel_thumb_path, )
        )
        self.update_thumb_task.start()
        QTimer.singleShot(300, poll_task)

    @with_conn
    def save_files(self, parent: QWidget, mf: Mf, data: tuple):
        target_dir, rel_files_to_copy = data
        abs_files_to_copy = [
            Utils.get_abs_any_path(mf.mf_current_path, i)
            for i in rel_files_to_copy
        ]
        if target_dir is None:
            downloads = os.path.expanduser("~/Downloads")
            target_dir = QFileDialog.getExistingDirectory(directory=downloads)
            if not target_dir:
                target_dir = downloads
        copy_files_win = self.copy_files_win(
            files_to_copy=abs_files_to_copy,
            target_dir=target_dir,
            action_type="copy"
        )
        copy_files_win.finished_.connect(Utils.reveal_files)

    @with_conn
    def set_buffer(self, parent: QWidget, mf: Mf, data: tuple):
        buffer_type, rel_files_to_copy = data
        abs_files_to_copy = [
            Utils.get_abs_any_path(mf.mf_current_path, i)
            for i in rel_files_to_copy
        ]
        self.buffer = Buffer(
            type_=buffer_type,
            source_mf=Mf.current_mf,
            files_to_copy=abs_files_to_copy
        )
        if self.buffer.type_ == "cut":
            for i in self.grid.selected_widgets:
                i.set_transparent_frame(0.5)
        self.grid.buffer = self.buffer

    @with_conn
    def paste_files(self, parent: QWidget, mf: Mf):
        target_dir = Utils.get_abs_any_path(
            mf_path=Mf.current_mf.mf_current_path,
            rel_path=Dynamic.current_dir
        )
        # готовим информацию для сканера
        # сканировать директорию куда вставлены изображения
        self.scaner_data[Mf.current_mf].append(target_dir)
        # сканировать директорию откуда вырезано
        if self.buffer.type_ == "cut":
            dirs_to_scan = list(set(
                os.path.dirname(i)
                for i in self.buffer.files_to_copy
            ))
            if self.buffer.source_mf == Mf.current_mf:
                self.scaner_data[Mf.current_mf].extend(dirs_to_scan)
            else:
                self.scaner_data[self.buffer.source_mf].extend(dirs_to_scan)
        copy_files_win = self.copy_files_win(
            files_to_copy=self.buffer.files_to_copy,
            target_dir=target_dir,
            action_type=self.buffer.type_
        )
        del self.buffer
        del self.grid.buffer
        copy_files_win.finished_.connect(lambda x: self.start_scaner_task())

    @with_conn
    def open_in_app(self, parent: QWidget, mf: Mf, data: tuple):
        rel_paths, app_path = data
        for i in rel_paths:
            abs_path = Utils.get_abs_any_path(mf.mf_current_path, i)
            if app_path:
                subprocess.Popen(["open", "-a", app_path, abs_path])
            else:
                subprocess.Popen(["open", abs_path])

    @with_conn
    def reveal_in_finder(self, parent: QWidget, mf: Mf, rel_paths: list):
        abs_paths = [
            Utils.get_abs_any_path(mf.mf_current_path, i)
            for i in rel_paths
        ]
        if os.path.isdir(abs_paths[0]):
            subprocess.Popen(["open", abs_paths[0]])
        else:
            Utils.reveal_files(abs_paths)

    @with_conn
    def copy_name(self, parent: QWidget, mf: Mf, rel_paths: list[str]):
        names = [
            os.path.splitext(os.path.basename(i))[0]
            for i in rel_paths
        ]
        Utils.copy_text("\n".join(names))

    @with_conn
    def copy_path(self, parent: QWidget, mf: Mf, rel_paths: list[str]):
        abs_paths = [
            Utils.get_abs_any_path(mf.mf_current_path, i)
            for i in rel_paths
        ]
        Utils.copy_text("\n".join(abs_paths))

    @with_conn
    def remove_files(self, parent: QWidget, mf: Mf, rel_paths: list, ms = 300):
        
        def poll_file_remover():
            if not file_remover.proc_q.empty():
                file_remover.proc_q.get()
            if not file_remover.is_alive():
                file_remover.terminate_join()
                self.scaner_data[mf].extend(dirs_to_scan)
                self.start_scaner_task()
            else:
                QTimer.singleShot(ms, poll_file_remover)

        def start_file_remover():
            file_remover.start()
            QTimer.singleShot(ms, poll_file_remover)

        abs_paths = [
            Utils.get_abs_any_path(mf.mf_current_path, i)
            for i in rel_paths
        ]
        dirs_to_scan = list(set(os.path.dirname(i) for i in abs_paths))
        self.remove_files_win = ConfirmWindow(
            f"{Lng.delete_forever[Cfg.lng]} ({len(abs_paths)})?"
        )
        file_remover = ProcessWorker(
                target=FilesRemover.start,
                args=(abs_paths, )
            )
        self.remove_files_win.center_to_parent(self.window())
        self.remove_files_win.ok_clicked.connect(start_file_remover)
        self.remove_files_win.ok_clicked.connect(
            self.remove_files_win.deleteLater
        )
        self.remove_files_win.show()
    
    @with_conn
    def upload_files(self, parent: QWidget, mf: Mf, abs_paths: list[str]):

        def fin(target_dir: str):
            self.upload_win.deleteLater()
            files_to_copy = [
                i
                for i in abs_paths
                if i.endswith(ImgUtils.ext_all)
            ]

            self.buffer = Buffer(
                type_="copy",
                source_mf=Mf.current_mf,
                files_to_copy=files_to_copy
            )

            self.grid.buffer = self.buffer
            self.paste_files(self.grid, Mf.current_mf)

        target_dir = Utils.get_abs_any_path(mf.mf_current_path, Dynamic.current_dir)
        target_files = [
            os.path.join(target_dir, os.path.basename(i))
            for i in abs_paths
            if i.endswith(ImgUtils.ext_all)
        ]
        self.upload_win = UploadWin(target_dir, target_files)
        self.upload_win.ok_clicked.connect(lambda: fin(target_dir))
        self.upload_win.center_to_parent(self)
        self.upload_win.show()

    @with_conn
    def open_info_win(self, parent: QWidget, mf: Mf, rel_paths: list[str]):
        
        abs_paths = [
            Utils.get_abs_any_path(mf.mf_current_path, i)
            for i in rel_paths
        ]
        self.info_win = WinInfo(abs_paths)
        self.info_win.adjustSize()
        self.info_win.center_to_parent(self)
        self.info_win.show()
        # self.info_win.finished_.connect(open_delayed)

    def open_settings_win(self, settings_item: SettingsItem):
        self.bar_top.settings_btn.set_solid_style()
        self.settings_win = WinSettings(settings_item)
        self.settings_win.closed.connect(self.bar_top.settings_btn.set_normal_style)
        self.settings_win.center_to_parent(self.window())
        self.settings_win.show()

    def open_dates_win(self):
        self.dates_win = WinDates()
        self.dates_win.center_to_parent(self)
        self.dates_win.dates_btn_solid.connect(lambda: self.bar_top.dates_btn.set_solid_style())
        self.dates_win.dates_btn_normal.connect(lambda: self.bar_top.dates_btn.set_normal_style())
        self.dates_win.reload_thumbnails.connect(lambda: self.grid.reload_thumbnails())
        self.dates_win.show()

    def open_view_win(self):

        if len(self.grid.selected_widgets) == 1:
            path_to_wid = self.grid.path_to_wid.copy()
            is_selection = False
        else:
            path_to_wid = {i.rel_path: i for i in self.grid.selected_widgets}
            is_selection = True
        wid = self.grid.selected_widgets[-1]
        self.view_win = WinImageView(wid.rel_path, path_to_wid, is_selection)
        self.view_win.open_win_info.connect(
            lambda rel_paths: self.open_info_win(self.view_win, Mf.current_mf, rel_paths)
        )
        self.view_win.copy_path.connect(
            lambda rel_paths: self.copy_path(self.view_win, Mf.current_mf, rel_paths)
        )
        self.view_win.copy_name.connect(
            lambda rel_paths: self.copy_name(self.view_win, Mf.current_mf, rel_paths)
        )
        self.view_win.reveal_in_finder.connect(
            lambda rel_paths: self.reveal_in_finder(self.view_win, Mf.current_mf, rel_paths)
        )
        self.view_win.set_fav.connect(
            self.set_fav
        )
        self.view_win.save_files.connect(
            lambda data: self.save_files(self.view_win, Mf.current_mf, data)
        )
        self.view_win.switch_image_sig.connect(
            lambda path: self.grid.select_viewed_image(path)
        )
        self.view_win.no_connection.connect(
            lambda: self.open_win_smb(self.view_win, Mf.current_mf)
        )
        self.view_win.open_in_app.connect(
            lambda data: self.open_in_app(self.window(), Mf.current_mf, data)
        )

        if WinImageView.xx == 0:
            self.view_win.resize(Static.ww, Static.hh)
            self.view_win.center_to_parent(self.window())
        else:
            self.view_win.resize(WinImageView.ww, WinImageView.hh)
            self.view_win.move(WinImageView.xx, WinImageView.yy)
        self.view_win.show()

    def start_wachdog(self):
        return

        def poll_task():
            q = self.watchdog_task.proc_q
            if not q.empty():
                watchdog_item: WatchDogItem = q.get()
                print(
                    watchdog_item.mf.alias,
                    watchdog_item.event.event_type
                )
            self.watchdog_timer.start(1000)

        if hasattr(self, "watchdog_task"):
            self.watchdog_task.terminate_join()
            
        mf_list: list[Mf] = []
        for mf in Mf.mf_list:
            if mf.get_available_path():
                mf_list.append(mf)
        if mf_list:
            self.watchdog_task = ProcessWorker(
                target=DirWatcher.start,
                args=(mf_list, )
            )
            self.watchdog_timer = QTimer(self)
            self.watchdog_timer.setSingleShot(True)
            self.watchdog_timer.timeout.connect(poll_task)
            self.watchdog_timer.start(1000)
            self.watchdog_task.start()

    def poll_scaner_task(self, ms: int = 3000):
        if not hasattr(self, "scaner_task") or not self.scaner_task:
            self.scaner_poll_timer.start(ms)
            return
        reload_gui_ = False
        while not self.scaner_task.proc_q.empty():
            text, reload_gui = self.scaner_task.proc_q.get()
            if not reload_gui_:
                reload_gui_ = reload_gui
            if self.bar_bottom.progress_bar.text() != text:
                self.bar_bottom.progress_bar.setText(text)
        if not self.scaner_task.is_alive():
            self.scaner_task.terminate_join()
            self.bar_bottom.progress_bar.start_timer_text()
            if reload_gui_:
                self.grid.reload_thumbnails()
                self.left_menu.tree_wid.init_ui()
        else:
            self.scaner_poll_timer.start(ms)

    def start_scaner_task(self, ms: int = 3000):

        if not hasattr(self, "scaner_task"):
            # print("первая инициация сканера")
            self.scaner_task = None

            self.scaner_check_timer = QTimer(self)
            self.scaner_check_timer.setSingleShot(True)
            self.scaner_check_timer.timeout.connect(self.start_scaner_task)

            self.scaner_poll_timer = QTimer(self)
            self.scaner_poll_timer.setSingleShot(True)
            self.scaner_poll_timer.timeout.connect(self.poll_scaner_task)

        can_start = False
        alive = self.scaner_task.is_alive() if self.scaner_task else False

        # задача завершена
        if not alive:
            # print("сканер завершен, можно запускать новый")
            can_start = True

        if can_start:
            if self.scaner_data:
                # print("штатно запускаю SINGLE сканер")
                self.scaner_task = ProcessWorker(
                    target=SingleDirScaner.start,
                    args=(SingleDirScanerItem(self.scaner_data), Cfg.lng, )
                    )
            else:
                # print("штатно запускаю ОБЩИЙ сканер")
                self.scaner_task = ProcessWorker(
                    target=AllDirScaner.start,
                    args=(Mf.mf_list, Cfg.lng, )
                )
                self.scaner_data.clear()
            self.bar_bottom.progress_bar.stop_timer_text()
            self.scaner_task.start()
            self.scaner_poll_timer.stop()
            self.scaner_poll_timer.start(ms)
            self.scaner_check_timer.stop()
            self.scaner_check_timer.start(Cfg.scaner_minutes * 60 * 1000)
        else:
            # проверяем каждую минуту, что задача завершена
            self.scaner_check_timer.stop()
            self.scaner_check_timer.start(1*5000)
            # print("ожидание сканера")

    def restart_scaner_task(self):
        try:
            self.scaner_task.terminate_join()
        except AttributeError as e:
            print("Win main restart scaner task", e)
        self.start_scaner_task()
        
    def center_screen(self):
        screen = QDesktopWidget().screenGeometry()
        size = self.geometry()
        x = (screen.width() - size.width()) // 2
        y = (screen.height() - size.height()) // 2
        self.move(x, y)

    def on_exit(self):
        try:
            if hasattr(self, "scaner_task"):
                self.scaner_task.terminate_join()
            ProcessWorker.stop_all()
        except Exception as e:
            print("on exit main win terminate error", e)
        Cfg.write_json_data()
        Servers.write_json_data()
        Filters.write_json_data()
        Mf.write_json_data()
        os._exit(0)

    def set_fav(self, data: tuple[str, int]):

        def finished(rel_path: str, value: int):
            self.grid.set_thumb_fav(rel_path, value)
            try:
                self.view_win.set_title()
            except AttributeError:
                ...

        rel_path, value = data
        self.task = FavManager(rel_path, value)
        self.task.sigs.finished_.connect(
            lambda: finished(rel_path, value)
        )
        UThreadPool.start(self.task)

    def reset_data_cmd(self, mf: Mf):

        def reset_data_finished():
            self.grid.reload_thumbnails()
            self.left_menu.tree_wid.init_ui()
            self.restart_scaner_task()

        self.grid.reload_thumbnails()
        self.left_menu.tree_wid.init_ui()
        self.reset_task = MfDataCleaner(mf.mf_alias)
        self.reset_task.sigs.finished_.connect(reset_data_finished)
        UThreadPool.start(self.reset_task)

    def copy_files_win(
            self,
            files_to_copy: list[str],
            target_dir: str,
            action_type: Literal["cut", "copy"]
        ):
        progress_win = WinCopyFiles(
            files_to_copy=files_to_copy,
            target_dir=target_dir,
            action_type=action_type
        )
        progress_win.center_to_parent(self)
        progress_win.show()   
        return progress_win
    
    def open_server_win(self):
        self.server_win = ServersWin()
        self.server_win.center_to_parent(self)
        self.server_win.show()

    def closeEvent(self, a0: QCloseEvent | None) -> None:
        self.hide()
        a0.ignore()
    
    def keyPressEvent(self, a0: QKeyEvent | None) -> None:
        
        if a0.key() == Qt.Key.Key_V:
            if hasattr(self, "buffer"):
                self.paste_files(self.grid, Mf.current_mf)
        
        elif a0.key() == Qt.Key.Key_W:
            if a0.modifiers() == Qt.KeyboardModifier.ControlModifier:
                self.hide()

        elif a0.key() == Qt.Key.Key_F:
            if a0.modifiers() == Qt.KeyboardModifier.ControlModifier:
                self.bar_top.search_wid.setFocus()

        elif a0.key() == Qt.Key.Key_K:
            if a0.modifiers() == Qt.KeyboardModifier.ControlModifier:
                self.open_server_win()

        elif a0.key() == Qt.Key.Key_Escape:
            if self.isFullScreen():
                self.showNormal()
                self.raise_()
            else:
                a0.ignore()

        elif a0.key() == Qt.Key.Key_Equal:
            if a0.modifiers() == Qt.KeyboardModifier.ControlModifier:
                if Dynamic.thumb_size_index < len(Static.pixmap_sizes) - 1:
                    Dynamic.thumb_size_index += 1
                    self.bar_bottom.slider._on_value_changed(Dynamic.thumb_size_index)

        elif a0.key() == Qt.Key.Key_Minus:
            if a0.modifiers() == Qt.KeyboardModifier.ControlModifier:
                if Dynamic.thumb_size_index > 0:
                    Dynamic.thumb_size_index -= 1
                    self.bar_bottom.slider._on_value_changed(Dynamic.thumb_size_index)


    def dragEnterEvent(self, a0):
        a0.acceptProposedAction()
        return super().dragEnterEvent(a0)
    
    def dropEvent(self, a0):

        if not a0.mimeData().hasUrls() or a0.source() is not None:
            return
        
        elif Dynamic.search_widget_text:
            try:
                self.noti_wid.deleteLater()
            except (AttributeError, RuntimeError) as e:
                print(e)
            self.noti_wid = NotifyWid(
                self.grid,
                Lng.drop_event_denied_msg[Cfg.lng],
                self.warning_svg,
                ms=3000
                )
            self.noti_wid._show()
            return

        paths: list[str] = [
            i.toLocalFile().rstrip(os.sep)
            for i in a0.mimeData().urls()
        ]

        if paths:
            self.upload_files(self.grid, Mf.current_mf, paths)
        return super().dropEvent(a0)
    
    def resizeEvent(self, a0):
        wid = self.splitter.widget(1)
        self.bar_path.setMaximumWidth(wid.width())
        return super().resizeEvent(a0)