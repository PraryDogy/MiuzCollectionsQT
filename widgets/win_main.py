import gc
import os

from PyQt5.QtCore import Qt, QTimer
from PyQt5.QtGui import QCloseEvent, QKeyEvent
from PyQt5.QtWidgets import (QDesktopWidget, QFrame, QPushButton, QSplitter,
                             QVBoxLayout, QWidget)

from cfg import Dynamic, JsonData, Static, ThumbData
from system.filters import UserFilter
from system.lang import Lang
from system.main_folder import MainFolder
from system.tasks import (CopyFilesTask, MainUtils, MoveFilesTask,
                          RemoveFilesTask, ScanSingleDirTask)
from system.utils import UThreadPool

from ._base_widgets import UHBoxLayout, UMainWindow, UVBoxLayout
from .bar_bottom import BarBottom
from .bar_macos import BarMacos
from .bar_top import BarTop
from .grid import Grid
from .menu_left import MenuLeft
from .win_dates import WinDates
from .win_downloads import WinDownloads
from .win_image_view import WinImageView
from .win_remove_files import RemoveFilesWin
from .win_upload import WinUpload
from .win_warn import WinSmb, WinWarn


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
    lang = (
        ("Все коллекции", "All collections"),
        ("Избранное", "Favorites"),
    )

    def __init__(self, argv: list[str]):
        super().__init__()
        self.resize(self.ww, self.hh)
        self.setMinimumWidth(self.min_w)

        self.setAcceptDrops(True)
        self.setMenuBar(BarMacos())
        self.set_window_title()

        h_wid_main = QWidget()
        h_lay_main = UHBoxLayout()
        h_lay_main.setContentsMargins(0, 0, 5, 0)
        h_wid_main.setLayout(h_lay_main)
        self.central_layout.addWidget(h_wid_main)

        # Создаем QSplitter
        splitter = QSplitter(Qt.Horizontal)

        # Левый виджет (MenuLeft)
        self.left_menu = MenuLeft()
        self.left_menu.set_window_title.connect(lambda: self.set_window_title())
        self.left_menu.reload_thumbnails.connect(lambda: self.grid.reload_thumbnails())
        self.left_menu.scroll_to_top.connect(lambda: self.grid.scroll_to_top())
        splitter.addWidget(self.left_menu)

        # Правый виджет
        right_wid = QWidget()
        splitter.addWidget(right_wid)
        right_lay = UVBoxLayout()
        right_lay.setContentsMargins(0, 0, 0, 0)
        right_wid.setLayout(right_lay)

        # Добавляем элементы в правую панель
        self.bar_top = BarTop()
        self.bar_top.open_dates_win.connect(lambda: self.open_dates_win())
        self.bar_top.reload_thumbnails.connect(lambda: self.grid.reload_thumbnails())
        self.bar_top.scroll_to_top.connect(lambda: self.grid.scroll_to_top())
        right_lay.addWidget(self.bar_top)

        sep_upper = USep()
        right_lay.addWidget(sep_upper)

        self.grid = Grid()
        self.grid.restart_scaner.connect(lambda: self.restart_scaner_task())
        self.grid.remove_files.connect(lambda rel_img_path_list: self.open_remove_files_win(rel_img_path_list))
        self.grid.move_files.connect(lambda rel_img_path_list: self.open_filemove_win(rel_img_path_list))
        self.grid.save_files.connect(lambda data: self.save_files_task(*data))
        self.grid.update_bottom_bar.connect(lambda: self.bar_bottom.toggle_types())
        self.grid.img_view.connect(lambda: self.open_img_view())
        right_lay.addWidget(self.grid)

        sep_bottom = USep()
        right_lay.addWidget(sep_bottom)

        self.bar_bottom = BarBottom()
        self.bar_bottom.reload_thumbnails.connect(lambda: self.grid.reload_thumbnails())
        self.bar_bottom.theme_changed.connect(self.reload_rubber)
        self.bar_bottom.resize_thumbnails.connect(lambda: self.grid.resize_thumbnails())
        right_lay.addWidget(self.bar_bottom)

        # Добавляем splitter в основной layout
        h_lay_main.addWidget(splitter)

        splitter.setStretchFactor(0, 0)
        splitter.setStretchFactor(1, 1)
        splitter.setSizes([Static.MENU_LEFT_WIDTH, self.width() - Static.MENU_LEFT_WIDTH])

        self.grid.setFocus()

        self.scaner_timer = QTimer(self)
        self.scaner_timer.setSingleShot(True)
        self.scaner_timer.timeout.connect(self.start_scaner_task)
        self.scaner_task = None
        self.scaner_task_canceled = False

        QTimer.singleShot(100, self.main_folder_check)

        if argv[-1] != self.argv_flag:
            self.start_scaner_task()

    def open_img_view(self):
        if len(self.grid.selected_widgets) == 1:
            path_to_wid = self.grid.path_to_wid.copy()
            is_selection = False
        else:
            path_to_wid = {i.rel_img_path: i for i in self.grid.selected_widgets}
            is_selection = True
        wid = self.grid.selected_widgets[-1]
        self.win_image_view = WinImageView(wid.rel_img_path, path_to_wid, is_selection)
        self.win_image_view.closed_.connect(lambda: self.closed_img_view())
        self.win_image_view.switch_image_sig.connect(lambda img_path: self.grid.select_viewed_image(img_path))
        self.win_image_view.center_relative_parent(self.window())
        self.win_image_view.show()
    
    def closed_img_view(self):
        del self.win_image_view
        gc.collect()

    def reload_rubber(self):
        self.grid.rubberBand.deleteLater()
        self.grid.load_rubber()

    def main_folder_check(self):
        main_folder = MainFolder.current.availability()
        if not main_folder:
            self.win_warn = WinSmb()
            self.win_warn.center_relative_parent(self)
            self.win_warn.show()

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

        if JsonData.new_scaner:
            from system.new_scaner.scaner_task import ScanerTask
        else:
            from system.old_scaner.scaner_task import ScanerTask

        if self.scaner_task is None:
            self.scaner_task = ScanerTask()
            self.scaner_task.sigs.finished_.connect(self.on_scaner_finished)
            self.scaner_task.sigs.progress_text.connect(lambda text: self.bar_bottom.progress_bar.setText(text))
            self.scaner_task.sigs.reload_gui.connect(lambda: self.grid.reload_thumbnails())
            self.scaner_task.sigs.reload_gui.connect(lambda: self.left_menu.init_ui())
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
            self.scaner_timer.start(JsonData.scaner_minutes * 60 * 1000)

    def restart_scaner_task(self):
        """
        Прерывает текущую задачу сканирования и инициирует её перезапуск.

        Если текущая задача ещё не завершена, устанавливается флаг отмены (self.scaner_task_canceled = True),
        и флаг состояния задачи переводится в "не должно выполняться" с помощью set_should_run(False).
        После завершения текущей задачи метод on_scaner_finished запустит короткий таймер.

        Если задача уже завершена, активный таймер останавливается, и запускается короткий таймер на 1 секунду
        для немедленного запуска новой задачи сканирования.
        """
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
        main_folder = MainFolder.current.name.capitalize()
        if Dynamic.curr_coll_name == Static.NAME_ALL_COLLS:
            t = self.lang[0][JsonData.lang]
        elif Dynamic.curr_coll_name == Static.NAME_FAVS:
            t = self.lang[1][JsonData.lang]
        elif Dynamic.curr_coll_name == Static.NAME_RECENTS:
            t = Lang.recents
        else:
            t = Dynamic.curr_coll_name
        t = f"{main_folder}: {t}"
        self.setWindowTitle(t)

    def center(self):
        screen = QDesktopWidget().screenGeometry()
        size = self.geometry()
        x = (screen.width() - size.width()) // 2
        y = (screen.height() - size.height()) // 2
        self.move(x, y)

    def on_exit(self):
        JsonData.write_json_data()
        MainFolder.write_json_data()
        UserFilter.write_json_data()
        os._exit(0)

    def open_dates_win(self):
        self.win_dates = WinDates()
        self.win_dates.center_relative_parent(self)
        self.win_dates.dates_btn_solid.connect(lambda: self.bar_top.dates_btn.set_solid_style())
        self.win_dates.dates_btn_normal.connect(lambda: self.bar_top.dates_btn.set_normal_style())
        self.win_dates.reload_thumbnails.connect(lambda: self.grid.reload_thumbnails())
        self.win_dates.scroll_to_top.connect(lambda: self.grid.scroll_to_top())
        self.win_dates.show()

    def open_warn_win(self, title: str, text: str, restart_app: bool = False):
        self.win_warn = WinWarn(title, text)
        self.win_warn.adjustSize()
        self.win_warn.center_relative_parent(self)
        self.win_warn.show()

    def open_filemove_win(self, rel_img_path_list: list):

        def move_files_task(data: tuple[str, MainFolder], img_path_list: list):
            print(data, img_path_list)
            return
            dest, main_folder = data
            self.move_files_task = MoveFilesTask(main_folder, dest, img_path_list)
            # self.move_files_task.reload_gui.connect(lambda: self.grid.reload_thumbnails())
            # self.move_files_task.set_progress_text.connect(lambda text: self.bar_bottom.progress_bar.setText(text))
            # self.move_files_task.run()

        main_folder_path = MainFolder.current.availability()
        if main_folder_path:
            img_path_list = [
                MainUtils.get_abs_path(main_folder_path, i)
                for i in rel_img_path_list
            ]
            self.win_upload = WinUpload()
            self.win_upload.clicked.connect(lambda data: move_files_task(data, img_path_list))
            self.win_upload.center_relative_parent(self.window())
            self.win_upload.show()
        else:
            self.win_smb = WinSmb()
            self.win_smb.center_relative_parent(self.window())
            self.win_smb.show()

    def open_remove_files_win(self, rel_img_path_list: list):
        main_folder_path = MainFolder.current.availability()
        if main_folder_path:
            img_path_list = [
                MainUtils.get_abs_path(main_folder_path, i)
                for i in rel_img_path_list
            ]
            self.remove_files_win = RemoveFilesWin(img_path_list)
            self.remove_files_win.center_relative_parent(self.window())
            self.remove_files_win.finished_.connect(lambda: self.remove_task_start(img_path_list))
            self.remove_files_win.show()
        else:
            self.win_smb = WinSmb()
            self.win_smb.center_relative_parent(self.window())
            self.win_smb.show()
    
    def remove_task_start(self, img_path_list: list[str]):
        remove_files_task = RemoveFilesTask(img_path_list)
        remove_files_task.signals_.progress_text.connect(lambda text: self.bar_bottom.progress_bar.setText(text))
        remove_files_task.signals_.reload_gui.connect(lambda: self.grid.reload_thumbnails())
        UThreadPool.start(remove_files_task)

    def open_upload_win(self, img_path_list: list):

        def cmd(data):
            try:
                self.win_upload.deleteLater()
            except Exception:
                ...
            self.upload_task_start(data, img_path_list)

        self.win_upload = WinUpload()
        self.win_upload.clicked.connect(cmd)
        self.win_upload.center_relative_parent(self.window())
        self.win_upload.show()

    def upload_task_start(self, data: tuple[MainFolder, str], img_path_list: list[str]):
        main_folder, dest = data
        copy_files_task = CopyFilesTask(dest, img_path_list)
        cmd = lambda img_path_list: self.upload_task_finished(main_folder, img_path_list)
        copy_files_task.signals_.finished_.connect(cmd)
        UThreadPool.start(copy_files_task)
        self.open_downloads_win()

    def upload_task_finished(self, main_folder: MainFolder, img_path_list: list[str]):
        try:
            self.win_downloads.deleteLater()
        except Exception:
            ...
        if img_path_list:
            scan_dir = os.path.dirname(img_path_list[0])
            self.single_dir_task = ScanSingleDirTask(main_folder, scan_dir)
            self.single_dir_task.sigs.progress_text.connect(self.bar_bottom.progress_bar.setText)
            self.single_dir_task.sigs.reload_thumbnails.connect(self.grid.reload_thumbnails)
            self.single_dir_task.sigs.reload_thumbnails.connect(self.reload_rubber)
            UThreadPool.start(self.single_dir_task)

    def save_files_task(self, dest: str, img_path_list: list):
        copy_files_task = CopyFilesTask(dest, img_path_list)
        UThreadPool.start(copy_files_task)
        self.open_downloads_win()

    def open_downloads_win(self):
        self.win_downloads = WinDownloads()
        self.win_downloads.center_relative_parent(self)
        self.win_downloads.show()

    def closeEvent(self, a0: QCloseEvent | None) -> None:
        self.hide()
        a0.ignore()
    
    def keyPressEvent(self, a0: QKeyEvent | None) -> None:
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
                if Dynamic.thumb_size_ind < len(ThumbData.PIXMAP_SIZE) - 1:
                    Dynamic.thumb_size_ind += 1
                    self.bar_bottom.slider.move_(Dynamic.thumb_size_ind)

        elif a0.key() == Qt.Key.Key_Minus:
            if a0.modifiers() == Qt.KeyboardModifier.ControlModifier:
                if Dynamic.thumb_size_ind > 0:
                    Dynamic.thumb_size_ind -= 1
                    self.bar_bottom.slider.move_(Dynamic.thumb_size_ind)

    def dragEnterEvent(self, a0):
        a0.acceptProposedAction()
        return super().dragEnterEvent(a0)
    
    def dropEvent(self, a0):

        if not a0.mimeData().hasUrls() or a0.source() is not None:
            return
        main_folder_path = MainFolder.current.availability()
        if not main_folder_path:
            self.win_smb = WinSmb()
            self.win_smb.center_relative_parent(self.window())
            self.win_smb.show()
            return

        img_path_list: list[str] = [
            i.toLocalFile()
            for i in a0.mimeData().urls()
            # if os.path.isfile(i.toLocalFile())
        ]

        for i in img_path_list:
            if os.path.isdir(i):
                self.open_warn_win(Lang.attention, Lang.drop_only_files)
                return

        if img_path_list:
            self.open_upload_win(img_path_list)

        return super().dropEvent(a0)