import json
import os

from PyQt5.QtCore import Qt, QTimer
from PyQt5.QtGui import QCloseEvent, QKeyEvent
from PyQt5.QtWidgets import (QDesktopWidget, QFrame, QPushButton, QSplitter,
                             QVBoxLayout, QWidget)

from cfg import Dynamic, JsonData, Static, ThumbData
from system.filters import UserFilter, UserFilterErrors
from system.lang import Lang
from system.main_folder import MainFolder, MainFolderErrors
from system.tasks import (CopyFilesTask, MainUtils, MoveFilesTask,
                          RemoveFilesTask, ScanerTask, UploadFilesTask)
from system.utils import UThreadPool

from ._base_widgets import UHBoxLayout, UMainWindow, UVBoxLayout
from .bar_bottom import BarBottom
from .bar_macos import BarMacos
from .bar_top import BarTop
from .grid import Grid
from .menu_left import MenuLeft
from .win_dates import WinDates
from .win_downloads import WinDownloads
from .win_remove_files import RemoveFilesWin
from .win_upload import WinUpload
from .win_warn import WinError, WinWarn


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

    def __init__(self, argv: list[str]):
        super().__init__()
        self.setAcceptDrops(True)
        self.resize(Dynamic.root_g["aw"], Dynamic.root_g["ah"])
        self.setMinimumWidth(750)
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
        right_lay.addWidget(self.grid)

        sep_bottom = USep()
        right_lay.addWidget(sep_bottom)

        self.bar_bottom = BarBottom()
        self.bar_bottom.reload_thumbnails.connect(lambda: self.grid.reload_thumbnails())
        self.bar_bottom.theme_changed.connect(self.grid.reload_rubber)
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
        self.scaner_task: ScanerTask | None = None
        self.scaner_task_canceled = False

        if argv[-1] != self.argv_flag:
            self.start_scaner_task()

        QTimer.singleShot(100, self.check_connection)
        QTimer.singleShot(200, self.check_main_folders)
        QTimer.singleShot(300, self.check_user_filters)
            
    def check_connection(self):
        main_folder = MainFolder.current.is_available()
        if not main_folder:
            self.win_warn = WinWarn(Lang.no_connection, Lang.no_connection_descr)
            self.win_warn.center_relative_parent(self)
            self.win_warn.show()

    def check_main_folders(self):
        if MainFolderErrors.list_:
            text = "\n".join(
                json.dumps(i, indent=4, ensure_ascii=False)
                for i in MainFolderErrors.list_
            )
            title = f"{Lang.read_file_error} main_folder.json\n"
            text = "\n".join((title, text))

            self.win_folder_error = WinError(Lang.error, text)
            self.win_folder_error.center_relative_parent(self)
            self.win_folder_error.show()

    def check_user_filters(self):
        if UserFilterErrors.list_:
            text = "\n".join(
                json.dumps(i, indent=4, ensure_ascii=False)
                for i in UserFilterErrors.list_
            )
            title = f"{Lang.read_file_error} user_filters.json\n"
            text = "\n".join((title, text))

            self.win_filter_error = WinError(Lang.error, text)
            self.win_filter_error.center_relative_parent(self)
            self.win_filter_error.show()

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
        if self.scaner_task is None:
            self.scaner_task = ScanerTask()
            self.scaner_task.signals_.finished_.connect(self.on_scaner_finished)
            self.scaner_task.signals_.progress_text.connect(lambda text: self.bar_bottom.progress_bar.setText(text))
            self.scaner_task.signals_.reload_gui.connect(lambda: self.grid.reload_thumbnails())
            self.scaner_task.signals_.reload_gui.connect(lambda: self.left_menu.init_ui())
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
        # если задача не закончена, прерываем ее
        if not self.scaner_task.task_state.finished():
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
            t = Lang.all_colls
        elif Dynamic.curr_coll_name == Static.NAME_FAVS:
            t = Lang.fav_coll
        else:
            t = Dynamic.curr_coll_name
        if Dynamic.resents:
            t = Lang.recents
        t = f"{main_folder}: {t}"
        self.setWindowTitle(t)

    def center(self):
        screen = QDesktopWidget().screenGeometry()
        size = self.geometry()
        x = (screen.width() - size.width()) // 2
        y = (screen.height() - size.height()) // 2
        self.move(x, y)

    def on_exit(self):
        for i in UThreadPool.tasks:
            i.task_state.set_should_run(False)
        JsonData.write_json_data()
        MainFolder.write_json_data()
        UserFilter.write_json_data()

    def open_dates_win(self):
        self.win_dates = WinDates()
        self.win_dates.center_relative_parent(self)
        self.win_dates.dates_btn_solid.connect(lambda: self.bar_top.dates_btn.set_solid_style())
        self.win_dates.dates_btn_normal.connect(lambda: self.bar_top.dates_btn.set_normal_style())
        self.win_dates.reload_thumbnails.connect(lambda: self.grid.reload_thumbnails())
        self.win_dates.scroll_to_top.connect(lambda: self.grid.scroll_to_top())
        self.win_dates.show()

    def open_warn_win(self, title: str, text: str):
        self.win_warn = WinWarn(title, text)
        self.win_warn.adjustSize()
        self.win_warn.center_relative_parent(self)
        self.win_warn.show()

    def open_filemove_win(self, rel_img_path_list: list):
        main_folder_path = MainFolder.current.is_available()
        if main_folder_path:
            img_path_list = [
                MainUtils.get_img_path(main_folder_path, i)
                for i in rel_img_path_list
            ]
            self.upload_win = WinUpload()
            self.upload_win.center_relative_parent(self.window())
            cmd = lambda dest: self.filemove_task_start(dest, img_path_list)
            self.upload_win.finished_.connect(cmd)
            self.upload_win.show()
        else:
            self.open_warn_win(Lang.no_connection, Lang.no_connection_descr)

    def filemove_task_start(self, dest: str, img_path_list: list):
        task = MoveFilesTask(dest, img_path_list)
        task.reload_gui.connect(lambda: self.grid.reload_thumbnails())
        task.set_progress_text.connect(lambda text: self.bar_bottom.progress_bar.setText(text))
        task.run()

    def open_remove_files_win(self, rel_img_path_list: list):
        main_folder_path = MainFolder.current.is_available()
        if main_folder_path:
            img_path_list = [
                MainUtils.get_img_path(main_folder_path, i)
                for i in rel_img_path_list
            ]
            self.remove_files_win = RemoveFilesWin(img_path_list)
            self.remove_files_win.center_relative_parent(self.window())
            self.remove_files_win.finished_.connect(lambda: self.remove_task_start(img_path_list))
            self.remove_files_win.show()
        else:
            self.open_warn_win(Lang.no_connection, Lang.no_connection_descr)
    
    def remove_task_start(self, img_path_list: list[str]):
        remove_files_task = RemoveFilesTask(img_path_list)
        remove_files_task.signals_.progress_text.connect(lambda text: self.bar_bottom.progress_bar.setText(text))
        remove_files_task.signals_.reload_gui.connect(lambda: self.grid.reload_thumbnails())
        UThreadPool.start(remove_files_task)

    def open_upload_win(self, img_path_list: list):
        main_folder_path = MainFolder.current.is_available()
        if main_folder_path:
            self.upload_win = WinUpload()
            self.upload_win.finished_.connect(lambda dest: self.upload_task_start(dest, img_path_list))
            self.upload_win.center_relative_parent(self)
            self.upload_win.show()
        else:
            self.open_warn_win(Lang.no_connection, Lang.no_connection_descr)

    def upload_task_start(self, dest: str, img_path_list: list[str]):
        copy_files_task = CopyFilesTask(dest, img_path_list)
        cmd = lambda img_path_list: self.upload_task_finished(img_path_list)
        copy_files_task.signals_.finished_.connect(cmd)
        UThreadPool.start(copy_files_task)
        self.open_downloads_win()

    def upload_task_finished(self, img_path_list: list[str]):
        upload_files_task = UploadFilesTask(img_path_list)
        upload_files_task.signals_.progress_text.connect(lambda text: self.bar_bottom.progress_bar.setText(text))
        upload_files_task.signals_.reload_gui.connect(lambda: self.grid.reload_thumbnails())
        UThreadPool.start(upload_files_task)

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
        main_folder_path = MainFolder.current.is_available()
        if not main_folder_path:
            self.open_warn_win(Lang.no_connection, Lang.no_connection_descr)
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