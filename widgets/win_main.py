import os
import subprocess
from collections import defaultdict

from PyQt6.QtCore import Qt, QTimer
from PyQt6.QtGui import QCloseEvent, QGuiApplication, QIcon, QKeyEvent, QPixmap
from PyQt6.QtWidgets import (QFileDialog, QFrame, QHBoxLayout, QLabel,
                             QPushButton, QSplitter, QVBoxLayout, QWidget)
from typing_extensions import Literal

from cfg import Cfg, Dynamic, Static
from system.filters import Filters
from system.items import (ForcedScanerItem, ImgViewItem, SettingsItem,
                          UpdateThumbItem, WatchDogItem)
from system.lang import Lng
from system.main_folder import Mf
from system.multiprocess import (FilesRemover, ProcessWorker, UpdateThumb,
                                 WatchDog)
from system.scaner import BaseScaner, ForcedScaner
from system.shared_utils import ImgUtils
from system.tasks import SetFav, UThreadPool, Utils

from ._base_widgets import HSep, UMainWindow
from .bar_bottom import BarBottom
from .bar_macos import BarMacos
from .bar_path import PathBar
from .bar_top import BarTop
from .grid import Grid, GridStandart
from .menu_left import MenuLeft
from .win_copy_files import WinCopyFiles
from .win_dates import WinDates
from .win_filters import WinFilters
from .win_image_view import WinImageView
from .win_img_search import WinImgSearch
from .win_info import WinInfo
from .win_servers import ServersWin
from .win_settings import WinSettings
from .win_smb import WinSmb
from .win_upload import UploadWin
from .win_warn import ConfirmWindow, WarningWindow


class TestWid(QFrame):
    def __init__(self, parent=None):
        super().__init__(parent=parent)
        self.setFixedSize(100, 100)
        self.setStyleSheet("background: black;")

        v_layout = QVBoxLayout(self)

        btn = QPushButton('test btn')
        v_layout.addWidget(btn)
        btn.clicked.connect(self.reload)

    def reload(self):
        ...


class WinMain(UMainWindow):
    min_w = 750
    left_side_width = 250
    ww, hh = 1120, 760

    def __init__(self, argv: list):
        super().__init__()
        self.central_layout.setContentsMargins(0, 0, 0, 0)
        self.resize(self.ww, self.hh)
        self.setMinimumWidth(self.min_w)
        self.setWindowTitle(f"{Static.app_name}")
        self.setMenuBar(BarMacos())

        self.forced_scaner_dirs = set()
        self.go_to_url: str | None = None
        self.files_to_copy = set()

        h_wid_main = QWidget()
        h_lay_main = QHBoxLayout(h_wid_main)
        h_lay_main.setContentsMargins(5, 0, 5, 5)
        h_lay_main.setSpacing(0)
        self.central_layout.addWidget(h_wid_main)

        # Создаем QSplitter
        self.splitter = QSplitter(Qt.Orientation.Horizontal)
        self.splitter.setHandleWidth(14)

        # Левый виджет (MenuLeft)
        self.left_menu = MenuLeft()
        self.left_menu.mf_edit.connect(
            lambda settings_item: self.open_settings_win(settings_item)
        )
        self.left_menu.mf_new.connect(
            lambda settings_item: self.open_settings_win(settings_item)
        )
        self.left_menu.reveal.connect(
            lambda rel_paths: self.reveal_in_finder(rel_paths)
        )
        self.left_menu.on_tree_clicked.connect(
            lambda abs_path: self.on_tree_clicked(abs_path)
        )
        self.left_menu.on_mf_clicked.connect(
            lambda mf: self.on_mf_clicked(mf)
        )
        self.left_menu.on_hide_digits_clicked.connect(
            lambda: self.on_hide_digits_clicked()
        )
        self.left_menu.copy_path.connect(
            lambda rel_paths: self.copy_path(rel_paths)
        )
        self.splitter.addWidget(self.left_menu)

        # Правый виджет
        right_wid = QWidget()
        self.splitter.addWidget(right_wid)
        self.right_layout = QVBoxLayout(right_wid)
        self.right_layout.setContentsMargins(0, 0, 0, 0)
        self.right_layout.setSpacing(0)

        # Добавляем элементы в правую панель
        self.bar_top = BarTop()
        self.bar_top.open_dates_win.connect(
            lambda: self.open_dates_win()
        )
        self.bar_top.reload_thumbnails.connect(
            lambda: self.load_st_grid()
            )
        self.bar_top.open_settings_win.connect(
            lambda settings_item: self.open_settings_win(settings_item)
        )
        self.bar_top.open_filters_win.connect(
            lambda: self.open_filters_win()
        )
        self.bar_top.open_img_search.connect(
            lambda: self.img_search_start()
        )
        self.bar_top.exit_img_search.connect(
            lambda: self.img_search_exit()
        )
        self.bar_top.open_base_search.connect(
            lambda: self.base_search_start()
        )
        self.right_layout.addWidget(self.bar_top)

        # self.right_layout.addSpacerItem(QSpacerItem(0, 5))

        sep_upper = HSep()
        self.right_layout.addWidget(sep_upper)

        self.grid = Grid()
        self.load_st_grid()

        sep_bottom = HSep()
        self.right_layout.addWidget(sep_bottom)

        self.bar_path = PathBar()
        self.path_bar_update("")
        self.right_layout.addWidget(self.bar_path)
        wid = self.splitter.widget(1)
        QTimer.singleShot(
            100,
            lambda: self.bar_path.setMaximumWidth(wid.width())
        )

        sep_bottom = HSep()
        self.right_layout.addWidget(sep_bottom)

        self.bar_bottom = BarBottom()
        self.bar_bottom.progress_bar.setText(Lng.loading[Cfg.lng_index])
        self.bar_bottom.resize_thumbnails.connect(
            lambda: self.grid.resize_thumbnails()
        )
        self.right_layout.addWidget(self.bar_bottom)

        # Добавляем splitter в основной layout
        h_lay_main.addWidget(self.splitter)

        self.splitter.setStretchFactor(0, 0)
        self.splitter.setStretchFactor(1, 1)
        self.splitter.setSizes([
            self.left_side_width,
            self.width() - self.left_side_width
        ])

        self.load_st_grid()

        if "noscan" not in argv:
            self.start_scaner_task()
        else:
            print("СКАНЕР ВЫКЛЮЧЕН")

    @staticmethod
    def with_conn(fn: callable):
        def wrapper(self: "WinMain", *args):
            avaiable_mf_path = Mf.current_mf.get_avaiable_mf_path()
            if avaiable_mf_path:
                Mf.current_mf.set_mf_current_path(avaiable_mf_path)
                return fn(self, *args)
            else:
                self.open_win_smb(Mf.current_mf)
        return wrapper

    def set_no_filters(self):
        Dynamic.filters_enabled.clear()
        Dynamic.filter_favs = False
        Dynamic.filter_only_folder = False
        self.bar_top.filters_btn.set_normal_style()

        Dynamic.date_start = None
        Dynamic.date_end = None
        self.bar_top.dates_btn.set_normal_style()

        Dynamic.search_widget_text = None
        Dynamic.thumb_path_set.clear()
        self.bar_top.search_wid.clear()
        self.bar_top.show_base_search()

    def base_search_start(self):
        Dynamic.filters_enabled.clear()
        Dynamic.filter_favs = False
        Dynamic.filter_only_folder = False
        self.bar_top.filters_btn.set_normal_style()

        Dynamic.date_start = None
        Dynamic.date_end = None
        self.bar_top.dates_btn.set_normal_style()

        Dynamic.thumb_path_set.clear()

        Dynamic.current_dir = os.sep
        self.left_menu.tree_wid.expand_to_path(os.sep)

        self.load_st_grid()

    def img_search_start(self):

        def search_started():
            Dynamic.current_dir = os.sep
            self.left_menu.tree_wid.expand_to_path(os.sep)
            self.set_no_filters()
            self.bar_top.show_img_search()

        self.win_img_search = WinImgSearch()
        self.win_img_search.found_image.connect(self.load_st_grid)
        self.win_img_search.search_started.connect(search_started)
        self.win_img_search.center_to_parent(self)
        self.win_img_search.show()

    def img_search_exit(self):
        self.set_no_filters()
        self.load_st_grid()
    
    def show_in_app(self, rel_path: str):

        Dynamic.filters_enabled.clear()
        Dynamic.filter_favs = False
        Dynamic.filter_only_folder = False
        self.bar_top.filters_btn.set_normal_style()

        Dynamic.date_start = None
        Dynamic.date_end = None
        self.bar_top.dates_btn.set_normal_style()

        Dynamic.thumb_path_set.clear()
        Dynamic.search_widget_text = None
        self.bar_top.search_wid.clear()
        self.bar_top.show_base_search()

        current_dir = os.path.dirname(rel_path)
        Dynamic.current_dir = current_dir
        self.go_to_url = rel_path
        self.load_st_grid()
        self.left_menu.tree_wid.expand_to_path(current_dir)
    
    def path_bar_update(self, path: str):
        dir = f"/{Mf.current_mf.mf_alias}{path}"
        self.bar_path.update(dir)

    def on_hide_digits_clicked(self):
        self.win_warn = WarningWindow(Lng.hide_digits_full[Cfg.lng_index])
        self.win_warn.center_to_parent(self)
        self.win_warn.show()
        
    def open_filters_win(self):

        def on_closed():
            if not any((
                Dynamic.filter_only_folder,
                Dynamic.filter_favs,
                *Dynamic.filters_enabled,
            )):
                self.bar_top.filters_btn.set_normal_style()

        self.bar_top.filters_btn.set_solid_style()
        self.filters_win = WinFilters()
        self.filters_win.closed_.connect(
            on_closed
        )
        self.filters_win.reload_thumbnails.connect(
            self.load_st_grid
        )
        self.filters_win.center_to_parent(self.window())
        self.filters_win.show()

    def open_win_smb(self, mf: Mf):
        self.win_smb = WinSmb(mf)
        self.win_smb.center_to_parent(self.win_list[-2])
        self.win_smb.show()

    def on_mf_clicked(self, mf: Mf):
        self.set_no_filters()
        Mf.current_mf = mf
        Dynamic.current_dir = os.sep
        self.path_bar_update(Dynamic.current_dir)
        self.left_menu.tree_wid.abs_selected_path = os.sep
        self.left_menu.tree_wid.init_ui()
        self.load_st_grid()

        mf_path = mf.get_avaiable_mf_path()
        if not mf_path:
            self.open_win_smb(mf)
 
    @with_conn
    def on_tree_clicked(self, abs_path: str):
        rel_path = Utils.get_rel_any_path(
            mf_path=Mf.current_mf.mf_current_path,
            abs_img_path=abs_path
        )
        Dynamic.current_dir = rel_path
        self.set_no_filters()
        self.load_st_grid()
        self.path_bar_update(Dynamic.current_dir)

    @with_conn
    def start_update_thumb(self, rel_paths: list[str]):

        def poll_task():
            queue = self.update_thumb_task.process_queue
            if not queue.empty():
                update_thumb_items: list[UpdateThumbItem] = queue.get()
                for i in update_thumb_items:
                    wid = self.grid.url_to_wid.get(i.rel_img_path)
                    if wid:
                        wid.data_item.pixmap = Utils.pixmap_from_array(i.array)
                        wid.setup()
            if not self.update_thumb_task.is_alive():
                self.update_thumb_task.terminate_join()
            else:
                QTimer.singleShot(300, poll_task)

        self.update_thumb_task = ProcessWorker(
            target=UpdateThumb.start,
            args=(Mf.current_mf, rel_paths, )
        )
        self.update_thumb_task.start()
        QTimer.singleShot(300, poll_task)

    @with_conn
    def save_to_downloads(self, rel_paths: list[str]):
        downloads = os.path.expanduser("~/Downloads")
        abs_paths = [
            Utils.get_abs_any_path(Mf.current_mf.mf_current_path, i)
            for i in rel_paths
        ]
        copy_files_win = self.copy_files_win(
            files_to_copy=abs_paths,
            dest=downloads
        )
        copy_files_win.finished_.connect(
            Utils.reveal_files
        )

    @with_conn
    def set_files_to_copy(self, rel_paths: tuple):
        abs_files_to_copy = set(
            Utils.get_abs_any_path(Mf.current_mf.mf_current_path, i)
            for i in rel_paths
        )

        self.files_to_copy = abs_files_to_copy
        self.grid.files_to_copy = abs_files_to_copy

    @with_conn
    def paste_files(self, files_to_copy: list[str], dest: str):
        """
        files_to_copy, dest
        """
        copy_files_win = self.copy_files_win(
            files_to_copy=files_to_copy,
            dest=dest
        )
        copy_files_win.finished_.connect(lambda x: self.start_scaner_task())
        self.forced_scaner_dirs.add(dest)
        self.files_to_copy.clear()
        self.grid.files_to_copy.clear()

    @with_conn
    def open_in_app(self, rel_paths: list[str], app_path: str):
        for i in rel_paths:
            abs_path = Utils.get_abs_any_path(Mf.current_mf.mf_current_path, i)
            if app_path:
                subprocess.Popen(["open", "-a", app_path, abs_path])
            else:
                subprocess.Popen(["open", abs_path])

    @with_conn
    def reveal_in_finder(self, rel_paths: list):
        abs_paths = [
            Utils.get_abs_any_path(Mf.current_mf.mf_current_path, i)
            for i in rel_paths
        ]
        if os.path.isdir(abs_paths[0]):
            subprocess.Popen(["open", abs_paths[0]])
        else:
            Utils.reveal_files(abs_paths)

    @with_conn
    def copy_path(self, rel_paths: list[str]):
        abs_paths = [
            Utils.get_abs_any_path(Mf.current_mf.mf_current_path, i)
            for i in rel_paths
        ]
        Utils.copy_text("\n".join(abs_paths))

    @with_conn
    def remove_files(self, rel_paths: list, ms = 300):
        
        def poll_file_remover():
            if not file_remover.process_queue.empty():
                file_remover.process_queue.get()
            if not file_remover.is_alive():
                file_remover.terminate_join()
                for i in dirs_to_scan:
                    self.forced_scaner_dirs.add(i)

                self.start_scaner_task()
            else:
                QTimer.singleShot(ms, poll_file_remover)

        def start_file_remover():
            file_remover.start()
            QTimer.singleShot(ms, poll_file_remover)

        abs_paths = [
            Utils.get_abs_any_path(Mf.current_mf.mf_current_path, i)
            for i in rel_paths
        ]
        dirs_to_scan = list(set(os.path.dirname(i) for i in abs_paths))
        if len(abs_paths) == 1:
            text = f"{Lng.remove_file_question[Cfg.lng_index]}?"
        else:
            text = f"{Lng.remove_files_question[Cfg.lng_index]}?"
        self.remove_files_win = ConfirmWindow(text)
        file_remover = ProcessWorker(
                target=FilesRemover.start,
                args=(abs_paths, )
            )
        self.remove_files_win.center_to_parent(self.window())
        self.remove_files_win.ok_clicked.connect(
            start_file_remover
        )
        self.remove_files_win.ok_clicked.connect(
            self.remove_files_win.deleteLater
        )
        self.remove_files_win.show()
    
    @with_conn
    def upload_files(self, dropped_files: list[str]):

        def fin(dest: str):
            self.upload_win.deleteLater()
            self.paste_files(dropped_files, dest)


        dropped_files = [
            i
            for i in dropped_files
            if i.endswith(ImgUtils.ext_all)
        ]
        self.upload_win = UploadWin(
            mf=Mf.current_mf,
            current_dir=Dynamic.current_dir,
            files_to_copy=dropped_files
        )
        self.upload_win.ok_clicked.connect(
            lambda dest: fin(dest)
        )
        self.upload_win.center_to_parent(self)
        self.upload_win.show()

    @with_conn
    def open_info_win(self, rel_paths: list[str]):
        
        abs_paths = [
            Utils.get_abs_any_path(Mf.current_mf.mf_current_path, i)
            for i in rel_paths
        ]
        self.info_win = WinInfo(abs_paths)
        self.info_win.adjustSize()
        self.info_win.center_to_parent(UMainWindow.win_list[-2])
        self.info_win.show()

    def open_settings_win(self, settings_item: SettingsItem):
        self.bar_top.settings_btn.set_solid_style()
        self.settings_win = WinSettings(settings_item)
        self.settings_win.closed.connect(
            self.bar_top.settings_btn.set_normal_style
        )
        self.settings_win.center_to_parent(self.window())
        self.settings_win.show()

    def open_dates_win(self):
        self.dates_win = WinDates()
        self.dates_win.dates_btn_solid.connect(
            lambda: self.bar_top.dates_btn.set_solid_style()
        )
        self.dates_win.dates_btn_normal.connect(
            lambda: self.bar_top.dates_btn.set_normal_style()
        )
        self.dates_win.reload_thumbnails.connect(
            lambda: self.load_st_grid()
        )
        self.dates_win.center_to_parent(self)
        self.dates_win.show()

    def load_st_grid(self, layout_index: int = 3):

        def finished():
            self.grid.setFocus()
            if self.go_to_url:
                widget = self.grid.url_to_wid.get(self.go_to_url)
                if not widget:
                    return
                self.grid.select_by_url(self.go_to_url)
                QTimer.singleShot(
                    100,
                    lambda: self.grid.ensureWidgetVisible(widget)
                )
                self.go_to_url = str()

        Dynamic.loaded_thumbs = 0
        self.grid.deleteLater()
        self.grid = GridStandart()
        self.grid.files_to_copy = self.files_to_copy
        self.grid.restart_scaner.connect(
            lambda: self.restart_scaner_task()
        )
        self.grid.remove_files.connect(
            lambda rel_paths: self.remove_files(rel_paths)
        )
        self.grid.open_img_view.connect(
            lambda: self.open_view_win(Mf.current_mf)
        )
        self.grid.save_files.connect(
            lambda rel_paths: self.save_to_downloads(rel_paths)
        )
        self.grid.open_info_win.connect(
            lambda rel_paths: self.open_info_win(rel_paths)
        )
        self.grid.copy_path.connect(
            lambda rel_paths: self.copy_path(rel_paths)
        )
        self.grid.reveal_in_finder.connect(
            lambda rel_paths: self.reveal_in_finder(rel_paths)
        )
        self.grid.set_fav.connect(
            lambda data: self.set_fav(data)
        )
        self.grid.open_in_app.connect(
            lambda data: self.open_in_app(*data)
        )
        # контекстное меню, берешь files_to_copy из буффера
        self.grid.paste_files.connect(
            lambda: self.paste_files(
                self.files_to_copy,
                os.path.join(Mf.current_mf.mf_current_path, Dynamic.current_dir.strip(os.sep))
                )
        )
        self.grid.set_files_to_copy.connect(
            lambda rel_paths: self.set_files_to_copy(rel_paths)
        )
        self.grid.setup_mf.connect(
            lambda item: self.open_settings_win(item)
        )
        self.grid.path_bar_update.connect(
            lambda rel_path: self.path_bar_update(rel_path)
        )
        self.grid.update_thumb.connect(
            lambda rel_paths: self.start_update_thumb(rel_paths)
        )
        self.grid.show_in_app.connect(
            self.show_in_app
        )
        self.grid.finished_.connect(
            finished
        )
        self.grid.load_st_grid.connect(
            self.load_st_grid
        )
        self.grid.upload_files.connect(
            lambda abs_paths: self.upload_files(abs_paths)
        )
        # -1 для pyqt6
        self.right_layout.insertWidget(layout_index-1, self.grid)

    @with_conn
    def open_view_win(self, mf: Mf):
        if len(self.grid.selected_widgets) == 1:
            data_items = [i.data_item for i in self.grid.url_to_wid.values()]
            is_selection = False
        else:
            data_items = [i.data_item for i in self.grid.selected_widgets]
            is_selection = True
        start_data_item = self.grid.selected_widgets[0].data_item

        item = ImgViewItem(
            start_data_item=start_data_item,
            data_items=data_items,
            is_selection=is_selection
        )
        self.view_win = WinImageView(item)
        self.view_win.open_win_info.connect(
            lambda rel_paths: self.open_info_win(rel_paths)
        )
        self.view_win.copy_path.connect(
            lambda rel_paths: self.copy_path(rel_paths)
        )
        self.view_win.reveal_in_finder.connect(
            lambda rel_paths: self.reveal_in_finder(Mf.current_mf, rel_paths)
        )
        self.view_win.set_fav.connect(
            self.set_fav
        )
        self.view_win.save_files.connect(
            lambda rel_paths: self.save_to_downloads(rel_paths)
        )
        self.view_win.select_thumb.connect(
            lambda path: self.grid.select_by_url(path)
        )
        self.view_win.open_in_app.connect(
            lambda data: self.open_in_app(*data)
        )
        self.view_win.image_not_exists.connect(
            lambda: self.open_win_smb(Mf.current_mf)
        )
        if WinImageView.xx == 0:
            self.view_win.resize(self.ww, self.hh)
            self.view_win.center_to_parent(self.window())
        else:
            self.view_win.resize(WinImageView.ww, WinImageView.hh)
            self.view_win.move(WinImageView.xx, WinImageView.yy)
        self.view_win.show()

    def poll_scaner_task(self, ms: int = 3000):
        if not hasattr(self, "scaner_task") or not self.scaner_task:
            self.scaner_poll_timer.start(ms)
            return
        while not self.scaner_task.process_queue.empty():
            text = self.scaner_task.process_queue.get()
            if self.bar_bottom.progress_bar.text() != text:
                self.bar_bottom.progress_bar.setText(text)
        if not self.scaner_task.is_alive():
            self.scaner_task.terminate_join()
            self.bar_bottom.progress_bar.setText("")
            self.bar_bottom.progress_bar.start_timer_text()
            new_db_time = int(os.stat(Static.external_db).st_mtime)
            if self.db_mtime != new_db_time:
                self.load_st_grid()
                self.left_menu.tree_wid.init_ui()
        else:
            self.scaner_poll_timer.start(ms)

    def start_scaner_task(self, ms: int = 3000):

        if not hasattr(self, "scaner_task"):
            # print("первая инициация сканера")
            self.scaner_task = None
            self.db_mtime = 0

            self.scaner_check_timer = QTimer(self)
            self.scaner_check_timer.setSingleShot(True)
            self.scaner_check_timer.timeout.connect(
                self.start_scaner_task
            )

            self.scaner_poll_timer = QTimer(self)
            self.scaner_poll_timer.setSingleShot(True)
            self.scaner_poll_timer.timeout.connect(
                self.poll_scaner_task
            )

        can_start = False
        alive = self.scaner_task.is_alive() if self.scaner_task else False

        # задача завершена
        if not alive:
            can_start = True

        if can_start:
            if self.forced_scaner_dirs:
                forced_scaner_item = ForcedScanerItem(
                    mf=Mf.current_mf,
                    dirs_to_scan=self.forced_scaner_dirs.copy(),
                    lng_index=Cfg.lng_index
                )
                self.scaner_task = ProcessWorker(
                    target=ForcedScaner.start,
                    args=(forced_scaner_item, )
                    )
            else:
                # print("штатно запускаю ОБЩИЙ сканер")
                self.scaner_task = ProcessWorker(
                    target=BaseScaner.start,
                    args=(Mf.items, Cfg.lng_index, )
                )
            self.forced_scaner_dirs.clear()
            self.db_mtime = int(os.stat(Static.external_db).st_mtime)
            self.bar_bottom.progress_bar.stop_timer_text()
            self.scaner_task.start()
            self.scaner_poll_timer.stop()
            self.scaner_poll_timer.start(ms)
            self.scaner_check_timer.stop()
            self.scaner_check_timer.start(Cfg.scaner_minutes * 60 * 1000)
        else:
            # проверяем каждую минуту, что задача завершена
            self.scaner_check_timer.stop()
            self.scaner_check_timer.start(5000)

    def restart_scaner_task(self):
        try:
            self.scaner_task.terminate_join()
        except AttributeError as e:
            print("Win main restart scaner task", e)
        self.start_scaner_task()
        
    def center_screen(self):
        # Получаем геометрию первичного (главного) экрана
        screen = QGuiApplication.primaryScreen().geometry()
        # Получаем геометрию текущего окна
        size = self.geometry()
        
        # Вычисляем координаты центра
        x = (screen.width() - size.width()) // 2
        y = (screen.height() - size.height()) // 2
        
        # Перемещаем окно
        self.move(x, y)

    def on_exit(self):
        try:
            if hasattr(self, "scaner_task"):
                self.scaner_task.terminate_join()
            ProcessWorker.stop_all()
        except Exception as e:
            print("on exit main win terminate error", e)
        Cfg.write_json_data()
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
        self.task = SetFav(rel_path, value)
        self.task.sigs.finished_.connect(
            lambda: finished(rel_path, value)
        )
        UThreadPool.start(self.task)

    def copy_files_win(self, files_to_copy: list[str], dest: str):
        progress_win = WinCopyFiles(
            files_to_copy=files_to_copy,
            target_dir=dest
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
            dest = os.path.join(
                Mf.current_mf.mf_current_path,
                Dynamic.current_dir.strip(os.sep)
            )
            self.paste_files(self.files_to_copy, dest)
        
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
    
    def resizeEvent(self, a0):
        wid = self.splitter.widget(1)
        self.bar_path.setMaximumWidth(wid.width())
        return super().resizeEvent(a0)
    

# class WinMain(UMainWindow):
#     def __init__(self, *args):
#         super().__init__()

#         self.grid = GridStandart()
#         self.central_layout.addWidget(self.grid)

#     def center_screen(self):
#         screen = QDesktopWidget().screenGeometry()
#         size = self.geometry()
#         x = (screen.width() - size.width()) // 2
#         y = (screen.height() - size.height()) // 2
#         self.move(x, y)
