import os
from time import sleep

import sqlalchemy
from PyQt5.QtCore import QThread, QTimer
from watchdog.events import FileSystemEvent, PatternMatchingEventHandler
from watchdog.observers import Observer
from watchdog.observers.polling import PollingObserver

from cfg import cnf
from database import Dbase, ThumbsMd
from signals import gui_signals_app, utils_signals_app

from ..image_utils import BytesThumb, UndefBytesThumb
from ..main_utils import MainUtils


class Manager:
    flag = True
    observer_timeout = 5
    img_wait_time_sleep = 3
    img_wait_time_count = 2 * 60
    event_timer_timeout = 4 * 1000
    jpg_exsts = (".jpg", ".JPG", ".jpeg", ".JPEG", ".png", ".PNG")
    tiff_exsts = (".tiff", ".TIFF", ".psd", ".PSD", ".psb", ".PSB", ".tif", ".TIF")


class WaitWriteFinish:
    def __init__(self, src: str):
        flag = None
        current_timeout = 0

        while not flag:
            try:
                BytesThumb(src)
                current_timeout = 0
                flag = True

            except ZeroDivisionError as e:
                flag = None
                current_timeout += 1
                utils_signals_app.reset_event_timer_watcher.emit()

                sleep(Manager.img_wait_time_sleep)

                if current_timeout == Manager.img_wait_time_count:
                    break
                else:
                    continue


class MovedFile:
    def __init__(self, src: str, dest: str) -> None:
        coll = MainUtils.get_coll_name(dest)
        q = (
            sqlalchemy.update(ThumbsMd)
            .filter(ThumbsMd.src==src)
            .values({"src": dest, "collection": coll})
            )

        session = Dbase.get_session()
        try:
            session.execute(q)
            session.commit()
        finally:
            session.close()


class DeletedFile:
    def __init__(self, src: str):
        q = (sqlalchemy.delete(ThumbsMd)
             .filter(ThumbsMd.src==src))

        session = Dbase.get_session()
        try:
            session.execute(q)
            session.commit()
        finally:
            session.close()


class NewFile:
    def __init__(self, src: str):
        try:
            data = {"img150": BytesThumb(src).getvalue(),
                    "src": src,
                    "size": int(os.path.getsize(filename=src)),
                    "created": int(os.stat(path=src).st_birthtime),
                    "modified": int(os.stat(path=src).st_mtime),
                    "collection": MainUtils.get_coll_name(src)
                    }
            
        except FileNotFoundError:
            print("watcher > create thumb > file not found")
            return

        except Exception as e:
            print(f"wacher new file err {e}")
            data = {"img150": UndefBytesThumb().getvalue(),
                    "src": src,
                    "size": 666,
                    "created": 666,
                    "modified": 666,
                    "collection": "Errors"
                    }

        q = sqlalchemy.insert(ThumbsMd).values(data)

        session = Dbase.get_session()
        try:
            session.execute(q)
            session.commit()
        finally:
            session.close()


class Handler(PatternMatchingEventHandler):
    def __init__(self):
        dirs = [f"*/{i}/*" for i in cnf.stop_colls]
        super().__init__(ignore_directories=True, ignore_patterns=dirs)

    def on_any_event(self, event: FileSystemEvent) -> None:
        print(f"{event.event_type}: {event.src_path}")
        return super().on_any_event(event)

    def on_created(self, event: FileSystemEvent):
        if event.src_path.endswith(Manager.jpg_exsts):
            WaitWriteFinish(src=event.src_path)
            NewFile(src=event.src_path)
            utils_signals_app.reset_event_timer_watcher.emit()

        elif event.src_path.endswith(Manager.tiff_exsts):
            cnf.tiff_images.add(event.src_path)


    def on_deleted(self, event: FileSystemEvent):
        if event.src_path.endswith(Manager.jpg_exsts):
            DeletedFile(src=event.src_path)
            utils_signals_app.reset_event_timer_watcher.emit()

        elif event.src_path.endswith(Manager.tiff_exsts):
            try:
                cnf.tiff_images.remove(event.src_path)
            except KeyError:
                pass


    def on_moved(self, event: FileSystemEvent):
        if event.src_path.endswith(Manager.jpg_exsts):
            MovedFile(src=event.src_path, dest=event.dest_path)
            utils_signals_app.reset_event_timer_watcher.emit()

        elif event.src_path.endswith(Manager.tiff_exsts):
            try:
                cnf.tiff_images.remove(event.src_path)
            except KeyError:
                pass
            cnf.tiff_images.add(event.dest_path)


class WatcherThread(QThread):
    def __init__(self):
        super().__init__()
         
        self.event_timer = QTimer()
        self.event_timer.setSingleShot(True)
        self.event_timer.setInterval(Manager.event_timer_timeout)

        self.event_timer.timeout.connect(self.finished_event_timer)
        utils_signals_app.reset_event_timer_watcher.connect(self.reset_event_timer)

    def run(self):
        self.handler = Handler()
        self.observer = PollingObserver()

        # self.observer = Observer()
        Manager.flag = True

        self.observer.schedule(
            event_handler=self.handler,
            path=cnf.coll_folder,
            recursive=True
            )
        self.observer.start()

        try:
            while Manager.flag:
                sleep(Manager.observer_timeout)
        except KeyboardInterrupt:
            self.observer.stop()
            self.observer.join()
            print("watcher stoped")

        self.observer.stop()
        self.observer.join()
        print("watcher stoped")

    def reset_event_timer(self):
        self.event_timer.start()

    def finished_event_timer(self):
        gui_signals_app.reload_menu.emit()
        gui_signals_app.reload_thumbnails.emit()

    def clean_engine(self):
        Dbase.cleanup_engine()

    def stop_watcher(self):
        Manager.flag = False