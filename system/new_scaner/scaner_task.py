import gc
from time import sleep

from PyQt5.QtCore import QObject, QTimer, pyqtSignal

from cfg import JsonData

from ..database import Dbase
from ..lang import Lang
from ..main_folder import MainFolder
from ..utils import URunnable
from .scaner_utils import (DbUpdater, DirsCompator, DirsLoader, DirsUpdater,
                           HashdirUpdater, ImgCompator, ImgLoader, Inspector,
                           MainFolderRemover)


class ScanerSignals(QObject):
    finished_ = pyqtSignal()
    progress_text = pyqtSignal(str)
    reload_gui = pyqtSignal()


class ScanerTask(URunnable):
    short_timer = 15000
    long_timer = JsonData.scaner_minutes * 60 * 1000

    def __init__(self):
        """
        Сигналы: finished_, progress_text(str), reload_gui, remove_all_win(MainWin)
        """
        super().__init__()
        self.signals_ = ScanerSignals()
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
                t = f"{i.name}: {Lang.no_connection.lower()}"
                self.signals_.progress_text.emit(t)
                sleep(5)
            
        try:
            self.signals_.progress_text.emit("")
            self.signals_.finished_.emit()
        except RuntimeError as e:
            ...

    def main_folder_scan(self, main_folder: MainFolder):
        conn = Dbase.engine.connect()
        main_folder_remover = MainFolderRemover(conn)
        main_folder_remover.run()
        conn.close()

        coll_folder = main_folder.availability()
        if not coll_folder:
            print(main_folder.name, "coll folder not avaiable")
            return

        conn = Dbase.engine.connect()
        text = f"{main_folder.name.capitalize()}: {Lang.searching_updates.lower()}"
        self.signals_.progress_text.emit(text)
        args = (main_folder, self.task_state, conn)
        finder_dirs = DirsLoader.finder_dirs(*args)
        db_dirs = DirsLoader.db_dirs(*args)
        conn.close()
        if not finder_dirs or not self.task_state.should_run():
            print(main_folder.name, "no finder dirs")
            return

        args = (finder_dirs, db_dirs)
        new_dirs = DirsCompator.get_add_to_db_dirs(*args)
        del_dirs = DirsCompator.get_rm_from_db_dirs(*args)

        conn = Dbase.engine.connect()
        text = f"{main_folder.name.capitalize()}: {Lang.searching_images.lower()}"
        self.signals_.progress_text.emit(text)
        args = (new_dirs, main_folder, self.task_state, conn)
        finder_images = ImgLoader.finder_images(*args)
        db_images = ImgLoader.db_images(*args)
        conn.close()
        if not finder_images or not self.task_state.should_run():
            print(main_folder.name, "no finder images")
            return
        
        args = (finder_images, db_images)
        img_compator = ImgCompator(*args)
        del_images, new_images = img_compator.run()

        conn = Dbase.engine.connect()
        inspector = Inspector(del_images, main_folder, conn)
        is_remove_all = inspector.is_remove_all()
        conn.close()
        if is_remove_all:
            print("scaner > обнаружена попытка массового удаления фотографий")
            print("в папке:", main_folder.name, main_folder.get_current_path())
            return

        def text(hashdir_updater: HashdirUpdater):
            t = f"{Lang.updating_data} {Lang.izobrazhenii.lower()}: {hashdir_updater.total}"
            self.signals_.progress_text.emit(t)

        args = (del_images, new_images, main_folder, self.task_state)
        hashdir_updater = HashdirUpdater(*args)
        timer = QTimer(self)
        timer.timeout.connect(lambda: text(hashdir_updater))
        timer.start(100)
        del_images, new_images = hashdir_updater.run()
        timer.stop()

        conn = Dbase.engine.connect()
        db_updater = DbUpdater(del_images, new_images, main_folder, conn)
        db_updater.run()
        conn.close()

        if not self.task_state.should_run():
            self.signals_.reload_gui.emit()
            return

        conn = Dbase.engine.connect()
        args = (conn, main_folder, del_dirs, new_dirs)
        DirsUpdater.remove_db_dirs(*args)
        DirsUpdater.add_new_dirs(*args)
        conn.close()

        if del_images or new_images:
            self.signals_.reload_gui.emit()
