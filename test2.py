import os
from time import sleep

import sqlalchemy
from PyQt5.QtCore import QObject, QThread, QTimer
from watchdog.events import (FileSystemEvent, FileSystemEventHandler,
                             LoggingEventHandler)
from watchdog.observers import Observer
from watchdog.observers.polling import PollingObserver

from cfg import cnf
from database import Dbase, ThumbsMd
from signals import gui_signals_app, utils_signals_app


class Manager:
    jpg_exsts = (".jpg", ".JPG", ".jpeg", ".JPEG", ".png", ".PNG")
    tiff_exsts = (".tiff", ".TIFF", ".psd", ".PSD", ".psb", ".PSB", ".tif", ".TIF")
    curr_percent = 0
    progressbar_len = 50
    flag = True

    stop_colls: list = [
        "001 Test_1",
        ]
    
    @staticmethod
    def is_good_file(event: FileSystemEvent):
        if event.is_directory:
             return False
        for i in [os.sep + i + os.sep for i in Manager.stop_colls]:
            if i in event.src_path:
                return False
        return True
        

class Handler(FileSystemEventHandler):
    def on_any_event(self, event: FileSystemEvent) -> None:
        # print(f"{event.event_type}: {event.src_path}")
        return super().on_any_event(event)

    def on_created(self, event: FileSystemEvent):
        if not Manager.is_good_file(event):
            return

        if event.src_path.endswith(Manager.jpg_exsts):
            print("created jpg")
            
        elif event.src_path.endswith(Manager.tiff_exsts):
            print("created tiff")


    def on_deleted(self, event: FileSystemEvent):
        if not Manager.is_good_file(event):
            return

        if event.src_path.endswith(Manager.jpg_exsts):
            print("deleted jpg")

        elif event.src_path.endswith(Manager.tiff_exsts):
            print("deleted jpg")


    def on_moved(self, event):
        if not Manager.is_good_file(event):
            return

        if event.src_path.endswith(Manager.jpg_exsts):
            print("moved jpg")

        elif event.src_path.endswith(Manager.tiff_exsts):
            print("moved jpg")



handler = Handler()
observer = PollingObserver()
# self.observer = Observer()
Manager.flag = True

observer.schedule(
    event_handler=handler,
    path="/Volumes/Shares/Marketing/Photo/2024/01 - Январь/Test gallert",
    recursive=True
    )
observer.start()

try:
    while Manager.flag:
        sleep(1)
except KeyboardInterrupt:
    observer.stop()
    observer.join()

observer.stop()
observer.join()