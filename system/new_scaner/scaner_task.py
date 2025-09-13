import gc
import os
from time import sleep

from PyQt5.QtCore import QObject, pyqtSignal

from cfg import Cfg

from ..lang import Lng
from ..main_folder import MainFolder
from ..utils import URunnable
from .scaner_utils import (DirsCompator, DirsLoader, EmptyHashdirHandler,
                           RemovedMainFolderHandler, NewDirsHandler,
                           RemovedDirsHandler)


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
            if i.get_curr_path():
                print("scaner started", i.name)
                self.main_folder_scan(i)
                gc.collect()
                print("scaner finished", i.name)
            else:
                if i.curr_path:
                    true_name = os.path.basename(i.curr_path)
                else:
                    true_name = os.path.basename(i.paths[0])
                alias = i.name
                no_conn = Lng.no_connection[Cfg.lng].lower()
                self.send_text(f"{true_name} ({alias}): {no_conn}")
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
        coll_folder = main_folder.get_curr_path()
        if not coll_folder:
            print(main_folder.name, "coll folder not avaiable")
            return

        # удаляем все файлы и данные из бД по удаленному MainFolder
        main_folder_remover = RemovedMainFolderHandler()
        main_folder_remover.run()
        
        empty_remover = EmptyHashdirHandler()
        empty_remover.run()

        # собираем Finder директории и директории из БД
        dirs_loader = DirsLoader(main_folder, self.task_state)
        dirs_loader.progress_text.connect(self.send_text)
        finder_dirs = dirs_loader.finder_dirs()
        db_dirs = dirs_loader.db_dirs()
        if not finder_dirs or not self.task_state.should_run():
            print(main_folder.name, "no finder dirs")
            return

        # сравниваем кортежи (директория, дата изменения)
        # new_dirs: директории, которые нужно просканировать на изображения
        # и обновить в БД данные об изображениях и о директориях
        # del_dirs: директории, которых были удалены в Finder, то 
        # есть когда была удалена папка целиком
        new_dirs = DirsCompator.get_dirs_to_scan(finder_dirs, db_dirs)
        removed_dirs = DirsCompator.get_dirs_to_remove(finder_dirs, db_dirs)
        
        # обходим новые директории, добавляем / удаляем изображения
        if new_dirs:
            scan_dirs = NewDirsHandler(new_dirs, main_folder, self.task_state)
            scan_dirs.progress_text.connect(self.sigs.progress_text.emit)
            scan_dirs.run()
            self.sigs.reload_gui.emit()
        
        # удаляем удаленные Finder директории
        if removed_dirs:
            del_handler = RemovedDirsHandler(removed_dirs, main_folder)
            del_handler.run()
