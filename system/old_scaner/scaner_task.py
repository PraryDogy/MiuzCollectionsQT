import gc
from time import sleep

from PyQt5.QtCore import QObject, pyqtSignal

from cfg import Cfg

from ..lang import Lng
from ..main_folder import Mf
from ..tasks import URunnable
from .scaner_utils import (Compator, DbImages, DbUpdater, FinderImages,
                           HashdirUpdater, Inspector, MfRemover)


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
        print("Выбран старый сканер")

    def task(self):
        for i in Mf.list_:
            if i.set_curr_path():
                print("scaner started", i.name)
                self.mf_scan(i)
                gc.collect()
                print("scaner finished", i.name)
            else:
                t = f"{i.name}: {Lng.no_connection[Cfg.lng].lower()}"
                self.sigs.progress_text.emit(t)
                sleep(5)
            
        try:
            self.sigs.finished_.emit()
        except RuntimeError as e:
            ...
    
    def mf_scan(self, mf: Mf):
        """
        Выполняет полную синхронизацию содержимого указанной папки Mf
        с базой данных и директориями миниатюр (hashdir).

        Этапы выполнения:

        1. **MfRemover**
        - Если папка Mf была удалена, удаляются:
            - Все связанные записи в базе данных.
            - Все соответствующие миниатюры из hashdir.
        - После этого работа метода завершается.

        2. **FinderImages**
        - Выполняет рекурсивный поиск изображений в Mf.
        - Результаты будут использоваться для сравнения с базой данных.

        3. **Проверка can_scan**
        - Если флаг `can_scan` (из ScanerHelper) равен False, синхронизация
            прерывается сразу после поиска (FinderImages).

        4. **DbImages**
        - Загружает из базы все записи, связанные с текущим Mf.

        5. **Compator**
        - Сравнивает изображения, найденные в файловой системе, с записями в БД.
        - Формирует два списка:
            - `del_items`: устаревшие записи и файлы для удаления.
            - `new_items`: новые изображения, которых нет в БД.

        6. **FileUpdater**
        - Удаляет устаревшие миниатюры и создает новые в hashdir.
        - Может быть прерван по флагу `can_scan`; возвращает только 
            успешно обработанные элементы.

        7. **DbUpdater**
        - Обновляет базу данных на основе результатов FileUpdater:
            - Удаляет старые записи.
            - Добавляет новые записи о миниатюрах.

        Прерывание по `can_scan`:
        - Если прервано на этапе FinderImages — дальнейшие шаги (3–7) не выполняются.
        - Если прервано во время FileUpdater — DbUpdater всё равно выполнит частичное обновление, 
        основываясь на уже обработанных файлах.
        """

        mf_remover = MfRemover()
        mf_remover.progress_text.connect(lambda text: self.sigs.progress_text.emit(text))
        mf_remover.run()

        finder_images = FinderImages(mf, self.task_state)
        finder_images.progress_text.connect(lambda text: self.sigs.progress_text.emit(text))
        finder_images = finder_images.run()
        if finder_images and self.task_state.should_run():
            db_images = DbImages(mf)
            db_images.progress_text.connect(lambda text: self.sigs.progress_text.emit(text))
            db_images = db_images.run()
            compator = Compator(finder_images, db_images)
            del_items, new_items = compator.run()

            inspector = Inspector(del_items, mf)
            is_remove_all = inspector.is_remove_all()
            if is_remove_all:
                print("scaner > обнаружена попытка массового удаления фотографий")
                print("в папке:", mf.name, mf.curr_path)
                return

            file_updater = HashdirUpdater(del_items, new_items, mf, self.task_state)
            file_updater.progress_text.connect(lambda text: self.sigs.progress_text.emit(text))
            del_items, new_items = file_updater.run()
            db_updater = DbUpdater(del_items, new_items, mf)
            db_updater.reload_gui.connect(lambda: self.sigs.reload_gui.emit())
            db_updater.run()
