import gc
import os
import subprocess

from PyQt5.QtCore import Qt, QTimer
from PyQt5.QtGui import QCloseEvent, QKeyEvent
from PyQt5.QtWidgets import (QDesktopWidget, QFileDialog, QFrame, QPushButton,
                             QSplitter, QVBoxLayout, QWidget)

from cfg import Cfg, Dynamic, Static, ThumbData
from system.filters import Filters
from system.lang import Lng
from system.main_folder import Mf
from system.new_scaner.scaner_task import CustomScanerTask
from system.tasks import (CopyFilesManager, FavManager, FilesRemover,
                          MfDataCleaner, Utils, UThreadPool)

from ._base_widgets import (ClipBoardItem, NotifyWid, SettingsItem,
                            UHBoxLayout, UMainWindow, UVBoxLayout, WinManager)
from .bar_bottom import BarBottom
from .bar_macos import BarMacos
from .bar_top import BarTop
from .grid import Grid
from .menu_left import MenuLeft
from .progressbar_win import ProgressbarWin
from .win_dates import WinDates
from .win_image_view import WinImageView
from .win_info import WinInfo
from .win_settings import WinSettings
from .win_warn import WinQuestion, WinSmb, WinWarn


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
    argv_flag = "noscan"
    update_mins = 30
    min_w = 750
    ww, hh = 870, 500
    left_side_width = 250
    warning_svg = "./images/warning.svg"

    def __init__(self, argv: list[str]):
        super().__init__()
        self.resize(self.ww, self.hh)
        self.setMinimumWidth(self.min_w)

        self.setAcceptDrops(True)
        self.setMenuBar(BarMacos())
        
        self.view_win: WinImageView
        self.clipboard_item: ClipBoardItem = None

        h_wid_main = QWidget()
        h_lay_main = UHBoxLayout()
        h_lay_main.setContentsMargins(0, 0, 5, 0)
        h_wid_main.setLayout(h_lay_main)
        self.central_layout.addWidget(h_wid_main)

        # Создаем QSplitter
        splitter = QSplitter(Qt.Horizontal)

        # Левый виджет (MenuLeft)
        self.left_menu = MenuLeft()
        self.left_menu.left_menu_click.connect(
            lambda abs_path: self.left_menu_click(self.grid, Mf.current, abs_path)
        )
        self.left_menu.left_menu_click.connect(
            lambda: self.set_window_title()
        )
        self.left_menu.path_reveal.connect(
            lambda abs_path: self.reveal_in_finder(self.grid, Mf.current, [abs_path, ])
        )
        self.left_menu.restart_scaner.connect(
            lambda: self.restart_scaner_task()
        )
        self.left_menu.mf_edit.connect(
            lambda settings_item: self.open_settings_win(settings_item)
        )
        self.left_menu.mf_new.connect(
            lambda settings_item: self.open_settings_win(settings_item)
        )
        splitter.addWidget(self.left_menu)

        # Правый виджет
        right_wid = QWidget()
        splitter.addWidget(right_wid)
        right_lay = UVBoxLayout()
        right_lay.setContentsMargins(0, 0, 0, 0)
        right_wid.setLayout(right_lay)

        # Добавляем элементы в правую панель
        self.bar_top = BarTop()
        self.bar_top.open_dates_win.connect(self.open_dates_win)
        self.bar_top.reload_thumbnails.connect(
            lambda: self.grid.reload_thumbnails()
            )
        self.bar_top.open_settings_win.connect(self.open_settings_win)
        right_lay.addWidget(self.bar_top)

        sep_upper = USep()
        right_lay.addWidget(sep_upper)

        self.grid = Grid()
        self.grid.restart_scaner.connect(
            lambda: self.restart_scaner_task()
        )
        self.grid.remove_files.connect(
            lambda rel_paths: self.remove_files(self.grid, Mf.current, rel_paths))
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
            lambda: self.paste_files_here(self.grid,  Mf.current)
        )
        self.grid.copy_files.connect(
            lambda data: self.set_clipboard(self.grid, Mf.current, data)
        )
        self.grid.setup_mf.connect(
            self.open_settings_win
        )
        right_lay.addWidget(self.grid)

        sep_bottom = USep()
        right_lay.addWidget(sep_bottom)

        self.bar_bottom = BarBottom()
        self.bar_bottom.resize_thumbnails.connect(lambda: self.grid.resize_thumbnails())
        right_lay.addWidget(self.bar_bottom)

        # Добавляем splitter в основной layout
        h_lay_main.addWidget(splitter)

        splitter.setStretchFactor(0, 0)
        splitter.setStretchFactor(1, 1)
        splitter.setSizes([
            self.left_side_width,
            self.width() - self.left_side_width
        ])

        self.grid.setFocus()

        self.scaner_timer = QTimer(self)
        self.scaner_timer.setSingleShot(True)
        self.scaner_timer.timeout.connect(self.start_scaner_task)
        self.scaner_task = None
        self.scaner_task_canceled = False

        QTimer.singleShot(100, self.first_check)

        if argv[-1] != self.argv_flag:
            self.start_scaner_task()

    @staticmethod
    def with_conn(fn):
        def wrapper(self: "WinMain", parent: QWidget, mf: Mf, *args, **kwargs):
            path = mf.get_curr_path()
            if path:
                return fn(self, parent, mf, *args, **kwargs)
            else:
                self.open_win_smb(parent, mf)
        return wrapper

    def open_win_smb(self, parent: QWidget, mf: Mf):
        basename = os.path.basename(mf.current.paths[0])
        alias = mf.name
        noti = NotifyWid(
            parent,
            f"{basename} ({alias}): {Lng.no_connection_full[Cfg.lng].lower()}",
            self.warning_svg
            )
        noti._show()
    
    def first_check(self):
        if not Mf.current.get_curr_path():
            self.open_win_smb(self.grid, Mf.current)

    @with_conn
    def left_menu_click(self, parent: QWidget, mf: Mf, abs_path: str):
        rel_path = Utils.get_rel_path(mf.curr_path, abs_path)
        Dynamic.current_dir = rel_path
        self.grid.reload_thumbnails()

    @with_conn
    def save_files(self, parent: QWidget, mf: Mf, data: tuple):
        dest, rel_paths = data
        abs_files = [
            Utils.get_abs_path(mf.curr_path, i)
            for i in rel_paths
        ]
        if dest is None:
            dest = QFileDialog.getExistingDirectory()
            if dest:
                task = self.copy_files_task(dest, abs_files)
                task.sigs.finished_.connect(Utils.reveal_files)
                UThreadPool.start(task)
        else:
            task = self.copy_files_task(dest, abs_files)
            task.sigs.finished_.connect(Utils.reveal_files)
            UThreadPool.start(task)

    @with_conn
    def set_clipboard(self, parent: QWidget, mf: Mf, data: tuple):
        action_type, rel_paths = data
        if rel_paths:
            abs_paths = [
                Utils.get_abs_path(mf.curr_path, i)
                for i in rel_paths
            ]
            self.clipboard_item = ClipBoardItem()
            self.grid.clipboard_item = self.clipboard_item
            self.clipboard_item.action_type = action_type
            self.clipboard_item.files_to_copy = abs_paths
            self.clipboard_item.source_mf = Mf.current
            self.clipboard_item.source_dirs = list(set(
                os.path.dirname(i)
                for i in abs_paths
            ))
            if action_type == self.clipboard_item.type_cut:
                for i in self.grid.selected_widgets:
                    i.set_transparent_frame(0.5)

    @with_conn
    def open_in_app(self, parent: QWidget, mf: Mf, data: tuple):
        rel_paths, app_path = data
        for i in rel_paths:
            abs_path = Utils.get_abs_path(mf.curr_path, i)
            if app_path:
                subprocess.Popen(["open", "-a", app_path, abs_path])
            else:
                subprocess.Popen(["open", abs_path])

    @with_conn
    def reveal_in_finder(self, parent: QWidget, mf: Mf, rel_paths: list):
        abs_paths = [
            Utils.get_abs_path(mf.curr_path, i)
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
            Utils.get_abs_path(mf.curr_path, i)
            for i in rel_paths
        ]
        Utils.copy_text("\n".join(abs_paths))

    @with_conn
    def paste_files_here(self, parent: QWidget, mf: Mf):

        def reset_clipboard():
            self.clipboard_item = None
            self.grid.clipboard_item = None

        def set_type(type: str):
            self.clipboard_item.action_type = type

        def set_files_copied(files: list[str]):
            self.clipboard_item.files_copied = files

        def scan_dirs():
            if not self.clipboard_item.files_copied:
                print("ни один файл не был скопирован")
                reset_clipboard()
                return
            if self.clipboard_item.action_type == self.clipboard_item.type_cut:
                scaner_task = CustomScanerTask(
                    self.clipboard_item.source_mf,
                    self.clipboard_item.source_dirs
                )
                scaner_task.sigs.progress_text.connect(
                    self.bar_bottom.progress_bar.setText
                )
                scaner_task.sigs.reload_thumbnails.connect(
                    lambda: set_type(self.clipboard_item.type_copy)
                )
                scaner_task.sigs.reload_thumbnails.connect(scan_dirs)
                UThreadPool.start(scaner_task)
            elif self.clipboard_item.action_type == self.clipboard_item.type_copy:
                dirs = [self.clipboard_item.target_dir, ]
                scaner_task = CustomScanerTask(
                    self.clipboard_item.target_mf,
                    dirs
                )
                scaner_task.sigs.progress_text.connect(
                    self.bar_bottom.progress_bar.setText
                )
                scaner_task.sigs.reload_thumbnails.connect(
                    reset_clipboard
                )
                scaner_task.sigs.reload_thumbnails.connect(
                    self.grid.reload_thumbnails
                )
                UThreadPool.start(scaner_task)

        def remove_files():
            remove_task = FilesRemover(self.clipboard_item.files_to_copy)
            remove_task.sigs.finished_.connect(scan_dirs)
            UThreadPool.start(remove_task)

        def copy_files():
            task = self.copy_files_task(
                self.clipboard_item.target_dir,
                self.clipboard_item.files_to_copy
            )
            # task.sigs.finished_.connect(
            #     MainUtils.reveal_files
            # )
            task.sigs.finished_.connect(
                lambda files: set_files_copied(files)
            )
            if self.clipboard_item.action_type == self.clipboard_item.type_cut:
                task.sigs.finished_.connect(
                    lambda _: remove_files()
                )
            else:
                task.sigs.finished_.connect(
                    lambda _: scan_dirs()
                )
            UThreadPool.start(task)

        abs_current_dir = Utils.get_abs_path(mf.curr_path, Dynamic.current_dir)
        copy_self = abs_current_dir in self.clipboard_item.source_dirs
        if copy_self:
            self.win_warn = WinWarn(
                Lng.attention[Cfg.lng],
                Lng.copy_name_same_dir[Cfg.lng]
            )
            self.win_warn.center_to_parent(self)
            self.win_warn.show()
        elif self.clipboard_item:
            self.clipboard_item.target_mf = Mf.current
            self.clipboard_item.target_dir = abs_current_dir
            copy_files()

    @with_conn
    def remove_files(self, parent: QWidget, mf: Mf, rel_paths: list):
        
        def fin_remove(dirs_to_scan: list[str]):
            task = CustomScanerTask(Mf.current, dirs_to_scan)
            task.sigs.reload_thumbnails.connect(self.grid.reload_thumbnails)
            UThreadPool.start(task)
        
        def start_remove(paths: list[str], dirs_to_scan: list[str]):
            task = FilesRemover(paths)
            task.sigs.finished_.connect(lambda: fin_remove(dirs_to_scan))
            UThreadPool.start(task)

        abs_paths = [
            Utils.get_abs_path(mf.curr_path, i)
            for i in rel_paths
        ]
        dirs_to_scan = list(set(os.path.dirname(i) for i in abs_paths))
        self.remove_files_win = WinQuestion(
            Lng.attention[Cfg.lng],
            f"{Lng.delete_forever[Cfg.lng]} ({len(abs_paths)})?"
        )
        self.remove_files_win.center_to_parent(self.window())
        self.remove_files_win.ok_clicked.connect(
            lambda: start_remove(abs_paths, dirs_to_scan)
        )
        self.remove_files_win.ok_clicked.connect(
            self.remove_files_win.deleteLater
        )
        self.remove_files_win.show()
    
    @with_conn
    def upload_files(self, parent: QWidget, mf: Mf, abs_paths: list):

        def shorten_path(path, max_len=50):
            if len(path) <= max_len:
                return path
            return '…' + path[-(max_len-1):]  # оставляем конец, добавляем '…' спереди

        def fin(target_dir: str):
            self.upload_win.deleteLater()
            self.clipboard_item = ClipBoardItem()
            self.grid.clipboard_item = self.clipboard_item
            self.clipboard_item.action_type = ClipBoardItem.type_copy
            self.clipboard_item.target_mf = Mf.current
            self.clipboard_item.target_dir = target_dir
            self.clipboard_item.files_to_copy = abs_paths
            self.clipboard_item.source_dirs = list(set(os.path.dirname(i) for i in abs_paths))
            self.paste_files_here(self.grid, Mf.current)

        target_dir = Utils.get_abs_path(mf.curr_path, Dynamic.current_dir)
        text = (
            Lng.upload_files_in[Cfg.lng],
            shorten_path(target_dir)
        )
        self.upload_win = WinQuestion(
            Lng.attention[Cfg.lng],
            "\n".join(text)
        )
        self.upload_win.center_to_parent(self)
        self.upload_win.ok_clicked.connect(lambda: fin(target_dir))
        self.upload_win.show()

    @with_conn
    def open_info_win(self, parent: QWidget, mf: Mf, rel_paths: list[str]):
        
        def open_delayed():
            """Отображает окно WinInfo после его инициализации."""
            self.info_win.adjustSize()
            self.info_win.center_to_parent(self)
            self.info_win.show()
        
        abs_paths = [
            Utils.get_abs_path(mf.curr_path, i)
            for i in rel_paths
        ]
        self.info_win = WinInfo(abs_paths)
        self.info_win.finished_.connect(open_delayed)

    def open_settings_win(self, settings_item: SettingsItem):
        self.bar_top.settings_btn.set_solid_style()
        self.settings_win = WinSettings(settings_item)
        self.settings_win.closed.connect(self.bar_top.settings_btn.set_normal_style)
        self.settings_win.reset_data.connect(self.reset_data_cmd)
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

        def on_closed():
            self.view_win = None
            gc.collect

        if len(self.grid.selected_widgets) == 1:
            path_to_wid = self.grid.path_to_wid.copy()
            is_selection = False
        else:
            path_to_wid = {i.rel_path: i for i in self.grid.selected_widgets}
            is_selection = True
        wid = self.grid.selected_widgets[-1]
        self.view_win = WinImageView(wid.rel_path, path_to_wid, is_selection)
        self.view_win.closed_.connect(
            lambda: on_closed()
        )
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
        self.view_win.center_to_parent(self.window())
        self.view_win.show()

    def start_scaner_task(self):
        """
        Инициализирует и запускает задачу сканирования ScanerTask.

        Если задача ещё не была создана (self.scaner_task is None), создаётся новая задача,
        подключаются её сигналы к соответствующим обработчикам, и она отправляется на выполнение
        в пользовательский пул потоков (UThreadPool).

        Если текущая задача уже завершена, объект self.scaner_task сбрасывается в None и метод
        рекурсивно вызывает сам себя для запуска новой задачи.

        Если задача ещё выполняется, метод откладывает повторную попытку запуска на 3 секунды
        с помощью QTimer.singleShot.
        """

        if Cfg.new_scaner:
            from system.new_scaner.scaner_task import ScanerTask
        else:
            from system.old_scaner.scaner_task import ScanerTask

        if self.scaner_task is None:
            self.scaner_task = ScanerTask()
            self.scaner_task.sigs.finished_.connect(self.on_scaner_finished)
            self.scaner_task.sigs.progress_text.connect(self.bar_bottom.progress_bar.setText)
            self.scaner_task.sigs.reload_thumbnails.connect(self.grid.reload_thumbnails)
            UThreadPool.start(self.scaner_task)
        elif self.scaner_task.task_state.finished():
            self.scaner_task = None
            self.start_scaner_task()
        else:
            QTimer.singleShot(3000, self.start_scaner_task)

    def on_scaner_finished(self):
        """
        Обрабатывает завершение текущей задачи сканирования.

        Если задача была остановлена вручную (флаг self.scaner_task_canceled установлен в True),
        запускается короткий таймер на 1 секунду для быстрого перезапуска сканирования.

        Если задача завершилась штатно, запускается длительный таймер с интервалом, заданным
        в JsonData.scaner_minutes (в минутах, конвертированных в миллисекунды), для
        следующего автоматического запуска сканирования.
        """
        self.scaner_timer.stop()
        if self.scaner_task_canceled:
            self.scaner_task_canceled = False
            self.scaner_timer.start(1000)
        else:
            self.scaner_timer.start(Cfg.scaner_minutes * 60 * 1000)

    def restart_scaner_task(self):
        """
        Прерывает текущую задачу сканирования и инициирует её перезапуск.

        Если текущая задача ещё не завершена, устанавливается флаг отмены (self.scaner_task_canceled = True),
        и флаг состояния задачи переводится в "не должно выполняться" с помощью set_should_run(False).
        После завершения текущей задачи метод on_scaner_finished запустит короткий таймер.

        Если задача уже завершена, активный таймер останавливается, и запускается короткий таймер на 1 секунду
        для немедленного запуска новой задачи сканирования.
        """
        self.bar_bottom.progress_bar.setText(Lng.preparing[Cfg.lng])
        
        if self.scaner_task is None:
            self.scaner_timer.stop()
            self.scaner_timer.start(1000)

        # если задача не закончена, прерываем ее
        elif not self.scaner_task.task_state.finished():
            self.scaner_task.task_state.set_should_run(False)
            # ставим флаг,чтобы on_scaner_finished запустил короткий таймер
            # прерванная задача завершится и запустит короткий таймер
            self.scaner_task_canceled = True
        else:
            # если задача закончена, значит стоит долгий таймер
            self.scaner_timer.stop()
            # если задача закончена, немедленно запускаем новый сканер
            self.scaner_timer.start(1000)
        
    def set_window_title(self):
        if Dynamic.current_dir is None:
            return
        if Mf.current.curr_path:
            true_name = os.path.basename(Mf.current.curr_path)
        else:
            true_name = os.path.basename(Mf.current.paths[0])
        alias = Mf.current.name
        mappings = {
            Static.NAME_FAVS: Lng.favorites[Cfg.lng],
            Static.NAME_RECENTS: Lng.recents[Cfg.lng],
            "": f"{true_name} ({alias})"
        }
        if Dynamic.current_dir in mappings:
            t = mappings.get(Dynamic.current_dir)
        else:
            t = os.path.basename(Dynamic.current_dir)
        self.setWindowTitle(t)

    def center_screen(self):
        screen = QDesktopWidget().screenGeometry()
        size = self.geometry()
        x = (screen.width() - size.width()) // 2
        y = (screen.height() - size.height()) // 2
        self.move(x, y)

    def on_exit(self):
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
        self.task = FavManager(rel_path, value)
        self.task.sigs.finished_.connect(
            lambda: finished(rel_path, value)
        )
        UThreadPool.start(self.task)

    def reset_data_cmd(self, mf: Mf):

        def fin():
            if mf.curr_path:
                true_name = os.path.basename(mf.curr_path)
            else:
                true_name = os.path.basename(mf.paths[0])
            alias = mf.name
            self.win_warn = WinWarn(
                Lng.attention[Cfg.lng],
                f"{true_name} ({alias}): {Lng.data_was_reset[Cfg.lng].lower()}"
            )
            self.win_warn.center_to_parent(self.window())
            self.win_warn.show()
            self.restart_scaner_task()

        self.reset_task = MfDataCleaner(mf.name)
        self.reset_task.sigs.finished_.connect(fin)
        UThreadPool.start(self.reset_task)

    def copy_files_task(self, target_dir: str, files_to_copy: list[str]):
        """
        Создает QRunnable и окно с прогрессбаром для копирования файлов.
        Возвращает QRunnable (можно доподключить сигналы).
        """

        def set_below_label(data: tuple[int, int], win: ProgressbarWin):
            count, total = data
            win.below_label.setText(
                f"{Lng.copying[Cfg.lng]} {count} {Lng.from_[Cfg.lng]} {total}"
            )

        def set_above_label(text: str, dest_name: str, win: ProgressbarWin):
            win.above_label.setText(
                f"\"{text}\" {Lng.in_[Cfg.lng]} \"{dest_name}\""
            )

        def copy_files(target_dir: str, files_to_copy: list[str]):
            dest_name = os.path.basename(os.path.basename(target_dir))
            progress_win = ProgressbarWin(Lng.copying[Cfg.lng])
            progress_win.progressbar.setMaximum(100)
            progress_win.center_to_parent(self)
            progress_win.show()
            task = CopyFilesManager(target_dir, files_to_copy)
            progress_win.cancel.connect(
                lambda: task.task_state.set_should_run(False)
            )
            task.sigs.value_changed.connect(
                progress_win.progressbar.setValue
            )
            task.sigs.progress_changed.connect(
                lambda data: set_below_label(data, progress_win)
            )
            task.sigs.file_changed.connect(
                lambda text: set_above_label(text, dest_name, progress_win)
            )
            task.sigs.finished_.connect(
                progress_win.deleteLater
            )
            return task
        
        return copy_files(target_dir, files_to_copy)

    def closeEvent(self, a0: QCloseEvent | None) -> None:
        self.hide()
        a0.ignore()
    
    def keyPressEvent(self, a0: QKeyEvent | None) -> None:
        
        if a0.key() == Qt.Key.Key_V:
            self.paste_files_here(self.grid, Mf.current)
        
        if a0.key() == Qt.Key.Key_W:
            if a0.modifiers() == Qt.KeyboardModifier.ControlModifier:
                self.hide()

        elif a0.key() == Qt.Key.Key_F:
            if a0.modifiers() == Qt.KeyboardModifier.ControlModifier:
                self.bar_top.search_wid.setFocus()

        elif a0.key() == Qt.Key.Key_Escape:
            if self.isFullScreen():
                self.showNormal()
                self.raise_()
            else:
                a0.ignore()

        elif a0.key() == Qt.Key.Key_Equal:
            if a0.modifiers() == Qt.KeyboardModifier.ControlModifier:
                if Dynamic.thumb_size_index < len(ThumbData.PIXMAP_SIZE) - 1:
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
            noti = NotifyWid(
                self.grid,
                Lng.drop_event_denied_msg[Cfg.lng],
                self.warning_svg
                )
            noti._show()
            return

        paths: list[str] = [
            i.toLocalFile().rstrip(os.sep)
            for i in a0.mimeData().urls()
        ]

        for i in paths:
            if os.path.isdir(i):
                self.win_warn = WinWarn(Lng.attention[Cfg.lng], Lng.drop_only_files[Cfg.lng])
                self.win_warn.adjustSize()
                self.win_warn.center_to_parent(self)
                self.win_warn.show()
                return

        if paths:
            self.upload_files(self.grid, Mf.current, paths)

        return super().dropEvent(a0)