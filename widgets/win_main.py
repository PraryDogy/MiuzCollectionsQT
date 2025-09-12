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
from system.main_folder import MainFolder
from system.tasks import (CopyFilesTask, CustomScanerTask, FavTask, MainUtils,
                          ResetDataTask, RmFilesTask)
from system.utils import UThreadPool

from ._base_widgets import (ClipBoardItem, SettingsItem, UHBoxLayout,
                            UMainWindow, UVBoxLayout)
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
from .win_upload import WinUpload
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
    left_side_width = 210

    def __init__(self, argv: list[str]):
        super().__init__()
        self.resize(self.ww, self.hh)
        self.setMinimumWidth(self.min_w)

        self.setAcceptDrops(True)
        self.setMenuBar(BarMacos())
        
        self.win_image_view: WinImageView

        h_wid_main = QWidget()
        h_lay_main = UHBoxLayout()
        h_lay_main.setContentsMargins(0, 0, 5, 0)
        h_wid_main.setLayout(h_lay_main)
        self.central_layout.addWidget(h_wid_main)

        # Создаем QSplitter
        splitter = QSplitter(Qt.Horizontal)

        # Левый виджет (MenuLeft)
        self.left_menu = MenuLeft()
        self.left_menu.clicked_.connect(lambda: self.grid.reload_thumbnails())
        self.left_menu.clicked_.connect(lambda: self.set_window_title())
        self.left_menu.no_connection.connect(self.open_win_smb)
        self.left_menu.setup_main_folder.connect(self.open_settings)
        self.left_menu.setup_new_folder.connect(self.open_settings)
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
        self.bar_top.reload_thumbnails.connect(lambda: self.grid.reload_thumbnails())
        self.bar_top.open_settings_win.connect(self.open_settings)
        right_lay.addWidget(self.bar_top)

        sep_upper = USep()
        right_lay.addWidget(sep_upper)

        self.grid = Grid()
        self.grid.restart_scaner.connect(lambda: self.restart_scaner_task())
        self.grid.remove_files.connect(lambda rel_img_paths: self.remove_files(rel_img_paths))
        self.grid.move_files.connect(lambda rel_img_paths: self.paste_files_here(rel_img_paths))
        self.grid.no_connection.connect(self.open_win_smb)
        self.grid.img_view.connect(lambda: self.open_img_view())
        self.grid.save_files.connect(self.save_files)
        self.grid.open_info_win.connect(self.open_win_info)
        self.grid.copy_path.connect(self.copy_path)
        self.grid.copy_name.connect(self.copy_name)
        self.grid.reveal_in_finder.connect(self.reveal_in_finder)
        self.grid.set_fav.connect(self.set_fav)
        self.grid.open_in_app.connect(self.open_in_app)
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
        
        def first_check():
            for i in MainFolder.list_:
                if not i.get_curr_path():
                    self.open_win_smb()
                    break

        QTimer.singleShot(100, first_check)

        if argv[-1] != self.argv_flag:
            self.start_scaner_task()
            
    def save_files(self, data: tuple):

        def set_below_label(data: tuple[int, int], win: ProgressbarWin):
            count, total = data
            win.below_label.setText(
                f"{Lng.copying[Cfg.lng]} {count} {Lng.from_[Cfg.lng]} {total}"
            )

        def set_above_label(text: str, dest_name: str, win: ProgressbarWin):
            win.above_label.setText(
                f"\"{text}\" {Lng.in_[Cfg.lng]} \"{dest_name}\""
            )

        def copy_files_start(dest: str, abs_files: list[str]):
            dest_name = os.path.basename(dest)
            progress_win = ProgressbarWin(Lng.copying[Cfg.lng])
            progress_win.progressbar.setMaximum(100)
            progress_win.center_to_parent(self)
            progress_win.show()
            task = CopyFilesTask(dest, abs_files)
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
                MainUtils.reveal_files
            )
            task.sigs.finished_.connect(
                progress_win.deleteLater
            )
            UThreadPool.start(task)

        dest, rel_img_paths = data
        main_folder_path = MainFolder.current.get_curr_path()
        if main_folder_path:
            abs_files = [
                MainUtils.get_abs_path(main_folder_path, i)
                for i in rel_img_paths
            ]
            if dest is None:
                dest = QFileDialog.getExistingDirectory()
                if dest:
                    copy_files_start(dest, abs_files)
            else:
                copy_files_start(dest, abs_files)
        else:
            self.open_win_smb()

    def open_win_info(self, rel_img_paths: list[str]):
        
        def open_delayed():
            """Отображает окно WinInfo после его инициализации."""
            self.win_info.adjustSize()
            self.win_info.center_to_parent(self)
            self.win_info.show()
        
        main_folder_path = MainFolder.current.get_curr_path()
        if main_folder_path:
            abs_paths = [
                MainUtils.get_abs_path(main_folder_path, i)
                for i in rel_img_paths
            ]
            self.win_info = WinInfo(abs_paths)
            self.win_info.finished_.connect(open_delayed)
        else:
            self.open_win_smb()

    def open_win_smb(self):
        self.win_smb = WinSmb()
        self.win_smb.center_to_parent(self.window())
        self.win_smb.show()
    
    def open_img_view(self):
        if len(self.grid.selected_widgets) == 1:
            path_to_wid = self.grid.path_to_wid.copy()
            is_selection = False
        else:
            path_to_wid = {i.rel_img_path: i for i in self.grid.selected_widgets}
            is_selection = True
        wid = self.grid.selected_widgets[-1]
        self.win_image_view = WinImageView(wid.rel_img_path, path_to_wid, is_selection)
        self.win_image_view.closed_.connect(self.image_view_closed)
        self.win_image_view.open_win_info.connect(self.open_win_info)
        self.win_image_view.copy_path.connect(self.copy_path)
        self.win_image_view.copy_name.connect(self.copy_name)
        self.win_image_view.reveal_in_finder.connect(self.reveal_in_finder)
        self.win_image_view.set_fav.connect(self.set_fav)
        self.win_image_view.save_files.connect(self.save_files)
        self.win_image_view.switch_image_sig.connect(
            lambda img_path: self.grid.select_viewed_image(img_path)
        )
        self.win_image_view.no_connection.connect(self.open_win_smb)
        self.win_image_view.center_to_parent(self.window())
        self.win_image_view.show()

    def image_view_closed(self):
        del self.win_image_view
        self.win_image_view = None
        gc.collect

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
            self.scaner_task.sigs.reload_gui.connect(self.reload_gui)
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
        if MainFolder.current.curr_path:
            true_name = os.path.basename(MainFolder.current.curr_path)
        else:
            true_name = os.path.basename(MainFolder.current.paths[0])
        alias = MainFolder.current.name
        data = {
            Static.NAME_FAVS: Lng.favorites[Cfg.lng],
            Static.NAME_RECENTS: Lng.recents[Cfg.lng],
            "": f"{true_name} ({alias})"
        }
        if Dynamic.current_dir in data:
            t = data.get(Dynamic.current_dir)
        else:
            t = os.path.basename(Dynamic.current_dir)
        self.setWindowTitle(t)

    def center(self):
        screen = QDesktopWidget().screenGeometry()
        size = self.geometry()
        x = (screen.width() - size.width()) // 2
        y = (screen.height() - size.height()) // 2
        self.move(x, y)

    def on_exit(self):
        Cfg.write_json_data()
        Filters.write_json_data()
        MainFolder.write_json_data()
        os._exit(0)

    def set_fav(self, data: tuple[str, int]):

        def finished(rel_img_path: str, value: int):
            self.grid.set_thumb_fav(rel_img_path, value)
            if self.win_image_view:
                self.win_image_view.set_title()

        rel_img_path, value = data
        self.task = FavTask(rel_img_path, value)
        self.task.sigs.finished_.connect(
            lambda: finished(rel_img_path, value)
        )
        UThreadPool.start(self.task)

    def open_in_app(self, data: tuple[list[str], str | None]):
        rel_img_paths, app_path = data
        main_folder_path = MainFolder.current.get_curr_path()
        if main_folder_path:
            for i in rel_img_paths:
                abs_path = MainUtils.get_abs_path(main_folder_path, i)
                if app_path:
                    subprocess.Popen(["open", "-a", app_path, abs_path])
                else:
                    subprocess.Popen(["open", abs_path])
        else:
            self.open_win_smb()

    def reveal_in_finder(self, rel_img_paths: list[str]):
        main_folder_path = MainFolder.current.get_curr_path()
        if main_folder_path:
            abs_paths = [
                MainUtils.get_abs_path(main_folder_path, i)
                for i in rel_img_paths
            ]
            if os.path.isdir(abs_paths[0]):
                subprocess.Popen(["open", abs_paths[0]])
            else:
                MainUtils.reveal_files(abs_paths)
        else:
            self.open_win_smb()

    def copy_name(self, rel_img_paths: list[str]):
        main_folder_path = MainFolder.current.get_curr_path()
        if main_folder_path:
            names = [
                os.path.splitext(os.path.basename(i))[0]
                for i in rel_img_paths
            ]
            MainUtils.copy_text("\n".join(names))
        else:
            self.open_win_smb()

    def copy_path(self, rel_img_paths: list[str]):
        main_folder_path = MainFolder.current.get_curr_path()
        if main_folder_path:
            abs_paths = [
                MainUtils.get_abs_path(main_folder_path, i)
                for i in rel_img_paths
            ]
            MainUtils.copy_text("\n".join(abs_paths))
        else:
            self.open_win_smb()

    def open_dates_win(self):
        self.win_dates = WinDates()
        self.win_dates.center_to_parent(self)
        self.win_dates.dates_btn_solid.connect(lambda: self.bar_top.dates_btn.set_solid_style())
        self.win_dates.dates_btn_normal.connect(lambda: self.bar_top.dates_btn.set_normal_style())
        self.win_dates.reload_thumbnails.connect(lambda: self.grid.reload_thumbnails())
        self.win_dates.show()

    def reset_data_cmd(self, main_folder: MainFolder):

        def fin():
            if main_folder.curr_path:
                true_name = os.path.basename(main_folder.curr_path)
            else:
                true_name = os.path.basename(main_folder.paths[0])
            alias = main_folder.name
            self.win_warn = WinWarn(
                Lng.attention[Cfg.lng],
                f"{true_name} ({alias}): {Lng.data_was_reset[Cfg.lng].lower()}"
            )
            self.win_warn.center_to_parent(self.window())
            self.win_warn.show()
            self.restart_scaner_task()

        self.reset_task = ResetDataTask(main_folder.name)
        self.reset_task.sigs.finished_.connect(fin)
        UThreadPool.start(self.reset_task)

    def paste_files_here(self):

        def scan_dirs(item: ClipBoardItem):
            if item.action_type == item.type_cut:
                ...
            else:
                # self.restart_scaner_task()
                dirs = [item.target_dir, ]
                update_task = CustomScanerTask(item.target_main_folder, dirs)
                update_task.sigs.progress_text.connect(self.bar_bottom.progress_bar.setText)
                update_task.sigs.finished_.connect(self.reload_gui)
                UThreadPool.start(update_task)

            self.grid.clipboard_item = None

        def remove_files(item: ClipBoardItem, files_copied: list[str]):
            item.files_copied = files_copied
            remove_task = RmFilesTask(item.files_to_copy)
            remove_task.sigs.finished_.connect(
                scan_dirs(item)
            )
            UThreadPool.start(remove_task)

        def copy_files(item: ClipBoardItem):
            copy_task = CopyFilesTask(item.target_dir, item.files_to_copy)
            if item.action_type == item.type_cut:
                copy_task.sigs.finished_.connect(
                    lambda files_copied: remove_files(item, files_copied)
            )
            else:
                copy_task.sigs.finished_.connect(lambda _: scan_dirs(item))
            UThreadPool.start(copy_task)

        main_folder_path = MainFolder.current.get_curr_path()
        if main_folder_path:
            if self.grid.clipboard_item:
                item = self.grid.clipboard_item
                item.target_dir = MainUtils.get_abs_path(main_folder_path, Dynamic.current_dir)
                item.target_main_folder = MainFolder.current
                copy_files(item)
        else:
            self.open_win_smb()

    def remove_files(self, rel_img_paths: list):
        # нужно добавить сканирование директории епта
        
        def start_remove(img_paths: list[str]):
            task = RmFilesTask(img_paths)
            task.sigs.finished_.connect(self.restart_scaner_task)
            UThreadPool.start(task)
        
        main_folder_path = MainFolder.current.get_curr_path()
        if main_folder_path:
            img_paths = [
                MainUtils.get_abs_path(main_folder_path, i)
                for i in rel_img_paths
            ]
            self.remove_files_win = WinQuestion(
                Lng.attention[Cfg.lng],
                f"{Lng.delete_forever[Cfg.lng]} ({len(img_paths)})?"
            )
            self.remove_files_win.center_to_parent(self.window())
            self.remove_files_win.ok_clicked.connect(
                lambda: start_remove(img_paths)
            )
            self.remove_files_win.ok_clicked.connect(
                self.remove_files_win.deleteLater
            )
            self.remove_files_win.show()
        else:
            self.open_win_smb()

    def reload_gui(self):
        self.grid.reload_thumbnails()
        self.left_menu.init_ui()
    
    def upload_files(self, img_paths: list):

        def set_below_label(data: tuple[int, int], win: ProgressbarWin):
            count, total = data
            win.below_label.setText(
                f"{Lng.copying[Cfg.lng]} {count} {Lng.from_[Cfg.lng]} {total}"
            )

        def set_above_label(text: str, dest_name: str, win: ProgressbarWin):
            win.above_label.setText(
                f"\"{text}\" {Lng.in_[Cfg.lng]} \"{dest_name}\""
            )

        def copy_files_fin(files: list, dest: str, main_folder: MainFolder):
            if not files:
                return

            task = CustomScanerTask(main_folder, [dest, ])
            task.sigs.progress_text.connect(
                self.bar_bottom.progress_bar.setText
            )
            task.sigs.finished_.connect(
                self.reload_gui
            )
            UThreadPool.start(task)

        def copy_files_start(data: tuple):
            main_folder, dest = data
            dest_name = os.path.basename(dest)
            progress_win = ProgressbarWin(Lng.copying[Cfg.lng])
            progress_win.progressbar.setMaximum(100)
            progress_win.center_to_parent(self)
            progress_win.show()
            task = CopyFilesTask(dest, img_paths)
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
                lambda files: copy_files_fin(files, dest, main_folder)
            )
            task.sigs.finished_.connect(
                progress_win.deleteLater
            )
            UThreadPool.start(task)

        if MainFolder.current.get_curr_path():
            self.win_upload = WinUpload()
            self.win_upload.clicked.connect(lambda data: copy_files_start(data))
            self.win_upload.no_connection.connect(self.open_win_smb)
            self.win_upload.center_to_parent(self.window())
            self.win_upload.show()
        else:
            self.open_win_smb()

    def open_settings(self, settings_item: SettingsItem):
        self.bar_top.settings_btn.set_solid_style()
        self.win_settings = WinSettings(settings_item)
        self.win_settings.closed.connect(self.bar_top.settings_btn.set_normal_style)
        self.win_settings.reset_data.connect(self.reset_data_cmd)
        self.win_settings.center_to_parent(self.window())
        self.win_settings.show()

    def closeEvent(self, a0: QCloseEvent | None) -> None:
        self.hide()
        a0.ignore()
    
    def keyPressEvent(self, a0: QKeyEvent | None) -> None:
        
        if a0.key() == Qt.Key.Key_V:
            self.paste_files_here()
        
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

        img_paths: list[str] = [
            i.toLocalFile()
            for i in a0.mimeData().urls()
            # if os.path.isfile(i.toLocalFile())
        ]

        for i in img_paths:
            if os.path.isdir(i):
                self.win_warn = WinWarn(Lng.attention[Cfg.lng], Lng.drop_only_files[Cfg.lng])
                self.win_warn.adjustSize()
                self.win_warn.center_to_parent(self)
                self.win_warn.show()
                return

        if img_paths:
            self.upload_files(img_paths)

        return super().dropEvent(a0)