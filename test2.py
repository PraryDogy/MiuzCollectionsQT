import os
from time import sleep

from watchdog.events import FileSystemEvent, PatternMatchingEventHandler
from watchdog.observers.polling import PollingObserver


class Manager:
    src = "/Volumes/Files"
    flag = True


def smb_connected():
    if not os.path.exists(Manager.src):
        print("deleted")
        Manager.flag = False
        return False
    return True


class Handler(PatternMatchingEventHandler):
    def __init__(self, observer: PollingObserver):
        self.observer: PollingObserver = observer

        dirs = [
            f"*/{i}/*"
            for i in ("001 Test_1", "002 Test_2")
            ]

        super().__init__(
            # ignore_directories=True,
            ignore_patterns=dirs
            )

    def on_created(self, event: FileSystemEvent):
        if not smb_connected():
            self.observer.stop()
            return
        print("created:\n", event)

    def on_deleted(self, event: FileSystemEvent):
        if not smb_connected():
            self.observer.stop()
            return
        print("deleted:\n", event)


    def on_moved(self, event):
        if not smb_connected():
            self.observer.stop()
            return
        print("moved:\n", event)


observer = PollingObserver()
handler = Handler(observer)


observer.schedule(
    event_handler=handler,
    path=Manager.src,
    recursive=True,
    )
observer.start()

try:
    while Manager.flag:
        sleep(1)
except KeyboardInterrupt:
    observer.stop()
observer.join()

print("end watchdog")