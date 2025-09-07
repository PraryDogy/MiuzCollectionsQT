import gc
from time import sleep

from PyQt5.QtCore import QObject, QTimer, pyqtSignal

from cfg import Cfg

from ..database import Dbase
from ..lang import Lng
from ..main_folder import MainFolder
from ..utils import URunnable
from .scaner_utils import (DbUpdater, DirsCompator, DirsLoader, DirsUpdater,
                           HashdirUpdater, ImgCompator, ImgLoader, Inspector,
                           MainFolderRemover, ImgRemover)


class ScanerSigs(QObject):
    finished_ = pyqtSignal()
    progress_text = pyqtSignal(str)
    reload_gui = pyqtSignal()


class ScanerTask(URunnable):
    short_timer = 15000
    long_timer = Cfg.scaner_minutes * 60 * 1000

    def __init__(self):
        """
        Сигналы: finished_, progress_text(str), reload_gui, remove_all_win(MainWin)
        """
        super().__init__()
        self.sigs = ScanerSigs()
        self.pause_flag = False
        self.user_canceled_scan = False
        print("Выбран новый сканер")

    def task(self):
        for i in MainFolder.list_:
            if i.availability():
                print("scaner started", i.name)
                self.main_folder_scan(i)
                gc.collect()
                print("scaner finished", i.name)
            else:
                self.send_text(f"\"{i.name}\": {Lng.no_connection[Cfg.lng].lower()}")
                sleep(5)
        try:
            self.send_text("")
            self.sigs.finished_.emit()
        except RuntimeError as e:
            ...

    def main_folder_scan(self, main_folder: MainFolder):
        try:
            self._cmd(main_folder)
        except (Exception, AttributeError) as e:
            print("new scaner task, main folder scan error", e)

    def send_text(self, text: str):
        self.sigs.progress_text.emit(text)

    def _cmd(self, main_folder: MainFolder):
        coll_folder = main_folder.availability()
        if not coll_folder:
            print(main_folder.name, "coll folder not avaiable")
            return

        # удаляем все файлы и данные по удаленному MainFolder
        conn = Dbase.engine.connect()
        main_folder_remover = MainFolderRemover(conn)
        main_folder_remover.run()
        conn.close()

        # собираем Finder директории и базу данных
        dirs_loader = DirsLoader(main_folder, self.task_state)
        dirs_loader.progress_text.connect(self.send_text)
        finder_dirs = dirs_loader.finder_dirs()
        db_dirs = dirs_loader.db_dirs()
        if not finder_dirs or not self.task_state.should_run():
            print(main_folder.name, "no finder dirs")
            return

        # сравниваем Finder и БД директории
        new_dirs = DirsCompator.get_add_to_db_dirs(finder_dirs, db_dirs)
        del_dirs = DirsCompator.get_rm_from_db_dirs(finder_dirs, db_dirs)

        # например была удалена папка Collection 1, тогда все данные
        # в THUMBS и hadhdir будут удалены через ImgRemover
        conn = Dbase.engine.connect()
        img_remover = ImgRemover(del_dirs, main_folder, conn)
        img_remover.run()
        conn.close()

        # ищем изображения в новых (обновленных) директориях
        img_loader = ImgLoader(new_dirs, main_folder, self.task_state)
        img_loader.progress_text.connect(self.send_text)
        finder_images = img_loader.finder_images()
        db_images = img_loader.db_images()
        if not self.task_state.should_run():
            print(main_folder.name, "no finder images")
            return

        # сравниваем Finder и БД изображения
        img_compator = ImgCompator(finder_images, db_images)
        del_images, new_images = img_compator.run()

        # запрещаем удалять сразу все изображения относящиеся к папке
        conn = Dbase.engine.connect()
        inspector = Inspector(del_images, main_folder, conn)
        is_remove_all = inspector.is_remove_all()
        conn.close()
        if is_remove_all:
            print("scaner > обнаружена попытка массового удаления фотографий")
            print("в папке:", main_folder.name, main_folder.get_current_path())
            return

        # создаем / обновляем изображения в hashdir
        hashdir_updater = HashdirUpdater(del_images, new_images, self.task_state, main_folder)
        hashdir_updater.progress_text.connect(self.send_text)
        del_images, new_images = hashdir_updater.run()

        # обновляем БД
        conn = Dbase.engine.connect()
        db_updater = DbUpdater(del_images, new_images, main_folder, conn)
        db_updater.run()
        conn.close()

        if not self.task_state.should_run():
            self.sigs.reload_gui.emit()
            return

        # обновляем информацию о директориях в БД
        conn = Dbase.engine.connect()
        DirsUpdater.remove_db_dirs(conn, main_folder, del_dirs)
        DirsUpdater.add_new_dirs(conn, main_folder, new_dirs)
        conn.close()

        self.send_text("")
        if del_dirs or new_dirs:
            self.sigs.reload_gui.emit()
