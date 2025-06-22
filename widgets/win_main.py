import os
from typing import Literal

from PyQt5.QtCore import Qt, QTimer
from PyQt5.QtGui import QCloseEvent, QKeyEvent
from PyQt5.QtWidgets import (QDesktopWidget, QFrame, QPushButton, QSplitter,
                             QVBoxLayout, QWidget)

from base_widgets import LayoutHor, LayoutVer
from base_widgets.wins import WinFrameless
from cfg import Dynamic, JsonData, Static, ThumbData
from lang import Lang
from main_folder import MainFolder
from signals import SignalsApp
from utils.main import UThreadPool
from utils.tasks import (CopyFilesTask, RemoveFilesTask, ScanerTask,
                         UploadFilesTask)

from .bar_bottom import BarBottom
from .bar_macos import BarMacos
from .bar_top import BarTop
from .grid.grid import Grid
from .menu_left import MenuLeft
from .win_smb import WinSmb
from .win_upload import WinUpload


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


class WinMain(WinFrameless):
    argv_flag = "noscan"

    def __init__(self, argv: list[str]):
        super().__init__()
        self.setAcceptDrops(True)
        self.resize(Dynamic.root_g["aw"], Dynamic.root_g["ah"])
        self.setMinimumWidth(750)
        self.setMenuBar(BarMacos())

        h_wid_main = QWidget()
        h_lay_main = LayoutHor()
        h_lay_main.setContentsMargins(0, 0, 5, 0)
        h_wid_main.setLayout(h_lay_main)
        self.central_layout.addWidget(h_wid_main)

        # Создаем QSplitter
        splitter = QSplitter(Qt.Horizontal)

        # Левый виджет (MenuLeft)
        left_wid = MenuLeft()
        splitter.addWidget(left_wid)

        # Правый виджет
        right_wid = QWidget()
        splitter.addWidget(right_wid)
        right_lay = LayoutVer()
        right_lay.setContentsMargins(0, 0, 0, 0)
        right_wid.setLayout(right_lay)

        # Добавляем элементы в правую панель
        self.bar_top = BarTop()
        right_lay.addWidget(self.bar_top)

        sep_upper = USep()
        right_lay.addWidget(sep_upper)

        self.grid = Grid()
        self.grid.restart_scaner.connect(lambda: self.restart_scaner_task())
        self.grid.remove_files.connect(lambda img_path_list: self.remove_task_cmd(img_path_list))
        right_lay.addWidget(self.grid)

        sep_bottom = USep()
        right_lay.addWidget(sep_bottom)

        self.bar_bottom = BarBottom()
        self.bar_bottom.theme_changed.connect(self.grid.reload_rubber)
        right_lay.addWidget(self.bar_bottom)

        # Добавляем splitter в основной layout
        h_lay_main.addWidget(splitter)

        splitter.setStretchFactor(0, 0)
        splitter.setStretchFactor(1, 1)
        splitter.setSizes([Static.MENU_LEFT_WIDTH, self.width() - Static.MENU_LEFT_WIDTH])

        self.grid.setFocus()

        SignalsApp.instance.win_main_cmd.connect(self.win_main_cmd)
        SignalsApp.instance.win_main_cmd.emit("set_title")

        self.scaner_timer = QTimer(self)
        self.scaner_timer.setSingleShot(True)
        self.scaner_timer.timeout.connect(self.start_scaner_task)
        self.scaner_task: ScanerTask | None = None
        self.scaner_task_canceled = False

        if argv[-1] != self.argv_flag:
            self.start_scaner_task()

    def start_scaner_task(self):
        """
        Логика работы сканера:

        1. Первый запуск или завершён предыдущий:
        - Если self.scaner_task == None:
            - Создаётся новый ScanerTask.
            - Подключается слот on_scaner_finished к сигналу завершения задачи.
            - Задача запускается в пуле потоков.
        
        2. Повторный запуск после завершения:
        - Если задача завершена (self.scaner_task.is_finished()):
            - self.scaner_task сбрасывается в None.
            - Метод вызывается повторно, что приведёт к пункту 1.
        
        3. Задача ещё выполняется:
        - Используется QTimer.singleShot(3000, ...) для повторной проверки
            через 3 секунды (без создания конфликта с основным таймером).
        """

        if self.scaner_task is None:
            self.scaner_task = ScanerTask()
            self.scaner_task.signals_.finished_.connect(self.on_scaner_finished)
            self.scaner_task.signals_.progress_text.connect(lambda text: self.set_progress_text(text))
            self.scaner_task.signals_.reload_gui.connect(lambda: self.reload_gui())
            UThreadPool.start(self.scaner_task)

        elif self.scaner_task.task_state.finished():
            self.scaner_task = None
            self.start_scaner_task()

        else:
            QTimer.singleShot(3000, self.start_scaner_task)

    def on_scaner_finished(self):
        """
        Обработка завершения задачи сканера.

        - Если задача была отменена через restart_scaner_task (флаг scaner_task_canceled == True):
        - Сбрасывает флаг.
        - Запускает таймер self.scaner_timer с короткой задержкой (1 секунда) для немедленного 
            повторного запуска сканера.

        - Если задача завершилась штатно:
        - Запускает таймер self.scaner_timer на заданное пользователем время (scaner_minutes),
            после которого будет запущен следующий цикл сканирования.
        """
        if self.scaner_task_canceled:
            self.scaner_task_canceled = False
            self.scaner_timer.start(1000)
        else:
            self.scaner_timer.start(JsonData.scaner_minutes * 60 * 1000)

    def restart_scaner_task(self):
        """
        Прерывает текущую задачу сканера (если есть) и подготавливает её к немедленному
        повторному запуску.

        - Устанавливает флаг scaner_task_canceled в True, чтобы on_scaner_finished запустил таймер
        с минимальной задержкой.
        - Вызывает cancel() текущей задачи, чтобы прервать её выполнение.
        - Если основной таймер self.scaner_timer уже запущен, останавливает его, чтобы избежать
        нежелательной задержки перед следующим запуском.
        """
        if self.scaner_task:
            self.scaner_task_canceled = True
            self.scaner_task.task_state.set_should_run(False)
        
        if self.scaner_timer.isActive():
            self.scaner_timer.stop()

        # флаг finished у сканера не срабатывает, поэтому немедленно вызываем
        # старт сканера
        self.start_scaner_task()
    
    def win_main_cmd(self, flag: Literal["show", "exit", "set_title"]):
        if flag == "show":
            self.show()
        elif flag == "exit":
            self.on_exit()
        elif flag == "set_title":
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
        else: 
            raise Exception("app > win main > wrong flag", flag)

    def center(self):
        screen = QDesktopWidget().screenGeometry()
        size = self.geometry()
        x = (screen.width() - size.width()) // 2
        y = (screen.height() - size.height()) // 2
        self.move(x, y)
    
    def hide_(self, *args):
        self.hide()

    def set_progress_text(self, text: str):
        self.bar_bottom.progress_bar.setText(text)

    def reload_gui(self):
        self.grid.signals_cmd("reload")

    def on_exit(self):
        for i in UThreadPool.tasks:
            i.task_state.set_should_run(False)
        JsonData.write_json_data()

    def open_smb_win(self):
        self.smb_win = WinSmb()
        self.smb_win.adjustSize()
        self.smb_win.center_relative_parent(self)
        self.smb_win.show()

    def upload_task_cmd(self, dest: str, img_path_list: list[str]):
        copy_files_task = CopyFilesTask(dest, img_path_list, False)
        cmd = lambda img_path_list: self.upload_task_finished(img_path_list)
        copy_files_task.signals_.finished_.connect(cmd)
        UThreadPool.start(copy_files_task)

    def upload_task_finished(self, img_path_list: list[str]):
        upload_files_task = UploadFilesTask(img_path_list)
        upload_files_task.signals_.progress_text.connect(lambda text: self.set_progress_text(text))
        upload_files_task.signals_.reload_gui.connect(lambda: self.reload_gui())
        UThreadPool.start(upload_files_task)
    
    def remove_task_cmd(self, img_path_list: list[str]):
        remove_files_task = RemoveFilesTask(img_path_list)
        remove_files_task.signals_.progress_text.connect(lambda text: self.set_progress_text(text))
        remove_files_task.signals_.reload_gui.connect(lambda: self.reload_gui())
        UThreadPool.start(remove_files_task)

    def closeEvent(self, a0: QCloseEvent | None) -> None:
        self.hide()
        a0.ignore()
    
    def keyPressEvent(self, a0: QKeyEvent | None) -> None:
        if a0.key() == Qt.Key.Key_W:
            if a0.modifiers() == Qt.KeyboardModifier.ControlModifier:
                self.hide_(a0)

        elif a0.key() == Qt.Key.Key_F:
            if a0.modifiers() == Qt.KeyboardModifier.ControlModifier:
                SignalsApp.instance.wid_search_cmd.emit("focus")

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
                    SignalsApp.instance.slider_change_value.emit(Dynamic.thumb_size_ind)

        elif a0.key() == Qt.Key.Key_Minus:
            if a0.modifiers() == Qt.KeyboardModifier.ControlModifier:
                if Dynamic.thumb_size_ind > 0:
                    Dynamic.thumb_size_ind -= 1
                    SignalsApp.instance.slider_change_value.emit(Dynamic.thumb_size_ind)

    def dragEnterEvent(self, a0):
        a0.acceptProposedAction()
        return super().dragEnterEvent(a0)
    
    def dropEvent(self, a0):

        if not a0.mimeData().hasUrls() or a0.source() is not None:
            return
        main_folder_path = MainFolder.current.is_available()
        if not main_folder_path:
            self.open_smb_win()
            return

        img_path_list: list[str] = [
            i.toLocalFile()
            for i in a0.mimeData().urls()
            if os.path.isfile(i.toLocalFile())
        ]

        self.win_upload = WinUpload()
        self.win_upload.finished_.connect(lambda dest: self.upload_task_cmd(dest, img_path_list))
        self.win_upload.center_relative_parent(self)
        self.win_upload.show()

        return super().dropEvent(a0)