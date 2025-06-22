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
from utils.tasks import (CopyFilesTask, MainUtils, RemoveFilesTask, ScanerTask,
                         UploadFilesTask)

from .bar_bottom import BarBottom
from .bar_macos import BarMacos
from .bar_top import BarTop
from .grid.grid import Grid
from .menu_left import MenuLeft
from .win_remove_files import RemoveFilesWin
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
        self.grid.remove_files.connect(lambda rel_img_path_list: self.open_remove_files_win(rel_img_path_list))
        self.grid.move_files.connect(lambda rel_img_path_list: self.open_filemove_win(rel_img_path_list))
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
        if not self.scaner_task.task_state.finished():
            # если задача не закончена, прерываем ее
            self.scaner_task.task_state.set_should_run(False)
            # ставим флаг,чтобы on_scaner_finished запустил короткий таймер
            # прерванная задача завершится и запустит короткий таймер
            self.scaner_task_canceled = True
        else:
            # если задача закончена, значит стоит долгий таймер
            self.scaner_timer.stop()
            # если задача закончена, немедленно запускаем новый сканер
            self.scaner_timer.start(1000)

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

    def open_filemove_win(self, rel_img_path_list: list):
        main_folder_path = MainFolder.current.is_available()
        if main_folder_path:
            img_path_list = [
                MainUtils.get_img_path(main_folder_path, i)
                for i in rel_img_path_list
            ]
            filemove_win = WinUpload()
            filemove_win.center_relative_parent(self.window())
            cmd = lambda dest: self.filemove_task_start(dest, img_path_list)
            filemove_win.finished_.connect(cmd)
            filemove_win.show()
        else:
            self.open_smb_win()

    def filemove_task_start(self, dest: str, img_path_list: list):
        # файлы будут скопированы в папку назначения и удалены из исходной папки
        is_movefiles = True
        copy_task = CopyFilesTask(dest, img_path_list, is_movefiles)
        cmd = lambda new_img_path_list: self.filemove_task_fin(img_path_list, new_img_path_list)
        copy_task.signals_.finished_.connect(cmd)
        UThreadPool.start(copy_task)
        
    def filemove_task_fin(self, img_path_list: list, new_img_path_list: list):
        remove_task = RemoveFilesTask(img_path_list)
        cmd = lambda: self.filemove_task_fin_sec(new_img_path_list)
        remove_task.signals_.finished_.connect(cmd)
        remove_task.signals_.progress_text.connect(lambda text: self.set_progress_text(text))
        remove_task.signals_.reload_gui.connect(lambda: self.reload_gui())
        UThreadPool.start(remove_task)

    def filemove_task_fin_sec(self, new_img_path_list: list):
        upload_task = UploadFilesTask(new_img_path_list)
        upload_task.signals_.progress_text.connect(lambda text: self.set_progress_text(text))
        upload_task.signals_.reload_gui.connect(lambda: self.reload_gui())
        UThreadPool.start(upload_task)

    def open_remove_files_win(self, rel_img_path_list: list):
        main_folder_path = MainFolder.current.is_available()
        if main_folder_path:
            img_path_list = [
                MainUtils.get_img_path(main_folder_path, i)
                for i in rel_img_path_list
            ]
            rem_win = RemoveFilesWin(img_path_list)
            rem_win.center_relative_parent(self.window())
            rem_win.finished_.connect(lambda: self.remove_task_start(img_path_list))
            rem_win.show()
        else:
            self.open_smb_win()
    
    def remove_task_start(self, img_path_list: list[str]):
        remove_files_task = RemoveFilesTask(img_path_list)
        remove_files_task.signals_.progress_text.connect(lambda text: self.set_progress_text(text))
        remove_files_task.signals_.reload_gui.connect(lambda: self.reload_gui())
        UThreadPool.start(remove_files_task)

    def ope_upload_win(self, img_path_list: list):
        main_folder_path = MainFolder.current.is_available()
        if main_folder_path:
            win_upload = WinUpload()
            win_upload.finished_.connect(lambda dest: self.upload_task_start(dest, img_path_list))
            win_upload.center_relative_parent(self)
            win_upload.show()
        else:
            self.open_smb_win()

    def upload_task_start(self, dest: str, img_path_list: list[str]):
        copy_files_task = CopyFilesTask(dest, img_path_list, False)
        cmd = lambda img_path_list: self.upload_task_finished(img_path_list)
        copy_files_task.signals_.finished_.connect(cmd)
        UThreadPool.start(copy_files_task)

    def upload_task_finished(self, img_path_list: list[str]):
        upload_files_task = UploadFilesTask(img_path_list)
        upload_files_task.signals_.progress_text.connect(lambda text: self.set_progress_text(text))
        upload_files_task.signals_.reload_gui.connect(lambda: self.reload_gui())
        UThreadPool.start(upload_files_task)

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

        self.ope_upload_win(img_path_list)

        return super().dropEvent(a0)