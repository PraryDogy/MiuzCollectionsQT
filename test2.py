import os
from time import sleep

import sqlalchemy
from PyQt5.QtCore import QThread, QTimer, QObject
from watchdog.events import FileSystemEvent, PatternMatchingEventHandler
from watchdog.observers.polling import PollingObserver

from cfg import cnf
from database import Dbase, ThumbsMd
from signals import gui_signals_app, utils_signals_app

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
    
    @staticmethod
    def is_stop_dir(src: str, stop_dirs: list):
        for i in stop_dirs:
            if i in src:
                return True
        return False


class Handler(PatternMatchingEventHandler):
    def __init__(self):

        self.stop_dirs = [
            os.path.join(cnf.coll_folder, i)
            for i in cnf.stop_colls
            ]

        super().__init__()

    def on_created(self, event: FileSystemEvent):
        if not Manager.smb_connected():
            return
        
        elif event.is_directory:
            return
        
        elif Manager.is_stop_dir(event.src_path, self.stop_dirs):
            return

        elif event.src_path.endswith(Manager.jpg_exsts):
            ...

        elif event.src_path.endswith(Manager.tiff_exsts):
            ...

        print(event)

    def on_deleted(self, event: FileSystemEvent):
        if not Manager.smb_connected():
            return
        
        elif event.is_directory:
            return

        elif Manager.is_stop_dir(event.src_path, self.stop_dirs):
            return

        elif event.src_path.endswith(Manager.jpg_exsts):
            ...

        elif event.src_path.endswith(Manager.tiff_exsts):
            ...

        print(event)

    def on_moved(self, event: FileSystemEvent):
        if not Manager.smb_connected():
            return
        
        elif event.is_directory:
            return

        elif Manager.is_stop_dir(event.src_path, self.stop_dirs):
            return

        elif event.src_path.endswith(Manager.jpg_exsts):
            ...

        elif event.src_path.endswith(Manager.tiff_exsts):
            ...

        print(event)


class WatcherThread(object):
    def __init__(self):
        super().__init__()

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


a = WatcherThread()
a.run()