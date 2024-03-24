import os
from time import sleep

import sqlalchemy
from PyQt5.QtCore import QThread, QTimer, QObject
from watchdog.events import FileSystemEvent, PatternMatchingEventHandler
from watchdog.observers.polling import PollingObserver

from cfg import cnf
from database import Dbase, ThumbsMd
from signals import gui_signals_app, utils_signals_app

from ..image_utils import BytesThumb, UndefBytesThumb
from ..main_utils import MainUtils


class Manager:
    jpg_exsts = (".jpg", ".JPG", ".jpeg", ".JPEG", ".png", ".PNG")
    tiff_exsts = (".tiff", ".TIFF", ".psd", ".PSD", ".psb", ".PSB", ".tif", ".TIF")

    @staticmethod
    def smb_connected():
        if not os.path.exists(cnf.coll_folder):
            print("smb deleted")
            utils_signals_app.watcher_stop.emit()
            utils_signals_app.watcher_start.emit()
            return False
        return True


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
                sleep(3)

                if current_timeout == 60: # wait image ... sec
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

        dirs = [
            f"*/{i}/*"
            for i in cnf.stop_colls
            ]

        super().__init__(
            # ignore_directories=True,
            ignore_patterns=dirs
            )

    def on_created(self, event: FileSystemEvent):
        if not Manager.smb_connected():
            return
        
        elif event.is_directory:
            return

        elif event.src_path.endswith(Manager.jpg_exsts):
            WaitWriteFinish(src=event.src_path)
            NewFile(src=event.src_path)

        elif event.src_path.endswith(Manager.tiff_exsts):
            cnf.tiff_images.add(event.src_path)

        utils_signals_app.watcher_timer.emit()
        print(event)

    def on_deleted(self, event: FileSystemEvent):
        if not Manager.smb_connected():
            return
        
        elif event.is_directory:
            return

        if event.src_path.endswith(Manager.jpg_exsts):
            DeletedFile(src=event.src_path)

        elif event.src_path.endswith(Manager.tiff_exsts):
            try:
                cnf.tiff_images.remove(event.src_path)
            except KeyError:
                pass

        utils_signals_app.watcher_timer.emit()
        print(event)

    def on_moved(self, event: FileSystemEvent):
        if not Manager.smb_connected():
            return
        
        elif event.is_directory:
            return

        if event.src_path.endswith(Manager.jpg_exsts):
            MovedFile(src=event.src_path, dest=event.dest_path)

        elif event.src_path.endswith(Manager.tiff_exsts):
            try:
                cnf.tiff_images.remove(event.src_path)
            except KeyError:
                pass
            cnf.tiff_images.add(event.dest_path)

        utils_signals_app.watcher_timer.emit()
        print(event)


class WatcherThread(QThread):
    def __init__(self):
        super().__init__()

        self.event_timer = QTimer()
        self.event_timer.setSingleShot(True)
        self.event_timer.setInterval(5000)
        self.event_timer.timeout.connect(self.reload_gui)
        utils_signals_app.watcher_timer.connect(self.reset_event_timer)

    def run(self):
        self.flag = True
        self.handler = Handler()
        self.observer = PollingObserver()

        self.observer.schedule(
            event_handler=self.handler,
            path=cnf.coll_folder,
            recursive=True
            )
        self.observer.start()

        try:
            while self.flag:
                sleep(cnf.watcher_timeout)
        except KeyboardInterrupt:
            self.observer.stop()

        self.observer.join()
        print("watcher stoped")

    def stop_watcher(self):
        self.flag = False
        self.observer.stop()
        Dbase.cleanup_engine()

    def reload_gui(self):
        gui_signals_app.reload_menu.emit()
        gui_signals_app.reload_thumbnails.emit()

    def reset_event_timer(self):
        self.event_timer.stop()
        self.event_timer.start()