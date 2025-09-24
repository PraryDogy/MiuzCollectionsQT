import gc
import os
from time import sleep

from PyQt5.QtCore import QObject, pyqtSignal

from cfg import Cfg

from ..lang import Lng
from ..main_folder import Mf
from ..tasks import URunnable
from ..utils import Utils
from .scaner_utils import (DirsCompator, DirsLoader, EmptyHashdirHandler,
                           NewDirsHandler, RemovedDirsHandler,
                           RemovedMfCleaner)


class ScanerTask(URunnable):

    class Sigs(QObject):
        finished_ = pyqtSignal()
        progress_text = pyqtSignal(str)
        reload_thumbnails = pyqtSignal()
        reload_menu = pyqtSignal()

    short_timer = 15000
    long_timer = Cfg.scaner_minutes * 60 * 1000

    def __init__(self):
        """
        Сигналы: finished_, progress_text(str), reload_gui, remove_all_win(MainWin)
        """
        super().__init__()
        self.sigs = ScanerTask.Sigs()
        self.pause_flag = False
        self.user_canceled_scan = False
        self.reload_gui_flag = False
        print("Выбран новый сканер")

    def task(self):
        for i in Mf.list_:
            if i.get_curr_path():
                print("scaner started", i.name)
                self.mf_scan(i)
                gc.collect()
                print("scaner finished", i.name)
            else:
                if i.curr_path:
                    true_name = os.path.basename(i.curr_path)
                else:
                    true_name = os.path.basename(i.paths[0])
                alias = i.name
                no_conn = Lng.no_connection[Cfg.lng].lower()
                self.sigs.progress_text.emit(f"{true_name} ({alias}): {no_conn}")
                print("scaner no connection", true_name, alias)
                sleep(5)
            try:
                if self.reload_gui_flag:
                    self.set_flag(False)
                    self.sigs.reload_menu.emit()
                    self.sigs.reload_thumbnails.emit()
            except RuntimeError as e:
                print("new scaner task error:", e)
        try:
            self.sigs.progress_text.emit("")
            self.sigs.finished_.emit()
        except RuntimeError as e:
            ...

    def set_flag(self, value: bool):
        self.reload_gui_flag = value

    def mf_scan(self, mf: Mf):
        try:
            self._mf_scan(mf)
        except (Exception, AttributeError) as e:
            print("new scaner task, main folder scan error", e)

    def _mf_scan(self, mf: Mf):
        # удаляем все файлы и данные из бД по удаленному Mf
        mf_remover = RemovedMfCleaner()
        deleted_mfs = mf_remover.run()
        if deleted_mfs:
            print("main folders deleted", deleted_mfs)
        
        empty_remover = EmptyHashdirHandler()
        empty_remover.reload_gui.connect(lambda: self.set_flag(True))
        empty_remover.run()

        # собираем Finder директории и директории из БД
        dirs_loader = DirsLoader(mf, self.task_state)
        dirs_loader.progress_text.connect(self.sigs.progress_text.emit)
        finder_dirs = dirs_loader.finder_dirs()
        db_dirs = dirs_loader.db_dirs()
        if not finder_dirs or not self.task_state.should_run():
            print(mf.name, "no finder dirs")
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
            self.set_flag(True)
            scan_dirs = NewDirsHandler(new_dirs, mf, self.task_state)
            scan_dirs.progress_text.connect(self.sigs.progress_text.emit)
            scan_dirs.run()
        
        # удаляем удаленные Finder директории
        if removed_dirs:
            self.set_flag(True)
            del_handler = RemovedDirsHandler(removed_dirs, mf)
            del_handler.run()


class _CustomScanerSigs(QObject):
    reload_thumbnails = pyqtSignal()
    progress_text = pyqtSignal(str)


class CustomScanerTask(URunnable):
    def __init__(self, mf: Mf, dirs_to_scan: list[str]):
        """
        Аналог полноценного сканера, но принимает список директорий
        и выполняет сканирование для каждой из них в пределах Mf.   
        dirs: [abs dir path, ...]
        """
        super().__init__()
        self.sigs = _CustomScanerSigs()
        self.mf = mf
        self.dirs_to_scan = dirs_to_scan
        
    def task(self):
        dirs_to_scan = (
            (i, int(os.stat(i).st_mtime))
            for i in self.dirs_to_scan
        )
        dirs_to_scan = [
            (Utils.get_rel_path(self.mf.curr_path, abs_path), st_mtime)
            for abs_path, st_mtime in dirs_to_scan
        ]
        
        scan_dirs = NewDirsHandler(dirs_to_scan, self.mf, self.task_state)
        scan_dirs.progress_text.connect(self.sigs.progress_text.emit)
        del_images, new_images = scan_dirs.run()

        if del_images or new_images:
            self.sigs.reload_thumbnails.emit()