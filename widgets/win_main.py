import os
import subprocess
from time import time

from PyQt5.QtCore import Qt, QTimer
from PyQt5.QtGui import QCloseEvent, QIcon, QKeyEvent
from PyQt5.QtWidgets import (QDesktopWidget, QFileDialog, QFrame, QLabel,
                             QPushButton, QSplitter, QVBoxLayout, QWidget)
from typing_extensions import Literal, Optional

from cfg import Dynamic, Static, cfg
from system.filters import Filters
from system.items import (Buffer, ExtScanerItem, OnStartItem, SettingsItem,
                          SingleDirScanerItem)
from system.lang import Lng
from system.main_folder import Mf
from system.multiprocess import FilesRemover, OnStartTask, ProcessWorker
from system.scaner import AllDirScaner, SingleDirScaner
from system.shared_utils import ImgUtils
from system.tasks import FavManager, MfDataCleaner, UThreadPool, Utils

from ._base_widgets import NotifyWid, UHBoxLayout, UMainWindow, UVBoxLayout
from .bar_bottom import BarBottom
from .bar_macos import BarMacos
from .bar_path import PathBar
from .bar_top import BarTop
from .grid import Grid
from .menu_left import MenuLeft
from .servers_win import ServersWin
from .win_copy_files import WinCopyFiles
from .win_dates import WinDates
from .win_image_view import WinImageView
from .win_info import WinInfo
from .win_settings import WinSettings
from .win_upload import UploadWin
from .win_warn import WinQuestion, WinWarn


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
    scaner_timeout_max = 5 * 60
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

        self.view_win: WinImageView
        self.buffer: Buffer = None

        h_wid_main = QWidget()
        h_lay_main = UHBoxLayout()
        h_lay_main.setContentsMargins(5, 0, 5, 5)
        h_wid_main.setLayout(h_lay_main)
        self.central_layout.addWidget(h_wid_main)

        # Создаем QSplitter
        self.splitter = QSplitter(Qt.Horizontal)
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
        self.bar_top.history_press.connect(
            lambda: self.history_press()
        )
        self.bar_top.level_up.connect(
            lambda: self.level_up()
        )
        right_lay.addWidget(self.bar_top)

        sep_upper = USep()
        right_lay.addWidget(sep_upper)

        self.grid = Grid()
        self.grid.restart_scaner.connect(
            lambda: self.restart_scaner_task()
        )
        self.grid.remove_files.connect(
            lambda rel_paths: self.remove_files(self, Mf.current, rel_paths, ))
        self.grid.no_connection.connect(
            lambda: self.open_win_smb(self.grid, Mf.current)
        )
        self.grid.open_img_view.connect(
            lambda: self.open_view_win()
        )
        self.grid.save_files.connect(
            lambda data: self.save_files(self.grid, Mf.current, data)
        )
        self.grid.open_info_win.connect(
            lambda rel_paths: self.open_info_win(self.grid, Mf.current, rel_paths)
        )
        self.grid.copy_path.connect(
            lambda rel_paths: self.copy_path(self.grid, Mf.current, rel_paths)
        )
        self.grid.copy_name.connect(
            lambda rel_paths: self.copy_name(self.grid, Mf.current, rel_paths)
        )
        self.grid.reveal_in_finder.connect(
            lambda rel_paths: self.reveal_in_finder(self.grid, Mf.current, rel_paths)
        )
        self.grid.set_fav.connect(
            self.set_fav
        )
        self.grid.open_in_app.connect(
            lambda data: self.open_in_app(self.grid, Mf.current, data))
        self.grid.paste_files.connect(
            lambda: self.paste_files(self.grid,  Mf.current)
        )
        self.grid.copy_files.connect(
            lambda data: self.set_clipboard(self.grid, Mf.current, data)
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
        self.bar_bottom.progress_bar.setText(Lng.loading[cfg.lng])
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

    @staticmethod
    def with_conn(fn):
        def wrapper(self: "WinMain", parent: QWidget, mf: Mf, *args, **kwargs):
            if mf.get_available_path():
                return fn(self, parent, mf, *args, **kwargs)
            else:
                self.open_win_smb(parent, mf)
        return wrapper
    
    def path_bar_update(self, path: str):
        dir = f"/{Mf.current.alias}{path}"
        self.bar_path.update(dir)
    
    def on_start(self, argv: list[Literal["noscan", ""]], ms = 300):

        def poll_task(tsk: ProcessWorker, tmr: QTimer):
            if not tsk.is_alive():
                tsk.terminate_join()
                if argv[-1] != "noscan":
                    self.start_scaner_task(scaner_item=None)
            else:
                tmr.start(ms)

        self.grid.reload_thumbnails()

        on_start_item = OnStartItem(Mf.list_)
        tsk = ProcessWorker(target=OnStartTask.start, args=(on_start_item, ))
        tmr = QTimer(self)
        tmr.setSingleShot(True)
        tmr.timeout.connect(lambda: poll_task(tsk, tmr))

        tsk.start()
        tmr.start(ms)
    
    def level_up(self):
        if Dynamic.current_dir:
            root = os.path.dirname(Dynamic.current_dir)
            if root == os.sep:
                root = ""
            Dynamic.current_dir = root
            self.left_menu.tree_wid.expand_to_path(root)
            self.left_menu.setCurrentIndex(1)
            self.grid.reload_thumbnails()

    def history_press(self):
        self.left_menu.tree_wid.expand_to_path(Dynamic.current_dir)
        self.left_menu.setCurrentIndex(1)
        self.grid.reload_thumbnails()
    
    def go_to_widget(self, rel_path: str):
        dirname = os.path.dirname(rel_path)
        Dynamic.current_dir = dirname
        self.left_menu.tree_wid.expand_to_path(dirname)
        self.left_menu.setCurrentIndex(1)
        self.grid.go_to_url = rel_path
        self.grid.reload_thumbnails()

    def open_win_smb(self, parent: QWidget, mf: Mf):
        try:
            self.noti_wid.deleteLater()
        except (AttributeError, RuntimeError) as e:
            print(e)

        basename = os.path.basename(mf.current.paths[0])
        alias = mf.alias
        self.noti_wid = NotifyWid(
            parent,
            f"{basename} ({alias}): {Lng.no_connection_full[cfg.lng].lower()}",
            self.warning_svg,
            ms=3000
            )
        self.noti_wid._show()

    @with_conn
    def save_files(self, parent: QWidget, mf: Mf, data: tuple):

        def save_finished(files):
            Utils.reveal_files(files)
            self.buffer = None

        dest, dst_rel_paths = data
        src_abs_paths = [
            Utils.get_abs_any_path(mf.curr_path, i)
            for i in dst_rel_paths
        ]

        if self.buffer is None:
            self.buffer = Buffer(
                type_="copy",
                dirs_to_scan=None,
                files_to_copy=src_abs_paths,
                dst_dir=None,
                mf_to_scan=None
            )
            self.grid.buffer = self.buffer
        else:
            self.buffer.files_to_copy = src_abs_paths

        if dest is None:
            dest = QFileDialog.getExistingDirectory(
                directory=os.path.expanduser("~/Downloads")
            )
            if dest:
                self.buffer.dst_dir = dest
                copy_files_win = self.copy_files_win()
                copy_files_win.finished_.connect(save_finished)
        else:
            self.buffer.dst_dir = dest
            copy_files_win = self.copy_files_win()
            copy_files_win.finished_.connect(Utils.reveal_files)

    @with_conn
    def set_clipboard(self, parent: QWidget, mf: Mf, data: tuple):
        action_type, rel_paths = data
        if rel_paths:
            abs_paths = [
                Utils.get_abs_any_path(mf.curr_path, i)
                for i in rel_paths
            ]
            src_dirs = list(set(os.path.dirname(i) for i in abs_paths))
            self.buffer = Buffer(
                type_=action_type,
                dirs_to_scan=src_dirs,
                files_to_copy=abs_paths,
                dst_dir=None,
                mf_to_scan=None
            )

            self.grid.buffer = self.buffer
            if self.buffer.type_ == "cut":
                for i in self.grid.selected_widgets:
                    i.set_transparent_frame(0.5)

    @with_conn
    def open_in_app(self, parent: QWidget, mf: Mf, data: tuple):
        rel_paths, app_path = data
        for i in rel_paths:
            abs_path = Utils.get_abs_any_path(mf.curr_path, i)
            if app_path:
                subprocess.Popen(["open", "-a", app_path, abs_path])
            else:
                subprocess.Popen(["open", abs_path])

    @with_conn
    def reveal_in_finder(self, parent: QWidget, mf: Mf, rel_paths: list):
        abs_paths = [
            Utils.get_abs_any_path(mf.curr_path, i)
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
            Utils.get_abs_any_path(mf.curr_path, i)
            for i in rel_paths
        ]
        Utils.copy_text("\n".join(abs_paths))

    @with_conn
    def paste_files(self, parent: QWidget, mf: Mf):

        def scan_dirs(files: list[str]):
            if not files:
                return

            self.buffer.mf_to_scan = Mf.current
            self.buffer.dst_dir = abs_current_dir
            scaner_data = {
                self.buffer.mf_to_scan: [self.buffer.dst_dir, ], 
            }
            if self.buffer.type_ == "cut":
                # если Mf откуда вырезаны файлы и Mf куда вставлены файла
                # это разные объекты, то нужно просканировать оба объекта
                if self.buffer.mf_to_scan != Mf.current:
                    scaner_data.update(
                        {Mf.current: self.buffer.dirs_to_scan,}
                    )
                # если файлы вырезаны и вставлены в рамках одного Mf,
                # то нужно просканировать директорию, откуда вырезаны файлы
                # и директорию, куда вставлены файлы
                else:
                    scaner_data[self.buffer.mf_to_scan].extend(
                        self.buffer.dirs_to_scan
                    )
            scaner_item = SingleDirScanerItem(data=scaner_data)
            self.start_scaner_task(scaner_item=scaner_item)

        def start_copy_files():
            self.buffer.dst_dir = Utils.get_abs_any_path(
                mf_path=Mf.current.curr_path,
                rel_path=Dynamic.current_dir
            )
        
            copy_files_win = self.copy_files_win()
            copy_files_win.finished_.connect(lambda files: scan_dirs(files))

        abs_current_dir = Utils.get_abs_any_path(
            mf_path=mf.curr_path, 
            rel_path=Dynamic.current_dir
        )
        if self.buffer.dirs_to_scan:
            copy_self = abs_current_dir in self.buffer.dirs_to_scan
            if copy_self:
                # копировать в себя нельзя
                self.win_warn = WinWarn(
                    Lng.attention[cfg.lng],
                    Lng.copy_name_same_dir[cfg.lng]
                )
                self.win_warn.resize(330, 90)
                self.win_warn.center_to_parent(self)
                self.win_warn.show()
                return
        elif self.buffer:
            start_copy_files()

    @with_conn
    def remove_files(self, parent: QWidget, mf: Mf, rel_paths: list, ms = 300):
        
        def poll_file_remover():
            if not file_remover.proc_q.empty():
                file_remover.proc_q.get()
            if not file_remover.is_alive():
                file_remover.terminate_join()
                scaner_item = SingleDirScanerItem({mf: dirs_to_scan, })
                self.start_scaner_task(scaner_item=scaner_item)
            else:
                QTimer.singleShot(ms, poll_file_remover)

        def start_file_remover():
            file_remover.start()
            QTimer.singleShot(ms, poll_file_remover)

        abs_paths = [
            Utils.get_abs_any_path(mf.curr_path, i)
            for i in rel_paths
        ]
        dirs_to_scan = list(set(os.path.dirname(i) for i in abs_paths))
        self.remove_files_win = WinQuestion(
            Lng.attention[cfg.lng],
            f"{Lng.delete_forever[cfg.lng]} ({len(abs_paths)})?"
        )
        file_remover = ProcessWorker(
                target=FilesRemover.start,
                args=(abs_paths, )
            )
        self.remove_files_win.resize(330, 80)
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
                dirs_to_scan=None,
                files_to_copy=files_to_copy,
                dst_dir=target_dir,
                mf_to_scan=Mf.current
            )

            self.grid.buffer = self.buffer
            self.paste_files(self.grid, Mf.current)

        target_dir = Utils.get_abs_any_path(mf.curr_path, Dynamic.current_dir)
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
            Utils.get_abs_any_path(mf.curr_path, i)
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
        self.settings_win.reset_data.connect(lambda mf: self.reset_data_cmd(mf))
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
            lambda rel_paths: self.open_info_win(self.view_win, Mf.current, rel_paths)
        )
        self.view_win.copy_path.connect(
            lambda rel_paths: self.copy_path(self.view_win, Mf.current, rel_paths)
        )
        self.view_win.copy_name.connect(
            lambda rel_paths: self.copy_name(self.view_win, Mf.current, rel_paths)
        )
        self.view_win.reveal_in_finder.connect(
            lambda rel_paths: self.reveal_in_finder(self.view_win, Mf.current, rel_paths)
        )
        self.view_win.set_fav.connect(
            self.set_fav
        )
        self.view_win.save_files.connect(
            lambda data: self.save_files(self.view_win, Mf.current, data)
        )
        self.view_win.switch_image_sig.connect(
            lambda path: self.grid.select_viewed_image(path)
        )
        self.view_win.no_connection.connect(
            lambda: self.open_win_smb(self.view_win, Mf.current)
        )
        self.view_win.open_in_app.connect(
            lambda data: self.open_in_app(self.window(), Mf.current, data)
        )

        if WinImageView.xx == 0:
            self.view_win.resize(Static.ww, Static.hh)
            self.view_win.center_to_parent(self.window())
        else:
            self.view_win.resize(WinImageView.ww, WinImageView.hh)
            self.view_win.move(WinImageView.xx, WinImageView.yy)
        self.view_win.show()

    def start_scaner_task(
            self,
            scaner_item: Optional[SingleDirScanerItem],
            ms: int = 1000
        ):

        def poll_task(tsk: ProcessWorker, tmr: QTimer):
            reload_gui = False
            while not tsk.proc_q.empty():
                self.scaner_timeout = time()
                scaner_item: ExtScanerItem = tsk.proc_q.get()
                if not reload_gui:
                    reload_gui = scaner_item.reload_gui
                if self.bar_bottom.progress_bar.text() != scaner_item.gui_text:
                    self.bar_bottom.progress_bar.setText(scaner_item.gui_text)
            if not tsk.is_alive():
                tsk.terminate_join()
                self.bar_bottom.progress_bar.start_timer_text()
                if reload_gui:
                    self.grid.reload_thumbnails()
                    self.left_menu.reload_tree()
            else:
                tmr.start(ms)

        # первая инициация
        if not hasattr(self, "scaner_timeout"):
            print("первая инициация сканера")
            self.scaner_timeout = time()
            self.loop_tmr = QTimer(self)
            self.loop_tmr.setSingleShot(True)
            self.loop_tmr.timeout.connect(
                lambda: self.start_scaner_task(scaner_item=scaner_item)
            )
            self.scaner_task = None

        can_start = False
        alive = self.scaner_task.is_alive() if self.scaner_task else False
        timeout = time() - self.scaner_timeout

        # задача зависла
        if alive and timeout > self.scaner_timeout_max:
            print("сканер завис, принудительно завершаю")
            self.scaner_task.terminate_join()
            can_start = True

        # задача завершена
        elif not alive:
            print("сканер завершен, можно запускать новый")
            can_start = True

        # задача жива и таймаут меньше заданного времени
        # то есть задача еще что то делает и сбрасывает таймаут
        elif alive and timeout < self.scaner_timeout_max:
            print("сканер еще работает, жду завершения")
            can_start = False

        if can_start:
            from datetime import datetime
            now = datetime.now().time().replace(microsecond=0)
            print("штатно запускаю сканер", now)
            if scaner_item:
                self.scaner_task = ProcessWorker(
                    target=SingleDirScaner.start,
                    args=(scaner_item, )
                    )
            else:
                self.scaner_task = ProcessWorker(
                    target=AllDirScaner.start,
                    args=(Mf.list_, )
                )

            self.bar_bottom.progress_bar.stop_timer_text()
            tmr = QTimer(self)
            tmr.setSingleShot(True)
            tmr.timeout.connect(lambda: poll_task(self.scaner_task, tmr))

            self.scaner_task.start()
            tmr.start(ms)
            self.loop_tmr.stop()
            self.loop_tmr.start(cfg.scaner_minutes * 60 * 1000)

        else:
            # проверяем каждую минуту, что задача завершена
            self.loop_tmr.stop()
            self.loop_tmr.start(1*60*1000)

    def restart_scaner_task(self):
        self.scaner_task.terminate_join()
        self.start_scaner_task(scaner_item=None)
        
    def center_screen(self):
        screen = QDesktopWidget().screenGeometry()
        size = self.geometry()
        x = (screen.width() - size.width()) // 2
        y = (screen.height() - size.height()) // 2
        self.move(x, y)

    def on_exit(self):
        cfg.write_json_data()
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
            self.left_menu.reload_tree()
            self.restart_scaner_task()

        self.grid.reload_thumbnails()
        self.left_menu.reload_tree()
        self.reset_task = MfDataCleaner(mf.alias)
        self.reset_task.sigs.finished_.connect(reset_data_finished)
        UThreadPool.start(self.reset_task)

    def copy_files_win(self):
        progress_win = WinCopyFiles(
            src_urls=self.buffer.files_to_copy,
            dst_dir=self.buffer.dst_dir,
            is_cut=self.buffer.type_
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
            self.paste_files(self.grid, Mf.current)
        
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
                Lng.drop_event_denied_msg[cfg.lng],
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
            self.upload_files(self.grid, Mf.current, paths)
        return super().dropEvent(a0)
    
    def resizeEvent(self, a0):
        wid = self.splitter.widget(1)
        self.bar_path.setMaximumWidth(wid.width())
        return super().resizeEvent(a0)